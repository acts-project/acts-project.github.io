#!/usr/bin/env python3
"""
Multi-version documentation deployment script.

Determines deployment target based on git ref and maintains a versions index.
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Optional


def parse_git_ref(ref: str) -> tuple[str, str]:
    """
    Parse a git ref to determine version type and name.

    Returns:
        Tuple of (version_type, version_name) where version_type is 'tag', 'branch', or 'unknown'
    """
    if ref.startswith("refs/tags/"):
        return ("tag", ref.removeprefix("refs/tags/"))
    elif ref.startswith("refs/heads/"):
        return ("branch", ref.removeprefix("refs/heads/"))
    else:
        # Might be a short ref like 'main' or 'v1.2.3'
        return ("unknown", ref)


def normalize_version(version: str) -> str:
    """
    Normalize version string for folder naming.

    Strips leading 'v' if present for consistency.
    """
    return version.lstrip("v")


def get_target_folder(ref_type: str, ref_name: str, main_branch: str = "main") -> str:
    """
    Determine the target folder for deployment.

    - main branch -> root (empty string for target-folder)
    - tags -> v{version}/
    """
    if ref_type == "branch" and ref_name == main_branch:
        return ""  # Deploy to root
    elif ref_type == "tag":
        version = normalize_version(ref_name)
        return f"v{version}"
    elif ref_type == "unknown" and ref_name == main_branch:
        return ""
    elif ref_type == "unknown":
        # Assume it's a version tag
        version = normalize_version(ref_name)
        return f"v{version}"
    else:
        # Other branches - deploy to branch name folder
        safe_name = re.sub(r"[^a-zA-Z0-9._-]", "-", ref_name)
        return safe_name


def load_versions_index(index_path: Path) -> dict:
    """Load existing versions index or create empty one."""
    if index_path.exists():
        with open(index_path) as f:
            return json.load(f)
    return {"versions": [], "main": None, "generated_at": None}


def update_versions_index(
    index_path: Path,
    ref_type: str,
    ref_name: str,
    target_folder: str,
    main_branch: str = "main",
) -> dict:
    """
    Update the versions index with new deployment info.

    Returns the updated index.
    """
    index = load_versions_index(index_path)
    now = datetime.now(timezone.utc).isoformat()

    if ref_type == "branch" and ref_name == main_branch:
        index["main"] = {
            "path": ".",
            "updated_at": now,
        }
    elif ref_type == "tag" or (ref_type == "unknown" and ref_name != main_branch):
        version = normalize_version(ref_name)
        version_entry = {
            "version": version,
            "path": target_folder,
            "tag": ref_name,
            "deployed_at": now,
        }

        # Update or add version entry
        existing_versions = {v["version"]: i for i, v in enumerate(index["versions"])}
        if version in existing_versions:
            index["versions"][existing_versions[version]] = version_entry
        else:
            index["versions"].append(version_entry)

        # Sort versions by semver (descending)
        index["versions"].sort(key=lambda v: parse_semver(v["version"]), reverse=True)

    index["generated_at"] = now
    return index


def parse_semver(version: str) -> tuple:
    """
    Parse semver string for sorting.

    Returns tuple for comparison, handling non-semver gracefully.
    """
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-(.+))?", version)
    if match:
        major, minor, patch, prerelease = match.groups()
        # Prerelease versions sort before release versions
        pre_sort = (0, prerelease) if prerelease else (1, "")
        return (int(major), int(minor), int(patch), pre_sort)
    # Fallback for non-semver: sort alphabetically at the end
    return (0, 0, 0, (0, version))


def save_versions_index(index_path: Path, index: dict) -> None:
    """Save versions index to file."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)
        f.write("\n")


def deploy_docs(
    source_dir: Path,
    deploy_dir: Path,
    target_folder: str,
) -> Path:
    """
    Deploy documentation to target folder.

    Returns the path where docs were deployed.
    """
    if target_folder:
        target_path = deploy_dir / target_folder
    else:
        target_path = deploy_dir

    # Clean target directory if it exists (for updates)
    if target_path.exists():
        shutil.rmtree(target_path)

    target_path.mkdir(parents=True, exist_ok=True)

    # Copy all files from source to target
    for item in source_dir.iterdir():
        dest = target_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    return target_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deploy documentation with multi-version support"
    )
    parser.add_argument(
        "--ref",
        required=True,
        help="Git ref (e.g., refs/tags/v1.2.3 or refs/heads/main)",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        required=True,
        help="Directory containing documentation to deploy",
    )
    parser.add_argument(
        "--deploy-dir",
        type=Path,
        required=True,
        help="Root directory for deployed documentation",
    )
    parser.add_argument(
        "--main-branch",
        default="main",
        help="Name of the main branch (default: main)",
    )
    parser.add_argument(
        "--index-file",
        type=Path,
        default=None,
        help="Path to versions index JSON file (default: deploy-dir/versions.json)",
    )
    parser.add_argument(
        "--output-target-folder",
        action="store_true",
        help="Only output the target folder path (for CI integration)",
    )

    args = parser.parse_args()

    ref_type, ref_name = parse_git_ref(args.ref)
    target_folder = get_target_folder(ref_type, ref_name, args.main_branch)

    # If only outputting target folder, print and exit
    if args.output_target_folder:
        print(target_folder)
        return 0

    # Validate source directory
    if not args.source_dir.exists():
        print(f"Error: Source directory does not exist: {args.source_dir}", file=sys.stderr)
        return 1

    # Determine index file path
    index_path = args.index_file or (args.deploy_dir / "versions.json")

    # Deploy documentation
    print(f"Deploying {ref_type} '{ref_name}' to '{target_folder or '(root)'}'")
    deployed_path = deploy_docs(args.source_dir, args.deploy_dir, target_folder)
    print(f"Documentation deployed to: {deployed_path}")

    # Update versions index
    index = update_versions_index(
        index_path, ref_type, ref_name, target_folder, args.main_branch
    )
    save_versions_index(index_path, index)
    print(f"Updated versions index: {index_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

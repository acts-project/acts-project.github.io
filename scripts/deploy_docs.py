# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "typer>=0.9.0",
#     "rich>=13.0.0",
#     "pydantic>=2.0.0",
# ]
# ///
"""Multi-version documentation deployment script."""

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

import typer
from pydantic import BaseModel
from rich import print as rprint
from rich.console import Console

console = Console()
app = typer.Typer()


class MainBranchInfo(BaseModel):
    path: str = "."
    updated_at: str


class VersionEntry(BaseModel):
    version: str
    path: str
    tag: str
    deployed_at: str


class VersionsIndex(BaseModel):
    versions: list[VersionEntry] = []
    main: MainBranchInfo | None = None
    generated_at: str | None = None

    @classmethod
    def load(cls, path: Path) -> "VersionsIndex":
        if path.exists():
            return cls.model_validate_json(path.read_text())
        return cls()

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2) + "\n")


RefType = Literal["tag", "branch", "unknown"]


def parse_git_ref(ref: str) -> tuple[RefType, str]:
    """Parse a git ref to determine version type and name."""
    if ref.startswith("refs/tags/"):
        return ("tag", ref.removeprefix("refs/tags/"))
    elif ref.startswith("refs/heads/"):
        return ("branch", ref.removeprefix("refs/heads/"))
    else:
        return ("unknown", ref)


def normalize_version(version: str) -> str:
    """Normalize version string, stripping leading 'v' if present."""
    return version.lstrip("v")


def parse_semver(version: str) -> tuple:
    """Parse semver string for sorting."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-(.+))?", version)
    if match:
        major, minor, patch, prerelease = match.groups()
        pre_sort = (0, prerelease) if prerelease else (1, "")
        return (int(major), int(minor), int(patch), pre_sort)
    return (0, 0, 0, (0, version))


def get_target_folder(ref_type: RefType, ref_name: str, main_branch: str) -> str:
    """Determine the target folder for deployment."""
    if ref_type == "branch" and ref_name == main_branch:
        return ""
    elif ref_type == "tag":
        return f"tags/v{normalize_version(ref_name)}"
    elif ref_type == "unknown" and ref_name == main_branch:
        return ""
    elif ref_type == "unknown":
        return f"tags/v{normalize_version(ref_name)}"
    else:
        return re.sub(r"[^a-zA-Z0-9._-]", "-", ref_name)


def deploy_docs(source_dir: Path, deploy_dir: Path, target_folder: str) -> Path:
    """Deploy documentation to target folder."""
    target_path = deploy_dir / target_folder if target_folder else deploy_dir

    if target_path.exists():
        shutil.rmtree(target_path)

    target_path.mkdir(parents=True, exist_ok=True)

    for item in source_dir.iterdir():
        dest = target_path / item.name
        if item.is_dir():
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    return target_path


def update_index(
    index: VersionsIndex,
    ref_type: RefType,
    ref_name: str,
    target_folder: str,
    main_branch: str,
) -> VersionsIndex:
    """Update the versions index with new deployment info."""
    now = datetime.now(timezone.utc).isoformat()

    if ref_type == "branch" and ref_name == main_branch:
        index.main = MainBranchInfo(updated_at=now)
    elif ref_type == "tag" or (ref_type == "unknown" and ref_name != main_branch):
        version = normalize_version(ref_name)
        entry = VersionEntry(
            version=version,
            path=target_folder,
            tag=ref_name,
            deployed_at=now,
        )

        existing = {v.version: i for i, v in enumerate(index.versions)}
        if version in existing:
            index.versions[existing[version]] = entry
        else:
            index.versions.append(entry)

        index.versions.sort(key=lambda v: parse_semver(v.version), reverse=True)

    index.generated_at = now
    return index


@app.command()
def deploy(
    ref: Annotated[str, typer.Option(help="Git ref (e.g., refs/tags/v1.2.3 or refs/heads/main)")],
    source_dir: Annotated[Path, typer.Option(help="Directory containing documentation to deploy")],
    deploy_dir: Annotated[Path, typer.Option(help="Root directory for deployed documentation")],
    main_branch: Annotated[str, typer.Option(help="Name of the main branch")] = "main",
    index_file: Annotated[Path | None, typer.Option(help="Path to versions index JSON file")] = None,
    output_target_folder: Annotated[bool, typer.Option(help="Only output the target folder path")] = False,
) -> None:
    """Deploy documentation with multi-version support."""
    ref_type, ref_name = parse_git_ref(ref)
    target_folder = get_target_folder(ref_type, ref_name, main_branch)

    if output_target_folder:
        print(target_folder)
        raise typer.Exit()

    if not source_dir.exists():
        rprint(f"[red]Error:[/red] Source directory does not exist: {source_dir}")
        raise typer.Exit(1)

    index_path = index_file or (deploy_dir / "versions.json")

    rprint(f"[blue]Deploying[/blue] {ref_type} [bold]{ref_name}[/bold] to [green]{target_folder or '(root)'}[/green]")
    deployed_path = deploy_docs(source_dir, deploy_dir, target_folder)
    rprint(f"[green]Documentation deployed to:[/green] {deployed_path}")

    index = VersionsIndex.load(index_path)
    index = update_index(index, ref_type, ref_name, target_folder, main_branch)
    index.save(index_path)
    rprint(f"[green]Updated versions index:[/green] {index_path}")


if __name__ == "__main__":
    app()

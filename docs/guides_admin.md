## <a name="admin-corner">Administrator's corner</a>

This section gives useful information to the administrators of the Acts
project. For normal developers the sections below are irrelevant.

### <a name="tag-release">Make a new Acts release</a>

In order to release a new version of Acts the following steps need to be taken:

1. Check out all open issues and MRs associated with the *milestone* that you want to tag
   [here](https://gitlab.cern.ch/acts/acts-core/milestones).
2. Merge master into the `release` branch.
3. In that branch, change the content of the file `version_number` at the repository
   root to the new version `X.Y.Z` and commit.
4. Pushing this commit to the remote repository should trigger a CI build. Make
   sure that everything compiles without any warnings and all tests look fine.
5. Create a new annotated tag locally. The tag should have the format
   `vX.YY.ZZ` and an associated tag message 'version vX.YY.ZZ' and should point to the
   commit created in step 3.
6. Push the tag to the remote repository. This should trigger a CI job which
   rebuilds to documentation and deploys it to the Acts webpage. Make sure that 
   the new release appears
   under the **Releases** section on the [Acts webpage](http://acts.web.cern.ch/ACTS/).
7. If there is not yet a *milestone* for the next release, create it in 
   [Gitlab](https://gitlab.cern.ch/acts/acts-core/milestones) 
   (e.g. if 1.23.02 was just released, a *milestone* version 1.23.03 should exist
   for the next minor release for bug fixes).
8. Check that the release notes appear on the release's page on GitLab under:
   `https://gitlab.cern.ch/acts/acts-core/tags/vX.YY.ZZ` after the post-merge CI
   jobs have completed.


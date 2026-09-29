# Upload this repository to GitHub

Upload only this repository directory, not its parent research workspace.
It is already initialized with branch `main`; no commit or remote exists yet.

## 1. Install Git LFS

Certificate storage is approximately 2.34 GB. The included `.gitattributes`
already selects these files for Git LFS. If you use Homebrew on macOS:

```sh
brew install git-lfs
```

Otherwise follow [GitHub's Git LFS installation instructions](https://docs.github.com/en/repositories/working-with-files/managing-large-files/installing-git-large-file-storage).
Install it **before** running `git add`.

Git LFS keeps a local object cache when files are staged, so allow roughly
another 2.4 GB of free disk space plus a margin for Git's own files. GitHub LFS
storage and downloads also use the repository owner's account allowance;
check [your LFS quota and billing settings](https://docs.github.com/en/billing/concepts/product-billing/git-lfs).

## 2. Choose the public commit identity

Open [GitHub Settings → Emails](https://github.com/settings/emails), enable
email privacy and copy the exact GitHub-provided `noreply` address. The name
and email stored in Git commits are public when the repository is public.
A public display name or pseudonym can be used; it need not be your legal name.
Your GitHub account remains visible as the repository owner.

In Terminal, change into this repository directory. Then run the following,
replacing both placeholders with the identity you want published:

```sh
git lfs install --local
git config --local user.name "YOUR_PUBLIC_DISPLAY_NAME"
git config --local user.email "YOUR_GITHUB_NOREPLY_EMAIL"
git var GIT_AUTHOR_IDENT
git var GIT_COMMITTER_IDENT
```

Check the two identities before continuing. These settings apply only to this
repository and override ordinary global Git identity settings. If the displayed
identity is unexpected, fix it before committing. See [GitHub's commit-email
guide](https://docs.github.com/en/account-and-profile/how-tos/email-preferences/setting-your-commit-email-address).

## 3. Create an empty GitHub repository

Go to [github.com/new](https://github.com/new), choose a repository name and
visibility, and leave README, license and `.gitignore` initialization unchecked.
Copy its HTTPS repository URL after creation.

## 4. Commit and upload

From the local repository directory:

```sh
git add .
git lfs ls-files
git status --short
git commit -m "Publish proposed eleven-square proof and certificates"
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the remote URL with the one you copied. The LFS listing should contain
`data/objects/` certificate files. If it is empty, stop before committing and
check that Git LFS was installed. Use your configured GitHub authentication;
if necessary, see [GitHub command-line authentication](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github).

These steps follow [GitHub's existing-project upload guide](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github).

See [the privacy review](PRIVACY_REVIEW.md) for the cleanup scope.

## What is excluded

`.gitignore` excludes generated workspaces, composition-check workspaces,
virtual environments, Python caches, logs, environment files and temporary
partial outputs. No prior author history is present. Publish through Git;
there is no need to upload a ZIP of the enclosing workspace.

For later revisions, run `python3 -B VERIFY.py --check-package` before committing
and review `git status --short`. That command checks package integrity and
privacy patterns, not mathematical proof soundness.

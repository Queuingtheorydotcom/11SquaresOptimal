# Privacy review of the publication

The publication was reviewed at both levels: ordinary repository files and the
decompressed certificate payloads. Filenames, browsable source, supporting prose,
Git exclusions and the local Git metadata were also inspected.

The final scan covered **3,677 publishable files**, including **2,638 compressed
payloads** (about 11.3 GB after decoding). It found no private account/device
identifiers, actual email addresses, network addresses or credential patterns.
The email-like matches were Python matrix-multiplication expressions; the
remaining path-like match was the privacy scanner’s own detection expression.
All were inspected. No unindexed compressed payloads were present.

The cleanup removes private workstation/home paths, private project and temporary
directory identifiers, conversation quotations, and references to personal
execution approvals and CPU preferences. The corresponding certificate/source
hashes and file-length bindings were updated; the final composition check still
accepts the same mathematical case sets. This was not a new full geometry replay.

Public upstream attribution and copyright/license notices remain. These include
published authors' names and project pseudonyms. They are intentional scholarly
credits, not leaked private device information.

There is no prior Git commit history, stored remote, or Git object history in
this prepared repository. Generated workspaces and environments are excluded
at the repository root. Source directories whose historical names include
`work` remain publishable; they contain verification code, not local run output.

Before the first commit, explicitly choose the public display name and GitHub
`noreply` email described in [UPLOAD.md](UPLOAD.md). Future commits and the GitHub
account used to host the repository introduce their own public identity metadata.
The file cleanup cannot choose that identity for you.

Privacy review combines exact known-identifier checks, common secret/address
patterns and manual inspection. It does not promise perfect detection of every
possible identifying inference. `python3 -B VERIFY.py --check-package` repeats
the included integrity and private-identifier checks; it is not a proof verifier.

---
name: release-evidence
description: Check a packaged Nav Center DMG against the distribution gates and report which are met, unmet, or impossible to establish locally. Use before publishing a beta artifact, tagging a release, or answering whether a build is distributable.
disable-model-invocation: true
---

# Release evidence

`docs/RELEASE.md` and `docs/PUBLIC_RELEASE_CHECKLIST.md` define gates that are
easy to claim and tedious to verify: Developer ID signing, an `Accepted` notary
result, stapling, Gatekeeper acceptance, checksum agreement with the published
sidecar, and the absolute rule that an `-unsigned.dmg` is never distributable.
Source-only CI and the offline dependency-stub tests establish none of them.

## Usage

```sh
bash .claude/skills/release-evidence/verify-artifact.sh /path/to/NavCenter-0.1.0-beta.1-macos-arm64.dmg
```

Set `NAV_CENTER_EXPECTED_TEAM_ID` and `NAV_CENTER_EXPECTED_SHA256` from
independently trusted publisher configuration and the build/release record.
Never derive them from the downloaded candidate or its adjacent sidecars.
The skill delegates to `scripts/verify-release-artifact.sh`, which authenticates
the expected Developer ID team and app bundle, checks the trusted digest,
mounts read-only, verifies nested code and platform acceptance, then detaches.
It signs nothing and submits nothing to Apple.

A passing run establishes these artifact checks only. Clean-machine install,
offline launch, core workflows, update/uninstall behavior, architecture and
minimum-macOS acceptance, and source/private-data scans remain separate gates.
Record the source revision, trusted build record, command, and exact artifact
digest with the result.

Human merge and release authority stays with the user: this skill produces
evidence, never a decision to publish, distribute, or submit to Apple.

# Security

This repository uses [GitGuardian](https://www.gitguardian.com/) for secret detection.

## What is scanned

- **Code & commits**: every push and pull request is scanned by the
  `GitGuardian scan` GitHub Action (`.github/workflows/gitguardian.yml`) using
  `ggshield`.
- **Pre-commit**: developers can install the pre-commit hook
  (`.pre-commit-config.yaml`) to block secrets before they are committed.
- **Issue attachments**: GitHub's native GitGuardian app does **not** scan file
  attachments on issues (e.g. `logs.txt`). The
  `GitGuardian scan issue attachments` workflow
  (`.github/workflows/gitguardian-issues.yml`) downloads issue bodies, comments
  and attachments and scans them with ggshield. Findings are reported both as a
  failing CI check and, when `GITGUARDIAN_SOURCE_UUID` is set, as incidents in
  the GitGuardian dashboard (Bring Your Own Source).

## What GitGuardian does when it finds sensitive info

1. **Detection**: ggshield matches content against 450+ secret detectors
   (API keys, tokens, passwords, certificates, DB connection strings, etc.).
2. **CI gate**: the workflow is marked as failed, which (when configured as a
   required status check) blocks merging of the pull request.
3. **Incident creation**: an incident is created in the GitGuardian dashboard
   with the secret type, location (file/line/URL), validity status and severity.
4. **Alerting**: notifications are sent according to your workspace settings
   (email, Slack, etc.).
5. **Remediation guidance**: the dashboard provides steps to revoke/rotate the
   secret and remove it from history.
6. **Presence check**: GitGuardian verifies whether the secret is still
   accessible; if revoked, the incident can be resolved.

## Required secrets (GitHub repository settings)

- `GITGUARDIAN_API_KEY` - service account / personal access token with `scan`
  (and `scan:create-incidents` for BYOS) permissions.
- `GITGUARDIAN_SOURCE_UUID` (optional) - UUID of a "Custom Source" created in
  the GitGuardian dashboard, used to attach issue-attachment findings to a
  dedicated source.
- `GITHUB_TOKEN` - provided automatically by GitHub Actions.

## Configuration

- `.gitguardian.yaml` - ignore paths and scan options for ggshield.
- `.pre-commit-config.yaml` - local pre-commit hook.
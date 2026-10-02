#!/usr/bin/env bash
# Keep skill and release-workflow verification on the same security boundary.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$repo_root/scripts/verify-release-artifact.sh" "$@"

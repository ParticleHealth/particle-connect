# Private-to-Public Sync Workflow

## Overview

This private repo (`particle-connect-private`) syncs to the public repo
[ParticleHealth/particle-connect](https://github.com/ParticleHealth/particle-connect)
via a GitHub Actions workflow on every push to `main`.

## How it works

1. **Push to `main`** on this private repo
2. **Checks job** runs — scans for accidentally committed secrets or sensitive files (`.env`, `credentials`, `secrets`)
3. **Sync job** runs (only if checks pass):
   - Strips private-only directories: `_private/`, `.planning/`, `.claude/`
   - Strips private-only files: `CLAUDE.md`, `CLAUDE.local.md`
   - Force-pushes the cleaned tree to the public repo

## What stays private

| Path | Purpose |
|---|---|
| `_private/` | Internal notes, experiments, anything not for public |
| `.planning/` | Roadmaps, research, project state |
| `.claude/` | Local AI assistant settings |
| `CLAUDE.md` | Project instructions for AI |

## What gets synced to public

Everything else at the top level, including:
- `particle-flat-observatory/`
- `particle-health-starters/`
- `README.md`
- `LICENSE`

## Setup requirements

- A deploy key (SSH) with write access on the public repo
- The private key stored as `PUBLIC_REPO_DEPLOY_KEY` secret on this repo
- The workflow file at `.github/workflows/sync-to-public.yml`

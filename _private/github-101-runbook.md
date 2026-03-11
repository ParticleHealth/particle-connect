# GitHub 101 Runbook

A quick-reference guide for the solutions team to get set up with Git, GitHub Desktop, and this repository.

> **Audience**: Anyone from "I've never used Git" to "I know Git but need a refresher on our workflow."

---

## Table of Contents

1. [Install Git](#1-install-git)
2. [Install GitHub Desktop](#2-install-github-desktop)
3. [Clone This Repo](#3-clone-this-repo)
4. [Your Local Folder — What Just Happened?](#4-your-local-folder--what-just-happened)
5. [Branching, Committing, and Pull Requests](#5-branching-committing-and-pull-requests)
6. [Understanding .gitignore](#6-understanding-gitignore)
7. [Using Claude Code for Git](#7-using-claude-code-for-git)
8. [Quick Reference Cheat Sheet](#8-quick-reference-cheat-sheet)
9. [Common Mistakes and How to Fix Them](#9-common-mistakes-and-how-to-fix-them)

---

## 1. Install Git

Git is the version control tool that runs under the hood. GitHub Desktop uses it, but you should also have it available on the command line.

### macOS

Open Terminal and run:

```bash
xcode-select --install
```

This installs Apple's Command Line Tools, which includes Git. Verify with:

```bash
git --version
```

Alternatively, install via Homebrew:

```bash
brew install git
```

### First-time setup

Tell Git who you are (use your work email):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@particlehealth.com"
```

---

## 2. Install GitHub Desktop

GitHub Desktop gives you a visual interface for Git — no command line needed for day-to-day work.

### Steps

1. Go to [desktop.github.com](https://desktop.github.com/) and download the installer
2. Run the installer
3. Open GitHub Desktop and sign in with your **GitHub account**
   - If you don't have a GitHub account, create one at [github.com](https://github.com/) using your work email
   - Make sure your account has been added to the **ParticleHealth** organization — ask your manager or the engineering team if you're not sure

---

## 3. Clone This Repo

"Cloning" means downloading a copy of the repository to your computer so you can work on it locally.

### Using GitHub Desktop

1. Open GitHub Desktop
2. Click **File > Clone Repository**
3. Select the **GitHub.com** tab
4. Search for `particle-connect-private` (or find it under the ParticleHealth org)
5. Choose a **local path** — this is where the files will live on your machine
   - Recommended: `~/Documents/GitHub/particle-connect-private`
6. Click **Clone**

### Using the command line

```bash
cd ~/Documents/GitHub
git clone https://github.com/ParticleHealth/particle-connect-private.git
cd particle-connect-private
```

> **Note**: You'll need access to the private repo. If you get a permission error, ask someone on the team to add you as a collaborator.

---

## 4. Your Local Folder — What Just Happened?

After cloning, you have a complete copy of the repository on your machine. Here's what's inside:

```
particle-connect-private/
├── particle-api-quickstarts/        # Python SDK + workflows + quick-starts
├── particle-analytics-quickstarts/  # Flat data pipeline + SQL queries
├── management-ui/                   # Browser-based admin UI
├── agent-documentation/             # AI-agent-friendly docs
├── _private/                        # Internal-only docs (you are here)
├── README.md
└── .git/                            # Hidden folder — Git's brain (don't touch)
```

### Key concept: local vs. remote

| Term | What it means |
|------|--------------|
| **Local** | The copy on your computer. You can edit freely — nothing affects anyone else until you push. |
| **Remote** (origin) | The copy on GitHub. This is the shared "source of truth." |
| **main** branch | The primary branch. All finished work ends up here. |

You work locally, then sync your changes back to the remote.

---

## 5. Branching, Committing, and Pull Requests

> **Golden rule**: Never push directly to `main`. Always work on a branch and open a pull request (PR).

### Why branches?

Think of `main` as the "clean copy" that everyone trusts. A branch is your personal workspace where you can make changes without affecting anyone else. When your work is ready, you ask the team to review it via a **pull request** before it gets merged into `main`.

```
main  ─────────────────────────●──────────  (stable, always works)
                              ↑
your-branch  ──●──●──●───────┘  (your work, merged after review)
```

### Step 1: Pull the latest from main

Always start from a fresh copy of `main`.

**GitHub Desktop**: Make sure you're on the `main` branch (top bar), then click **Fetch origin** → **Pull origin**.

**Command line**:

```bash
git checkout main
git pull
```

### Step 2: Create a branch

Name your branch something descriptive. Use lowercase with hyphens.

**GitHub Desktop**: Click the **Current Branch** dropdown → **New Branch** → name it → click **Create Branch**.

**Command line**:

```bash
git checkout -b your-branch-name
```

#### Branch naming best practices

| Pattern | Example | When to use |
|---------|---------|-------------|
| `feature/short-description` | `feature/add-mrn-search` | Adding something new |
| `fix/short-description` | `fix/query-timeout` | Fixing a bug |
| `docs/short-description` | `docs/update-setup-guide` | Documentation changes |
| `update/short-description` | `update/retry-logic` | Improving existing functionality |

**Avoid**: spaces, uppercase, vague names like `my-branch` or `test`.

### Step 3: Make your changes and commit

Edit your files in your editor, then commit as you go. Each commit should be one logical change.

**GitHub Desktop**:
1. You'll see your changed files listed in the left panel
2. Check the files you want to include
3. Write a short summary at the bottom (e.g., "Add retry logic to query workflow")
4. Click **Commit to your-branch-name**

**Command line**:

```bash
# See what changed
git status

# Stage specific files (don't use "git add ." — be intentional)
git add path/to/file1.py path/to/file2.py

# Commit with a message
git commit -m "Add retry logic to query workflow"
```

You can make multiple commits on your branch. That's fine — it helps reviewers see your thought process.

#### Good commit messages

| Do | Don't |
|----|-------|
| `Add patient search by MRN` | `update stuff` |
| `Fix timeout in document download` | `fix` |
| `Remove unused config fields` | `changes` |

**Rule of thumb**: Start with a verb. Describe *what* the change does, not *that* you changed something.

### Step 4: Push your branch

Pushing uploads your branch to GitHub. This does **not** change `main` — it just makes your branch visible on GitHub.

**GitHub Desktop**: Click **Publish branch** (first push) or **Push origin** (subsequent pushes).

**Command line**:

```bash
# First push — sets up tracking
git push -u origin your-branch-name

# Subsequent pushes
git push
```

### Step 5: Open a pull request (PR)

A pull request is how you ask the team to review and merge your changes into `main`.

**GitHub Desktop**: After pushing, GitHub Desktop shows a **Create Pull Request** button. Click it — it opens GitHub in your browser.

**On GitHub** (browser):
1. You'll see a banner at the top of the repo: *"your-branch-name had recent pushes — Compare & pull request"*. Click it.
2. Fill in the PR:
   - **Title**: Short description of what you did (e.g., "Add MRN search to patient workflow")
   - **Description**: Explain *why* you made the change and anything reviewers should know
3. Click **Create pull request**

**Command line** (using GitHub CLI):

```bash
gh pr create --title "Add MRN search to patient workflow" --body "Description of changes"
```

#### What makes a good PR

- **Small and focused** — one feature or fix per PR, not a grab bag of changes
- **Clear title** — a reviewer should understand the PR from the title alone
- **Description with context** — what changed, why, and anything the reviewer should test or watch for
- **No unrelated changes** — if you noticed something else to fix, make a separate PR

### Step 6: Get a review and merge

1. Ask a teammate to review your PR (you can assign reviewers on GitHub)
2. Address any feedback by making new commits on the same branch and pushing — the PR updates automatically
3. Once approved, click **Merge pull request** on GitHub (or ask the reviewer to merge it)
4. After merging, delete the branch — GitHub will prompt you to do this

### Step 7: Clean up locally

After your PR is merged, switch back to `main` and pull the latest:

**GitHub Desktop**: Switch to `main` branch → **Fetch origin** → **Pull origin**. Delete the old branch from **Branch > Delete**.

**Command line**:

```bash
git checkout main
git pull
git branch -d your-branch-name
```

### The full cycle

```
pull main → create branch → edit → commit → push branch → open PR → review → merge → repeat
```

---

## 6. Understanding .gitignore

### What is .gitignore?

A `.gitignore` file tells Git which files and folders to **ignore** — meaning Git won't track them, commit them, or push them to GitHub.

### Why does it matter?

Some files should never be in the repository:

| File type | Why it's ignored | Example |
|-----------|-----------------|---------|
| **Secrets / credentials** | Security risk — anyone with repo access can see them | `.env`, `credentials.json`, API keys |
| **Virtual environments** | Large, machine-specific, easily recreated | `.venv/`, `node_modules/` |
| **Build artifacts** | Generated output, not source code | `dist/`, `__pycache__/`, `.pyc` files |
| **OS junk files** | System-generated, not useful to others | `.DS_Store` |
| **IDE settings** | Personal editor config | `.idea/`, `.vscode/settings.json` |

### How it works

The `.gitignore` file sits in the root of the repo. Each line is a pattern:

```gitignore
# Ignore all .env files (secrets!)
.env
.env.*

# Ignore Python virtual environments
.venv/

# Ignore compiled Python files
__pycache__/
*.pyc

# Ignore macOS system files
.DS_Store
```

### What to do if you see an ignored file

- **Don't** manually add it with `git add -f` (force)
- If you think it shouldn't be ignored, ask the team before changing `.gitignore`
- If you accidentally committed a secret, tell the team immediately — it needs to be rotated even after removal

### Best practice

Before committing, glance at the file list in GitHub Desktop or run `git status`. If you see files you don't recognize or didn't intend to change, pause and check.

---

## 7. Using Claude Code for Git

If you have [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed, you can do all of this in plain English. Claude Code runs Git commands for you — just tell it what you want.

### Example prompts

| What you want to do | What to tell Claude Code |
|----------------------|--------------------------|
| Start a new branch | *"Pull latest from main and create a branch called feature/add-query-retry"* |
| Commit your work | *"Commit my changes with the message 'Add retry logic to query workflow'"* |
| Push and open a PR | *"Push this branch and open a PR with a summary of what I changed"* |
| Check status | *"What branch am I on and do I have uncommitted changes?"* |
| See what changed | *"Show me a diff of everything I changed on this branch"* |
| Clean up after merge | *"Switch back to main, pull latest, and delete the old branch"* |

### Tips

- **Be specific about branch names.** Claude Code will create exactly the branch name you give it.
- **Ask it to commit specific files.** e.g., *"Commit only the Python files, not the notebook"*
- **Let it write your commit messages.** e.g., *"Commit these changes with a good commit message"* — it'll read your diff and write one for you.
- **Use `/commit`** — a built-in shortcut that stages, summarizes, and commits in one step.
- **Ask before destructive actions.** Claude Code will confirm before doing anything risky (force push, hard reset, etc.), but it's good habit to be explicit: *"Don't push yet, just commit locally."*

---

## 8. Quick Reference Cheat Sheet

### GitHub Desktop actions

| Action | How |
|--------|-----|
| Get latest changes | **Fetch origin** → **Pull origin** |
| Create a new branch | **Current Branch** dropdown → **New Branch** |
| Switch branches | **Current Branch** dropdown → select branch |
| See what you changed | Look at the **Changes** tab |
| Commit your work | Write a message → **Commit to branch-name** |
| Push to GitHub | **Publish branch** (first time) or **Push origin** |
| Open a pull request | Click **Create Pull Request** after pushing |
| Delete a merged branch | **Branch > Delete** |
| Undo last commit (before push) | **Repository > Undo...** |
| View history | Click the **History** tab |

### Command line equivalents

| Task | Command |
|------|---------|
| Check what branch you're on | `git branch` |
| Create and switch to a new branch | `git checkout -b branch-name` |
| Switch to an existing branch | `git checkout branch-name` |
| See changed files | `git status` |
| See line-by-line changes | `git diff` |
| Pull latest | `git pull` |
| Stage files | `git add <file>` |
| Commit | `git commit -m "message"` |
| Push branch (first time) | `git push -u origin branch-name` |
| Push branch (subsequent) | `git push` |
| Open a pull request | `gh pr create --title "title" --body "description"` |
| Delete a merged branch locally | `git branch -d branch-name` |
| View recent history | `git log --oneline -10` |

---

## 9. Common Mistakes and How to Fix Them

### "I edited the wrong file"

If you haven't committed yet:

**GitHub Desktop**: Right-click the file in the Changes list → **Discard changes**.

**Command line**:

```bash
git checkout -- path/to/file
```

### "I committed but haven't pushed yet"

**GitHub Desktop**: **Repository > Undo** will undo the last commit and return your changes to the staging area.

### "I committed a secret / .env file"

1. **Don't push.** If you already pushed, notify the team immediately.
2. The secret (API key, password, etc.) needs to be **rotated** even after removal — once it's in Git history, it's there.
3. Remove the file and add it to `.gitignore`.

### "git pull says there's a conflict"

This happens when someone else changed the same lines you changed.

1. Open the conflicting file — you'll see markers like `<<<<<<< HEAD`
2. Edit the file to keep the correct version
3. Save, commit, and push

If you're not sure how to resolve it, ask a teammate before guessing.

### "I don't know what branch I'm on"

**GitHub Desktop**: The current branch is shown at the top of the window.

**Command line**:

```bash
git branch
```

For this repo, you'll usually be on `main`.

---

## Need Help?

- **Git concepts**: [git-scm.com/book](https://git-scm.com/book/en/v2) (free, official book)
- **GitHub Desktop docs**: [docs.github.com/en/desktop](https://docs.github.com/en/desktop)
- **Internal questions**: Ask in the team Slack channel or reach out to the engineering team

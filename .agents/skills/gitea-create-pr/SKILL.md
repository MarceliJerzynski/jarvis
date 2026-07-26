---
name: gitea-create-pr
description: Automates the Git and Gitea Pull Request (PR) creation workflow. Trigger when the user says "Zrób PRa", "Zrób PR", "Utwórz PR", "create PR", or requests publishing changes to the develop branch.
---

# Gitea Pull Request Creation Workflow

This skill automates the entire process of preparing a branch, rebasing onto the latest develop, auto-committing local changes with a professional Jira-prefixed message, pushing to Gitea, and automatically creating a Gitea Pull Request using the Gitea REST API.

---

## ────────────────────
## 1. Trigger Conditions
- Triggered when the user issues commands like:
  - "Zrób PRa"
  - "Zrób PR"
  - "Utwórz PR"
  - "Stwórz pull request do developa"
  - "publish my changes"

---

## 2. Core Workflow Steps

### Step 1: Guard Current Branch & Smart Checkout
1. Run `git branch --show-current < /dev/null` to identify the current branch name.
2. Extract the **Jira ID** from the branch name using a regex pattern (e.g., `feature/COMSPPROD-3044` -> ID: `COMSPPROD-3044`, `bugfix/COMSPPROD-123` -> ID: `COMSPPROD-123`).
3. **Branch Verification:**
   - If the current branch is `develop` or the user is on an incorrect branch:
     - Ask the user which branch they want to be on, or if they want to create a new branch.
     - If creating a new branch, ask for the branch name (suggest `<prefix>/<Jira-ticket-id>` as per `utils/git-workflow.md`).
4. **Smart Checkout (Stash & Pop):**
   - If switching to another branch or creating a new branch, verify if there are uncommitted changes using `git status --porcelain < /dev/null`.
   - If uncommitted changes exist:
     - Run `git stash < /dev/null` to temporarily save changes.
     - Run the checkout command: `git checkout <target_branch> < /dev/null` or `git checkout -b <new_branch> develop < /dev/null`.
     - Run `git stash pop < /dev/null` to restore the changes.
5. Verify the checkout succeeded by running `git branch --show-current < /dev/null`.

### Step 2: Synchronize & Rebase to Develop
1. Fetch the latest `develop` from origin:
   ```bash
   git fetch origin develop < /dev/null
   ```
2. Rebase the current branch onto the latest origin develop:
   ```bash
   git rebase origin/develop < /dev/null
   ```
3. **Conflict Resolution Guard:**
   - If the rebase fails with conflicts (e.g., git output shows conflict files or status is `REBASE-i` / `REBASE-m`):
     - Run `git status < /dev/null` to find all conflicted files.
     - Clearly list the conflicted files to the user.
     - **Stop execution and ask the user to resolve the conflicts.**
     - Once the user resolves conflicts, run `git add <files> < /dev/null` and `git rebase --continue < /dev/null` to complete the rebase.

### Step 3: Automatically Commit Changes (English & Jira Prefixed)
1. Run `git status --porcelain < /dev/null` to check for uncommitted changes.
2. If uncommitted changes exist:
   - Run `git diff < /dev/null` to analyze the exact code changes.
   - Generate a professional, concise summary of the changes **in English** (as required by style guidelines).
   - If the **Jira ID** is not yet resolved from the branch name, ask the user for it first.
   - Format the commit message as: `{Jira_ID}: {Summary}` (e.g., `COMSPPROD-3044: Added input validation for material allocation`).
   - Commit the changes:
     ```bash
     git commit -am "{Jira_ID}: {Summary}" < /dev/null
     ```

### Step 4: Push to Remote
1. Push the current branch to origin:
   ```bash
   git push origin HEAD < /dev/null
   ```

### Step 5: Create Gitea Pull Request via REST API
1. Run the Python helper tool bundled with this skill:
   ```bash
   python3 /workspace/jarvis/.agents/skills/gitea-create-pr/scripts/gitea_api_tool.py "develop" "<head_branch>" "<pr_title>" "<pr_description>" < /dev/null
   ```
   - `<head_branch>`: The active local branch.
   - `<pr_title>`: Format as `{Jira_ID}: {Commit_Summary_Title}`.
   - `<pr_description>`: Detailed summary of changes in English (supports Markdown).
2. **Network/VPN Failures Fallback:**
   - If the script fails with a host resolution error (such as `Name or service not known` or `Could not resolve host`), the host's VPN is disconnected.
   - **Explicitly inform the user that the host's VPN connection has probably disconnected** (as per `utils/local-environment.md`).
   - Provide the user with a clickable **direct Gitea link** to manually compare and create the PR in their browser:
     ```
     https://git.psi-mt.de/SP/sp-prod/compare/develop...<head_branch>
     ```

### Step 6: Return to Develop
1. After successfully creating the PR, switch back to `develop`:
   ```bash
   git checkout develop < /dev/null
   ```
2. Pull the latest develop changes:
   ```bash
   git pull < /dev/null
   ```

---

## 3. Standard UI Formatting
- Your response must ALWAYS begin with `────────────────────` and end with `────────────────────`.
- All output in commits, titles, and descriptions must be in **English**.

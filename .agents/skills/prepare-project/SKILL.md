---
name: prepare-project
description: Prepares the development project and workspaces for work. Trigger when the user says "przygotuj projekt", "prepare project", "prepare workspace", "sync develop", or requests aligning workspaces with remote develop branch.
---

# Project and Workspace Preparation Workflow

This skill automates the process of aligning your main development workspaces (`sp-met-global` and `sp-prod`) with the latest remote `develop` branch. It safely handles any local uncommitted changes using stash operations to ensure no work is lost.

---

## ────────────────────
## 1. Trigger Conditions
- Triggered when the user issues commands like:
  - "przygotuj projekt"
  - "prepare project"
  - "prepare workspace"
  - "sync develop"
  - "align workspaces"

---

## 2. Core Workflow Steps

### Step 1: Run the Preparation Tool
1. Execute the shell script bundled with this skill:
   ```bash
   bash /workspace/jarvis/.agents/skills/prepare-project/scripts/prepare_project.sh < /dev/null
   ```
2. **VPN Disconnection Guard:**
   - If the script outputs errors related to `git pull` or connectivity issues, check if the host VPN is disconnected.
   - Explicitly warn the user that their VPN might be disconnected (as per `utils/local-environment.md`).

### Step 2: Present Sync Results
1. Output a beautiful summary of the synchronization results to the user.
2. If any stash conflicts occur during restoration, point the user to the respective directories where conflicts need manual review.

---

## 3. Standard UI Formatting
- Your response must ALWAYS begin with `────────────────────` and end with `────────────────────`.

---
name: jira-import
description: Imports Jira tickets automatically by ID and saves them to the workspace. Trigger when the user says "Importuj COMSPPROD-3044", "pobierz jire COMSPPROD-123", "pobierz zadanie COMSPPROD-123", "import jira", or requests fetching a Jira issue.
---

# Jira Issue Automatic Import Workflow

This skill automates the process of fetching a Jira ticket's title, type, status, assignee, priority, and rich description (including converting Atlassian Document Format JSON to clean Markdown) using the Jira Cloud REST API, saving the final file as `{project-root}/jiras/{JIRA_ID}-imported.md`.

---

## ────────────────────
## 1. Trigger Conditions
- Triggered when the user issues commands like:
  - "Importuj COMSPPROD-3044"
  - "Pobierz jire COMSPPROD-123"
  - "pobierz zadanie COMSPPROD-456"
  - "import jira COMSPPROD-789"
  - "fetch jira issue COMSPPROD-123"

---

## 2. Core Workflow Steps

### Step 1: Extract the Jira ID
1. Parse the user's prompt to extract the target **Jira ID** (e.g., `COMSPPROD-3044`, `COMSPCORE-1234`).
2. If no Jira ID is found, ask the user to provide it.

### Step 2: Execute the Fetch Tool
1. Run the Python fetch tool bundled with this skill:
   ```bash
   python3 /workspace/jarvis/.agents/skills/jira-import/scripts/jira_fetch.py "<JIRA_ID>" < /dev/null
   ```
2. **Success Handling:**
   - Display a clean success confirmation.
   - Point the user to the newly imported Markdown file: `jiras/<JIRA_ID>-imported.md`.
   - Print a brief summary of the ticket (Title, Type, Status, Assignee, Priority) for instant feedback.
3. **Failure Handling (401 Unauthorized / Expired Session):**
   - If the request fails with status `401` or another connection error, it means the browser `Cookie` session has expired.
   - **Helpfully guide the user on how to update their session cookies:**
     1. Open Jira Cloud in their browser (`https://collaboration-psise.atlassian.net`).
     2. Open DevTools (**F12**) -> **Network** tab -> Reload (**F5**).
     3. Filter for `myself` or `api`, click any request, and go to **Headers** -> **Request Headers**.
     4. Find the **`cookie:`** header, copy its entire value.
     5. Paste it inside their private config file at: `/home/node-user/.gemini/tmp/jarvis-2/memory/jira_config.json` inside the `"cookie"` field.
     6. Run the import command again!

---

## 3. Standard UI Formatting
- Your response must ALWAYS begin with `────────────────────` and end with `────────────────────`.

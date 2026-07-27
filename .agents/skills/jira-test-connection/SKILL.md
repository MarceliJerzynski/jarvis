---
name: jira-test-connection
description: Tests the Jira connection status, verifies API authentication, and checks the validity of browser cookies or API tokens. Trigger when the user says 'test jira', 'verify jira connection', 'check jira connection', 'test jira connection', or asks to verify if Jira credentials are correct.
---

# Jira Connection Verification Workflow

This skill verifies the status of the connection to Jira Cloud, checking the validity of the current browser cookies or API token, without fetching or creating any local files or importing tickets.

---

## 1. Trigger Conditions
- Triggered when the user issues commands like:
  - "test jira"
  - "test jira connection"
  - "verify jira connection"
  - "check jira"
  - "sprawdź połączenie z jirą"

---

## 2. Core Workflow Steps

### Step 1: Execute the Connection Test Script
1. Run the connection test utility bundled with this skill:
   ```bash
   python3 /workspace/jarvis/.agents/skills/jira-test-connection/scripts/jira_test.py < /dev/null
   ```

2. **Success Handling:**
   - Display a success confirmation message showing that the connection is working.
   - Show the authenticated user's display name, email, and active status.

3. **Failure Handling (401 Unauthorized / Expired Session):**
   - Inform the user that their browser session has expired (HTTP 401).
   - **Guide the user on how to update their session cookies:**
     1. Open Jira Cloud in their browser (`https://collaboration-psise.atlassian.net`).
     2. Open DevTools (**F12**) -> **Application** (or **Storage**) tab -> **Cookies** -> `https://collaboration-psise.atlassian.net`.
     3. Select all cookies, copy them as a table, or copy the entire **`cookie:`** request header from the Network tab.
     4. Paste the cookies/header to the agent, and the agent will parse and save them to the configuration file!

---

## 3. Standard UI Formatting
- Your response must ALWAYS begin with `────────────────────` and end with `────────────────────`.

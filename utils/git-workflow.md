# Git Branch & Commit Workflow Guidelines

## 1. Branch Naming Convention
Whenever the user asks you to create a new Git branch, you must strictly follow this naming convention:
- **Format:** `<prefix>/<Jira-ticket-id>`
- **Prefix:** Use `bugfix` or `feature` depending on the type of work being performed.
- **Example:** `bugfix/COMSPPROD-2137` or `feature/COMSPPROD-1234`

### Rules:
1. If the Jira ticket ID or the type of work is known from the context or the user prompt, use those values directly.
2. If this information is NOT known or is ambiguous, **ask the user** for the Jira ticket ID and/or the branch type *before* attempting to create any branch.

## 2. Commit Message Convention
Whenever the user asks you to commit changes, the commit message must start with the Jira ticket ID associated with the current branch/task:
- **Format:** `<Jira-ticket-id>: <message>`
- **Example:** `COMSPPROD-2137: Resolved Grid API Null Pointer Exception on rapid tab switches`

### Rules:
1. Always prefix the commit message with the exact Jira ticket ID, followed by a colon and a space.

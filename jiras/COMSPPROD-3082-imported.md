# COMSPPROD-3082: Extend validation of Line Schedule Reject for TargetItem

- **Type:** Task
- **Status:** In Progress
- **Priority:** 3-Major
- **Assignee:** Marceli Jerzyński
- **Jira Link:** https://collaboration-psise.atlassian.net/browse/COMSPPROD-3082

---

## Description

When rejecting a schedule currently the Line Schedule Status is checked and if all Items have status “Scheduled”. Back then this was sufficient to make sure no items were moved, because MOVED was a status. Now we are not changing the status anymore when moving, but set “TargetItem”. Therefore the validation needs to be extended to check, that no Item has a “TargetItem”.

While doing this, please check if the validation could be “easily” used to disable the Reject Button.

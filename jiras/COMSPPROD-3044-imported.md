# COMSPPROD-3044: Charging for Sublines

- **Type:** Story
- **Status:** Deferred
- **Priority:** 4-Minor
- **Assignee:** Unassigned
- **Jira Link:** https://collaboration-psise.atlassian.net/browse/COMSPPROD-3044

---

## Description

As a

* Line Operator

I want to

* book the charging into a Subline, when applicable for the allocation

So that

* the material is charged into the Subline



*Design Idea*

In case the material is allocated to a PO-Step of a Line with Sublines a different version of “Production Line Charge” screen should open, when pressing “Charge”.

It should contain underneath “Line” a Dropdown to select a SubLine. The “Default Inline Stockarea” and Stockareas to select are based on the selected SubLine.

_Possible values to select / Preselection_

* In case that there is a clear first / next Substep (order given) only the Sublines on this steps can be selected. In this case the Subline with highest Prio (0) should be preselected.
* In case there is no clear first step, all Sublines of all Substeps which could be executed next are available. In this case preselect any Subline from this selection with Prio 0.



The model would support that sublines have sublines. The UI does not need to support this. The level of Line with subline is sufficient.

As part of this task reduce the size of Storage Area List to 5 entries.

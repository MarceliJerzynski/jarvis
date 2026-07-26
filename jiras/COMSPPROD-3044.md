# COMSPPROD-3044 - Book Charging into Subline for Line Allocation

Title: Book charging into a Subline during line allocation

Type: User Story

User Story

As a

Line Operator

I want to

book the charging into a Subline, when applicable for the allocation

So that

the material is charged into the Subline

Design Idea / Solution Details

In case the material is allocated to a PO-Step of a Line with Sublines, a different version of the “Production Line Charge” screen should open when pressing “Charge”.

It should contain underneath “Line” a Dropdown to select a SubLine. The “Default Inline Stockarea” and Stockareas to select are based on the selected SubLine.

The model supports nested sublines (sublines having sublines). The UI does not need to support this; representing the single level of Line with subline is sufficient.

Selection Rules / Business Logic

In case that there is a clear first / next Substep (order given), only the Sublines on this step can be selected. In this case, the Subline with the highest priority (0) should be preselected.

In case there is no clear first step, all Sublines of all Substeps which could be executed next are available. In this case, preselect any Subline from this selection with priority 0.

Acceptance Criteria / Detailed Requirements

1. When a Line Operator initiates a "Charge" action, the system must check if the material is allocated to a PO-Step of a Line that contains Sublines.
2. If the Line has Sublines, open the customized version of the “Production Line Charge” screen.
3. The screen must feature a dropdown field labeled “Subline” positioned directly underneath the “Line” selection field.
4. Selection of a Subline must dynamically update the “Default Inline Stockarea” and the available list of Stockareas based on the chosen Subline.
5. If there is a clear, ordered first or next Substep, restrict the Subline dropdown to only include the Sublines corresponding to that specific step, with the highest priority (0) Subline preselected.
6. If there is no clear first step, display all Sublines from all next executable Substeps, preselecting any available Subline with priority 0.

Additional Work Included in This Ticket

As part of this task, reduce the size of the Storage Area List to 5 entries.

Out of Scope

UI support for nested sublines (sublines having sublines). The UI only needs to represent a single level of Line with direct Sublines, even though the database/domain model supports deeper nesting.

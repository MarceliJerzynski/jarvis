# PSImetals Service Platform (SP) - Allocation (`allocation`) Domain Guidelines

This document provides a comprehensive developer guideline and structural overview of the **Allocation (`allocation`)** domain component located within `sp-met-global/components/allocation`. It covers the system's architecture, core allocation and reservation concepts, operational rules, and integration handlers.

---

## 1. Module & Architecture Guidelines

The `allocation` domain is the logical binding layer that bridges physical materials (`mat` domain) with operational routing plans (`prodorder` domain). It defines what specific materials are planned for processing or have been produced by individual operational steps across plant lines.

This component is split into decoupled layers following the platform's multi-module architecture:
*   [**`-com-api` Layer** (API Contracts & Payloads)](../architecture/com-api.md) — Exposes internal allocation interfaces (`AllocationAppServiceIf`) and integration schemas (`AllocationMesg`, `AllocationDto`).
*   [**`-com` Layer** (Communication & Orchestration)](../architecture/com.md) — Implements REST application endpoints (`AllocationAppService`) and message bus listeners (`AllocationMesgHandler`).
*   [**`-business` Layer** (Domain Model & Binding Rules)](../architecture/business.md) — Implements core entities (`Allocation`, `Reservation`), transaction locking, consistency validators, and business logic (`AllocationService`).
*   [**`-infrastructure` Layer** (JPA Mappings & Repositories)](../architecture/infrastructure.md) — Defines persistence repositories (`AllocationRepository`, `ReservationRepository`) and feasibility matching rules (`FeasibleMatchRule`).
*   [**`-liquibase` Layer** (Schema Evolutions)](../architecture/liquibase.md) — Manages database schema migrations for allocations and reservations.
*   [**`-test` Layer** (Separated Automated Tests)](../architecture/test.md) — Houses the complete suite of automated test cases (e.g., allocation of charged materials, lot reservations, and deallocations).

---

## 2. Core Allocation & Reservation Concepts

The platform distinguishes between physical discrete unit allocations and logical bulk material reservations.

```text
ProdStep (Process Step) 
   │
   ├── Allocation (Physical binding of a discrete unit to a step)
   │      └── AbstractMat (The physical material unit, e.g., PieceMat, Heat)
   │
   └── Reservation (Logical binding of a bulk quantity to a step)
          └── Lot (Bulk material or grouped lot)
```

### Core Entity Definitions

#### 1. `Allocation` (Physical Unit Binding)
*   **Identities:** Composite primary key `id` (`AllocationId` comprising `matId` and `stepId`).
*   **Target Material:** References `AbstractMat` (the physical material unit being allocated).
*   **Target Step:** References `ProdStep` (the process step this material is bound to).
*   **Direction (`stepRelation`):** Governed by the `AllocationStepRelation` enum, which defines the material's process relationship relative to the step:
    *   `BEFORE`: Material is allocated as an **INPUT** to the step. It must physically exist *before* the step can start and will be processed or consumed during execution.
    *   `AFTER`: Material is allocated as an **OUTPUT** of the step. It represents a physical item produced *after* the operational step is completed (e.g., hot-rolled coil produced after the mill step).
*   **Properties:** Allocated quantity `amount` (`Amount`) and originating system identifier `originApp`.

#### 2. `Reservation` (Bulk/Lot Reservation)
*   **Identities:** Composite primary key `id` (`ReservationId` comprising `lotId` and `stepId`).
*   **Target Lot:** References a `Lot` entity (representing bulk or grouped material lots rather than individual countable pieces).
*   **Target Step:** References `ProdStep` (the process step).
*   **Properties:** Reserved bulk quantity `amount` (`Amount`).

---

## 3. Allocation Constraints & Operations

The `AllocationService` coordinates allocation lifecycles, enforcing critical business safety constraints, consistency rules, and database locks.

### A. Core Lifecycle Operations
*   **Allocate (`process` / `processAllocate`):** Creates or updates the binding between a material and a process step.
    *   If the material is already allocated to a different step, the old allocation is automatically removed, and the new one is persisted.
    *   Fires an `AllocationEvent` containing the previous step and the newly assigned step for downstream system synchronization.
*   **Deallocate (`deallocate`):** Detaches and removes an existing allocation. Fires a deallocation domain event.
*   **Allocate After (`allocateAfter`):** Convenience method to quickly allocate a material as the output (`AFTER` relation) of its associated step.

---

### B. Business Integrity Constraints

#### 1. Line Execution Constraint (Inexecutable Steps)
If a physical material unit (`Mat`) is currently **charged (loaded)** onto a production line, the platform enforces a strict execution safety check during allocation:
*   Resolves the active line via `mat.getChargedToLine()`.
*   Verifies if the targeted `ProdStep` can be executed by that line (checks if the line is listed inside the step's alternative equipment list: `step.getProdStepPlantUnits()`).
*   If the step cannot be executed by the line, throws an `AllocationToInexecutableStepException` to prevent incorrect plant-floor routing assignments.

#### 2. Feasibility Match Rules
To ensure physical materials meet the planned product characteristics, the platform can apply compatibility validation before completing an allocation:
*   Invokes `FeasibleMatchRule.matchMat(...)` to compare material details (shape, dimensions, steel grade) against step target specifications.
*   Resolves a compatibility score. If the score falls below the configured threshold (e.g., due to width mismatch or grade conflicts), throws an `AllocationInfeasibleException`.
*   *Note:* The feasibility check can be configured to execute selectively depending on which scheduling or tracking application (`context.senderInfo()`) requested the allocation.

#### 3. Transaction Locks
To protect transactional data consistency and prevent race conditions across parallel MES processors:
*   The service applies a strict pessimistic lock using `SPLockServiceIf` (scoped to the material natural ID) prior to making any allocation or deallocation changes.

---

## 4. Integration & Messaging Ingestions

Allocations and deallocations can be continuously synchronized from external scheduling or MES systems within the `-com` module:

*   **Bus Messages (`AllocationMesgHandler`):** Listens to `AllocationMesg` events on the bus. Maps the input `AllocationDto` via MapStruct and invokes `service.process(...)` to apply the allocation/deallocation.
*   **App Services (`AllocationAppService`):** Implements internal endpoint contracts to expose allocation processes (`AllocationDto`) to sibling components (e.g., LAPS schedulers).

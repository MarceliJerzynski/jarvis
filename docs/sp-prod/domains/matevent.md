# PSImetals Service Platform (SP) - Material Events (`matevent`) Domain Guidelines

This document provides a comprehensive developer guideline and structural overview of the **Material Events (`matevent`)** domain component located within `sp-prod-prodtracking`. It covers the system's architecture, event model hierarchy, physical tracking logs, and the highly robust, transaction-safe **Undo (Compensation) Pattern**.

---

## 1. Module & Architecture Guidelines

The `matevent` domain is the chronological journal and ledger of the Production Tracking (`prodtracking`) component. It logs every physical, quality, or logical operation executed on a material on the shop floor, and provides the architectural framework to safely reverse/undo these actions.

This component is split into decoupled layers following the platform's multi-module architecture:
*   [**`-com-api` Layer** (API Contracts & Payloads)](../architecture/com-api.md) — Exposes internal undo endpoints (`MaterialEventAppServiceIf`), event detail and list DTOs (`MaterialEventDetailResponseDto`, `MaterialEventShortDto`), differences mappings (`MatFieldDifference`), and simulation contracts (`UndoMaterialEventsSimulationResponseDto`).
*   [**`-com` Layer** (Communication & Orchestration)](../architecture/com.md) — Implements REST controllers (`MaterialEventAppService`) and MapStruct difference serializers (`MaterialEventMapper`, `MatExtendedDataFlatMapper`).
*   [**`-business` Layer** (Domain Model & Undo Services)](../architecture/business.md) — Defines the core abstract event (`MatEvent`), concrete tracking events (e.g., `LocationMatEvent`, `ChargingEvent`), event factories, the atomic closure builder (`UndoClosureBuilder`), and the rollback engine (`MatEventUndoService`).
*   [**`-infrastructure` Layer** (JPA Mappings & Repositories)](../architecture/infrastructure.md) — Integrates JPA mappings for tracking tables and event query helpers (`LocationMatEventRepository`).
*   [**`-liquibase` Layer** (Schema Evolutions)](../architecture/liquibase.md) — Manages database schema migrations for tracking event ledgers and physical snapshots.
*   [**`-test` Layer** (Separated Automated Tests)](../architecture/test.md) — Houses the complete suite of automated test cases (e.g., `MatEventUndoServiceTest`, event creation tests, and unlinking trials).

---

## 2. The Material Event Model

Every operational transaction on the plant floor creates a subclass of the abstract **`MatEvent`** entity.

```text
BusinessTrackingEvent (Core tracking event base)
   └── MatEvent (Abstract material tracking base)
          ├── Spatial Tracking: LocationMatEvent, RelocationEvent
          ├── Plant Arrival/Departure: BookedInMatEvent, BookedOutMatEvent, ReactivatedMatEvent
          ├── Production Consumptions: ChargingEvent, DischargingEvent, TreatmentEvent
          ├── Pedigree & Transformations: TransformationConsumptionEvent, FinalConsumptionEvent, ScrapConsumptionEvent
          ├── Quality & Testing: CompletedInspectionEvent, TakenSampleEvent, RejectedSampleEvent
          └── Special Operations: WeighingEvent, DataSyncMatEvent
```

### Core Event Properties (`MatEvent`)
*   **Identities:** Primary identifier mapped via `BusinessTrackingEventId`.
*   **Material Bindings:**
    *   `mat`: References the physical `Mat` being operated on.
    *   `matBusinessCode`: Captured natural key of the material. Required because if a material creation is undone, the material record itself is deleted, but the event log remains as a canceled history referencing the code.
*   **Process Groups:** Optional grouping under a logical `ProdProcess` block.
*   **Structural Flags:**
    *   `modifiesMat`: Boolean defining if this event updates material parameters (e.g., thickness, weight, status).
    *   `undoable`: Boolean defining if this action can be legally reversed.
*   **Routings:** Associated with a `ProdStep` and sub-step `ProdStepType` to connect tracking logs with scheduling orders.

---

## 3. The Undo (Compensation) Pattern

In a physical plant, mistakes happen (e.g., a scanner reads the wrong coil, or a crane operator selects the wrong furnace). Reversing these actions requires a highly safe transaction-control mechanism called the **Undo Pattern**, which ensures the digital state of the plant perfectly mirrors physical reality without corrupting database integrity.

The Undo Pattern consists of three core components:

```text
[Undo Request] ──> UndoClosureBuilder ──> MatEventUndoService ──> [Apply Snapshots & Handlers]
                      (Computes an           (Coordinates the
                     atomic closure)          rollback engine)
```

---

### A. The Snapshot State (`MatExtendedDataCommand`)
Rather than writing manual reversal code for every single property, the platform uses a **state-snapshot pattern**.
Every material event captures the pre-operation state of the material inside a **`MatExtendedDataCommand`**:
*   `matData` (`Optional<MatData>`): Core properties, dimensions, weights, status, and grade specs of the material *before* the event occurred.
    *   *Note:* If `matData` is empty, it means the material did not exist prior to this event (e.g., a Book-In event). Undoing this event will physically delete the material record from the database.
*   `matRelocationData` (`Location`): Physical spatial location (yard coordinates or charged line) *before* the event occurred.
*   `allocationData` (`AllocationData`): Scheduler routing and step allocation bindings *before* the event occurred.

When an undo is executed, the rollback engine simply restores these three snapshot elements to their original states.

---

### B. The Atomic Closure (`UndoClosureBuilder`)
You cannot undo a single step in isolation if downstream operations depend on its outcomes. The **`UndoClosureBuilder`** computes an atomic list of material events (called a **Closure**) that must be rolled back together to maintain domain consistency, enforcing three critical rules:

1.  **No Subsequent Events Constraint:**
    *   If any active event has been recorded on the material *after* the targeted operation, the undo is blocked (throws `MatEventHasSubsequentEventException`).
    *   *Example:* You cannot undo a coil's Charging event if the coil has already been Rolled or Discharged.
2.  **Atomic Operation Grouping:**
    *   A single physical action on the shop floor can write multiple database logs under a single logical transaction called a **`TrackingOperation`**.
    *   The builder resolves and groups *all* material events belonging to the same `TrackingOperation` to ensure the rollback is fully atomic.
3.  **Undoability Guard:**
    *   If any event within the computed tracking operation has the `undoable` flag set to `false`, the entire transaction is locked and cannot be reversed (throws `MatEventClosureNotUndoableException` / `LastOperationNotUndoableException`).

---

### C. The Rollback Engine (`MatEventUndoService`)
Once the atomic closure of events is resolved, the `MatEventUndoService` executes the rollback:

1.  **Temporal Cancellation:**
    *   Sets the temporal status of each event in the closure to `CANCELED`. **Undone events are never physically deleted from the database ledger**; they are retained as canceled history logs for audit trails.
    *   If the material was created by the event, the `cancel(true)` routine disconnects the material reference.
2.  **Snapshot Application:**
    *   Applies the captured `MatExtendedDataCommand` back onto the physical material (`Mat`). This instantly restores metadata, dimensions, spatial positions, and step allocations to their exact pre-event states.
3.  **Specialized CDI Handlers (`MatEventUndoHandlerIf`):**
    *   When restoring snapshot properties is not sufficient to fully reverse an event (e.g., an event that generated test samples, or registered third-party MES notifications), the service delegates to qualified CDI handlers.
    *   Handlers implementing `MatEventUndoHandlerIf` are looked up by event type (e.g., `TakenSampleEventUndoHandler` is invoked to physically delete created quality samples).
4.  **Notifications:**
    *   Fires domain-level notifications (`MatEventCancelledDomainEvent` and `TrackingOperationCancelledDomainEvent`) to synchronize downstream schedulers, ERP systems, and warehouse managers.

---

### D. Strategy-Based Undoability (`DetermineUndoableMatEventIf`)
The decision of whether a specific `MatEvent` can be undone is delegated to a strategy class implementing the **`DetermineUndoableMatEventIf`** interface:

1.  **Default Strategy (`DefaultDetermineUndoableMatEvent`):**
    *   Located in: `components/prodtracking/sp-prod-prodtracking-business/`
    *   Annotated with Quarkus `@DefaultBean` and `@ApplicationScoped`.
    *   By default, returns `true` for all events (allowing all operations to be legally undoable).
2.  **LAPS Customization Strategy (`LapsDetermineUndoableMatEvent`):**
    *   Located in: `components/laps/sp-prod-laps-business/`
    *   Implements `DetermineUndoableMatEventIf` and acts as a CDI override bean in the LAPS runtime context.
    *   Maintains a static array of allowed `MatEventData` subclass references (`UNDO_ALLOWED`) to filter undo operations.
    *   Only events whose data subclass (or descendant) is assignable from one of the following classes are permitted to be undone in LAPS:
        *   `ChargingEventData`
        *   `DischargingEventData`
        *   `FinalConsumptionEventData`
        *   `RelocationEventData`
        *   `ScrapConsumptionEventData`
        *   `TransformationConsumptionEventData`
        *   `TreatmentEventData`
        *   `WeighingEventData`


# PSImetals Service Platform (SP) - Production Order (`prodorder`) Domain Guidelines

This document provides a comprehensive developer guideline and structural overview of the **Production Order (`prodorder`)** domain component located within `sp-met-global/components/prodorder`. It covers the system's architecture, hierarchical structures, material specifications, routing logic, and business operations.

---

## 1. Module & Architecture Guidelines

The `prodorder` domain is responsible for managing production routes, operational steps, scheduling requirements, and material specifications for active manufacturing orders. It acts as the bridge between external ERP planning systems and plant-floor execution.

This component strictly follows the platform's multi-module architecture:
*   [**`-com-api` Layer** (API Contracts & Payloads)](../architecture/com-api.md) — Exposes order contracts (`ProdOrderAppServiceIf`, `ProdStepAppServiceIf`) and integration schemas (`ProdOrderMesg`, `ProdOrderStatusMesg`).
*   [**`-com` Layer** (Communication & Ingestion)](../architecture/com.md) — Implements message bus handlers (`ProdOrderMesgHandler`, `ProdOrderStatusMesgHandler`) and REST application controllers (`ProdOrderAppService`).
*   [**`-business` Layer** (Domain Model & Routing Rules)](../architecture/business.md) — Defines the core order entities (`ProdOrder`, `ProdStep`, `MatSpec`), validation checks, and CRUD operations (`ProdOrderService`).
*   [**`-infrastructure` Layer** (JPA Mappings & Repositories)](../architecture/infrastructure.md) — Implements database repositories (`ProdOrderRepository`, `ProdOrderTypeRepository`) and pre-fetch query utilities (`ProdOrderFullFetchHelper`).
*   [**`-liquibase` Layer** (Schema Evolutions)](../architecture/liquibase.md) — Declares schema migrations for orders, operational steps, alternative units, and quality products.
*   [**`-test` Layer** (Separated Automated Tests)](../architecture/test.md) — Houses the complete suite of domain unit and integration tests (e.g., cloning, routing, and status transition tests).

---

## 2. Order & Route Structures

The domain is modeled as a rich graph representation of production routing and material requirements.

```text
ProdOrder (The Production Order)
   ├── MatSpec (Input specifications criteria - matSpecIn)
   ├── MatSpec (Output specifications criteria - matSpecOut)
   └── ProdStep (List of operational routing steps)
          ├── RouteLink (Directed links pointing to next/prev steps forming a DAG)
          ├── MatSpec (Step-specific input/output overrides & variant lists)
          └── ProdStepPlantUnit (Capable lines / units for execution)
                 ├── ProdStepPlantUnitProdRate (Production rates / speeds)
                 └── SecondaryMatSpec (Auxiliary materials & tooling requirements)
```

### Core Entity Definitions

#### 1. `ProdOrder` (Production Order)
*   **Identities:** Primary identifier `id` (`ProdOrderId`), unique alphanumeric code `businessCode` (used by plant floor), and ERP-defined code `erpCode`.
*   **Type & Status:** Associated with a `ProdOrderType` (e.g., heat order, plate order) and governed by `ProdOrderStatus` (`ACTIVE`, `CANCELED`, `CLOSED`).
*   **Demands & Customers:** Integrates details of the customer demand using references to `Demand` and `CustomerShort`.
*   **Target Quantities:** Tracks input and output boundaries with tolerances using `tgtAmountIn` and `tgtAmountOut` (`AmountWithTol`).
*   **Routings (`steps`):** Contains an ordered list of `ProdStep` entities representing the operational routing.

#### 2. `MatSpec` (Material Specifications)
Describes chemical, geometric, and physical parameters required or produced by orders or individual steps:
*   **Properties:** Associated with a catalog `MaterialMaster`, `MatType`, and steel `Grade`.
*   **Geometry Limits:** Embeds dimensional limits via `tgtGeometry`, `minGeometry`, and `maxGeometry` (`StdGeometry` holding length, width, thickness, outer/inner diameter).
*   **Piece Weight:** Tracks weight limits with tolerance via `pieceWeight` (`WeightWithTol`).
*   **Variants:** Multiple prioritize variants are supported (`matSpecVariantsIn` / `matSpecVariantsOut`), enabling alternative material options prioritized by `prio`.

#### 3. `ProdStep` (Operational Step)
Represents a single manufacturing operation (e.g., Caster step, Reheating Furnace step, Rolling Mill step, Cutting step).
*   **Route Graph (DAG):** Employs `RouteLink` entities (`nextStepLinks` / `prevStepLinks`) connecting steps as a Directed Acyclic Graph (DAG) to represent branching and joining flows (e.g., slab splitting or bundle assembly).
*   **Step Overrides:** Can override target quantities (`tgtAmountIn` / `tgtAmountOut`), estimated processing duration, and material specs (`matSpecIn` / `matSpecOut`).
*   **Yields:** Tracks material yields using `yieldFactor` (`Ratio` representing output-to-input material ratio).
*   **Alternative Plant Units (`prodStepPlantUnits`):** Lists different physical machines or lines capable of executing this step.

#### 4. `ProdStepPlantUnit` (Capable Execution Units)
Associates a production step with a core `PlantUnit`.
*   **Priorities:** Sorted by `prio` (lower values define more preferred lines or equipment).
*   **Production Rates:** Embeds a `prodRate` (`ProdStepPlantUnitProdRate` holding speed limits like pieces/hour or tons/hour).
*   **Secondary Materials:** Maps `SecondaryMatSpec` list to define auxiliary processing requirements (e.g. tooling specs, custom gases, or strap types).

---

## 3. Core Business Operations

The domain logic is orchestrated through CDI business services and event publishers.

### A. Order Lifecycles & Synchronizations
The `ProdOrderService` encapsulates transactional CRUD and status flows:
*   **Synchronization (`sync`):** Upserts a production order into the database. Deep-merges routing steps, capable plant units, and material specs.
*   **Activation (`activate`):** Transitions the order state to `ACTIVE`, enabling scheduler engines or tracking modules to process it. Fires `TO_BE_ACTIVATED` and `ACTIVATED` domain events.
*   **Closure (`close`):** Transitions the order state to `CLOSED` after physical fulfillment is completed. Fires `TO_BE_CLOSED` and `CLOSED` domain events.
*   **Deletion (`delete`):** Triggers Cascade-On-Delete routines to wipe associated steps, alternative plant configurations, and specs. Fires `TO_BE_DELETED` and `DELETED` domain events.

### B. Route Graph Builders
Developers can utilize the **`ProdRouteBuilder`** fluent API helper to construct operational routes within services or test environments. It provides high-level constructs:
*   `step(ProdStepData)`: Appends an operational step sequentially.
*   `branchStep(ProdStepData)` / `fork()`: Creates alternative process branches.
*   `joinStep(ProdStepData)`: Merges parallel processing forks back into a single operational stream.
*   `subStep(...)`: Appends sub-step links for hierarchical step structures.

### C. Issue & Hold Locks
`ProdOrder` implements the `IssueOwnerIf` interface, integrating with the **`ProdOrderIssueContainer`**:
*   Enables quality, execution delay, or scheduling issues (`ProdOrderIssue`) to be directly assigned to production orders.
*   Supports order hold locks and blocks (`Blocks`) to suspend schedulers or execution systems if severe defects or scheduling conflicts occur.

---

## 4. Integration & Messaging Ingestions

Production orders and status transitions are continuously ingested from external systems (ERP/MES) inside the `-com` module:

*   **Order Syncs (`ProdOrderMesgHandler`):** Listens to `ProdOrderMesg` events on the bus. If the message `isRemoved()` flag is true, it triggers order deletion. Otherwise, maps DTOs via MapStruct and calls `service.sync(...)` to process the upsert.
*   **Status Updates (`ProdOrderStatusMesgHandler`):** Listens to `ProdOrderStatusMesg` events on the bus. Resolves natural IDs to local orders, and executes status transitions (`CLOSED` -> `close()`, `ACTIVE` -> `activate()`).

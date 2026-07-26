# PSImetals Service Platform (SP) - Metallurgical & Domain Glossary

This glossary acts as the single source of truth for metallurgical terminology and domain mappings across the PSImetals Service Platform (`sp-met-global` and `sp-prod` workspaces). It aligns real-world physical steel mill concepts with their digital equivalents in the platform's codebase.

---

## 1. Physical Material Hierarchy (`mat` Domain)

*   **AbstractMat (Base Entity):** The abstract ancestor of all material entities. Holds custom metadata (`AbstractMatData`) and unique business codes (e.g., Coil ID, Slab ID).
*   **Mat (Abstract Material Unit):** Represents physical, countable material units. Tracks defects (`MatIssue`), holds/blocks (`Blocks`), locations (`MatLocationLink`), and lifecycle status (`MatStatus`).
*   **PieceMat (Discrete Material):** Countable physical items with standard geometric dimensions (length, width, thickness, outer/inner diameter). Examples: Coils, Slabs, Plates, Sheets. Geometries are dynamically calculated using qualified `GeometryCalculator` implementations.
*   **Heat (Liquid Melt):** Liquid metal batches in steelmaking, furnaces, or continuous casters. Uniquely identified by a Heat ID.
*   **Bundle / Lot (Grouped Material):** Grouping of multiple material pieces (e.g., bundles of steel bars, lots of bulk raw materials).
*   **UncountableBulk (Bulk Material):** Non-countable resources like fluids, chemical additives, or scrap metal piles.

---

## 2. Spatial Topologies & Sequences (`plantunit` Domain)

*   **PlantUnit (Base topology):** Abstract representation of physical plant locations.
*   **Line (Production Line):** High-level active processing lines (e.g., Continuous Casters, Hot Rolling Mills, Galvanizing Lines). Lines have entries (`storageAreasEntry`), exit buffers (`storageAreasExit`), and inline positions (`storageAreasInLine`).
*   **StorageArea (Storage Position):** Warehouses, yards, stacks, and transport stops. Storage areas hold hierarchical paths (e.g., `YardA/RowB/Bay3/Slot2`) and are governed by access strategies.
*   **LocationManager (Access Strategy):** Handles physical stacking rules:
    *   **FifoLocationManager (FIFO):** First-In-First-Out (e.g., tunnel furnaces or conveyor belts). Items are only accessible from the front (`accessOrder == 0`).
    *   **LifoLocationManager (LIFO):** Last-In-First-Out (e.g., physical stacks of steel plates or coils). Stacking a new item shifts down the access order of existing ones. Only the top item (`accessOrder == 0`) is accessible.
    *   **RandomLocationManager (Random):** General open yard blocks. All items are directly accessible (`accessOrder == 0`).
*   **StorableIf (Interface):** Implemented by any physical entity tracked spatially across storage areas.

---

## 3. Order Management & Routings (`prodorder` Domain)

*   **ProdOrder (Production Order):** Represents active manufacturing paths, input/output quantity tolerances, and material specs. Acts as the link to external ERP/planning systems.
*   **ProdStep (Process Step):** A single manufacturing operation (e.g., Caster step, Mill step). Steps are linked together to form a Directed Acyclic Graph (DAG) using `RouteLink` entities to represent branching and joining (e.g., slab splitting or coil bundling).
*   **MatSpec (Material Specification):** Defines geometric limits (`StdGeometry`), target grade specifications, and prioritised material variants for an order or a specific process step.

---

## 4. Scheduling & Bindings (`allocation` Domain)

*   **Allocation (Physical Binding):** A concrete, spatial-temporal binding between a discrete `PieceMat` and a planning `ProdStep`.
    *   **BEFORE Relation (INPUT):** The material is staged as an input to be processed.
    *   **AFTER Relation (OUTPUT):** The material represents a physical output produced by that step.
*   **Reservation (Logical Binding):** Logical quantity reservation of bulk or lot materials (`Lot`) mapped to a planning step (rather than individual pieces).
*   **FeasibleMatchRule (Compatibility Guard):** Checks if a material matches the planned geometric and steel grade limits of a process step before allowing the allocation.

---

## 5. Event Logs & Rollbacks (`matevent` Domain)

*   **MatEvent (Tracking Event):** Log records of physical or chemical operations on materials (e.g., `ChargingEvent`, `DischargingEvent`, `RelocationEvent`).
*   **Snapshot State (MatExtendedDataCommand):** Stores the complete pre-operation state (metadata, location, and allocations) of a material before an event occurs.
*   **Undo Pattern (Compensation):** The rollback engine (`MatEventUndoService`) that cancels tracking events (setting status to `CANCELED` but retaining the record for audit) and restores the material's state using snapshots and specialized CDI handlers.
*   **UndoClosureBuilder (Atomic Closure):** Computes the atomic group of events that must be rolled back together, enforcing that no subsequent events have occurred on the material.

---

## 6. Key Codebase Architectural Conventions

*   **Repository Pattern (Ports & Adapters):**
    *   **Repository Interfaces (`*RepositoryIf`):** Defined as ports in the `-business` module. They must extend `RepositoryBaseIf<Entity, IdType>`.
    *   **Repository Implementations (`*Repository`):** Defined as JPA adapters in the `-infrastructure` module. They must extend `AbstractPanacheRepositoryBase<Entity, IdType>`, implement the respective `*RepositoryIf` interface, and be annotated with `@ApplicationScoped`.
*   **AppService Pattern (API & Application Layer):**
    *   **AppService Interfaces (`*AppServiceIf`):** Defined in the `-com-api` module. They act as public API contracts (REST / endpoints).
    *   **AppService Implementations (`*AppService`):** Defined in the `-com` module, implementing the respective `*AppServiceIf` interface and annotated with CDI scopes (e.g., `@ApplicationScoped`).
*   **MapStruct Extensible Mappers:**
    *   Written as a `public abstract class` extending `ExtensibleEntityMapperIf<Data, Entity, DTO>`. This supports full serialization between snapshot data, JPA entities, and DTOs.
    *   Annotated with MapStruct `@Mapper(config = ExtensibleEntityMappingConfig.class, ...)`.
*   **Localized Base Exceptions:**
    *   Exceptions extend the component's base exception (e.g., `SpProdtrackingException`, which extends `BaseException`).
    *   They define constructors accepting `Object... aParams` to allow localized message parameter interpolation.

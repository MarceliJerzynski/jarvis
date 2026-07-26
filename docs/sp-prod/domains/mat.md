# PSImetals Service Platform (SP) - Material (`mat`) Domain Guidelines

This document provides a comprehensive overview of the **Material (`mat`)** domain component located within `sp-met-global/components/mat`. It outlines the module's architecture, dependencies, core material structures, and the physical and logical operations that can be performed on materials.

---

## 1. Module & Architecture Guidelines

The `sp-met-global-mat` component strictly adheres to the standardized, multi-module architecture of the PSImetals Service Platform. For detailed, layer-by-layer architectural guidelines, design principles, and directory structures, please refer to the dedicated architecture documentation:

*   [**`-com-api` Layer** (API Contracts & Payloads)](../architecture/com-api.md)
*   [**`-com` Layer** (Communication & Orchestration)](../architecture/com.md)
*   [**`-business` Layer** (Domain Model & DDD Rules)](../architecture/business.md)
*   [**`-infrastructure` Layer** (JPA Mappings & Ports/Adapters)](../architecture/infrastructure.md)
*   [**`-liquibase` Layer** (Schema Evolutions)](../architecture/liquibase.md)
*   [**`-test` Layer** (Separated Automated Tests)](../architecture/test.md)
*   [**`-ui` Layer** (Angular & Frontend)](../architecture/ui.md)

---

## 2. Material Hierarchy & Data Structure

Materials are designed using a rich object inheritance model (mapped with JPA `@Inheritance(strategy = InheritanceType.JOINED)`) to represent both countable physical products, liquid intermediates, and bulk quantities.

```text
AbstractMat (Base Abstract Entity)
   └── Mat (Abstract Material Unit)
          ├── PieceMat (Discrete physical products e.g., coils, slabs, plates)
          ├── Heat (Liquid metal / melt melts)
          ├── Bundle (Bundled materials)
          ├── Lot (Material lots)
          └── UncountableBulk (Non-countable bulk material e.g., raw gravel, powder, fluids)
```

### Core Entity Definitions

#### 1. `AbstractMat` (Base Class)
*   **Identities:** Primary identifier `id` (`MatId`) and custom unique natural identifier `businessCode` (e.g., Coil Number or Heat ID).
*   **Properties:** Reference to standard catalog configurations (`MatType`, `MaterialMaster`), current quantity/amount (`Amount`), and steel grade details (`GradeSpec`).
*   **Extensibility:** Leverages a generic custom meta-data merging mechanism (`AbstractMatData`) to dynamically handle custom fields.

#### 2. `Mat` (Abstract Material Unit)
*   **Location Tracking:** References a `MatLocationLink` (which maps to physical Locations like storage areas or lines).
*   **Gross Weight:** Tracked via `grossWeight` (`Weight`).
*   **Holds & Blocks:** Managed by the `blocks` property (`Blocks` enum - e.g., quality hold, custom block) to lock materials from production.
*   **Quality Issues:** Holds a list of active defects (`MatIssue` entities).
*   **Test Results:** Associated with characterization test results (`TestResult` entities).
*   **Planned Connectors:** `plannedCode` connects casting output materials (planned slabs) with hot rolling input.
*   **Lifecycle Status:** Managed via `MatStatus` enum:
    *   `ANNOUNCED`: Expected/announced in the yard but not yet physically active.
    *   `PRODUCTIVE`: Fully active, available on the shop floor or yard.
    *   `PLANNED`: Material planned for future production.
    *   `CONSUMED`: Inactive. Material was used to produce another material.
    *   `BOOKED_OUT`: Inactive. Material shipped out of the system.
    *   `CANCELLED`: Inactive. Cancelled production.

#### 3. `PieceMat` (Discrete Materials)
*   Models concrete physical products (such as slabs, coils, plates).
*   **Properties:** Shape-specific dimensional geometries (`StdGeometry` holding length, width, thickness, outer/inner diameter, etc.), specialized piece weight (`Weight`), and `multiPiece` flag.
*   **Geometry Completion:** Employs CDI-qualified `GeometryCalculator` implementations (e.g., `CoilGeometryCalculator`, `HollowCylinderGeometryCalculator`) to dynamically compute/complete geometrical properties (e.g., inner/outer diameter from weight and width).

#### 4. `Heat` (Liquid Melts)
*   Models molten metal batches in meltshops or casters.
*   Holds custom metadata and properties via `HeatData`.

#### 5. `UncountableBulk` (Bulk Materials)
*   Models non-countable warehouse items (fluid, gravel, scrap piles).
*   Holds properties via `UncountableBulkData`.

#### 6. `Bundle` & `Lot`
*   Models groupings of individual materials, holding bundle types, groupings, and specific metadata.

---

## 3. Supported Material Operations

The domain supports a wide range of physical, quality-related, and lifecycle operations executed via domain services and application APIs:

### A. Lifecycle & Status Transitions
*   **Book-In (`create`):** Registers new material into the system. Invoked through `AbstractMatService` (standard domain event triggers) or `MatSyncAppService` (DataSync ingestion). Generates a `MatBookInDomainEvent`.
*   **Update (`update`):** Modifies material properties. DataSync updates fire a `MatSyncDomainEvent` to synchronize downstreams.
*   **Consume (`consume`):** Invoked when material is processed to make a new product. Validates that the material has been cleared of any physical location, sets quantity to `0`, and changes status to `CONSUMED`.
*   **Book-Out (`bookOut`):** Marks material as shipped or removed from plant inventories. Changes status to `BOOKED_OUT`.
*   **Reactivate (`reactivate`):** Restores material previously in `BOOKED_OUT` status back to `PRODUCTIVE`.
*   **Delete / Cancel (`remove`):** Removes material from the repository (firing `beforeDelete` and `deleted` domain events).

### B. Quality Issues & Defects Management
Quality defects are managed through the internal domain delegate `MatIssueContainer`, which enforces a strict rule: **Defects/issues can only be registered on materials currently in the `PRODUCTIVE` status.**
*   **Save Issue (`saveIssue`):** Adds a quality defect (`MatIssue`) to the material. Automatically caps or completes coordinates/dimensions (`Area`) for issues on `PieceMat` relative to the piece's physical geometry.
*   **Settle Issue (`settleIssue`):** Marks a registered quality issue as resolved/settled, which may release any active holds or blocks.
*   **Delete Issue (`deleteIssue`):** Removes a defect from the material by local ID.
*   **Defect Hold Control (`setBlocks`):** Locks the material from relocation or production processing depending on the assigned defect's block triggers.
*   **Defect Propagation:** Connects issues across the material pedigree tree. A material's quality issue can reference a `source` issue (the defect on the parent material, e.g., slab) and populate `targets` (defects on subsequent children materials, e.g., rolled coil).

### C. Physical Tracking & Relocation
Material relocations are handled by the `MatRelocationService` (extending `RelocationService<Mat>`):
*   **Relocate (`relocate`):** Moves material to a different physical location (e.g. storage yard position, Line).
*   **Consistency Guards:** Automatically ignores outdated relocation messages by tracking timestamps to prevent out-of-order execution.
*   **Charge Checks:** Developers can use `isCharged()` to verify if a material is active inside a production Line, and retrieve the respective active line using `getChargedToLine()`.
*   Updates the `MatLocationLink` and fires `MatRelocationDomainEvent`.

### D. Testing & Quality Characterization
*   **Associate Test Result (`addMat`):** Links test/characterization records (`TestResult` entities) containing characteristic values (`TestCharResult`) to the material unit.
*   **Dissociate Test Result (`removeMat`):** Detaches quality test results from the material unit.

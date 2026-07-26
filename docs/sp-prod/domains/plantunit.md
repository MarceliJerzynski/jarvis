# PSImetals Service Platform (SP) - Plant Unit (`plantunit`) Domain Guidelines

This document provides a comprehensive developer guideline and structural overview of the **Plant Unit (`plantunit`)** core domain component located within `sp-met-global/components/core`. It covers the system's architecture, hierarchical structures, location tracking mechanisms, sequence managers, and physical relocation services.

---

## 1. Module & Architecture Guidelines

The `plantunit` domain is a part of the **MET Global Core** layer. It provides fundamental topologies (lines, yards, warehouses) and physical storage tracking utilized by business modules such as Material Tracking (`mat`), Scheduling (`laps`), and Production.

This domain is structured across decoupled modules following the platform's modular conventions:
*   [**`-com-api` Layer** (API Contracts & Payloads)](../architecture/com-api.md) — Exposes plant topology DTOs (`LineDto`, `StorageAreaDto`, `PlantUnitScopeDto`) and DataSync message schemas (`LineDataSyncElementDataDto`, `StorageAreaMsg`).
*   [**`-com` Layer** (Communication & Ingestion)](../architecture/com.md) — Implements DataSync event handlers (`LineDataSyncHandler`, `StorageAreaMsgHandler`) and application endpoints (`PlantUnitAppService`).
*   [**`-business` Layer** (Domain Model & Relocation Logic)](../architecture/business.md) — Defines base models (`PlantUnit`, `Line`, `StorageArea`), the physical tracking ports (`StorableIf`, `LocationLink`), sequential access strategies (`LocationManager`), and the generic `RelocationService`.
*   [**`-infrastructure` Layer** (JPA Mappings & Repositories)](../architecture/infrastructure.md) — Implements JPA/database persistence adapters (`StorageAreaRepository`, `LineRepository`).
*   [**`-liquibase` Layer** (Schema Evolutions)](../architecture/liquibase.md) — Defines the database schemas for physical locations, lines, and location links.
*   [**`-test` Layer** (Separated Automated Tests)](../architecture/test.md) — Contains the automated unit and integration tests (e.g., LIFO/FIFO relocation tests).

---

## 2. Plant Unit Topologies & Hierarchy

The physical plant layout is designed around an extensible hierarchical model mapped with JPA `@Inheritance(strategy = InheritanceType.JOINED)`.

```text
PlantUnit (Base Abstract Entity)
   ├── Line (Production lines - e.g., casters, rolling mills)
   ├── StorageArea (Warehouses, yards, in-line buffers, transport stops)
   └── Specialized Units: Inventory, Shipping, Supply, Transport
```

### Core Entity Definitions

#### 1. `PlantUnit` (Base Class)
*   **Identities:** Primary identifier `id` (`PlantUnitId`).
*   **Scopes:** Associated with a `PlantUnitScope` which defines logical subsets of plant elements for security, user roles, or planning boundaries.
*   **Properties:** Display metadata (`displayName`, `displayText`, `displaySequenceNumber`) and production mappings (`ProdStepType2PlantUnit`).

#### 2. `Line` (Production Lines)
*   Models active plant processing lines (such as a blast furnace, continuous caster, hot strip mill, or coating line).
*   **Hierarchical Sub-lines:** References a parent `containerLine` and contains a set of nested `subLines` allowing arbitrarily deep line hierarchies.
*   **Storage Associations:** Connects physical production processes to material storage by mapping three distinct types of `StorageArea` groups:
    *   **Entry Areas (`storageAreasEntry`)**: Storage areas where raw materials or parts are staged prior to line processing. Includes a `defaultStorageAreaEntry`.
    *   **In-Line Areas (`storageAreasInLine`)**: Buffer positions directly integrated on the line itself (e.g., rollers, furnaces, waiting slots). Includes a `defaultStorageAreaInLine`.
    *   **Exit Areas (`storageAreasExit`)**: Storage areas where finished or intermediate products are placed after processing. Includes a `defaultStorageAreaExit`.
*   **Properties:** `capacityRelevant`, `schedulingRequested` flags, `type` (`LineType` reference), and `erpResourceId` (for external ERP synchronization).

#### 3. `StorageArea` (Physical & Logical Storage)
*   An abstraction for any place where physical objects (materials, equipment, tools) can be stored or positioned.
*   **Hierarchical Paths:** Supports recursively nested sub-areas (`container` and `subAreas` list). A storage area's alphanumeric code represents a path from the root separated by `'/'` (e.g., `YardA/RowB/Bay3/Slot2`).
*   **Types (`StorageAreaType`):**
    *   `YARD`: General warehouse yard, inventory area, or stock zone.
    *   `LINE`: Internal in-line buffer or waiting position inside a production line.
    *   `STOP`: A loading or unloading zone for Means of Transport (MOTs) (e.g., truck stop, wagon stop).
    *   `EQUIP`: Storage positions on specialized plant equipment.
*   **Properties:** `accessStrategy` (`StorageAreaAccessStrategy` enum), `ownershipMode` (`OwnershipMode` enum), and `localCode` (local identifier relative to parent container).

---

## 3. Location Management & Sequence Strategies

To support physical material stacking and sequence constraints (such as conveyor belts or plate stacks), the platform utilizes **`LocationManager`** strategies.

### The `LocationManager` Model
`LocationManager` is an `@Immutable` JPA entity mapped as a `@Subselect` on the `STORAGEAREA` table. It is responsible for organizing the order and accessibility of physical items placed inside a specific `StorageArea`.

Each storage area's `StorageAreaAccessStrategy` resolves to a concrete `LocationManager` implementation using JPA discriminator annotations:

#### 1. `FifoLocationManager` (Discriminator: `"FIFO"`)
*   Models First-In-First-Out sequences (e.g., conveyor belts or tunnel furnaces where items enter one end and must leave from the opposite end).
*   **Behavior:** Newly added items are appended at the end (access order index is set to `maxAccessOrder + 1`).
*   **Order Constraints:** Items are ordered. An item can only be legally removed when its `accessOrder == 0` (i.e. it is at the front).

#### 2. `LifoLocationManager` (Discriminator: `"LIFO"`)
*   Models Last-In-First-Out sequences (e.g., a physical stack of plates or coils where new products are stacked on top of old ones).
*   **Behavior:** Newly added items are placed on top (access order index is set to `0`).
*   **Shifting:** Automatically increments the `accessOrder` of all existing items in the stack by `1`.
*   **Order Constraints:** Items are ordered. Only the top item (`accessOrder == 0`) is directly accessible.

#### 3. `RandomLocationManager` (Discriminator: `"NONE"`)
*   Models standard open storage zones where all items are randomly accessible (e.g., open yard blocks).
*   **Behavior:** Always assigns access order index `0` to all items.
*   **Order Constraints:** Unordered. All stored items are directly accessible.

---

## 4. Physical Relocation & Tracking

The physical tracking of items moving across the plant floor is governed by a unified interface contract and relocation services.

### Core Tracking Constructs

#### 1. `StorableIf` (Interface)
Any domain object that can be physically stored or relocated must implement the `StorableIf` interface:
*   `getLocationLink()`: Returns the item's current location link relationship.
*   `getLocation()`: Utility returning the embedded `Location` value object (defaults to `Location.NONE`).
*   `getBusinessCode()`: Unique business code (e.g., Coil Number, Container ID).
*   `isPhysical()`: Verifies if the object has physical existence (only physical items can have locations).

#### 2. `LocationLink` (Base Association Entity)
An abstract entity (mapped with `@Inheritance(strategy = InheritanceType.JOINED)`) representing the physical association of a `StorableIf` object with its current location.
*   **Properties:**
    *   `area` (`StorageArea`): The storage area entity being occupied.
    *   `storageManager` (`LocationManager`): Reference to the area's sequence manager.
    *   `accessOrder`: The item's sequence index in the area (managed by the `LocationManager`). `0` indicates the item is directly accessible.
    *   `code`: Alphanumeric code of the position.
    *   `relocationTime`: The timestamp of when the relocation occurred.

#### 3. `Location` (Value Object)
An `@Embeddable` JPA value object representing a snapshot of a location.
*   Contains an `area` reference, position `code`, `relocationTime`, and `accessOrder`.
*   Includes `Location.NONE` to model unknown or empty locations (e.g., before booking-in).

---

### The Relocation Workflow
The abstract `RelocationService<T extends StorableIf>` handles the transactional physical movement of items across the plant:

1.  **Physical Guard:** Verifies if the storable object `isPhysical()` is true (throws `StorableCannotBeRelocatedException` if false).
2.  **Redundancy Check:** If the requested target location matches the item's current location, the relocation is skipped.
3.  **Source Eviction:** If the item was previously assigned to a physical storage area, the service invokes `locationManager.remove(storable)` to release its spot and (if ordered) recalculate and shift the access orders of the remaining items.
4.  **Ownership Check:** Verifies if the current system has relocation permission over the target `StorageArea`. If `ownershipMode` restricts external movements and the relocation was system-initiated, throws `IncorrectStorageOwnershipException`.
5.  **Target Placement:** Ingests the item into the target area by calling `locationManager.add(storable, targetLocation.getAccessOrder())`. The manager recalculates local sequences (e.g., shifting stacks on LIFO).
6.  **Timestamping:** Updates the `LocationLink` with the new position code and relocation timestamp.
7.  **Event Notification:** Fires a CDI `RelocationDomainEvent` (subclassed by concrete domains, e.g., `MatRelocationDomainEvent`) for downstream synchronization.

---

## 5. Master Data Ingestion & DataSync

Plant units (lines, storage areas, and scopes) are imported and synchronized from external master data sources or MES orchestrators. This is managed in the `-com` module:

*   **Handlers:** Classes like `LineDataSyncHandler`, `StorageAreaMsgHandler`, and `PlantUnitScopeDataSyncHandler` listen to bus messages.
*   **Mappings:** Ingested JSONs are parsed into DTOs and mapped to JPA entities via MapStruct mappers (e.g., `LineDataMapper`, `StorageAreaDataMapper`), automatically creating or updating the local plant unit registries.

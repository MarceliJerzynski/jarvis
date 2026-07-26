# PSImetals Service Platform (SP) - Architecture Guidelines

Each business component is strictly divided into decoupled sub-modules (Maven modules) to preserve clean boundaries and enforce correct dependency directions. This document contains guidelines for each layer of the Clean Architecture.

---

## 1. `-com-api` Module (API Definition Layer)

The `-com-api` module is the API definition layer of the component.

### Key Guidelines & Conventions
*   **Purpose:** It serves as the decoupled contract for the component's public interface.
*   **Contents:**
    *   Consists primarily of `AppServiceIf` interfaces containing the definitions of the API endpoints.
    *   Contains Data Transfer Objects (DTOs) and API schemas used for serialization and communication.
    *   Contains DataSync payload definitions and element data DTOs (e.g., `*DataSyncElementDataDto`) used for external data ingestion and synchronization.
*   **Rules:**
    *   Must not contain any business or database logic.
    *   Acts as a shared contract that can be depended on by other components or the presentation layer.

---

## 2. `-com` Module (Communication & Application Layer)

The `-com` module is the communication and application layer of the component.

### Key Guidelines & Conventions
*   **Purpose:** Orchestrates high-level application flows and exposes endpoints to external clients or other services.
*   **Dependencies:**
    *   Depends on **`-com-api`** (to implement its interfaces).
    *   Depends on **`-business`** (to delegate core business logic).
*   **Contents:**
    *   Mainly consists of `AppService` classes implementing the `AppServiceIf` interfaces declared in `-com-api`.
    *   Contains REST controllers, endpoint routing, and event/integration message handlers.
    *   Contains DataSync bus event handlers (implementing `BusEventHandlerIf` or annotated with `@BusEventHandler`) and synchronization application services (`*SyncAppService` inheriting from standard base sync services) to process incoming master and transactional data.
*   **Rules:**
    *   Should only handle orchestration, request translation (DTO <-> Domain), transactions, and security checks.
    *   Delegates all actual business calculations and state transitions to the `-business` layer.

---

## 3. `-business` Module (Domain Model & Core Business Layer)

The `-business` module is the domain model and core business layer of the component. It represents the pure Domain Layer in Domain-Driven Design (DDD).

### Key Guidelines & Conventions
*   **State Management (Encapsulation):**
    *   Each domain entity must manage its own internal state.
    *   Setter methods must be `private` (or completely omitted) to prevent external modification of entity states and maintain rich domain encapsulated behaviors.
*   **Aggregates:**
    *   Within an aggregate, only the **Aggregate Root** should expose `public` methods.
    *   Non-root entities belonging to the aggregate must have `package-protected` methods and must be invoked/managed exclusively through the Aggregate Root.
*   **Dependency Directions:**
    *   The `-business` module is completely independent of all other modules in the application. It has **no** dependency on `-com`, `-infrastructure`, or `-com-api`.
    *   However, it is not completely free of all dependencies: it depends on Hibernate for mapping annotations.
    *   Other modules, like `-com`, depend directly on `-business`.

---

## 4. `-infrastructure` Module (Infrastructure & Persistence Layer)

The `-infrastructure` module is the infrastructure and persistence layer of the component.

### Key Guidelines & Conventions
*   **Contents:**
    *   Contains database mappings, JPA entity implementations, persistence repositories, and external gateway integrations.
*   **Dependency Inversion Principle:**
    *   Because the `-business` module is independent of `-infrastructure`, dependency inversion is applied here.
    *   The `-business` module defines the repository interfaces (as Domain/Application "ports"), and the `-infrastructure` module implements them (as "adapters").

---

## 5. `-liquibase` Module (Database Migrations)

The `-liquibase` module is responsible for database migrations and schema evolution.

### Key Guidelines & Conventions
*   **No Direct SQL DDL:** Direct or manual SQL DDL changes are forbidden.
*   **Liquibase Changelogs:**
    *   All schema changes (tables, indexes, columns, constraints) must be declared in XML format inside the `-liquibase` module's resources.
    *   Location: `components/<component>/sp-prod-<component>-liquibase/src/main/resources/liquibase/`
*   **Evolution:** Ensures identical database structures across local, testing, development, and production environments.

---

## 6. `-test` Module (Testing Layer)

The `-test` module is a dedicated, separate testing layer for each component.

### Key Guidelines & Conventions
*   **Separation of Tests:**
    *   **No tests inside business or infrastructure modules:** All unit, integration, and component tests must reside within their designated `-test` sibling module (e.g., `components/prodtracking/sp-prod-prodtracking-test/`). This is an intentional design choice.
*   **Frameworks:**
    *   Tests utilize **JUnit 5**, **QuarkusTest**, and **Mockito**.
    *   Many tests extend `BusinessComponentTestBase` to configure mock contexts and setup transactions.
*   **Code Coverage:**
    *   Analyzed using **JaCoCo**. Exclusion patterns are defined for generated JPA models (`*Gen.*`, `*Id.*`, `*_*`).

---

## 7. `-ui` Module (User Interface Layer)

The `-ui` module is the user interface layer (where applicable, such as LAPS).

### Key Guidelines & Conventions
*   **Technology Stack:** Built using **Angular** and managed by **PNPM**.
*   **Contents:**
    *   Exposes components, web assets, and shared UI libraries.
*   **Local Development:**
    *   Located in: `components/laps/sp-prod-laps-ui/sp-prod-laps-ui-web/src/main/angular`
    *   Allows proxy configurations to connect directly to local backend or remote dev clusters.

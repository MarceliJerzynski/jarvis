# PSImetals Service Platform (SP) Production - Developer Guidelines & Instructions

This workspace contains the sources for the **PSImetals Service Platform (SP) Production** domain. It is a modern, Quarkus-based microservice architecture responsible for managing line scheduling, material allocation, and production tracking in metal processing plants (mills, meltshops, and rolling facilities).

---

## 1. Project Overview

The project is structured as a multi-module Maven repository containing three core business domains:
*   **LAPS (Line Allocation and Planning System / Scheduling):** Manages production planning, line allocation, and task scheduling. Includes an Angular-based web UI.
*   **Line Schedule (`lineschedule`):** Handles the ingestion, removal, and overall management of line schedules.
*   **Production Tracking (`prodtracking`):** Tracks physical materials, movements, and production events on the plant floor.

> 💡 **Repository Distribution Note:** The vast majority of the backend codebase, business logic, and test coverage resides within the **`prodtracking`** component, rather than `laps` or `lineschedule`. The only major exception is the **User Interface (UI)**, which is located entirely within the **`laps`** component (`sp-prod-laps-ui`).

### Core Technologies
*   **Backend:** Java 21+, Quarkus, Jakarta CDI, Hibernate ORM, Lombok.
*   **Frontend:** Angular (v20+), PNPM (package manager), Ag-Grid, Highcharts.
*   **Database:** PostgreSQL / Oracle (depending on target), Liquibase for schema migrations.
*   **Deployment:** Docker, Kubernetes (Local development target is Rancher Desktop via Helm).
*   **Testing:** JUnit 5, QuarkusTest, Mockito, JaCoCo for code coverage.

---

## 2. Directory Structure & Architecture

```text
C:\Projects\sp-prod\
├── pom.xml                               # Root parent Maven project
├── applications\
│   └── laps\
│       └── sp-prod-app-laps-deployable\  # Executable Quarkus application for LAPS
├── components\
│   ├── laps\                             # LAPS business component
│   │   ├── sp-prod-laps-business\        # Core LAPS business logic
│   │   ├── sp-prod-laps-com\             # Communication integration layer
│   │   ├── sp-prod-laps-com-api\         # Internal/External API declarations
│   │   ├── sp-prod-laps-infrastructure\  # Repositories & JPA entities
│   │   ├── sp-prod-laps-liquibase\       # Database schema migrations
│   │   ├── sp-prod-laps-test\            # Dedicated testing module for LAPS
│   │   └── sp-prod-laps-ui\              # Angular user interface modules
│   ├── lineschedule\                     # Line Schedule business component
│   └── prodtracking\                     # Production Tracking business component
├── docs\                                 # Extensive technical documentation
│   ├── design\                           # System designs (e.g., UndoMatEvents, BookProductionAlgo)
│   ├── development\                      # Developer notes (e.g., defect propagation)
│   └── instructions\                     # Framework setup manuals (Camunda, JaCoCo, etc.)
├── kubernetes\                           # Helm charts and local k8s deploy scripts
└── testdata\                             # Sample JSONs, imports, and data sync scopes
```

### Architectural Conventions
The project is designed using **Domain-Driven Design (DDD)** principles with the core intent of following **Clean Architecture** (slightly modified/adapted to fit the modular architecture of the PSImetals platform).

Each component is strictly divided into decoupled sub-modules to preserve clean boundaries and enforce correct dependency directions. Please read the modular instructions for each layer in the consolidated [**Architecture Guidelines**](./architecture.md):
1.  **[-com-api](./architecture.md#1--com-api-module-api-definition-layer)**: API definition module. Consists primarily of `AppServiceIf` interfaces containing endpoint definitions, along with DTOs and API schemas.
2.  **[-com](./architecture.md#2--com-module-communication--application-layer)**: Communication and application layer module. It depends on `-com-api` and `-business`. It consists mainly of application services (`AppService` classes) implementing the `AppServiceIf` interfaces declared in `-com-api`.
3.  **[-business](./architecture.md#3--business-module-domain-model--core-business-layer)**: Domain model and core business layer (DDD). Each domain entity manages its own state (private setters). Within aggregates, only the Aggregate Root has public methods (non-root entities use package-protected methods). Independent of all layers except Hibernate.
4.  **[-infrastructure](./architecture.md#4--infrastructure-module-infrastructure--persistence-layer)**: Infrastructure layer module. Contains database mappings (JPA) and repository implementations. Employs Dependency Inversion (implementing repository interfaces defined in `-business`).
5.  **[-liquibase](./architecture.md#5--liquibase-module-database-migrations)**: XML database migration files.
6.  **[-test](./architecture.md#6--test-module-testing-layer)**: Separate test project containing all unit/integration tests for that component.
7.  **[-ui](./architecture.md#7--ui-module-user-interface-layer)**: Standardized web assets and frontend builds (if applicable).

<!-- Automatically import general architecture guidelines into session memory -->
@./architecture.md

<!-- Automatically import domain guidelines into session memory -->
@./domains/allocation.md
@./domains/mat.md
@./domains/matevent.md
@./domains/plantunit.md
@./domains/prodorder.md

### Business Domains
To understand the core business domains, physical models, and workflows implemented across the platform, please refer to the dedicated domain documentation guidelines:

> ⚠️ **Disclaimer:** Domain docs describe the intended structure but may drift from actual code over time. When in doubt, or before performing non-trivial changes, always verify against the actual entity and service classes in the codebase.
*   [**Allocation (`allocation`) Domain**](./domains/allocation.md): Physical bindings of materials to process steps (BEFORE/AFTER directions), bulk quantity reservations, and compatibility matching rule guidelines.
*   [**Material (`mat`) Domain**](./domains/mat.md): Core material entities (PieceMat, Heat, etc.), status transitions, quality issues, and relocation guidelines.
*   [**Material Events (`matevent`)**](./domains/matevent.md): Material tracking events, history, and the undo/compensation patterns.
*   [**Plant Unit (`plantunit`) Domain**](./domains/plantunit.md): Core plant topologies (Lines, StorageAreas), sequential stack access strategies (LIFO/FIFO LocationManagers), and physical item relocation.
*   [**Production Order (`prodorder`) Domain**](./domains/prodorder.md): Routing paths, operational process steps (DAG/RouteLinks), material specs (variants, geometries, weights), and alternative equipment assignments.

---

## 3. Building and Running

### Backend Build (Maven)
To clean, compile, and package the entire backend project:
```bash
mvn clean install
```
*   **Build UI skip:** If you only want to build the backend services and skip compiling Angular assets:
    ```bash
    mvn clean install -Dskip-ui
    ```
*   **Build Service skip:** If you want to skip building backend components and focus only on the UI:
    ```bash
    mvn clean install -Dskip-service
    ```

### Local Frontend Development (Angular)
The LAPS frontend is located in:
`components/laps/sp-prod-laps-ui/sp-prod-laps-ui-web/src/main/angular`

To run locally with a proxy connection to your local backend/dev cluster:
1.  Navigate to the directory:
    ```bash
    cd components/laps/sp-prod-laps-ui/sp-prod-laps-ui-web/src/main/angular
    ```
2.  Install dependencies:
    ```bash
    pnpm install
    ```
3.  Start with proxy to local backend (e.g., Quarkus Dev Mode):
    ```bash
    pnpm run start:app-proxy
    ```
4.  Standard standalone start:
    ```bash
    pnpm run start:app
    ```

### Local Kubernetes Deployment (Helm & Rancher Desktop)
Scripts are provided in the `/kubernetes` folder to package and upgrade deployment charts:
*   **Deploying to Local K8s:** Run `kubernetes/up.cmd` (runs `mvn clean install` first, then executes the local Helm upgrade in namespace `sp-laps`).
*   **Uninstalling from Local K8s:** Run `kubernetes/down.cmd`.

---

## 4. Testing Guidelines

### Test Separation Rule
*   **No tests inside business/infrastructure modules:** To preserve project cleanliness and proper build separation, all test classes must reside within their designated `-test` sibling modules (e.g., `components/prodtracking/sp-prod-prodtracking-test/`).

### Running Tests
*   Run all tests across the repository:
    ```bash
    mvn test
    ```
*   Run tests for a specific module:
    ```bash
    mvn -pl components/prodtracking/sp-prod-prodtracking-test test
    ```
*   Run a single test case:
    ```bash
    mvn -pl components/prodtracking/sp-prod-prodtracking-test -Dtest=MatEventUndoServiceTest test
    ```

### JaCoCo Code Coverage
The workspace is configured to generate code coverage reports via JaCoCo. Ensure that new tests are properly integrated so coverage remains high. For detailed setup and exclusion patterns (e.g., excluding generated JPA meta-models `*Gen.*`, `*Id.*`, `*_*`), refer to:
`docs/instructions/jacoco/quarkus-jacoco-instructions.adoc`

---

## 5. Key Development Conventions

### Lombok
*   Use Lombok annotations (`@Getter`, `@Setter`, `@Builder`, `@NoArgsConstructor`, `@AllArgsConstructor`) to eliminate Java boilerplate.
*   `lombok.config` is configured at the root to automatically append `@Generated` annotations (`lombok.addLombokGeneratedAnnotation = true`). This ensures code-coverage tools like JaCoCo ignore Lombok's auto-generated bytecode.

### Material Events (MatEvents) and Physical Tracking
*   **Physical Domain Model:** Real-world metal items are represented by classes like `PieceMat`.
*   **State History:** Every physical action creates a `MatEvent`. Each event carries data representing the source and destination (e.g., `LocationMatEvent`) or specialized processing details.
*   **The "Undo" (Compensation) Pattern:**
    *   Undoing a step requires executing a compensation operation managed by `MatEventUndoService`.
    *   Wycofywanie (Undo) uses CDI beans qualifying as `MatEventUndoHandlerIf` per event type.
    *   To prevent inconsistent database states, `UndoClosureBuilder` recursively resolves dependent events (e.g., an allocation cannot be undone if subsequent charging occurred).
    *   Events must store complete material snapshots (`matDataBefore` / `matDataAfter`) in JSON columns using JPA Attribute Converters to allow restoration of physical state.

### Liquibase Schema Migrations
*   Direct SQL DDL changes are forbidden.
*   All schema changes must be declared in XML format inside the respective component's `-liquibase` module (e.g., `components/prodtracking/sp-prod-prodtracking-liquibase/src/main/resources/liquibase/`).

### Coding & Language Style Conventions
*   **Comments Language:** All code comments (Java, TypeScript, SQL, HTML, XML, etc.) **must always be written in English** — never in Polish or any other language, even if the user prompt or conversation is in another language.
*   **Java Method Arguments:** Java method parameters/arguments must always start with the lowercase prefix **`a`** (e.g., `aData`, `aDto`, `aMat`, `aEvent`). This aligns with PSImetals naming conventions.
*   **Consult Guidelines/Documentation First:** Before analyzing, designing, or implementing changes to the codebase, you **must always first consult** any matching architectural and domain documentation files inside the `.gemini/` directory (e.g., `.gemini/architecture/` and `.gemini/domains/`). Codebase searches (using grep or glob) must follow as a second step to verify specific implementation details, rather than bypassing the conceptual documentation.
*   **Continuous Self-Documentation & Gap Discovery:** If at any point you require additional domain, design, or architectural details that are not covered in `GEMINI.md` or its linked guidelines, you must seek them directly within the codebase. Once your task is completed, you must inform the user about these newly discovered details/patterns and ask for explicit permission to document them in the appropriate guidelines files.

---

## 7. Terminology & Vocabulary

To maintain unambiguous communication and alignment when collaborating in this repository, please adhere to the following terminology definitions:
*   **Component ("Komponent"):** Refers strictly to one of the core, high-level business systems: `sp-prod-laps`, `sp-prod-lineschedule`, or `sp-prod-prodtracking` (e.g., "the `prodtracking` component").
*   **Module ("Moduł"):** Refers specifically to a targeted architectural layer/sub-module within a component, such as `business`, `com`, `com-api`, `infrastructure`, `test`, `liquibase`, or `ui` (e.g., "the `com` module of LAPS").

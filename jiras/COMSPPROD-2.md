# COMSPPROD-2 - Extend ProdOrder on level of SP Prod

Title: Extend ProdOrder on level of SP Prod

Type: Technical Task

Context / Business Motivation

ProdOrder is marked as extensible in MET Global. This task is about adding a specific, concrete extension to the ProdOrder entity on the level of the SP Prod domain to support custom fields, starting with a single test attribute "test" of type String.

Problem Description / Task

Currently, the ProdOrder entity lacks SP Prod-level extension fields. We need to implement a concrete extension mapping for ProdOrder that allows custom fields to be populated from external systems via the standard `ProdOrderMesg` message bus payload, persisted to the database, and returned whenever the Production Order is retrieved or processed.

Acceptance Criteria / Detailed Requirements

1. **JPA Entity Extension:** Implement a concrete JPA extension entity `ProdOrderSPProdExt` extending the abstract `ProdOrderExt` class, using the discriminator value `"PRODORDERSPPRODEXT"`.
2. **Database Schema:** Create a database column `TEST` (type `VARCHAR(255)`) on the `PRODORDEREXT` table to persist this attribute.
3. **Payload Ingestion:** Integrate the extension with the standard `ProdOrderMesg` payload. The MapStruct mapping layers must map the `test` attribute from the incoming `ProdOrderMesg` DTO extension into the database entity.
4. **Payload Retrieval:** Ensure the `test` attribute is returned to the outside whenever a `ProdOrder` is queried or retrieved (embedded in `ProdOrderDto` under the DTO extensions list).
5. **Testing Verification:** Write unit and integration tests in the dedicated `-test` module to verify the complete persistence, mapping, and retrieval flow of the extension.

Out of Scope

UI/UX frontend changes (displaying the "test" attribute on Angular screens or grid columns). The extension is strictly exposed in the API payloads (JSON DTOs) and is ready for frontend consumption, but visual changes on Angular views are excluded from this ticket.

Technical / Implementation Notes

### 1. `[-com-api]` Module (API Contracts)
- **DTO Extension:** Create `de.psi.metals.sp.prod.prodorder.com.api.extensions.ProdOrderSPProdExtDto` implementing `DtoExtensionIf`.
- **Annotations:**
  ```java
  @Data
  @NoArgsConstructor
  @DtoExtension(
      type = "prod-order-sp-prod-ext-dto",
      version = 1,
      groupName = CommunicationConstants.DTO_EXTENSIONS_GROUP_PROD_ORDER
  )
  public class ProdOrderSPProdExtDto implements DtoExtensionIf {
      private String test;
  }
  ```

### 2. `[-com]` Module (Communication & Mapping)
- **MapStruct Mapper:** Create `de.psi.metals.sp.prod.prodorder.com.extensions.ProdOrderSPProdExtMapper`:
  ```java
  @Mapper
  public abstract class ProdOrderSPProdExtMapper 
      implements EntityExtensionMapperIf<ProdOrderSPProdExtData, ProdOrderSPProdExt, ProdOrderSPProdExtDto> {
  }
  ```

### 3. `[-business]` Module (Domain Model)
- **Extension Entity:** Create `de.psi.metals.sp.prod.prodorder.business.extensions.ProdOrderSPProdExt` extending `ProdOrderExt<ProdOrderSPProdExtData>`:
  ```java
  @ToString(callSuper = true)
  @Entity
  @DynamicInsert
  @DynamicUpdate
  @DiscriminatorValue("PRODORDERSPPRODEXT")
  public class ProdOrderSPProdExt extends ProdOrderExt<ProdOrderSPProdExtData> implements Serializable {
      @Column(name = "TEST")
      private String test = null;

      // Getter, setter, fillData, and applyData overrides...
  }
  ```
- **Extension Data:** Create `de.psi.metals.sp.prod.prodorder.business.extensions.ProdOrderSPProdExtData` implementing `EntityExtensionDataIf`.

### 4. `[-liquibase]` Module (Database Migration)
- **Changelog XML:** Add a changeset to add the column `TEST` to the `PRODORDEREXT` table:
  ```xml
  <changeSet author="psi" id="sp-prod-prodorder-add-test-ext-col">
      <addColumn tableName="PRODORDEREXT">
          <column name="TEST" type="VARCHAR(255)"/>
      </addColumn>
  </changeSet>
  ```

### 5. `[-test]` Module (Verification)
- **Unit/Integration Tests:** Add tests to verify that `ProdOrderSPProdExt` is correctly saved to the database and retrieved when mapping to `ProdOrderDto`. Check against `ProdOrderMapperTest` for reference.

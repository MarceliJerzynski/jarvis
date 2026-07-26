# COMSPPROD-2998: Script for celaning materials does not work with specyfic materials

- **Type:** Task
- **Status:** Open
- **Priority:** 4-Minor
- **Assignee:** Ihab Tazi
- **Jira Link:** https://collaboration-psise.atlassian.net/browse/COMSPPROD-2998

---

## Description

Script for celaning materials does not o nmaterials with:


| **action** | **prefix on dev-08** |
| --- | --- |
| reject samples | CY_REJECT |
| unplaned sample | CY_UNSAMPLE |
| inspections | CY_INSPECTION |
| rest flag | CY_REST |
| cancel event | CP_CANCEL_EV |
| displace with new length | CP_DISPLACE_NL_3 |
| with issues | CY_ISSUE |






script:


```
  vMatRec        gloDefPrj.typMatPrjRec;
  vEK            gloDefPrj.typEreigniskontextPrj;
  vChargedLineId ANLAGE.ANLAGE%TYPE;
  vChargedLine   ANLAGE%ROWTYPE;
  vPParCatMask   gloDefPPAR.typPParCategoryMask;
  vPParRefMask   gloDefPPAR.typPParReferenceMask;
  vLocation      gloDefPES.typLagerort;
  vMatFehler_L   gloDefPrj.typTabMatDefect;
  vtPPAR         typTPPar := typTPPar();
  vCnt           NUMBER := 0;
BEGIN
  -- Loop over MATs with a select of materials where id is CPY_*
  FOR mat IN (
    SELECT ME_ID, BEZEICHNUNG 
    FROM MAT 
    WHERE MAT.BEZEICHNUNG LIKE NVL(:BizCodePattern, 'CPY_BOOK__71619%')
  ) LOOP
    vCnt := vCnt + 1;

    -- Get the material record:
    entMat.selByName(
      pi_Bezeichnung => mat.BEZEICHNUNG,
      po_MatPrjRec   => vMatRec
    );

    vEK.FA_NR        := vMatRec.vMat.FA_NR;
    vEK.AG_ID        := vMatRec.vMat.AG_ID;
    vEK.SUBSYSTEM    := gloDefPrj.SUBSYSTEM_OFFICE;
    vEK.FLAGCOMPLETE := TRUE;

    -- Check if the material is charged:
    IF vMatRec.vMat.DTEINGESETZT IS NOT NULL THEN
      -- Displace the material:
      -- Get ONLY the last event from MATEREIGNIS, with METYP Einsatz and subtyp Einsatz,
      -- for Mat bezeichnung, to get the line (ANLAGE) where it is currently used
      SELECT ANLAGE 
      INTO vChargedLineId 
      FROM (
        SELECT ANLAGE
        FROM MATEREIGNIS
        WHERE ME_ID = vMatRec.vMat.ME_ID
          AND METYP = 'Einsatz'
          AND SUBTYP = 'Einsatz' 
        ORDER BY EREIGNISID DESC
      ) 
      WHERE ROWNUM <= 1;

      tabAnlage.sel(
        pi_Anlage => vChargedLineId,
        po_Row    => vChargedLine
      );

      kmpPES.MatAbsatz(
        vMatRec, 
        vEk, 
        pi_lagerOrt => vLocation
      );
    END IF;

    -- Now deallocate the material if it has FA_NR (is allocated):
    IF vMatRec.vMAT.FA_NR IS NOT NULL THEN
      -- Deallocate the material:
      kmpMat.DEALLOCATEMAT(
        PIO_MATPRJREC => vMatRec,
        PIO_EC        => vEK
      );
    END IF;

    FOR ta IN (SELECT TAID FROM TA WHERE ME_ID = vMatRec.vMat.ME_ID) LOOP
      kmpTAWTM.storniereTa(
        pi_TAID  => ta.TAID, 
        pi_force => TRUE
      );
    END LOOP;

    -- Finally delete the material:
    kmpMatPes.loescheMat(pi_ME_ID => vMatRec.vMat.ME_ID);

    IF vCnt > 50 THEN
      vCnt := 0;
      COMMIT;
    END IF;
  END LOOP;

  COMMIT;
END;{noformat}

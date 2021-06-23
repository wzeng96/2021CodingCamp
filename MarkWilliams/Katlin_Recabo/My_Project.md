### Original Plan
1. Parse FOTS ADME email
2. Compare parsed strings to existing data in Oracle Database
4. Determine whether to change or add information to this database based on comparison
5. If time allows, create API?

### Alternate/Updated approach
1. Pull incomplete ADME orders from Oracle database (COMA_ORDER_V2)
2. Compare compounds requested to those available
    - Is REG_NO 15 or 12 characters?
    - Obtain BARCODE_INFO, BARCODE_VOLUME > 45 uL
4. Obtain USER_NUM, PROJECT, ORDER_TYPE
5. Add Barcodes to ADME queue
6. Set order to complete and send email
    - FINAL_COMMENTS = "These compounds added to (insert ORDER_TYPE) queue"
    - FINAL_TABLE = Compound list
      - Determine separation character
    - SEND_EMAIL = Date/time stamp
    - Fill my name in two columns

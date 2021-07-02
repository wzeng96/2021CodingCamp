import cx_Oracle
import os
import pandas as pd

#Designating the location of the instant client
cx_Oracle.init_oracle_client(lib_dir=r"C:\opt\oracle\instantclient_19_11")

#Testing connection
with cx_Oracle.connect(user="coma", password="nihncgc", dsn="oradev05.ncats.nih.gov:1521/bprobedb") as connection:
    cursor = connection.cursor()
    tables = cursor.execute(
        f'SELECT' +
        f'  table_name ' +
        f'FROM' +
        f'  user_tables ' +
        f'ORDER BY ' +
        f'  table_name'
    )

    for row in tables:
        print(row)

#preparing empty table
FOTS_COMPOUNDS_df = pd.DataFrame(columns=['FOTS','NCGC'])
row = 0

#Establishing connection
connection = cx_Oracle.connect(user="coma", password="nihncgc",
                               dsn="oradev05.ncats.nih.gov:1521/bprobedb")
#Finding all of the compounds associated with unfinished ADME orders
orders_cursor = connection.cursor()
orders = orders_cursor.execute(
    f"select ORDERID, SAMPLE_ID " +
    f"from COMA_ORDER_V2 cross join COMPOUNDS " +
    f"where COMA_ORDER_V2.ORDERID=COMPOUNDS.ORDER_ID and COMA_ORDER_V2.STATUS= 'IN PROGRESS' and COMA_ORDER_V2.ORDERTYPE=6 " +
    f"order by ORDER_ID")

#Printing the FOTS IDs with the Compounds associated with them
for order_row in orders:
    #    print(order_row)
    order = order_row [0]
    compound = order_row [1]
    print(f"{order}: {compound}")
    FOTS_COMPOUNDS_df.loc[row] = [order, compound]
    row += 1

FOTS_COMPOUNDS_df

#pulling just the NCGCs from the table
for row in FOTS_COMPOUNDS_df.iterrows():
#    print(row[1]['NCGC'])
#If it includes the batch search the Sample_ID column
    if len(row[1]['NCGC']) == 15:
        sql ="""select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT
                from BARCODE_INFO cross join BARCODE_VOLUME
                where BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE
                and BARCODE_INFO.SAMPLE_ID = :c
                and BARCODE_VOLUME.AMOUNT > 45
                order by BARCODE_VOLUME.AMOUNT desc"""
#If it does not have a batch search the NCGCROOT column
    else:
        sql ="""select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT
                from BARCODE_INFO cross join BARCODE_VOLUME
                where BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE
                and BARCODE_INFO.NCGCROOT = :c
                and BARCODE_VOLUME.AMOUNT > 45
                order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc"""
#Make table with the batch, barcode and volume information
    barcodes_cursor = connection.cursor()
    barcodes = barcodes_cursor.execute(sql,c=row[1]['NCGC'])
    for barcode_row in barcodes:
        print(order_row)
        batch = barcode_row [0]
        barcode = barcode_row [1]
        vol = barcode_row [2]
        print(f"{batch}: {barcode}: {vol}")
        FOTS_BAR_df.loc[row] = [batch, barcode, vol]
        row += 1

FOTS_BAR_df
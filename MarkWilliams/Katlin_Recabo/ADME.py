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

#    for row in tables:
#        print(row)

#preparing empty FOTS_COMPOUNDS_df table
FOTS_COMPOUNDS_df = pd.DataFrame(columns=['FOTS','NCGC'])
comp_row = 0

#preparing empty FOTS_BAR_df table
FOTS_BAR_df = pd.DataFrame(columns=['Requested','NCGC','Barcode', 'Volume (uL)'])
bar_row = 0

#preparing empty ADME_df table
ADME_df = pd.DataFrame(columns=['Barcode', 'NCGC', 'Chemist', 'Project', 'Concentration','Volume', 'Format'])
ADME_row = 0

#Establishing connection
connection = cx_Oracle.connect(user="coma", password="nihncgc",
                               dsn="oradev05.ncats.nih.gov:1521/bprobedb")

#Finding all of the compounds associated with unfinished ADME orders
orders_cursor = connection.cursor()
orders = orders_cursor.execute(
    f"select ORDERID, SAMPLE_ID, DELIVERY_FORMAT, DELIVER_TO, PROJECT_ID " +
    f"from COMA_ORDER_V2 cross join COMPOUNDS " +
    f"where COMA_ORDER_V2.ORDERID=COMPOUNDS.ORDER_ID and COMA_ORDER_V2.STATUS= 'IN PROGRESS' and COMA_ORDER_V2.ORDERTYPE=6 " +
    f"order by ORDER_ID")

#Establishing variables
for order_row in orders:
    #    print(order_row)
    order = order_row [0]
    compounds = order_row [1]
    format_id = order_row [2]
    chem_id = order_row [3]
    project_id = order_row [4]
    #    print(f"{order}: {compounds}")
    FOTS_COMPOUNDS_df.loc[comp_row] = [order, compounds]
    comp_row += 1
    length = len(compounds)
    #    print(compounds,":", length)
    no_batch = compounds[0:12]


    #Finding the Delivery format name
    del_forms_cursor = connection.cursor()
    del_forms = del_forms_cursor.execute(
        f"select PLATE_FORMAT, ORDER_TYPE2, MINIMUM_VOLUME " +
        f"from DELIVERY_FORMAT " +
        f"where ID = '{format_id}' "
    )

    for del_forms_row in del_forms:
        del_form = del_forms_row [0]
        order_type = del_forms_row [1]
        min_vol = del_forms_row [2]

    #Finding the barcodes associated with the compounds listed
    #If the compound doesn't have a batch listed
    if length == 12:
        bar_count = 0
        barcodes_cursor = connection.cursor()
        try:
            barcodes = barcodes_cursor.execute(
                f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, BARCODE_INFO.CONCENTRATION " +
                f"from BARCODE_INFO cross join BARCODE_VOLUME " +
                f"where BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                f"and BARCODE_INFO.NCGCROOT = '{compounds}' " +
                f"and BARCODE_VOLUME.AMOUNT >= '{min_vol}' " +
                f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                f"fetch first 1 row only"
            )
        except:
            print(f"error: {compounds}:{min_vol}")
    #If it does have a batch listed, check how many instances of the requested batch have more than minimum volume
    else:
        search_cursor = connection.cursor()
        search = search_cursor.execute(
            f"select BARCODE_INFO.SAMPLE_ID " +
            f"from BARCODE_INFO join BARCODE_VOLUME " +
            f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
            f"where BARCODE_INFO.SAMPLE_ID = '{compounds}' " +
            f"and BARCODE_VOLUME.AMOUNT >= '{min_vol}' "
        )
        bar_count = 0
        for search_row in search:
            bar_count += 1

        #If the requested batch does not exist with more than minimum volume
        if bar_count == 0:
            barcodes_cursor = connection.cursor()
            barcodes = barcodes_cursor.execute(
                f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, BARCODE_INFO.CONCENTRATION " +
                f"from BARCODE_INFO cross join BARCODE_VOLUME " +
                f"where BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                f"and BARCODE_INFO.NCGCROOT = '{no_batch}' " +
                f"and BARCODE_VOLUME.AMOUNT >= '{min_vol}' " +
                f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                f"fetch first 1 row only"
            )

        #If the requested batch exists with more than minimum volume
        else:
            barcodes_cursor = connection.cursor()
            barcodes = barcodes_cursor.execute(
                f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, BARCODE_INFO.CONCENTRATION " +
                f"from BARCODE_INFO join BARCODE_VOLUME " +
                f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                f"where BARCODE_INFO.SAMPLE_ID = '{compounds}' " +
                f"and BARCODE_VOLUME.AMOUNT >= '{min_vol}' " +
                f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                f"fetch first 1 row only"
            )
    for barcode_row in barcodes:
        #        print(barcode_row)
        batch = barcode_row [0]
        barcode = barcode_row [1]
        vol = barcode_row [2]
        conc = barcode_row [3]
        #        print(f"{batch}: {barcode}: {vol}")
        FOTS_BAR_df.loc[bar_row] = [compounds, batch, barcode, vol]
        bar_row += 1

        ADME_df.loc[ADME_row] = [barcode,batch,chem_id,project_id,conc,'in solution', format_id]
        ADME_row += 1
 #       print(f"{order}: {compounds}: {batch}: {barcode}")
        ADME_cursor = connection.cursor()
        try:
            ADME = ADME_cursor.execute(
                f"insert into ADME " +
                f"values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','in solution', DEFAULT, '{format_id}', DEFAULT) "
            )
        except:
            print(f"Error: values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','in solution', '{format_id}') ")

connection.commit()
#print(FOTS_COMPOUNDS_df)
#print(FOTS_BAR_df)
#print(ADME_df)

#Setting order to complete
FOTS_cursor = connection.cursor()
FOTS = FOTS_cursor.execute(
    f"select COMA_ORDER_V2.ORDERID, DELIVERY_FORMAT.PLATE_FORMAT " +
    f"from COMA_ORDER_V2 join DELIVERY_FORMAT " +
    f"on COMA_ORDER_V2.DELIVERY_FORMAT=DELIVERY_FORMAT.ID " +
    f"where COMA_ORDER_V2.STATUS= 'IN PROGRESS' and COMA_ORDER_V2.ORDERTYPE=6 " +
    f"order by COMA_ORDER_V2.ORDERID"
)

for FOTS_row in FOTS:
    print(FOTS_row)
    FOTSNo = FOTS_row [0]
    order_type = FOTS_row [1]
    fin_com = "These compounds have been added to the " + order_type + "queue."
    completes_cursor = connection.cursor()
    try:
        completes = completes_cursor.execute(
            f"update COMA_ORDER_V2 " +
            f"set SEND_EMAIL = SYSDATE, FINAL_TABLE = '{ADME_df}', FINAL_COMMENTS = '{fin_com}', CONTACT = 'recabokm', COMA_CONTACT = 'Katlin Recabo' " +
            f"where ORDERID = '{FOTSNo}'"
        )
    except:
        print("These compounds have been added to the " + order_type + "queue.")

connection.commit()

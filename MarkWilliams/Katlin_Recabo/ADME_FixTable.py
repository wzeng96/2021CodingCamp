import cx_Oracle
import variables

cx_Oracle.init_oracle_client(lib_dir=r"C:\opt\oracle\instantclient_19_11")

#Establishing connection
connection = cx_Oracle.connect(user= variables.USER, password= variables.PASS,
                               dsn= variables.DSN)

#Finding all in progress ADME FOTS orders
FOTS_cursor = connection.cursor()
FOTS = FOTS_cursor.execute(
    f"select COMA_ORDER_V2.ORDERID, DELIVERY_FORMAT.PLATE_FORMAT, DELIVERY_FORMAT.ID, " +
    f"COMA_ORDER_V2.DELIVER_TO, DELIVERY_FORMAT.MINIMUM_VOLUME " +
    f"from COMA_ORDER_V2 join DELIVERY_FORMAT " +
    f"on COMA_ORDER_V2.DELIVERY_FORMAT=DELIVERY_FORMAT.ID " +
    f"where COMA_ORDER_V2.STATUS= 'IN PROGRESS' and COMA_ORDER_V2.ORDERTYPE=6 " +
    f"order by COMA_ORDER_V2.ORDERID"
)

for FOTS_row in FOTS:
    #print(FOTS_row)
    FOTSNo = FOTS_row [0]
    order_type = FOTS_row [1]
    format_id = FOTS_row [2]
    chem_id = FOTS_row [3]
    min_vol = FOTS_row [4]
    fin_com = "These have been added to the " + order_type + "queue."

    #Finding all of the compounds associated with each unfinished ADME order
    compounds_cursor = connection.cursor()
    compounds = compounds_cursor.execute(
        f"select ORDER_ID, SAMPLE_ID " +
        f"from COMPOUNDS " +
        f"where ORDER_ID = '{FOTSNo}' " +
        f"order by ORDER_ID"
    )
    comp_list = "NCGC ID"
    #Finding the barcodes for each of the compounds
    for compounds_row in compounds:
        compound = compounds_row [1]
        length = len(compound)
        no_batch = compound[0:12]

        #Finding the barcodes associated with the compounds listed
        #If the compound doesn't have a batch listed
        if length == 12:
            bar_count = 0
            barcodes_cursor = connection.cursor()
            try:
                barcodes = barcodes_cursor.execute(
                    f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, "+
                    f"BARCODE_INFO.CONCENTRATION, BARCODE_INFO.NOTES, BARCODE_INFO.PROJECT_ID_FK " +
                    f"from BARCODE_INFO join BARCODE_VOLUME " +
                    f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                    f"where (BARCODE_INFO.NCGCROOT = '{no_batch}' and BARCODE_VOLUME.AMOUNT >= '{min_vol}') " +
                    f"or (BARCODE_INFO.NCGCROOT = '{no_batch}' and BARCODE_VOLUME.NOTES like '%Dissolve to%' " +
                    f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                    f"fetch first 1 row only"
                )
            except:
                print(f"error: {compound}:{min_vol}")
        #If it does have a batch listed, check how many instances of the requested batch have more than minimum volume
        else:
            search_cursor = connection.cursor()
            search = search_cursor.execute(
                f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.NOTE " +
                f"from BARCODE_INFO join BARCODE_VOLUME " +
                f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                f"where (BARCODE_INFO.SAMPLE_ID = '{compound}' AND BARCODE_VOLUME.AMOUNT >= '{min_vol}') " +
                f"OR (BARCODE_INFO.SAMPLE_ID = '{compound}' AND BARCODE_INFO.NOTE like '%Dissolve to%') "
            )
            bar_count = 0
            for search_row in search:
                bar_count += 1

            #If the requested batch does not exist with more than minimum volume
            if bar_count == 0:
                barcodes_cursor = connection.cursor()
                barcodes = barcodes_cursor.execute(
                    f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, " +
                    f"BARCODE_INFO.CONCENTRATION, BARCODE_INFO.NOTES, BARCODE_INFO.PROJECT_ID_FK " +
                    f"from BARCODE_INFO join BARCODE_VOLUME " +
                    f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                    f"where (BARCODE_INFO.NCGCROOT = '{no_batch}' and BARCODE_VOLUME.AMOUNT >= '{min_vol}') " +
                    f"or (BARCODE_INFO.NCGCROOT = '{no_batch}' and BARCODE_VOLUME.NOTES like '%Dissolve to%' " +
                    f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                    f"fetch first 1 row only"
                )

            #If the requested batch exists with more than minimum volume
            else:
                barcodes_cursor = connection.cursor()
                barcodes = barcodes_cursor.execute(
                    f"select BARCODE_INFO.SAMPLE_ID, BARCODE_INFO.BARCODE, BARCODE_VOLUME.AMOUNT, " +
                    f"BARCODE_INFO.CONCENTRATION, BARCODE_INFO.NOTES, BARCODE_INFO.PROJECT_ID_FK " +
                    f"from BARCODE_INFO join BARCODE_VOLUME " +
                    f"on BARCODE_INFO.BARCODE = BARCODE_VOLUME.BARCODE " +
                    f"where (BARCODE_INFO.SAMPLE_ID = '{compound}' and BARCODE_VOLUME.AMOUNT >= '{min_vol}') " +
                    f"or (BARCODE_INFO.SAMPLE_ID = '{compound}' and BARCODE_VOLUME.NOTES like '%Dissolve to%' " +
                    f"order by BARCODE_INFO.SAMPLE_ID desc, BARCODE_VOLUME.AMOUNT desc " +
                    f"fetch first 1 row only"
                )
        for barcode_row in barcodes:
            #print(barcode_row)
            batch = barcode_row [0]
            barcode = barcode_row [1]
            vol = barcode_row [2]
            conc = barcode_row [3]
            note = barcode_row [4]
            comp_list = comp_list + "\n" + batch
            #Adding the compounds to the ADME queue is they have volume
            if vol >= min_vol:
                ADME_cursor = connection.cursor()
                try:
                    ADME = ADME_cursor.execute(
                        f"insert into ADME " +
                        f"values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','in solution', DEFAULT, '{format_id}', DEFAULT) "
                    )
                except:
                    print(f"Error: values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','in solution', '{format_id}') ")

            #Adding the compound to the ADME queue if they have to ve dissolved
            else:
                ADME_cursor = connection.cursor()
                try:
                    ADME = ADME_cursor.execute(
                        f"insert into ADME " +
                        f"values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','{note}', DEFAULT, '{format_id}', DEFAULT) "
                    )
                except:
                    print(f"Error: values ('{barcode}','{batch}','{chem_id}','{project_id}','{conc}','{note}', '{format_id}') ")
    completes_cursor = connection.cursor()
    try:
        completes = completes_cursor.execute(
            f"update COMA_ORDER_V2 " +
            f"set SEND_EMAIL = SYSDATE, FINAL_TABLE = '{comp_list}', FINAL_COMMENTS = '{fin_com}', CONTACT = 'recabokm', COMA_CONTACT = 'Katlin Recabo' " +
            f"where ORDERID = '{FOTSNo}'"
        )
    except:
        print("These compounds have been added to the " + order_type + "queue.")

connection.commit()

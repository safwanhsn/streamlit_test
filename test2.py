#Testing Azure Synapse SQL Connection
import pandas as pd
import numpy as np
import pyodbc

def dip_sql_connect():
    conn = pyodbc.connect(driver='{SQL Server}',
                            authentication='ActiveDirectoryPassword',
                            server='dipdevarmsawuw2001-ondemand.sql.azuresynapse.net',
                            database='dip',
                            uid='sahossain@suncor.com',
                            pwd='c0lum8iA@@@@')
    return conn

# cursor = dip_sql_connect()

cursor = pyodbc.connect('Driver={SQL Server};Server=tcp:dipdevarmsvruw2001.database.windows.net,1433;Database=dipdevarmsdbuw2001;Uid=sahossain@suncor.com;Pwd=c0lum8iA@@@@;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Authentication=ActiveDirectoryPassword')

pad_qry = """
SELECT TOP (1000) [PROJECT]
      ,[SURFACE_PAD]
      ,[PATTERN]
      ,[WELL_PAIR]
      ,[MAPPED_COMMON_WELLNAME]
      ,[OBS_SUNCOR_WELLBORE_ID]
      ,[TVDSS]
      ,[OBS_MD]
      ,[PROJECTED_MD]
      ,[FILE_MNEMONIC_NAME]
      ,[COMMON_MNEMONIC_NAME]
      ,[MNEMONIC_VALUE]
  FROM [dip].[dbo].[dts_mr_log_view]
"""
pads = pd.read_sql(pad_qry, cursor)

print(pads)


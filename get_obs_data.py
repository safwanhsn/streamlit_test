"""
Libraries
"""

#Computations
import pandas as pd
import numpy as np 
import datetime as dt
import streamlit as st

#Azure
import io
import os, uuid, sys
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core._match_conditions import MatchConditions
from azure.storage.filedatalake._models import ContentSettings

#! Can we get our OBS list through a SQL Query of wellbore description or a CSV table that will eventually become a SQL table
#!  Using change function show metadata DF of selected OBS well

"""
Functions to Connect to ADLS Gen2
"""
def initialize_storage_account(storage_account_name, storage_account_key):
    
    try:  
        global service_client

        service_client = DataLakeServiceClient(account_url="{}://{}.dfs.core.windows.net".format(
            "https", storage_account_name), credential=storage_account_key)
        
    
    except Exception as e:
        print(e)

def download_file():
    try:
        initialize_storage_account(st.secrets['azure_conn'], st.secrets['azure_key'])

        file_system_client = service_client.get_file_system_client(file_system="gold")

        directory_client = file_system_client.get_directory_client(r"dts\obs-well-mapping\mackay-river\parent-child\750-P01")

        file_client = directory_client.get_file_client("part-00000-d8a674b9-1c40-4fd9-8264-e0f058026633-c000.snappy.parquet")

        download = file_client.download_file()

        downloaded_bytes = download.readall()

        downloadedParquet = io.BytesIO(downloaded_bytes)

        dfParquet = pd.read_parquet(downloadedParquet) #! Speed this up

        return dfParquet


    except Exception as e:
     print(e)







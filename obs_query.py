import pandas as pd
import numpy as np
import pyodbc

import PIconnect as PI
import sys  
import clr 
# sys.path.append(r'C:Program Files (x86)PIPCAFPublicAssemblies4.0')    
# clr.AddReference('OSIsoft.AFSDK') 
sys.path.append(r'C:\Program Files (x86)\PIPC\AF\PublicAssemblies\4.0')    
clr.AddReference('OSIsoft.AFSDK') 
from OSIsoft.AF import *  
from OSIsoft.AF.PI import *  
from OSIsoft.AF.Asset import *  
from OSIsoft.AF.Data import *  
from OSIsoft.AF.Time import *  
from OSIsoft.AF.UnitsOfMeasure import *

import streamlit as st

def dip_sql_connect():
    conn = pyodbc.connect(driver='{SQL Server}',
                            server='dipdevarmsvruw2001.database.windows.net',
                            database='dipdevarmsdbuw2001',
                            uid='arbtest',
                            pwd='L0r3tt414')
    return conn

# @st.cache_resource
def get_temps(well, frequency, start, range_max, range_min):
    temp_qry = f"""
    SELECT
        TAG_DESCRIPTION.TAG_NAME, 
        META_CATEGORY_ENTITY, 
        VARIABLE_NAME, 
        VARIABLE_DESCRIPTION, 
        COMMENTS, 
        SERVER_NAME, 
        MDKB_DEPTH, 
        TVDSS_DEPTH, 
        INSTRUMENTATION_TYPE 
    FROM dbo.TAG_DESCRIPTION
    LEFT JOIN dbo.TAG_DEPTH
    ON TAG_DESCRIPTION.TAG_NAME = TAG_DEPTH.TAG_NAME
    WHERE META_CATEGORY_ENTITY = '{well}'
    AND MDKB_DEPTH <= {range_max}
    AND MDKB_DEPTH >= {range_min}
    ORDER BY MDKB_DEPTH
    """
    #! If we have multiple temp types - use statistics - filter down to what we have the most of i.e. DTS
    
    cursor = dip_sql_connect()
    obs_temps = pd.read_sql(temp_qry, cursor)
    cursor.close()

    if obs_temps.empty:
        st.warning('No tags found in DIP with associated mdkb')

    else:
        server = obs_temps.SERVER_NAME.iloc[0]
        print(server)

        
        #!Do speed test Dylan vs Alonso PI query and batching not bad
        # PI.AF.PI
        # PI.PIServer
        # PI.AF.PI.PIServers()
        # PI.AF.Time.AFTimeRange

        piServers = PI.AF.PI.PIServers()
        piServer = piServers[server]   

        data_table = []
        for row, column in obs_temps.iterrows():
            tag = column.TAG_NAME
            depth = column.MDKB_DEPTH
            try:
                print(tag, depth)
                pt = PI.AF.PI.PIPoint.FindPIPoint(piServer,tag)  
                name = pt.Name.lower()
            except PI.AF.PI.PIException:
                print('PI Tag not found')
                continue

            #Get interpolated values for time range
            timerange = PI.AF.Time.AFTimeRange(start,'*')  
            span = PI.AF.Time.AFTimeSpan.Parse(frequency)  
            interpolated = pt.InterpolatedValues(timerange, span, "", False)
            dates = [event.Timestamp.LocalTime for event in interpolated]
            values = [event.Value for event in interpolated]
            dic = {'Date':dates, str(depth):values}
            data = pd.DataFrame(dic).set_index('Date')
            data_table.append(data)
        df = pd.concat(data_table, axis=1).reset_index().sort_values(by='Date').set_index('Date')
        # df.to_csv('temp_temp.csv', index=False, header=True)
        #!2003 temps will be a slower query cuz more data management
        #! Option for temperature lookback and depth of temp. to user in form - temp profiler
        #!Concat dfs for each tag?
        return df
    


#! Apply caching to this so that we do not constantly have to re-query temps once it is in - or use state to do this - somehow cache temp pulls for wells youve done into state space and pull from there
# print(get_temps('OB12'))
#! Will the 01 and 1 differntiateion cause issue - if so use stripping

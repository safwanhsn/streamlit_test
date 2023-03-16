"""
Libraries
"""

#Streamlit components
from st_aggrid import AgGrid
import streamlit as st 

#Computation
import pandas as pd
import numpy as np 
import datetime as dt

#Visualization
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
from plotly.subplots import make_subplots

#Loading Data
from get_obs_data import get_obs_dict, get_obs_property
"""
State Session Variables
"""
obs_dict = get_obs_dict()
obs_property = get_obs_property()

"""
Page
"""
#Page Config
# st.set_page_config(page_title='OBS Well Analyzer')

#Sidebar
with st.sidebar:
    st.title("OBS Well Analyzer")
    st.caption("Dev Build")

    project = st.selectbox('Project', ['Firebag'])
    #! Default selection and error handling
    
    # Filter Section
    with st.expander("Filter"):
        #init. lists
    #     listPads = obsDictionary.SURFACE_PAD.unique()
    #     #! List Patterns?
    #     listParentWells = obsDictionary.WELL_PAIR.unique()
        listParameters = ['M_GR', 'LVMIFACIES', 'I_LVMI', 'I_BMFO', 'THERMOCOUPLE_TEMP', 'DTS_TEMP']
        listObsWells = obs_dict.COMMON_WELLNAME.unique()
        #! Save hardcoded lists to a csv in data folder of github
        


        

    #     #! Insert Filter Function Here
    #     surfacePad = st.multiselect('By Surface Pad', listPads)

    #     parentWell = st.multiselect('By Parent Well-Pair', listParentWells)

        availableParameter = st.multiselect('By Available Parameters', listParameters)

        if availableParameter:
            listObsWells = obs_property[(obs_property['COMMON_WELLNAME'].isin(listObsWells)) & \
                                        (obs_property['PROPERTY_SHORT_NAME'].isin(availableParameter))] \
                                        .COMMON_WELLNAME.unique()


    #     # wellType = st.multiselect('By Well Type', ('Observation', 'Vertical (WIP)')) #! DIP does not contain the metadata to do this yet I believe

    #     #! I think I want to do the above filtering like a form - And then maybe query the logs or a presaved csv or something or like distinct wihtin logs or query all log and filter to make list idk

        obsWell = st.selectbox('Observation Well', listObsWells)








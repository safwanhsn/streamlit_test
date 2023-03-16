# """
# Libraries
# """

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
# """
# State Session Variables
# """
obs_dict = get_obs_dict()
obs_property = get_obs_property()

#! Add this to state actually

#Figure Properties State Variables
if ['figureSelectIndex', 'listFigNames'] not in st.session_state:
    st.session_state.figureSelectIndex = 0
    st.session_state.listFigNames = ['1','2','3','4','5','6']

if ['traceSelectionMatrix'] not in st.session_state:
    st.session_state.traceSelectionMatrix = pd.DataFrame([[np.nan, np.nan, np.nan, np.nan, np.nan, np.nan]],columns=st.session_state.listFigNames)

if ['list1', 'list2', 'list']

# """
# Page
# """

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
        listParameters = ['M_GR', 'LVMIFACIES', 'I_LVMI', 'I_BMFO', 'THERMOCOUPLE_TEMP', 'DTS_TEMP']
        listObsWells = obs_dict.COMMON_WELLNAME.unique()
        #! Save hardcoded lists to a csv in data folder of github

    #     surfacePad = st.multiselect('By Surface Pad', listPads)
    #     parentWell = st.multiselect('By Parent Well-Pair', listParentWells)

        availableParameter = st.multiselect('By Available Parameters', listParameters)

        if availableParameter:
            listObsWells = obs_property[(obs_property['COMMON_WELLNAME'].isin(listObsWells)) & \
                                        (obs_property['PROPERTY_SHORT_NAME'].isin(availableParameter))] \
                                        .COMMON_WELLNAME.unique()

        obsWell = st.selectbox('Observation Well', listObsWells)
    
    #Trace Properties Section
    with st.expander('Trace Properties'):
        # obsAvailableParameters = obs_property[obs_property['COMMON_WELLNAME']==obsWell].PROPERTY_DESCRIPTION.unique()

        #! Temp form structure
        with st.form("Trace Select", clear_on_submit=False):
            chartScale = int(st.slider(label='Chart Scale',min_value=1, max_value=200, value=100))
            figureSelect = st.selectbox('Figure', st.session_state.listFigNames, index=st.session_state.figureSelectIndex)
            parameterToTrace = st.multiselect('Parameters to Trace', listParameters)
            parameterTraceAction = st.selectbox("Select Action", ['Add Traces', 'Clear Figure'])
            parameterTraceSubmit = st.form_submit_button("Submit")
        clearAllTraces = st.button('Clear All')

        st.write(st.session_state.traceSelectionMatrix)

        #Parameter Trace Submit Actions
        if parameterTraceSubmit:
            if parameterTraceAction == 'Add Traces':
                for parameter in parameterToTrace:
                    parametersToAppend = pd.DataFrame([],columns=st.session_state.listFigNames)
                    parametersToAppend.at[1, str(figureSelect)] = parameter
                    toAppend = [st.session_state.traceSelectionMatrix, parametersToAppend]
                    st.write(st.session_state.traceSelectionMatrix)
                    st.write(parametersToAppend)
                    st.session_state.traceSelectionMatrix = pd.concat([st.session_state.traceSelectionMatrix, parametersToAppend],axis=0)
                    # st.session_state.traceSelectionMatrix.drop_duplicates(inplace=True)


        #Clear All Figures Action
        if clearAllTraces:
            st.session_state.traceSelectionMatrix = st.session_state.traceSelectionMatrix.iloc[0:0]

        












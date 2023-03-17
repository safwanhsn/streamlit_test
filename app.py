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
from get_obs_data import get_obs_data, get_obs_dict, get_obs_property
# """
# State Session Variables
# """
obs_dict = get_obs_dict()
obs_property = get_obs_property()

#Figure Properties State Variables
if ['figureSelectIndex', 'listFigNames'] not in st.session_state:
    st.session_state.figureSelectIndex = 0
    st.session_state.listFigNames = ['1','2','3','4','5','6']

if 'traceSelectionMatrix' not in st.session_state:
    st.session_state.traceSelectionMatrix = pd.DataFrame([],columns=st.session_state.listFigNames)


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

        st.experimental_data_editor(st.session_state.traceSelectionMatrix,use_container_width=True)

        #Parameter Trace Submit Actions
        if parameterTraceSubmit==True:
            if parameterTraceAction == 'Add Traces':
                for parameter in parameterToTrace:
                    parametersToAppend = pd.DataFrame([],columns=st.session_state.listFigNames)
                    parametersToAppend.at[1, str(figureSelect)] = parameter
                    toAppend = [st.session_state.traceSelectionMatrix, parametersToAppend]
                    st.session_state.traceSelectionMatrix = pd.concat(toAppend,axis=0)
                    st.session_state.traceSelectionMatrix.drop_duplicates(inplace=True)
                st.experimental_rerun()
            
            if parameterTraceAction == 'Clear Figure':
                st.session_state.traceSelectionMatrix.loc[:,str(figureSelect)] = None
                st.experimental_rerun()

            #! Placeholder value - get the query here although later I want to unform that one and make a new form to run and in that func only query what hasn't been queried and concat that to our logs DF


        #Clear All Figures Action
        if clearAllTraces==True:
            st.session_state.traceSelectionMatrix = st.session_state.traceSelectionMatrix.iloc[0:0]
            st.experimental_rerun()


#Visualization 
fig1 = make_subplots(rows=1, cols=len(st.session_state.listFigNames))

           
for col in st.session_state.traceSelectionMatrix.columns:
    #! First I should query all data on a form run button at once and cache it based on the unique vals and ObsWell
    #? Function to query logs that we can cache?
    
    toPlot = st.session_state.traceSelectionMatrix[col]
    for parameter in toPlot:
        st.write(obs_property[(obs_property['COMMON_WELLNAME']==obsWell)&(obs_property['PROPERTY_SHORT_NAME']==parameter)].SOURCE.to_list[0])
        try:
            parameterSource = obs_property[(obs_property['COMMON_WELLNAME']==obsWell)&(obs_property['PROPERTY_SHORT_NAME']==parameter)]['SOURCE'].reset_index(drop=True).iat[0]

            if parameterSource == 'Log':
                #! Or query each one from here but that will be slow
                query = f"""
                SELECT * FROM [dbo].[fb_logs_view]
                WHERE [PROJECT] = '{project}' 
                AND [COMMON_WELLNAME] = '{obsWell}'
                AND [FILE_MNEMONIC_NAME] = '{parameter}'
                WHERE MNEMONIC_VALUE <> '-999.25'
                ORDER BY [MD]
                """
                with st.spinner("Querying Data"):
                    data = get_obs_data(query)
                fig1.append_trace(go.Scatter(x=data['MNEMONIC_VALUE'], y=data['MD'], name='Test'), 1, int(col))
        except:
            st.warning('No Source')


st.plotly_chart(fig1, theme="streamlit")


        












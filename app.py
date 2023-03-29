# """
# Libraries
# """

#Streamlit components
from st_aggrid import AgGrid
from streamlit_option_menu import option_menu
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
from get_obs_data import get_obs_data, get_obs_dict, get_obs_property, get_obs_log_fb, multi_filter
# """
# State Session Variables
# """
obs_dict = get_obs_dict()
obs_property = get_obs_property()
staticData = pd.read_csv('data/data.csv')

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

    project = st.selectbox('Project', ['Firebag', 'MacKay River (Unavailable)'])

    if project:
        obs_dict = obs_dict[obs_dict['PROJECT']==project]
        obs_property = obs_property[obs_property['PROJECT']==project]
         #! Default selection and error handling and filtering by project
    
    # Filter Section
    with st.expander("Filter"):

        #init. lists
        listParameters = staticData.PROPERTIES.unique()
        listObsWells = obs_dict.COMMON_WELLNAME.unique()

        obs_property = obs_property[obs_property['PROPERTY_DESCRIPTION'].isin(listParameters)]
        #? Are these variables necessary?
        

    #     surfacePad = st.multiselect('By Surface Pad', listPads)
    #     parentWell = st.multiselect('By Parent Well-Pair', listParentWells)

        availableParameter = st.multiselect('By Available Parameters', listParameters)

        if availableParameter:
            #? listObsWells = obs_property[(obs_property['COMMON_WELLNAME'].isin(listObsWells)) & \
            #?                             (obs_property['PROPERTY_DESCRIPTION'].isin(availableParameter))] \
            #?                             .COMMON_WELLNAME.unique()
            listObsWells = multi_filter(obs_property, listObsWells, availableParameter)

        #Obs Well Metadata
        obsWell = st.selectbox('Observation Well', listObsWells)
        #* obsWellUWI = obs_dict.loc[obs_dict['COMMON_WELLNAME'] == obsWell, 'CURRENT_UWI'].iloc[0]
        # obsWellBoreID = obs_dict.loc[obs_dict['COMMON_WELLNAME'] == obsWell, 'SUNCOR_WELLBORE_ID'].iloc[0]
        if obsWell:
            obsWellBoreID = obs_dict[obs_dict['COMMON_WELLNAME'] == obsWell].SUNCOR_WELLBORE_ID.unique()[0]
        obsWellProperties = obs_property[obs_property['COMMON_WELLNAME']==obsWell].PROPERTY_DESCRIPTION.unique()
    
    #Trace Properties Section
    with st.expander('Trace Properties'):
        # obsAvailableParameters = obs_property[obs_property['COMMON_WELLNAME']==obsWell].PROPERTY_DESCRIPTION.unique()

        #! Temp form structure
        with st.form("Trace Select", clear_on_submit=False):
            chartScale = int(st.slider(label='Chart Scale',min_value=1, max_value=200, value=100))
            figureSelect = st.selectbox('Figure', st.session_state.listFigNames, index=st.session_state.figureSelectIndex)
            parameterToTrace = st.multiselect('Parameters to Trace', obsWellProperties)
            parameterTraceAction = st.selectbox("Select Action", ['Add Traces', 'Clear Figure'])
            parameterTraceSubmit = st.form_submit_button("Submit")
        st.experimental_data_editor(st.session_state.traceSelectionMatrix,use_container_width=True)
        clearAllTraces = st.button('Clear All')
        plotTraces = st.button('Plot All')

        

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

if plotTraces == True:
    with st.spinner("Querying Data"):
        #! Keep the query one time out here
        data = get_obs_log_fb(obsWellBoreID)
        data['MD'] = data['MD'].astype(float)
    for col in st.session_state.traceSelectionMatrix.columns:
        #! First I should query all data on a form run button at once and cache it based on the unique vals and ObsWell
        toPlot = st.session_state.traceSelectionMatrix[col]
        for parameter in toPlot:
            # st.write(obs_property[(obs_property['COMMON_WELLNAME']==obsWell)&(obs_property['PROPERTY_SHORT_NAME']==parameter)]['SOURCE'].to_list()[1])
            try:
                # parameterSource = obs_property[(obs_property['COMMON_WELLNAME']==obsWell)&(obs_property['PROPERTY_SHORT_NAME']==parameter)]['SOURCE'].reset_index(drop=True).iat[0]
                parameterSource = 'Log' #! Fix this

                if parameterSource == 'Log':
                    sample = data[data['MNEMONIC_NAME']==parameter]
                    sample = sample.sort_values(by='MD').reset_index(drop=True)
                    fig1.append_trace(go.Scatter(x=sample['MNEMONIC_VALUE'], y=sample['MD'], name=parameter+f' {col}'), 1, int(col))
            except Exception as e:
                print(e)

# """
# Visualization Properties
# """
fig1.update_layout(
    autosize=False,
    width=chartScale*8,
    height=chartScale*8, 
    showlegend=True, 
    hovermode="y unified", 
    title=obsWell,
    yaxis_title="Depth (mKB)",
    legend_title="Traces",
    yaxis_range=[0,180])
fig1.update_xaxes(
    showgrid=True, 
    gridwidth=1, 
    nticks = 5)
fig1.update_yaxes(matches='y')
fig1.update_traces(hovertemplate=None)
fig1['layout']['yaxis']['autorange'] = "reversed"


# """
# Main Grid Elements
# """
# expParameterTraceAction = option_menu(
#                 None,
#                 ["Add Traces", "Pad Trends", "Parent SAGD"], 
#                 icons=['arrow-bar-up', 'x-circle'],
#                 default_index=0, orientation="horizontal"
#                 )



st.plotly_chart(fig1, theme="streamlit")

from streamlit_elements import elements, mui, html, dashboard

with elements("dashboard"):

    # You can create a draggable and resizable dashboard using
    # any element available in Streamlit Elements.

    

    # First, build a default layout for every element you want to include in your dashboard

    layout = [
        # Parameters: element_identifier, x_pos, y_pos, width, height, [item properties...]
        dashboard.Item("first_item", 0, 0, 2, 2),
        dashboard.Item("second_item", 2, 0, 2, 2, isDraggable=False, moved=False),
        dashboard.Item("third_item", 0, 2, 1, 1, isResizable=False),
    ]

    # Next, create a dashboard layout using the 'with' syntax. It takes the layout
    # as first parameter, plus additional properties you can find in the GitHub links below.

    with dashboard.Grid(layout):
        # mui.Paper("First item", key="first_item")

        mui.Paper("Second item (cannot drag)", key="second_item")
        mui.Paper("Third item (cannot resize)", key="third_item")

    # If you want to retrieve updated layout values as the user move or resize dashboard items,
    # you can pass a callback to the onLayoutChange event parameter.

    # def handle_layout_change(updated_layout):
    #     # You can save the layout in a file, or do anything you want with it.
    #     # You can pass it back to dashboard.Grid() if you want to restore a saved layout.
    #     print(updated_layout)

    # with dashboard.Grid(layout, onLayoutChange=handle_layout_change):
    #     mui.Paper("First item", key="first_item")
    #     mui.Paper("Second item (cannot drag)", key="second_item")
    #     mui.Paper("Third item (cannot resize)", key="third_item")
        with elements("nivo_charts", key="first-item"):

            # Streamlit Elements includes 45 dataviz components powered by Nivo.

            from streamlit_elements import nivo

            DATA = [
                { "taste": "fruity", "chardonay": 93, "carmenere": 61, "syrah": 114 },
                { "taste": "bitter", "chardonay": 91, "carmenere": 37, "syrah": 72 },
                { "taste": "heavy", "chardonay": 56, "carmenere": 95, "syrah": 99 },
                { "taste": "strong", "chardonay": 64, "carmenere": 90, "syrah": 30 },
                { "taste": "sunny", "chardonay": 119, "carmenere": 94, "syrah": 103 },
            ]

            with mui.Box(sx={"height": 500}):
                nivo.Radar(
                    data=DATA,
                    keys=[ "chardonay", "carmenere", "syrah" ],
                    indexBy="taste",
                    valueFormat=">-.2f",
                    margin={ "top": 70, "right": 80, "bottom": 40, "left": 80 },
                    borderColor={ "from": "color" },
                    gridLabelOffset=36,
                    dotSize=10,
                    dotColor={ "theme": "background" },
                    dotBorderWidth=2,
                    motionConfig="wobbly",
                    legends=[
                        {
                            "anchor": "top-left",
                            "direction": "column",
                            "translateX": -50,
                            "translateY": -40,
                            "itemWidth": 80,
                            "itemHeight": 20,
                            "itemTextColor": "#999",
                            "symbolSize": 12,
                            "symbolShape": "circle",
                            "effects": [
                                {
                                    "on": "hover",
                                    "style": {
                                        "itemTextColor": "#000"
                                    }
                                }
                            ]
                        }
                    ],
                    theme={
                        "background": "#FFFFFF",
                        "textColor": "#31333F",
                        "tooltip": {
                            "container": {
                                "background": "#FFFFFF",
                                "color": "#31333F",
                            }
                        }
                    }
                )


        












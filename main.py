import streamlit as st
import pandas as pd
import numpy as np
import pyodbc
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objs as go

import os,sys
from azure.storage.filedatalake import DataLakeServiceClient
from azure.core._match_conditions import MatchConditions
from azure.storage.filedatalake._models import ContentSettings

from st_aggrid import AgGrid

from obs_query import get_temps

#! TODO: Move these to another file
#! Probably need to write a query to somehow obtain the necessary logs based on my previous mapping? Or use DIP - Identify OBS wells 
#! Use my table + match with DIP "observation" - wellbore type to determine the list
def dip_sql_connect():
    conn = pyodbc.connect(driver='{SQL Server}',
                            server='dipdevarmsvruw2001.database.windows.net',
                            database='dipdevarmsdbuw2001',
                            uid='arbtest',
                            pwd='L0r3tt414')
    return conn

def dip_synapse_connect():
    conn2 = pyodbc.connect(DRIVER='{Devart ODBC Driver for Azure Synapse Analytics}',
                           server = '',
                           database = '',
                           uid = '',
                           pwd = '')
    return conn2

# @st.cache_resource
# def load_temps(a):
#     temps = get_temps(a)
#     return temps

# if ['c', 's3', 's4', 'sl1'] not in st.session_state:
#     st.session_state.c = ''
#     st.session_state.s3 = 'DTS'
#     st.session_state.s4 = '1y'
#     st.session_state.sl1 = ['0','400']

# def reload_temps():
#     global temps, temp2
#     try:
#         st.write(st.session_state.c, st.session_state.s3, st.session_state.s4, st.session_state.sl1[1], st.session_state.sl1[0])
#         temps = get_temps(st.session_state.c, st.session_state.s3, st.session_state.s4, st.session_state.sl1[1], st.session_state.sl1[0])
#         st.session_state.temp = temps
#         temp2 = pd.melt(st.session_state.temp.reset_index(), id_vars='Date', var_name = 'DEPT')
#         temp2 = temp2[pd.to_numeric(temp2.value, errors='coerce').notnull()]
#         st.session_state.temp2 = temp2
#     except Exception as e:
#         st.write(e)
if 'temp_queried' not in st.session_state:
    st.session_state.temp_queried=False
    

cursor = dip_sql_connect()

pad_qry = """
SELECT DISTINCT SurfacePadName, ProjectName FROM [dbo].[DimSagdSurfacePad]
"""
pads = pd.read_sql(pad_qry, cursor)

well_dict_qry = """
SELECT COMMON_WELLBORE_NAME, SUNCOR_WELLBORE_ID FROM [dbo].[wellbore_description]
"""
well_dict = pd.read_sql(well_dict_qry, cursor)

lst_obs = pd.read_csv('list_obs.csv')
surveys = pd.read_csv('surveys.csv')
logs = pd.read_csv('test_logs.csv')
obs_map = pd.read_csv('mapping.csv')
obs_map = pd.merge(obs_map, well_dict, how='left', left_on='OBS_SUNCOR_WELLBORE_ID', right_on='SUNCOR_WELLBORE_ID')
#! Add Name standardization to MacKay River step here



### Data Above ###
st.set_page_config(page_title='OBS Well Analyzer')

st.markdown(f'''
    <style>
        section[data-testid="stSidebar"] .css-ng1t4o {{width: 21rem;}}
        section[data-testid="stSidebar"] .css-1d391kg {{width: 21rem;}}
    </style>
''',unsafe_allow_html=True)

st.sidebar.title("OBS Well Analyzer")

st.sidebar.caption('Dev Build')


#Init variables
lstPadB = pads.SurfacePadName.to_list()
parent_wells = obs_map.WELL_PAIR.unique()
lstWellsB = obs_map.COMMON_WELLBORE_NAME.unique()

#Session state vars
if 'index' not in st.session_state:
    st.session_state.index = 0

if 'temp' not in st.session_state:
    st.session_state.temp = pd.DataFrame()

if 'temp2' not in st.session_state:
    st.session_state.temp2 = pd.DataFrame()

if 'c' not in st.session_state:
    st.session_state.c = ''




with st.sidebar:
    with st.expander("Filter"):
        a = st.multiselect('Project', ('Firebag', 'MacKay River'))

        if a:
            lstPadB = pads[pads['ProjectName'].isin(a)].SurfacePadName.to_list()
            parent_wells = obs_map[obs_map['PROJECT'].isin(a)].WELL_PAIR.unique()
            lstWellsB = obs_map[obs_map['PROJECT'].isin(a)].COMMON_WELLBORE_NAME.unique()


        b = st.multiselect('Surface Pad', lstPadB)

        if b:
            parent_wells = obs_map[obs_map['SURFACE_PAD'].isin(b)].WELL_PAIR.unique()
            lstWellsB = obs_map[obs_map['SURFACE_PAD'].isin(b)].COMMON_WELLBORE_NAME.unique()
    


        bc = st.multiselect('Parent Well-Pair', parent_wells)

        if bc:
            lstWellsB = obs_map[obs_map['WELL_PAIR'].isin(bc)].COMMON_WELLBORE_NAME.unique()

        # c = st.selectbox('Observation Well', lstWellsB)
        c = st.selectbox('Observation Well', ['OB11','OB12', 'OB70'])
        d = st.multiselect('Parameter', ['GR', 'VMI'])
        wellbore_type = st.multiselect('Wellbore Type', ['Observation', 'Vertical'])

    with st.expander('Trace Properties'):
        # with st.form("Trace Properties", clear_on_submit=False):
        scale = int(st.slider(label='Chart Scale',min_value=1, max_value=200, value=100))
        g = st.button('Reset Axes')
        left = st.button('Move Figure Left')
        h = st.selectbox('Figure', [1,2,3,4,5], index=st.session_state.index)
        ab = st.multiselect('Parameters to Trace', ['M_GR', 'I_BMFO', 'I_LVMI', 'Facies'], key='multiselect')
        ae = st.button('Add Traces')
        ag = st.button('Clear Figure')
        ac = st.button('Clear All')
       


    
if ac == True:
    # ab = []
    clr = pd.DataFrame([],columns=['1','2','3','4','5'])
    clr.to_csv('savedata.csv',header=True, index=False)

if ag == True:
    dta = pd.read_csv('savedata.csv')
    dta[str(h)] = None
    dta.to_csv('savedata.csv', header=True, index=False)

if left == True:
    if int(h) != 1:
        dta = pd.read_csv('savedata.csv')
        lefcol = int(h)-1
        temp = dta[str(lefcol)]
        dta[str(lefcol)] = dta[str(h)]
        dta[str(h)] = temp
        dta.to_csv('savedata.csv', header=True, index=False)
        st.session_state.index = int(h)-2
        st.experimental_rerun() #!Have to ensure that if we use re-run that the bottom calculation omitting does not effect anything bad or then we should move this code down
    


        #! I need to figure out a way using key to also update "Figure" val so we can track that figure
        #! And I need to rename the _3 to _2 etc.
        #! Or it might be handled already

        #! I eventually want to move it to nearest ACTIVE fig rather than defaulting to ...

        #!Bulk add trace to all/multiple figures would be good
    

svy = surveys[surveys['WELL_PAIR']==c]
log = logs[logs['COMMON_WELLBORE_NAME']==c]
log = log[log['MNEMONIC_VALUE']>-900]
gre = log[log['FILE_MNEMONIC_NAME']=='M_GR']
gre.rename({'MNEMONIC_VALUE':'Gamma Ray'},axis=1,inplace=True)
#Apply filter
gre = gre[(gre['Gamma Ray']>0) & (gre['Gamma Ray']<200)]
gr = gre
# gr = st.experimental_data_editor(gre)

vmi = log[log['FILE_MNEMONIC_NAME']=='I_LVMI']
vmi.rename({'MNEMONIC_VALUE':'VMI'},axis=1,inplace=True)
vmi = vmi[(vmi['VMI']>0) & (vmi['VMI']<1)]

bmfo = log[log['FILE_MNEMONIC_NAME']=='I_BMFO']
bmfo.rename({'MNEMONIC_VALUE':'BMFO'},axis=1,inplace=True)
bmfo = bmfo[(bmfo['BMFO']>0)]

gr.sort_values(by='MD', inplace=True)
vmi.sort_values(by='MD', inplace=True)
bmfo.sort_values(by='MD', inplace=True)

col1, col2 = st.columns([1,1])

test = pd.merge(vmi, bmfo, on='MD', how='inner')



# with col1:
#     brush = alt.selection(type='interval', resolve='global')
#     selection = alt.selection_multi(fields=['series'], bind='legend', init=[{'series': 'BMFO'}])


#     # fig1 = alt.Chart(svy).mark_point().transform_fold(
#     # fold=['MD', 'Z'], 
#     # as_=['variable', 'value']).encode(x='MD',  y='max(value):Q', color=alt.condition(brush, 'variable:N', alt.ColorValue('gray'))).add_selection(brush).properties(width=scale*3,height=scale*8)
#     fig0 = alt.Chart(gr).mark_line().transform_fold(
#     fold=['Gamma Ray'], 
#     as_=['variable', 'value']).encode(x='max(value):Q', y='MD', color=alt.condition(brush, 'variable:N', alt.ColorValue('gray'))).add_selection(brush).properties(width=scale*3,height=scale*8)

#     figA = alt.Chart(test).mark_line().transform_fold(
#     fold=['VMI', 'BMFO'], 
#     as_=['variable', 'value']).encode(x='max(value):Q', y='MD', 
#                                     color=alt.condition(brush, 'variable:N', alt.ColorValue('gray'), legend=alt.Legend(orient='bottom'))).add_selection(selection).interactive().properties(width=scale*3,height=scale*8)



    # figB = alt.Chart(bmfo).mark_line().transform_fold(
    # fold=['BMFO'], 
    # as_=['variable', 'value']).encode(x='max(value):Q', y='MD').interactive().properties(width=scale*3,height=scale*8)

    # figB = alt.Chart(bmfo).mark_line().transform_fold(
    # fold=['BMFO'], 
    # as_=['variable', 'value']).encode(
    #     alt.X('BMFO'),
    #     alt.Y('MD'),
        # alt.Color('series:N', scale=alt.Scale(scheme='category20b')),
        # opacity=alt.condition(selection, alt.value(1), alt.value(0.2))
    # ).add_selection(
    #     selection
    # )


    # fig1 = alt.Chart(svy).mark_point().transform_fold(
    # fold=['MD', 'Z'], 
    # as_=['variable', 'value']).encode(x='MD',  y='max(value):Q', color=alt.Color('variable:N', legend=alt.Legend(orient='bottom'))).add_selection(brush).properties(width=scale*3,height=scale*8)
    # fig2 = alt.Chart(svy).mark_point().encode(x='MD', y='TVD').properties(width=scale*3,height=scale*8)
    # fig3 = alt.Chart(svy).mark_point().encode(x='TVD', y='Z',color=alt.condition(brush, 'TVD', alt.ColorValue('#ff6361'))).properties(width=scale*3,height=scale*8)
    # fig4 = alt.Chart(svy).mark_point().encode(x='MD', y='TVD').properties(width=scale*3,height=scale*8)
    # fig5 = alt.Chart(svy).mark_point().encode(x='MD', y='TVD').properties(width=scale*3,height=scale*8)
    # fig6 = alt.Chart(svy).mark_point().encode(x='TVD', y='Z').properties(width=scale*3,height=scale*8)
    # if e:
    #     # st.altair_chart(fig1 | fig2 + fig3 | fig4 | fig5 | fig6)
    #     st.altair_chart(fig0 | figA)
    # else:
    #     # st.altair_chart(fig1 + fig2 + fig3)
    #     st.altair_chart(fig0)

# with col3:
#     # st.altair_chart(fig0)
#     st.write(' ')

# with col2:
#     st.write('Notes')

#######

fig = make_subplots(rows=1, cols=5)

y = vmi.MD.to_list()
# p1 = go.Scatter(x=gr['Gamma Ray'], y=gr['MD'], name='Gamma Ray')
# fig.append_trace(p1, 1, 1)
# p2 = go.Scatter(x=vmi['VMI'], y=vmi['MD'], name='VMI')
# p3 = go.Scatter(x=bmfo['BMFO'], y=bmfo['MD'], name='BMFO')
# fig.append_trace(p2, 1, 2)
# fig.append_trace(p3, 1, 2)
# fig.append_trace(p4, 1, 1)
#! Disucss with SMEs what our default traces will be
#! Date filtering will also be a very powerful feature

with st.expander('Temperature Profiler'):
    with st.form('Temperature Profiler'):
        h1 = st.selectbox('Figure', [1,2,3,4,5])
        s2 = st.selectbox('Instrumentation Type', ['DTS'])
        s3 = st.selectbox('Frequency', ['1mo', '1y', '2y'], index=1)
        
        s4a = (st.date_input('Start Date', value=dt.date(2004,1,1)))
        sel_end_date_a = (st.date_input('End Date', value=dt.date.today()))
        
        s4 = str(dt.datetime.strftime(s4a, '%m/%d/%Y'))
        sel_end_date = str(dt.datetime.strftime(sel_end_date_a, '%m/%d/%Y'))
        sl1 = st.slider(label='Depth (mKB)', value=[0,400], step = 10)
        
        gen_anim = st.checkbox('Generate Animation')
        bool_sagd_parent = st.checkbox('Generate SAGD Parent Data')
        r1 = st.form_submit_button("Trace")



if r1 == True:
        with st.spinner('Querying Temperature Profile...'):
                
                st.session_state.temp_queried = True
                temps = get_temps(c, s3, s4, sl1[1], sl1[0])
                st.session_state.temp = temps
                temp2 = pd.melt(st.session_state.temp.reset_index(), id_vars='Date', var_name = 'DEPT')
                temp2 = temp2[pd.to_numeric(temp2.value, errors='coerce').notnull()]
                st.session_state.temp2 = temp2

       
        testdf = pd.read_csv('savedata.csv')
        testdf.drop_duplicates(inplace=True)
        savedata = pd.DataFrame([], columns=['1','2','3','4','5'])
        savedata[str(h1)] = [s2]
        final = pd.concat([testdf, savedata],axis=0)
        final.drop_duplicates(inplace=True)
        final.to_csv('savedata.csv', index=False, header=True)
            

#Query SAGD parent data
if bool_sagd_parent == True:
    
    parent_qry = F"""
    SELECT 
        WELL_PAIR, 
        TIMESTAMP,
        EST_OIL_RATE, 
        IMP_STM_CHB_PRESS
    FROM ARB_SAA_NGF_CALC_DATA_VW
    WHERE WELL_PAIR = '{bc}' AND
    TIMESTAMP > 'str{s4a}' AND
    TIMESTAMP < 'str{sel_end_date_a}'
    ORDER BY TIMESTAMP ASC
    """
    # parent_sagd_df = pd.read_sql(well_dict_qry, cursor)

if (c != st.session_state.c) & (st.session_state.temp_queried == True):
    with st.spinner('Querying Temperature Profile...'):
        temps = get_temps(c, s3, s4, sl1[1], sl1[0])
        st.session_state.temp = temps
        temp2 = pd.melt(st.session_state.temp.reset_index(), id_vars='Date', var_name = 'DEPT')
        temp2 = temp2[pd.to_numeric(temp2.value, errors='coerce').notnull()]
        st.session_state.temp2 = temp2
        st.session_state.c = c
        #* This C will be used to control temp profiling
        #* This code for temp. profiling

if ae == True:
    for selected in ab:
        testdf = pd.read_csv('savedata.csv')
        testdf.drop_duplicates(inplace=True)
        # testdf = testdf.mask(testdf.duplicated())
        savedata = pd.DataFrame([], columns=['1','2','3','4','5'])
        savedata[str(h)] = [selected]
        final = pd.concat([testdf, savedata],axis=0)
        final.drop_duplicates(inplace=True)
        # final = final.mask(final.duplicated())
        #! We will need to drop dupes in all columns
        final.to_csv('savedata.csv', index=False, header=True)
        #! How are we handling blank selections - it seems good
        #! Ability to apply user filters? like taking out negs? can use interactive editor tbh
        #! Caching the SQL data and plot will be best because that way I dont have to do a savedata 


data = pd.read_csv('savedata.csv')
data.drop_duplicates(inplace=True)
# data = data.mask(data.duplicated())

    
for column in data.columns:
    sample = data[column]
    for s in sample:

        if s == 'DTS':
            # temps = pd.read_csv('temp_temp.csv').set_index('Date')
            # st.write(temps)

            p1 = px.scatter(x=st.session_state.temp2['value'], 
                         y=st.session_state.temp2['DEPT'], 
                         animation_frame=st.session_state.temp2["Date"], 
                         animation_group=st.session_state.temp2['DEPT'],
                         color=st.session_state.temp2['value'].astype(float),
                         color_continuous_scale='rdbu_r',
                         range_color=[-25,25],
                        #  range_x=[st.session_state.temp2['value'].min(), st.session_state.temp2['value'].max()]
                        range_x = [-200, 200]
                         )
            
            # frames = [go.Frame(data=[p1]) for k in range(10)]
            # fig2 = go.Figure(data = frames[0]["data"],
            #                  frames = frames[1:])
                             
                            
            
            #!Only if temps exists
            try:
                
                
            
                for i in range(0,len(st.session_state.temp)):
                    try:
                        tem = st.session_state.temp.iloc[i,:].astype(float)
                        
                        fig.append_trace(go.Scatter(x=tem, y=tem.index,opacity=0.8*(i/len(st.session_state.temp)),marker=dict(color='red'),
                                    showlegend=False,
                                    name=str(st.session_state.temp.index[i])),1, int(column))
                        #! Temperature profile should be a form that possesses not just which figure but how far to look back and the range of deprhs
                        #! Ability to plot a certain depth over time temp profile and also maybe even see the DF for a point
                        #! Use it like a function in the form to be able to plot - the timerange - the frequency/aggreg. - the well
                        #! I think that I should have a color dictionary so gamma ray always green etc.
                    except Exception as e:
                        continue
            except:
                st.warning('Query Temps')
        
     
        if s == 'Facies':
            
            #! Move var elsewhere
            cscale = [(0.00, "#003f5c"),   (0.05, "#003f5c"),
                        (0.05, "#58508d"), (0.15, "#58508d"),
                        (0.15, "#bc5090"),  (0.30, "#bc5090"),
                        (0.30, "#ff6361"),  (0.70, "#ff6361"),
                        (0.7, "#ffa600"),  (1, "#ffa600")]

            flog = log[log['FILE_MNEMONIC_NAME']=='I_LVMI'].sort_values(by='MD')
            fig.append_trace(go.Heatmap(x=[], y=flog['MD'], z=flog['MNEMONIC_VALUE'][:,np.newaxis], name=f'I_LVMI_Facies_{column}', showscale=False, colorscale=cscale, showlegend=True), 1, int(column))
            
            
        else:
            try:
                flog = log[log['FILE_MNEMONIC_NAME']==s]
                flog.sort_values(by='MD',inplace=True)
                fig.append_trace(go.Scatter(x=flog['MNEMONIC_VALUE'], y=flog['MD'], name=s+f'_{column}'), 1, int(column))
            except:
                continue

 #! Putting this here for more plot control with aggrid
with st.expander('Temps'):
    st.experimental_data_editor(st.session_state.temp2) #! Use AgGrid here later
    st.download_button(label='Download Temperature Data', data=st.session_state.temp.to_csv().encode('utf-8'), file_name=f'{c}_{s2}_temp_profile.csv', mime='text/csv')
    #!Use experimental re-load here if values modified

p1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
p1.update_layout(autosize=False,width=scale*3,height=scale*8, showlegend=True, yaxis_range=[0,180])
fig.update_layout(autosize=False,width=scale*8,height=scale*8, showlegend=True, yaxis_range=[0,180])
fig.update_coloraxes(
    colorbar=dict(
    tickmode='array',
    title='Facies',
    tickvals=[1,2,3,4,5],
    ticktext=['F1 (Sandstone)', 'F2 (Sandy IHS)', 'F3 (IHS)', 'F4 (Muddy IHS)', 'F5 (Mudstone)']
    ))
fig.update_xaxes(showgrid=True, gridwidth=1, nticks = 5)
fig.update_yaxes(matches='y')
fig.update_traces(hovertemplate=None)
fig.update_layout(hovermode="y unified", 
    title=c,
    yaxis_title="Depth (mKB)",
    legend_title="Traces",)
fig['layout']['yaxis']['autorange'] = "reversed"
p1['layout']['yaxis']['autorange'] = "reversed"
#! Work on tooltips functionality

sel = ['Gamma Ray', 'VMI', 'BMFO']
# fig.update_traces(selector=lambda t: t.name not in sel, visible='legendonly')
#have a g1-gn , vmi1-vmin, to be able to plot on any thingt
#! It defaults every time code runs so should be a parameter that keeps user defined traces active always

with col2:
    st.plotly_chart(fig,theme="streamlit")
with col1:
    if gen_anim == True:
        st.plotly_chart(p1, theme='streamlit')




# with st.form("Model Parameters", clear_on_submit=False):
#     st.write("Model Parameters")
#     selectbox_val = st.selectbox("Convective Top Model", ['V1', 'V2'])
#     af = st.experimental_data_editor(log)
#     submitted = st.form_submit_button("Run")



#? Really we want these to be optional filters to the overarching list of observation wells
#? The experimental data editor looks to be good
#? Filter option to compare a secondary well? Until we resolve the finite plots issue we can do allocate so its 1-2 1-2 1-2 11 22 33 123456 comparisons
#If combine plot then change it to add plots rather than horizontal concat
#Realistically, analyzing Dylan's plot - we would not plot everything on the same plot due to scale - And because of that in theory we can use Plotly and Dylan's style - I would like to give both options and let users test
#Investigate using repeated or faceted chart instead
#Be able to change the order of plots by having a function that plays with the concatenation order


cursor.close()


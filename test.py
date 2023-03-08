import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


import plotly.express as px
import plotly.subplots as sp
from plotly.offline import plot

# timeseries = pd.read_csv('timeseries_timeseries.csv')
# timeseries = pd.melt(timeseries, id_vars='Date', var_name = 'DEPT')
# print(timeseries)
timeseries = pd.read_csv('timeseries.csv')



p1 = px.scatter(x=timeseries['value'], 
             y=timeseries['DEPT'],
             animation_frame=timeseries["Date"],
             animation_group=timeseries['DEPT'],
             range_x=[timeseries.value.max(), timeseries.value.min()])
p2 = px.scatter(x=timeseries['value'], 
             y=timeseries['DEPT'],
             animation_frame=timeseries["Date"],
             animation_group=timeseries['DEPT'],
             range_x=[timeseries.value.max(), timeseries.value.min()])
# p1.update_layout(margin=dict(l=20, r=20, t=20, b=20))
# p1.update_layout(autosize=True,width=100*3,height=100*8, showlegend=True, yaxis_range=[0,500])

figure1_traces = []
figure2_traces = []
for trace in range(len(p1["data"])):
    figure1_traces.append(p1["data"][trace])
for trace in range(len(p2["data"])):
    figure2_traces.append(p2["data"][trace])

this_figure = sp.make_subplots(rows=1, cols=2) 

# Get the Express fig broken down as traces and add the traces to the proper plot within in the subplot
for traces in figure1_traces:
    this_figure.append_trace(traces, row=1, col=1)
for traces in figure2_traces:
    this_figure.append_trace(traces, row=1, col=2)

#Create a 1x2 subplot
this_figure.show()


# p1.update_yaxes(matches=None)
# p1.for_each_yaxis(lambda yaxis: yaxis.update(showticklabels=True))
# i = 0
# for row_idx, row_p1s in enumerate(p1._grid_ref): 
#     for col_idx, col_p1 in enumerate(row_p1s):
#           i+=1
#           print(i)
#           if i==1:
#             p1.update_yaxes(row=row_idx+1, col=col_idx+1,
#                 matches = 'y'+str(len(row_p1s)*row_idx+1))
#           if i==2:
#             p1.update_yaxes(row=row_idx+1, col=col_idx+1,
#                     matches = 'y'+str(len(row_p1s)*row_idx+1),
#                     range=[0,300])
p1.write_html("anim.html")


# p1 = make_subplots(rows=1, cols=1)

# for i in range(0,len(timeseries.columns)):
#     try:
#         tem = timeseries.iloc[:,i].astype(float)
        
# p1.append_trace(p1,1,1)
#                     name=str(timeseries.index[i])),1,1)
   
#     except Exception as e:
#         print(e)
# p1.show()
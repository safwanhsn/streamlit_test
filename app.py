import streamlit as st 
import pandas as pd

test = pd.read_csv('surveys.csv')
st.write(test)
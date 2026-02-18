import streamlit as st
import pandas as pd
# import sys
# sys.path.append('..') # Might be needed if you import from src
# from src import utils

st.title("Hotel Analytics Dashboard")

# Example loading data
# Note: Streamlit usually runs from the root of the repo if configured that way
try:
    df = pd.read_json('../data/review.json')
    st.write(df.head())
except Exception as e:
    st.error(f"Error loading data: {e}")

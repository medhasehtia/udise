import streamlit as st
import pandas as pd # Even if you don't use it yet, keep it if it's in your requirements.txt

st.title("Hello Streamlit!")
try:
    df = pd.read_csv("data/100_prof1.csv")
    st.write("Successfully loaded data file.")
except Exception as e:
    st.error(f"Error loading data: {e}")
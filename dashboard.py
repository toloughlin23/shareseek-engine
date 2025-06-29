import streamlit as st
from engine.promotion_manager import render_promotion_dashboard

st.set_page_config(page_title="Share-Seek Dashboard", layout="wide")

st.sidebar.title("Navigation")
view = st.sidebar.radio("Go to:", ["Paper Training"])

if view == "Paper Training":
    render_promotion_dashboard()

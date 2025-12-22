import streamlit as st
import pandas as pd

def init_portfolio():
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = pd.DataFrame(
            columns=["Ticker", "Quantity", "Buy_Price", "Buy_Date"]
        )

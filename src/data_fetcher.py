import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_historical_data(tickers, period="1y"):
    """
    Fetch historical price data for given tickers.
    
    Args:
        tickers: List of ticker symbols
        period: Time period (1mo, 3mo, 6mo, 1y, 2y, etc.)
    
    Returns:
        DataFrame with historical close prices
    """
    try:
        if len(tickers) == 1:
            data = yf.download(
                tickers[0],
                period=period,
                auto_adjust=True,
                progress=False
            )
            
            # Handle single ticker case - Close is already a Series
            if isinstance(data, pd.DataFrame):
                if "Close" in data.columns:
                    data = data["Close"]
                    # Convert Series to DataFrame with ticker as column name
                    data = pd.DataFrame(data, columns=[tickers[0]])
                else:
                    # If no Close column, data might already be the close prices
                    data = pd.DataFrame(data, columns=[tickers[0]])
            else:
                # If data is already a Series
                data = pd.DataFrame(data, columns=[tickers[0]])
        else:
            data = yf.download(
                tickers,
                period=period,
                auto_adjust=True,
                progress=False
            )
            
            # Handle multiple tickers case
            if isinstance(data, pd.DataFrame):
                if "Close" in data.columns:
                    data = data["Close"]
                # If data is already just close prices, keep as is
            
            # Ensure it's a DataFrame
            if not isinstance(data, pd.DataFrame):
                data = pd.DataFrame(data)
        
        # Final check - ensure we have data
        if data.empty:
            st.warning(f"No data returned for tickers: {tickers}")
            return pd.DataFrame()
        
        return data
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()


def get_price_on_date(ticker, buy_date):
    """
    Fetch closing price for a ticker on a specific date.
    Handles weekends and market holidays.
    
    Args:
        ticker: Stock ticker symbol
        buy_date: Date to fetch price for
    
    Returns:
        Float price or None if not found
    """
    try:
        target_date = pd.to_datetime(buy_date)
        
        # Fetch 10 days of data to handle weekends/holidays
        data = yf.download(
            ticker,
            start=target_date - pd.Timedelta(days=10),
            end=target_date + pd.Timedelta(days=5),
            auto_adjust=True,
            progress=False
        )
        
        if data.empty:
            return None
        
        # Get the closest available date
        data.index = pd.to_datetime(data.index)
        closest_date = min(data.index, key=lambda x: abs(x - target_date))
        
        return round(float(data.loc[closest_date, "Close"]), 2)
    
    except Exception as e:
        return None

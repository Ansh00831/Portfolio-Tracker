import pandas as pd
import numpy as np

def calculate_portfolio_values(portfolio_df, current_prices):
    """
    Calculate current values and returns for each holding.
    
    Args:
        portfolio_df: DataFrame with Ticker, Quantity, Buy_Price, Buy_Date
        current_prices: Dict of {ticker: current_price}
    
    Returns:
        DataFrame with calculated values
    """
    result_df = portfolio_df.copy()
    
    result_df["Current_Price"] = result_df["Ticker"].map(current_prices)
    result_df["Total_Cost"] = result_df["Quantity"] * result_df["Buy_Price"]
    result_df["Current_Value"] = result_df["Quantity"] * result_df["Current_Price"]
    result_df["Gain/Loss"] = result_df["Current_Value"] - result_df["Total_Cost"]
    result_df["Return %"] = (result_df["Gain/Loss"] / result_df["Total_Cost"]) * 100
    
    return result_df


def portfolio_summary(portfolio_df):
    """
    Calculate portfolio-level summary statistics.
    
    Returns:
        Tuple of (total_invested, total_value, total_return_pct)
    """
    total_invested = portfolio_df["Total_Cost"].sum()
    total_value = portfolio_df["Current_Value"].sum()
    total_return = ((total_value - total_invested) / total_invested) * 100
    
    return total_invested, total_value, total_return


def calculate_portfolio_returns(prices_df, portfolio_df):
    """
    Calculate time-weighted portfolio returns.
    Uses initial investment weights to avoid survivorship bias.
    Handles duplicate tickers by aggregating them.
    
    Args:
        prices_df: DataFrame with historical prices
        portfolio_df: DataFrame with portfolio holdings
    
    Returns:
        Tuple of (daily_returns_series, cumulative_returns_series)
    """
    # Work on a copy
    portfolio_copy = portfolio_df.copy()
    
    # Calculate initial value for each holding
    portfolio_copy["Initial_Value"] = portfolio_copy["Quantity"] * portfolio_copy["Buy_Price"]
    
    # Aggregate by ticker (handle duplicate tickers)
    aggregated = portfolio_copy.groupby("Ticker")["Initial_Value"].sum()
    
    # Calculate weights
    total_initial = aggregated.sum()
    weights = aggregated / total_initial
    
    # Calculate daily returns
    daily_returns = prices_df.pct_change().dropna()
    
    # Ensure weights align with daily_returns columns
    # Only use tickers that exist in both
    common_tickers = list(set(weights.index) & set(daily_returns.columns))
    weights = weights[common_tickers]
    daily_returns = daily_returns[common_tickers]
    
    # Weight the returns
    portfolio_returns = (daily_returns * weights).sum(axis=1)
    
    # Calculate cumulative returns
    portfolio_cumulative = (1 + portfolio_returns).cumprod()
    
    return portfolio_returns, portfolio_cumulative
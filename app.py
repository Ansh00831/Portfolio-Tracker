import streamlit as st
import pandas as pd
from datetime import date, datetime

from src.data_fetcher import fetch_historical_data, get_price_on_date
from src.portfolio_manager import load_portfolio, save_portfolio, delete_holdings
from src.calculations import calculate_portfolio_values, portfolio_summary, calculate_portfolio_returns
from src.risk_metrics import annualized_volatility, sharpe_ratio, max_drawdown, calculate_beta, value_at_risk_historical, value_at_risk_parametric, conditional_value_at_risk, calculate_drawdown_series
from src.visualizations import allocation_pie, performance_chart, returns_comparison, drawdown_chart

# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(
    page_title="Interactive Portfolio Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Initialize Session State
# ----------------------------
if "portfolio" not in st.session_state:
    st.session_state.portfolio = load_portfolio()

if "last_update" not in st.session_state:
    st.session_state.last_update = None

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    
    benchmark = st.selectbox(
        "Benchmark Index",
        options=["^GSPC", "^NSEI", "^DJI", "^IXIC"],
        format_func=lambda x: {
            "^GSPC": "S&P 500",
            "^NSEI": "NIFTY 50",
            "^DJI": "Dow Jones",
            "^IXIC": "NASDAQ"
        }[x],
        help="Select benchmark for comparison"
    )
    
    time_period = st.selectbox(
        "Analysis Period",
        options=["1mo", "3mo", "6mo", "1y", "2y"],
        index=3,
        help="Historical data period"
    )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save", use_container_width=True):
            save_portfolio(st.session_state.portfolio)
            st.success("Saved!")
    
    with col2:
        if st.button("📥 Load", use_container_width=True):
            st.session_state.portfolio = load_portfolio()
            st.success("Loaded!")
    
    if st.button("🗑️ Clear All", use_container_width=True, type="secondary"):
        st.session_state.portfolio = pd.DataFrame(
            columns=["Ticker", "Quantity", "Buy_Price", "Buy_Date"]
        )
        st.rerun()
    
    st.divider()
    
    if st.session_state.last_update:
        st.caption(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")

# ----------------------------
# Main Title
# ----------------------------
st.title("📊 Interactive Portfolio Tracker")

# ----------------------------
# Load Ticker Universe
# ----------------------------
try:
    tickers_df = pd.read_csv("data/tickers.csv")
except FileNotFoundError:
    st.error("❌ tickers.csv not found in data/ folder")
    st.stop()

# ----------------------------
# Add Asset Form
# ----------------------------
st.subheader("➕ Add Asset")

with st.form("add_asset", clear_on_submit=True):
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        ticker = st.selectbox(
            "Stock",
            tickers_df["Ticker"],
            format_func=lambda x: f"{x} - {tickers_df.loc[tickers_df['Ticker']==x,'Name'].values[0]}"
        )
    
    with col2:
        quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
    
    with col3:
        buy_date = st.date_input("Buy Date", value=date.today())
    
    # Auto-fill price
    auto_price = None
    if ticker and buy_date:
        with st.spinner("Fetching price..."):
            auto_price = get_price_on_date(ticker, buy_date)
    
    if auto_price:
        buy_price = st.number_input(
            "Buy Price (Auto-filled from historical data)",
            value=float(auto_price),
            step=0.01,
            format="%.2f"
        )
    else:
        buy_price = st.number_input(
            "Buy Price (Manual entry required)",
            min_value=0.01,
            step=0.01,
            format="%.2f"
        )
        if not auto_price:
            st.warning("⚠️ Could not fetch historical price. Please enter manually.")
    
    submitted = st.form_submit_button("Add to Portfolio", type="primary", use_container_width=True)
    
    if submitted:
        new_entry = pd.DataFrame([{
            "Ticker": ticker,
            "Quantity": int(quantity),
            "Buy_Price": float(buy_price),
            "Buy_Date": buy_date
        }])
        
        st.session_state.portfolio = pd.concat(
            [st.session_state.portfolio, new_entry],
            ignore_index=True
        )
        st.success(f"✅ {ticker} added successfully!")
        st.rerun()

# ----------------------------
# Check if Portfolio is Empty
# ----------------------------
if st.session_state.portfolio.empty:
    st.info("📝 Add assets to your portfolio to see analytics and insights.")
    st.stop()

# ----------------------------
# Fetch All Data
# ----------------------------
with st.spinner("📡 Fetching market data..."):
    try:
        tickers = st.session_state.portfolio["Ticker"].unique().tolist()
        
        # Fetch portfolio data
        prices_df = fetch_historical_data(tickers, period=time_period)
        
        # Fetch benchmark data
        benchmark_df = fetch_historical_data([benchmark], period=time_period)
        
        if prices_df.empty:
            st.error("❌ Failed to fetch price data. Please check your internet connection.")
            st.stop()
        
        # Get current prices
        current_prices = prices_df.iloc[-1].to_dict()
        
        # Update timestamp
        st.session_state.last_update = datetime.now()
        
    except Exception as e:
        st.error(f"❌ Error fetching data: {str(e)}")
        st.stop()

# ----------------------------
# Calculate Portfolio Values
# ----------------------------
portfolio_df = calculate_portfolio_values(
    st.session_state.portfolio,
    current_prices
)

total_invested, total_value, total_return = portfolio_summary(portfolio_df)

# ----------------------------
# Top KPIs
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "💰 Total Invested",
        f"${total_invested:,.2f}"
    )

with col2:
    st.metric(
        "📈 Current Value",
        f"${total_value:,.2f}",
        delta=f"${total_value - total_invested:,.2f}"
    )

with col3:
    color = "normal" if total_return >= 0 else "inverse"
    st.metric(
        "📊 Total Return",
        f"{total_return:.2f}%",
        delta=f"${total_value - total_invested:,.2f}",
        delta_color=color
    )

with col4:
    st.metric(
        "🎯 Total Holdings",
        len(st.session_state.portfolio)
    )

# ----------------------------
# Portfolio Holdings Table
# ----------------------------
st.subheader("📋 Portfolio Holdings")

# Add selection column for deletion
portfolio_display = portfolio_df.copy()
portfolio_display.insert(0, "Select", False)

# Format for display
portfolio_display["Buy_Price"] = portfolio_display["Buy_Price"].apply(lambda x: f"${x:.2f}")
portfolio_display["Current_Price"] = portfolio_display["Current_Price"].apply(lambda x: f"${x:.2f}")
portfolio_display["Total_Cost"] = portfolio_display["Total_Cost"].apply(lambda x: f"${x:,.2f}")
portfolio_display["Current_Value"] = portfolio_display["Current_Value"].apply(lambda x: f"${x:,.2f}")
portfolio_display["Gain/Loss"] = portfolio_display["Gain/Loss"].apply(lambda x: f"${x:,.2f}")
portfolio_display["Return %"] = portfolio_display["Return %"].apply(lambda x: f"{x:.2f}%")

# Editable dataframe
edited_df = st.data_editor(
    portfolio_display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Select": st.column_config.CheckboxColumn("Select", default=False),
    },
    disabled=["Ticker", "Quantity", "Buy_Price", "Buy_Date", "Current_Price", 
              "Total_Cost", "Current_Value", "Gain/Loss", "Return %"]
)

# Delete selected holdings
if edited_df["Select"].any():
    if st.button("🗑️ Delete Selected", type="secondary"):
        indices_to_keep = edited_df[~edited_df["Select"]].index.tolist()
        st.session_state.portfolio = st.session_state.portfolio.iloc[indices_to_keep].reset_index(drop=True)
        st.success("✅ Selected holdings removed!")
        st.rerun()

# ----------------------------
# Portfolio Allocation
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("🥧 Portfolio Allocation")
    st.plotly_chart(allocation_pie(portfolio_df), use_container_width=True)

with col2:
    st.subheader("📊 Top Holdings")
    top_holdings = portfolio_df.nlargest(5, "Current_Value")[["Ticker", "Current_Value", "Return %"]]
    
    for idx, row in top_holdings.iterrows():
        col_a, col_b, col_c = st.columns([2, 2, 1])
        col_a.write(f"**{row['Ticker']}**")
        col_b.write(f"${row['Current_Value']:,.2f}")
        
        return_val = row['Return %']
        if return_val >= 0:
            col_c.write(f"🟢 {return_val:.1f}%")
        else:
            col_c.write(f"🔴 {return_val:.1f}%")

# ----------------------------
# Calculate Returns
# ----------------------------
portfolio_returns, portfolio_cumulative = calculate_portfolio_returns(
    prices_df,
    st.session_state.portfolio
)

benchmark_returns = benchmark_df.pct_change().dropna().squeeze()
benchmark_cumulative = (1 + benchmark_returns).cumprod()

# ----------------------------
# Performance Comparison
# ----------------------------
st.subheader("📈 Performance Comparison")

portfolio_total_return = (portfolio_cumulative.iloc[-1] - 1) * 100
benchmark_total_return = (benchmark_cumulative.iloc[-1] - 1) * 100

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Portfolio Return",
        f"{portfolio_total_return:.2f}%",
        delta=f"{portfolio_total_return - benchmark_total_return:.2f}% vs benchmark"
    )

with col2:
    benchmark_name = {
        "^GSPC": "S&P 500",
        "^NSEI": "NIFTY 50",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ"
    }[benchmark]
    
    st.metric(
        f"{benchmark_name} Return",
        f"{benchmark_total_return:.2f}%"
    )

with col3:
    outperformance = portfolio_total_return > benchmark_total_return
    st.metric(
        "Relative Performance",
        "Outperforming" if outperformance else "Underperforming",
        delta=f"{abs(portfolio_total_return - benchmark_total_return):.2f}%",
        delta_color="normal" if outperformance else "inverse"
    )

# Performance chart
st.plotly_chart(
    performance_chart(portfolio_cumulative, benchmark_cumulative, benchmark),
    use_container_width=True
)

# ----------------------------
# Risk Metrics
# ----------------------------
st.subheader("⚠️ Risk Metrics")

vol = annualized_volatility(portfolio_returns)
sr = sharpe_ratio(portfolio_returns)
mdd = max_drawdown(portfolio_returns)
beta = calculate_beta(portfolio_returns, benchmark_returns)

# Calculate VaR and CVaR
var_95_hist = value_at_risk_historical(portfolio_returns, confidence_level=0.95)
var_95_param = value_at_risk_parametric(portfolio_returns, confidence_level=0.95)
cvar_95 = conditional_value_at_risk(portfolio_returns, confidence_level=0.95)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Annualized Volatility",
        f"{vol:.2%}",
        help="Standard deviation of returns (annualized)"
    )

with col2:
    sr_color = "normal" if sr > 1 else "inverse"
    sr_label = "Excellent" if sr > 1.5 else "Good" if sr > 1 else "Fair" if sr > 0 else "Poor"
    st.metric(
        "Sharpe Ratio",
        f"{sr:.2f}",
        delta=sr_label,
        delta_color=sr_color,
        help="Risk-adjusted return metric"
    )

with col3:
    st.metric(
        "Maximum Drawdown",
        f"{mdd:.2%}",
        help="Largest peak-to-trough decline"
    )

with col4:
    beta_label = "Defensive" if beta < 1 else "Neutral" if beta < 1.2 else "Aggressive"
    st.metric(
        "Beta",
        f"{beta:.2f}",
        delta=beta_label,
        help="Sensitivity to market movements"
    )

# ----------------------------
# Value at Risk & Expected Shortfall
# ----------------------------
st.subheader("📉 Downside Risk Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "VaR (95% Historical)",
        f"{var_95_hist:.2%}",
        help="Maximum expected loss at 95% confidence using historical data"
    )

with col2:
    st.metric(
        "VaR (95% Parametric)",
        f"{var_95_param:.2%}",
        help="Maximum expected loss at 95% confidence assuming normal distribution"
    )

with col3:
    st.metric(
        "Expected Shortfall (CVaR 95%)",
        f"{cvar_95:.2%}",
        help="Average loss when losses exceed VaR threshold"
    )

# Explanation of VaR
with st.expander("ℹ️ Understanding Value at Risk (VaR) & Expected Shortfall"):
    st.markdown("""
    **Value at Risk (VaR)**: Estimates the maximum loss over a given time period at a specified confidence level.
    - **Historical VaR**: Uses actual historical returns to calculate potential losses
    - **Parametric VaR**: Assumes returns follow a normal distribution
    
    **Expected Shortfall (CVaR)**: Also called Conditional VaR, it measures the average loss when losses exceed the VaR threshold. 
    This is more conservative than VaR as it accounts for tail risk.
    
    **Example**: A 95% VaR of 2% means there's a 5% chance of losing more than 2% in a single day.
    If CVaR is 3%, it means when losses exceed that 2% threshold, the average loss is 3%.
    """)

# ----------------------------
# Drawdown Chart
# ----------------------------
st.subheader("📊 Drawdown Analysis")

# Calculate drawdown series
drawdown_series = calculate_drawdown_series(portfolio_returns)

# Display drawdown chart
st.plotly_chart(
    drawdown_chart(drawdown_series),
    use_container_width=True
)

# Drawdown statistics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Current Drawdown",
        f"{drawdown_series.iloc[-1]:.2%}",
        help="Current decline from most recent peak"
    )

with col2:
    # Calculate average drawdown
    avg_drawdown = drawdown_series[drawdown_series < 0].mean() if len(drawdown_series[drawdown_series < 0]) > 0 else 0
    st.metric(
        "Average Drawdown",
        f"{avg_drawdown:.2%}",
        help="Average of all drawdown periods"
    )

with col3:
    st.metric(
        "Max Drawdown",
        f"{mdd:.2%}",
        help="Largest peak-to-trough decline"
    )

# Risk explanation
with st.expander("ℹ️ Understanding Risk Metrics"):
    st.markdown("""
    - **Volatility**: Measures price fluctuation. Lower is more stable.
    - **Sharpe Ratio**: Risk-adjusted returns. >1 is good, >2 is excellent.
    - **Maximum Drawdown**: Worst decline from peak. Lower is better.
    - **Beta**: Market sensitivity. <1 = defensive, >1 = aggressive.
    - **Drawdown**: Decline from a historical peak. Shows the portfolio's recovery patterns.
    """)

# ----------------------------
# Export Options
# ----------------------------
st.divider()
col1, col2 = st.columns(2)

with col1:
    csv = portfolio_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Portfolio (CSV)",
        data=csv,
        file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()











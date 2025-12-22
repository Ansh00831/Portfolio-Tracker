import plotly.graph_objects as go
import plotly.express as px

def allocation_pie(portfolio_df):
    """
    Create pie chart showing portfolio allocation by value.
    
    Args:
        portfolio_df: DataFrame with Current_Value column
    
    Returns:
        Plotly figure
    """
    fig = px.pie(
        portfolio_df,
        values="Current_Value",
        names="Ticker",
        title="Portfolio Allocation by Value",
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    return fig


def performance_chart(portfolio_cumulative, benchmark_cumulative, benchmark_ticker):
    """
    Create line chart comparing portfolio vs benchmark performance.
    
    Args:
        portfolio_cumulative: Series of cumulative portfolio returns
        benchmark_cumulative: Series of cumulative benchmark returns
        benchmark_ticker: Benchmark ticker symbol
    
    Returns:
        Plotly figure
    """
    benchmark_name = {
        "^GSPC": "S&P 500",
        "^NSEI": "NIFTY 50",
        "^DJI": "Dow Jones",
        "^IXIC": "NASDAQ"
    }.get(benchmark_ticker, benchmark_ticker)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=portfolio_cumulative.index,
        y=(portfolio_cumulative - 1) * 100,
        name="Portfolio",
        line=dict(color='#00C853', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=benchmark_cumulative.index,
        y=(benchmark_cumulative - 1) * 100,
        name=benchmark_name,
        line=dict(color='#FF6D00', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="Cumulative Returns (%)",
        xaxis_title="Date",
        yaxis_title="Return (%)",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def drawdown_chart(drawdown_series):
    """
    Create area chart showing portfolio drawdowns over time.
    
    Args:
        drawdown_series: Series of drawdown values (negative percentages)
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=drawdown_series.index,
        y=drawdown_series * 100,
        name="Drawdown",
        fill='tozeroy',
        line=dict(color='#FF5252', width=2),
        fillcolor='rgba(255, 82, 82, 0.3)'
    ))
    
    # Add horizontal line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # Mark maximum drawdown point
    max_dd_idx = drawdown_series.idxmin()
    max_dd_val = drawdown_series.min()
    
    fig.add_trace(go.Scatter(
        x=[max_dd_idx],
        y=[max_dd_val * 100],
        mode='markers',
        marker=dict(size=12, color='red', symbol='x'),
        name=f'Max Drawdown: {max_dd_val:.2%}',
        showlegend=True
    ))
    
    fig.update_layout(
        title="Portfolio Drawdown Over Time",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def returns_comparison(portfolio_returns, benchmark_returns):
    """
    Create histogram comparing return distributions.
    
    Args:
        portfolio_returns: Series of portfolio returns
        benchmark_returns: Series of benchmark returns
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=portfolio_returns * 100,
        name="Portfolio",
        opacity=0.7,
        nbinsx=50
    ))
    
    fig.add_trace(go.Histogram(
        x=benchmark_returns * 100,
        name="Benchmark",
        opacity=0.7,
        nbinsx=50
    ))
    
    fig.update_layout(
        title="Return Distribution",
        xaxis_title="Daily Return (%)",
        yaxis_title="Frequency",
        barmode='overlay'
    )
    
    return fig
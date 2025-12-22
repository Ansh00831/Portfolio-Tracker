import numpy as np
import pandas as pd
from scipy import stats

def annualized_volatility(returns, periods_per_year=252):
    """
    Calculate annualized volatility (standard deviation).
    
    Args:
        returns: Series of periodic returns
        periods_per_year: 252 for daily, 12 for monthly
    
    Returns:
        Float annualized volatility
    """
    return returns.std() * np.sqrt(periods_per_year)


def sharpe_ratio(returns, risk_free_rate=0.02, periods_per_year=252):
    """
    Calculate Sharpe ratio (risk-adjusted return).
    
    Args:
        returns: Series of periodic returns
        risk_free_rate: Annual risk-free rate (default 2%)
        periods_per_year: 252 for daily, 12 for monthly
    
    Returns:
        Float Sharpe ratio
    """
    excess_returns = returns - (risk_free_rate / periods_per_year)
    
    if excess_returns.std() == 0:
        return 0
    
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)


def max_drawdown(returns):
    """
    Calculate maximum drawdown (largest peak-to-trough decline).
    
    Args:
        returns: Series of periodic returns
    
    Returns:
        Float maximum drawdown (negative value)
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    
    return drawdown.min()


def calculate_drawdown_series(returns):
    """
    Calculate drawdown series for charting.
    
    Args:
        returns: Series of periodic returns
    
    Returns:
        Series of drawdown values over time
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    
    return drawdown


def calculate_beta(portfolio_returns, benchmark_returns):
    """
    Calculate portfolio beta (sensitivity to market).
    
    Args:
        portfolio_returns: Series of portfolio returns
        benchmark_returns: Series of benchmark returns
    
    Returns:
        Float beta value
    """
    # Align the series
    aligned = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
    
    if len(aligned) < 2:
        return 1.0
    
    portfolio_col = aligned.iloc[:, 0]
    benchmark_col = aligned.iloc[:, 1]
    
    covariance = portfolio_col.cov(benchmark_col)
    benchmark_variance = benchmark_col.var()
    
    if benchmark_variance == 0:
        return 1.0
    
    beta = covariance / benchmark_variance
    
    return beta


def value_at_risk_historical(returns, confidence_level=0.95):
    """
    Calculate Historical Value at Risk (VaR).
    
    Args:
        returns: Series of periodic returns
        confidence_level: Confidence level (default 0.95 for 95% VaR)
    
    Returns:
        Float VaR value (positive number representing potential loss)
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate the percentile
    var = np.percentile(returns, (1 - confidence_level) * 100)
    
    return abs(var)


def value_at_risk_parametric(returns, confidence_level=0.95):
    """
    Calculate Parametric Value at Risk (VaR) assuming normal distribution.
    
    Args:
        returns: Series of periodic returns
        confidence_level: Confidence level (default 0.95 for 95% VaR)
    
    Returns:
        Float VaR value (positive number representing potential loss)
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate mean and standard deviation
    mean = returns.mean()
    std = returns.std()
    
    # Z-score for the confidence level
    z_score = stats.norm.ppf(1 - confidence_level)
    
    # Parametric VaR
    var = -(mean + z_score * std)
    
    return abs(var)


def conditional_value_at_risk(returns, confidence_level=0.95):
    """
    Calculate Conditional Value at Risk (CVaR) / Expected Shortfall (ES).
    
    This measures the expected loss given that the loss exceeds VaR.
    
    Args:
        returns: Series of periodic returns
        confidence_level: Confidence level (default 0.95 for 95% CVaR)
    
    Returns:
        Float CVaR value (positive number representing expected loss in worst cases)
    """
    if len(returns) < 2:
        return 0.0
    
    # Calculate VaR threshold
    var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
    
    # Calculate average of returns below VaR threshold
    tail_losses = returns[returns <= var_threshold]
    
    if len(tail_losses) == 0:
        return abs(var_threshold)
    
    cvar = tail_losses.mean()
    
    return abs(cvar)

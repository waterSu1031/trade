pub fn calculate_sharpe_ratio(returns: &[f64], risk_free_rate: f64) -> f64 {
    if returns.is_empty() {
        return 0.0;
    }
    
    let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter()
        .map(|x| (x - mean_return).powi(2))
        .sum::<f64>() / returns.len() as f64;
    
    let std_dev = variance.sqrt();
    
    if std_dev == 0.0 {
        0.0
    } else {
        (mean_return - risk_free_rate) / std_dev
    }
}

pub fn calculate_volatility(prices: &[f64]) -> f64 {
    if prices.len() < 2 {
        return 0.0;
    }
    
    let returns: Vec<f64> = prices.windows(2)
        .map(|w| (w[1] / w[0]).ln())
        .collect();
    
    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns.iter()
        .map(|x| (x - mean).powi(2))
        .sum::<f64>() / returns.len() as f64;
    
    variance.sqrt()
}
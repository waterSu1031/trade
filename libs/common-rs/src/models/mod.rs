use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Trade {
    pub id: String,
    pub symbol: String,
    pub quantity: i32,
    pub price: f64,
    pub side: TradeSide,
    pub timestamp: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum TradeSide {
    Buy,
    Sell,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Position {
    pub symbol: String,
    pub quantity: i32,
    pub avg_price: f64,
    pub unrealized_pnl: f64,
}
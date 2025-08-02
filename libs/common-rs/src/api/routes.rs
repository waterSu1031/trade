use axum::{Router, routing::{get, post}};

pub fn create_routes() -> Router {
    Router::new()
        .route("/health", get(super::handlers::health_check))
        .route("/calculations/volatility", post(super::handlers::calculate_volatility))
        .route("/market-data/latest", get(super::handlers::get_market_data))
}
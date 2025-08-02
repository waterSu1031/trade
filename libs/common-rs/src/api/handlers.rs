use axum::{Json, response::Json as ResponseJson};
use serde::{Deserialize, Serialize};

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: String,
}

pub async fn health_check() -> ResponseJson<HealthResponse> {
    ResponseJson(HealthResponse {
        status: "ok".to_string(),
    })
}

#[derive(Deserialize)]
pub struct VolatilityRequest {
    pub prices: Vec<f64>,
}

#[derive(Serialize)]
pub struct VolatilityResponse {
    pub volatility: f64,
}

pub async fn calculate_volatility(
    Json(payload): Json<VolatilityRequest>,
) -> ResponseJson<VolatilityResponse> {
    let volatility = crate::services::calculations::calculate_volatility(&payload.prices);
    ResponseJson(VolatilityResponse { volatility })
}

pub async fn get_market_data() -> ResponseJson<serde_json::Value> {
    ResponseJson(serde_json::json!({
        "message": "Market data endpoint placeholder"
    }))
}
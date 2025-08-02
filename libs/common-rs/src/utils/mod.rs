use tracing::info;

pub fn init_logging() {
    tracing_subscriber::fmt::init();
    info!("Logging initialized");
}

pub fn format_currency(amount: f64) -> String {
    format!("${:.2}", amount)
}

pub fn timestamp_now() -> i64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs() as i64
}
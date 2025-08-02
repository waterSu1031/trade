use serde::Deserialize;
use config::{Config, ConfigError, File, Environment};

#[derive(Debug, Deserialize)]
pub struct Settings {
    pub server: ServerConfig,
    pub database: DatabaseConfig,
    pub redis: RedisConfig,
}

#[derive(Debug, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
}

#[derive(Debug, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
}

#[derive(Debug, Deserialize)]
pub struct RedisConfig {
    pub url: String,
    pub pool_size: u32,
}

impl Settings {
    pub fn new() -> Result<Self, ConfigError> {
        Config::builder()
            .add_source(File::with_name("config/default"))
            .add_source(Environment::with_prefix("TRADE_RS"))
            .build()?
            .try_deserialize()
    }
}
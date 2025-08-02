use criterion::{black_box, criterion_group, criterion_main, Criterion};
use trade_common_rs::services::calculations::{calculate_sharpe_ratio, calculate_volatility};

fn bench_sharpe_ratio(c: &mut Criterion) {
    let returns = vec![0.01, 0.02, -0.01, 0.03, 0.005]; // Sample returns
    let risk_free_rate = 0.02;
    
    c.bench_function("sharpe_ratio", |b| {
        b.iter(|| calculate_sharpe_ratio(black_box(&returns), black_box(risk_free_rate)))
    });
}

fn bench_volatility(c: &mut Criterion) {
    let prices = vec![100.0, 101.0, 99.0, 102.0, 98.0, 103.0];
    
    c.bench_function("volatility", |b| {
        b.iter(|| calculate_volatility(black_box(&prices)))
    });
}

criterion_group!(benches, bench_sharpe_ratio, bench_volatility);
criterion_main!(benches);
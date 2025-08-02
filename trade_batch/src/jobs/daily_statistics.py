"""
일일 통계 작업
- 거래 통계 계산
- 성과 분석
- 리포트 생성
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class DailyStatisticsCalculator:
    """일일 통계 계산 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
    
    async def calculate_trading_statistics(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """거래 통계 계산"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
            
        logger.info(f"{target_date} 거래 통계 계산 시작")
        
        stats = {
            'date': target_date.isoformat(),
            'summary': {},
            'by_symbol': {},
            'by_hour': {},
            'errors': []
        }
        
        try:
            # 전체 거래 요약
            summary = await self.db.fetchrow("""
                SELECT 
                    COUNT(*) as total_trades,
                    COUNT(DISTINCT symbol) as traded_symbols,
                    COUNT(DISTINCT orderId) as total_orders,
                    SUM(executed_qty) as total_volume,
                    SUM(executed_qty * executed_price) as total_turnover,
                    SUM(realizedPNL) as total_realized_pnl,
                    SUM(commission) as total_commission,
                    AVG(executed_price) as avg_price,
                    MAX(executed_price) as max_price,
                    MIN(executed_price) as min_price
                FROM trade_events
                WHERE DATE(time) = $1
            """, target_date)
            
            stats['summary'] = {
                'total_trades': summary['total_trades'] or 0,
                'traded_symbols': summary['traded_symbols'] or 0,
                'total_orders': summary['total_orders'] or 0,
                'total_volume': float(summary['total_volume'] or 0),
                'total_turnover': float(summary['total_turnover'] or 0),
                'total_realized_pnl': float(summary['total_realized_pnl'] or 0),
                'total_commission': float(summary['total_commission'] or 0),
                'avg_price': float(summary['avg_price'] or 0),
                'max_price': float(summary['max_price'] or 0),
                'min_price': float(summary['min_price'] or 0),
                'net_pnl': float((summary['total_realized_pnl'] or 0) - (summary['total_commission'] or 0))
            }
            
            # 심볼별 통계
            symbol_stats = await self.db.fetch("""
                SELECT 
                    symbol,
                    COUNT(*) as trades,
                    SUM(CASE WHEN side = 'BUY' THEN executed_qty ELSE 0 END) as buy_volume,
                    SUM(CASE WHEN side = 'SELL' THEN executed_qty ELSE 0 END) as sell_volume,
                    SUM(executed_qty * executed_price) as turnover,
                    SUM(realizedPNL) as realized_pnl,
                    SUM(commission) as commission,
                    AVG(executed_price) as avg_price,
                    MAX(executed_price) as high_price,
                    MIN(executed_price) as low_price,
                    COUNT(DISTINCT orderId) as orders
                FROM trade_events
                WHERE DATE(time) = $1
                GROUP BY symbol
                ORDER BY turnover DESC
            """, target_date)
            
            for row in symbol_stats:
                stats['by_symbol'][row['symbol']] = {
                    'trades': row['trades'],
                    'orders': row['orders'],
                    'buy_volume': float(row['buy_volume'] or 0),
                    'sell_volume': float(row['sell_volume'] or 0),
                    'net_volume': float((row['buy_volume'] or 0) - (row['sell_volume'] or 0)),
                    'turnover': float(row['turnover'] or 0),
                    'realized_pnl': float(row['realized_pnl'] or 0),
                    'commission': float(row['commission'] or 0),
                    'net_pnl': float((row['realized_pnl'] or 0) - (row['commission'] or 0)),
                    'avg_price': float(row['avg_price'] or 0),
                    'high_price': float(row['high_price'] or 0),
                    'low_price': float(row['low_price'] or 0),
                    'price_range': float((row['high_price'] or 0) - (row['low_price'] or 0))
                }
            
            # 시간대별 통계
            hourly_stats = await self.db.fetch("""
                SELECT 
                    EXTRACT(HOUR FROM time) as hour,
                    COUNT(*) as trades,
                    SUM(executed_qty) as volume,
                    SUM(executed_qty * executed_price) as turnover,
                    SUM(realizedPNL) as realized_pnl
                FROM trade_events
                WHERE DATE(time) = $1
                GROUP BY EXTRACT(HOUR FROM time)
                ORDER BY hour
            """, target_date)
            
            for row in hourly_stats:
                hour = int(row['hour'])
                stats['by_hour'][f"{hour:02d}:00"] = {
                    'trades': row['trades'],
                    'volume': float(row['volume'] or 0),
                    'turnover': float(row['turnover'] or 0),
                    'realized_pnl': float(row['realized_pnl'] or 0)
                }
                
        except Exception as e:
            logger.error(f"거래 통계 계산 실패: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    async def calculate_performance_metrics(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """성과 지표 계산"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
            
        logger.info(f"{target_date} 성과 지표 계산 시작")
        
        metrics = {
            'date': target_date.isoformat(),
            'returns': {},
            'risk_metrics': {},
            'trading_metrics': {},
            'errors': []
        }
        
        try:
            # 일간 수익률 계산
            daily_returns = await self.db.fetchrow("""
                WITH daily_pnl AS (
                    SELECT 
                        DATE(time) as trading_date,
                        SUM(realizedPNL) as daily_pnl,
                        SUM(commission) as daily_commission
                    FROM trade_events
                    WHERE DATE(time) BETWEEN $1 - INTERVAL '30 days' AND $1
                    GROUP BY DATE(time)
                ),
                portfolio_value AS (
                    SELECT 
                        SUM(ABS(position * avg_price)) as total_value
                    FROM positions
                    WHERE position != 0
                )
                SELECT 
                    dp.daily_pnl,
                    dp.daily_commission,
                    pv.total_value,
                    (dp.daily_pnl - dp.daily_commission) / NULLIF(pv.total_value, 0) * 100 as daily_return_pct
                FROM daily_pnl dp, portfolio_value pv
                WHERE dp.trading_date = $1
            """, target_date)
            
            if daily_returns:
                metrics['returns'] = {
                    'daily_pnl': float(daily_returns['daily_pnl'] or 0),
                    'daily_commission': float(daily_returns['daily_commission'] or 0),
                    'net_pnl': float((daily_returns['daily_pnl'] or 0) - (daily_returns['daily_commission'] or 0)),
                    'portfolio_value': float(daily_returns['total_value'] or 0),
                    'daily_return_pct': float(daily_returns['daily_return_pct'] or 0)
                }
            
            # 리스크 지표 계산 (30일 기준)
            risk_data = await self.db.fetch("""
                WITH daily_returns AS (
                    SELECT 
                        DATE(time) as trading_date,
                        SUM(realizedPNL - commission) as net_pnl
                    FROM trade_events
                    WHERE DATE(time) BETWEEN $1 - INTERVAL '30 days' AND $1
                    GROUP BY DATE(time)
                )
                SELECT 
                    STDDEV(net_pnl) as volatility,
                    AVG(net_pnl) as avg_daily_pnl,
                    MIN(net_pnl) as max_drawdown,
                    MAX(net_pnl) as max_profit,
                    COUNT(CASE WHEN net_pnl > 0 THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100 as win_rate
                FROM daily_returns
            """, target_date)
            
            if risk_data and len(risk_data) > 0:
                risk = risk_data[0]
                volatility = float(risk['volatility'] or 0)
                avg_pnl = float(risk['avg_daily_pnl'] or 0)
                
                metrics['risk_metrics'] = {
                    'volatility': volatility,
                    'avg_daily_pnl': avg_pnl,
                    'max_drawdown': float(risk['max_drawdown'] or 0),
                    'max_profit': float(risk['max_profit'] or 0),
                    'win_rate': float(risk['win_rate'] or 0),
                    'sharpe_ratio': (avg_pnl / volatility * (252 ** 0.5)) if volatility > 0 else 0
                }
            
            # 거래 효율성 지표
            trading_efficiency = await self.db.fetchrow("""
                SELECT 
                    AVG(CASE WHEN realizedPNL > 0 THEN realizedPNL ELSE 0 END) as avg_win,
                    AVG(CASE WHEN realizedPNL < 0 THEN ABS(realizedPNL) ELSE 0 END) as avg_loss,
                    COUNT(CASE WHEN realizedPNL > 0 THEN 1 END) as winning_trades,
                    COUNT(CASE WHEN realizedPNL < 0 THEN 1 END) as losing_trades,
                    AVG(commission / NULLIF(executed_qty * executed_price, 0)) * 100 as avg_commission_rate
                FROM trade_events
                WHERE DATE(time) = $1
            """, target_date)
            
            if trading_efficiency:
                avg_win = float(trading_efficiency['avg_win'] or 0)
                avg_loss = float(trading_efficiency['avg_loss'] or 0)
                
                metrics['trading_metrics'] = {
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'win_loss_ratio': (avg_win / avg_loss) if avg_loss > 0 else 0,
                    'winning_trades': trading_efficiency['winning_trades'] or 0,
                    'losing_trades': trading_efficiency['losing_trades'] or 0,
                    'avg_commission_rate': float(trading_efficiency['avg_commission_rate'] or 0)
                }
                
        except Exception as e:
            logger.error(f"성과 지표 계산 실패: {e}")
            metrics['errors'].append(str(e))
        
        return metrics
    
    async def generate_daily_report(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """일일 리포트 생성"""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
            
        logger.info(f"{target_date} 일일 리포트 생성 시작")
        
        # 거래 통계
        trading_stats = await self.calculate_trading_statistics(target_date)
        
        # 성과 지표
        performance_metrics = await self.calculate_performance_metrics(target_date)
        
        # 포지션 현황
        position_summary = await self._get_position_summary()
        
        # 주요 이벤트
        key_events = await self._get_key_events(target_date)
        
        # 리포트 생성
        report = {
            'report_date': target_date.isoformat(),
            'generated_at': datetime.now().isoformat(),
            'trading_statistics': trading_stats,
            'performance_metrics': performance_metrics,
            'position_summary': position_summary,
            'key_events': key_events,
            'recommendations': await self._generate_recommendations(trading_stats, performance_metrics)
        }
        
        # 리포트 저장
        await self._save_report(report)
        
        # Redis에 캐시
        await self.redis.set(
            f'daily_report:{target_date.isoformat()}',
            report,
            expire=86400 * 30  # 30일
        )
        
        logger.info(f"{target_date} 일일 리포트 생성 완료")
        
        return report
    
    async def _get_position_summary(self) -> Dict[str, Any]:
        """포지션 요약 조회"""
        positions = await self.db.fetch("""
            SELECT 
                COUNT(*) as total_positions,
                COUNT(CASE WHEN position > 0 THEN 1 END) as long_positions,
                COUNT(CASE WHEN position < 0 THEN 1 END) as short_positions,
                SUM(ABS(position * avg_price)) as total_exposure,
                SUM(unrealized_pnl) as total_unrealized_pnl,
                SUM(realized_pnl) as total_realized_pnl
            FROM positions
            WHERE position != 0
        """)
        
        if positions and len(positions) > 0:
            pos = positions[0]
            return {
                'total_positions': pos['total_positions'] or 0,
                'long_positions': pos['long_positions'] or 0,
                'short_positions': pos['short_positions'] or 0,
                'total_exposure': float(pos['total_exposure'] or 0),
                'total_unrealized_pnl': float(pos['total_unrealized_pnl'] or 0),
                'total_realized_pnl': float(pos['total_realized_pnl'] or 0)
            }
        
        return {}
    
    async def _get_key_events(self, target_date: date) -> List[Dict[str, Any]]:
        """주요 이벤트 조회"""
        events = []
        
        # 대량 거래
        large_trades = await self.db.fetch("""
            SELECT 
                symbol, side, executed_qty, executed_price, 
                executed_qty * executed_price as turnover, time
            FROM trade_events
            WHERE DATE(time) = $1
            AND executed_qty * executed_price > 100000  -- $100k 이상
            ORDER BY turnover DESC
            LIMIT 10
        """, target_date)
        
        for trade in large_trades:
            events.append({
                'type': 'large_trade',
                'symbol': trade['symbol'],
                'side': trade['side'],
                'quantity': float(trade['executed_qty']),
                'price': float(trade['executed_price']),
                'turnover': float(trade['turnover']),
                'time': trade['time'].isoformat()
            })
        
        # 큰 손실 거래
        large_losses = await self.db.fetch("""
            SELECT 
                symbol, realizedPNL, executed_qty, executed_price, time
            FROM trade_events
            WHERE DATE(time) = $1
            AND realizedPNL < -1000  -- $1k 이상 손실
            ORDER BY realizedPNL
            LIMIT 5
        """, target_date)
        
        for loss in large_losses:
            events.append({
                'type': 'large_loss',
                'symbol': loss['symbol'],
                'loss': float(loss['realizedPNL']),
                'quantity': float(loss['executed_qty']),
                'price': float(loss['executed_price']),
                'time': loss['time'].isoformat()
            })
        
        return events
    
    async def _generate_recommendations(
        self, 
        trading_stats: Dict[str, Any], 
        performance_metrics: Dict[str, Any]
    ) -> List[str]:
        """권장사항 생성"""
        recommendations = []
        
        # 수익률 기반 권장사항
        if performance_metrics.get('returns', {}).get('daily_return_pct', 0) < -2:
            recommendations.append("일일 손실이 2%를 초과했습니다. 리스크 관리 강화를 권장합니다.")
        
        # 승률 기반 권장사항
        win_rate = performance_metrics.get('risk_metrics', {}).get('win_rate', 0)
        if win_rate < 40:
            recommendations.append(f"승률이 {win_rate:.1f}%로 낮습니다. 진입 전략 재검토를 권장합니다.")
        
        # 거래 빈도 기반 권장사항
        total_trades = trading_stats.get('summary', {}).get('total_trades', 0)
        if total_trades > 1000:
            recommendations.append("일일 거래 횟수가 과도합니다. 오버트레이딩 주의가 필요합니다.")
        
        # 수수료 기반 권장사항
        total_commission = trading_stats.get('summary', {}).get('total_commission', 0)
        net_pnl = trading_stats.get('summary', {}).get('net_pnl', 0)
        if total_commission > abs(net_pnl) * 0.3:
            recommendations.append("수수료가 순손익의 30%를 초과합니다. 거래 빈도 조절이 필요합니다.")
        
        # 집중도 기반 권장사항
        by_symbol = trading_stats.get('by_symbol', {})
        if by_symbol:
            top_symbol_turnover = max(s['turnover'] for s in by_symbol.values())
            total_turnover = trading_stats.get('summary', {}).get('total_turnover', 0)
            if total_turnover > 0 and top_symbol_turnover / total_turnover > 0.5:
                recommendations.append("특정 종목에 거래가 집중되어 있습니다. 분산 투자를 고려하세요.")
        
        return recommendations
    
    async def _save_report(self, report: Dict[str, Any]):
        """리포트 저장"""
        await self.db.execute("""
            INSERT INTO daily_reports 
            (report_date, report_data, created_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (report_date) 
            DO UPDATE SET 
                report_data = $2,
                updated_at = $3
        """, 
        datetime.strptime(report['report_date'], '%Y-%m-%d').date(),
        json.dumps(report),
        datetime.now()
        )


async def calculate_daily_statistics(
    db_manager: DatabaseManager,
    ibkr_manager: Any,
    redis_manager: RedisManager
) -> Dict[str, Any]:
    """일일 통계 계산 실행"""
    calculator = DailyStatisticsCalculator(db_manager, redis_manager)
    
    # 어제 날짜 기준으로 리포트 생성
    yesterday = date.today() - timedelta(days=1)
    report = await calculator.generate_daily_report(yesterday)
    
    logger.info(f"일일 통계 계산 완료 - {yesterday}")
    
    return report
"""
데이터 정합성 검증 작업
- 포지션 정합성 검증
- 손익 재계산 및 검증
- 중복 데이터 제거
- 참조 무결성 검증
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import asyncpg

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class DataIntegrityChecker:
    """데이터 정합성 검증 클래스"""
    
    def __init__(self, db_manager: DatabaseManager, redis_manager: RedisManager):
        self.db = db_manager
        self.redis = redis_manager
        
    async def verify_position_integrity(self) -> Dict[str, Any]:
        """포지션 정합성 검증"""
        logger.info("포지션 정합성 검증 시작")
        
        results = {
            'verified_positions': 0,
            'corrected_positions': 0,
            'errors': []
        }
        
        try:
            # 현재 포지션이 있는 모든 종목 조회
            positions = await self.db.fetch("""
                SELECT symbol, position, avg_price, realized_pnl
                FROM positions
                WHERE position != 0
            """)
            
            for pos in positions:
                symbol = pos['symbol']
                current_position = float(pos['position'])
                
                # trade_events 기반으로 포지션 재계산
                recalculated = await self._recalculate_position(symbol)
                recalculated_position = recalculated['position']
                
                # 포지션 차이 확인
                position_diff = abs(current_position - recalculated_position)
                
                if position_diff > 0.0001:  # 허용 오차
                    logger.warning(
                        f"포지션 불일치 발견 - {symbol}: "
                        f"현재={current_position}, 재계산={recalculated_position}"
                    )
                    
                    # 포지션 수정
                    await self._correct_position(symbol, recalculated)
                    results['corrected_positions'] += 1
                else:
                    results['verified_positions'] += 1
                    
        except Exception as e:
            logger.error(f"포지션 정합성 검증 실패: {e}")
            results['errors'].append(str(e))
            
        logger.info(
            f"포지션 정합성 검증 완료 - "
            f"검증: {results['verified_positions']}, "
            f"수정: {results['corrected_positions']}"
        )
        
        return results
    
    async def verify_pnl_calculation(self) -> Dict[str, Any]:
        """손익 재계산 및 검증"""
        logger.info("손익 검증 시작")
        
        results = {
            'verified_pnl': 0,
            'corrected_pnl': 0,
            'total_pnl_diff': 0,
            'errors': []
        }
        
        try:
            # 최근 30일간의 거래 중 손익이 있는 거래 조회
            trades = await self.db.fetch("""
                SELECT execId, symbol, side, executed_qty, executed_price, 
                       commission, realizedPNL, time
                FROM trade_events
                WHERE realizedPNL != 0 
                AND time > $1
                ORDER BY time
            """, datetime.now() - timedelta(days=30))
            
            for trade in trades:
                # FIFO 기반 손익 재계산
                recalculated_pnl = await self._recalculate_pnl_fifo(trade)
                current_pnl = float(trade['realizedPNL'])
                
                pnl_diff = abs(current_pnl - recalculated_pnl)
                
                if pnl_diff > 0.01:  # 0.01 허용 오차
                    logger.warning(
                        f"손익 불일치 발견 - execId={trade['execId']}: "
                        f"현재={current_pnl}, 재계산={recalculated_pnl}"
                    )
                    
                    # 손익 수정
                    await self._correct_pnl(trade['execId'], recalculated_pnl)
                    results['corrected_pnl'] += 1
                    results['total_pnl_diff'] += pnl_diff
                else:
                    results['verified_pnl'] += 1
                    
        except Exception as e:
            logger.error(f"손익 검증 실패: {e}")
            results['errors'].append(str(e))
            
        logger.info(
            f"손익 검증 완료 - "
            f"검증: {results['verified_pnl']}, "
            f"수정: {results['corrected_pnl']}, "
            f"총 차이: {results['total_pnl_diff']:.2f}"
        )
        
        return results
    
    async def detect_and_remove_duplicates(self) -> Dict[str, Any]:
        """중복 데이터 검출 및 제거"""
        logger.info("중복 데이터 검출 시작")
        
        results = {
            'duplicate_trades': 0,
            'duplicate_orders': 0,
            'duplicate_prices': 0,
            'removed_total': 0,
            'errors': []
        }
        
        try:
            # trade_events 중복 체크 (동일한 execId)
            duplicate_trades = await self.db.fetch("""
                SELECT execId, COUNT(*) as cnt
                FROM trade_events
                GROUP BY execId
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicate_trades:
                # 가장 최근 것만 남기고 삭제
                await self.db.execute("""
                    DELETE FROM trade_events
                    WHERE execId = $1
                    AND ctid NOT IN (
                        SELECT max(ctid)
                        FROM trade_events
                        WHERE execId = $1
                    )
                """, dup['execId'])
                
                removed = dup['cnt'] - 1
                results['duplicate_trades'] += removed
                results['removed_total'] += removed
            
            # orders 중복 체크 (동일한 orderId와 시간)
            duplicate_orders = await self.db.fetch("""
                SELECT orderId, time, COUNT(*) as cnt
                FROM orders
                GROUP BY orderId, time
                HAVING COUNT(*) > 1
            """)
            
            for dup in duplicate_orders:
                # 가장 최근 것만 남기고 삭제
                await self.db.execute("""
                    DELETE FROM orders
                    WHERE orderId = $1 AND time = $2
                    AND ctid NOT IN (
                        SELECT max(ctid)
                        FROM orders
                        WHERE orderId = $1 AND time = $2
                    )
                """, dup['orderId'], dup['time'])
                
                removed = dup['cnt'] - 1
                results['duplicate_orders'] += removed
                results['removed_total'] += removed
            
            # price 데이터 중복 체크 (동일한 symbol과 timestamp)
            price_tables = ['price_1min', 'price_5min', 'price_1hour', 'price_1day']
            
            for table in price_tables:
                try:
                    duplicate_prices = await self.db.fetch(f"""
                        SELECT symbol, timestamp, COUNT(*) as cnt
                        FROM {table}
                        GROUP BY symbol, timestamp
                        HAVING COUNT(*) > 1
                    """)
                    
                    for dup in duplicate_prices:
                        await self.db.execute(f"""
                            DELETE FROM {table}
                            WHERE symbol = $1 AND timestamp = $2
                            AND ctid NOT IN (
                                SELECT max(ctid)
                                FROM {table}
                                WHERE symbol = $1 AND timestamp = $2
                            )
                        """, dup['symbol'], dup['timestamp'])
                        
                        removed = dup['cnt'] - 1
                        results['duplicate_prices'] += removed
                        results['removed_total'] += removed
                        
                except asyncpg.UndefinedTableError:
                    logger.warning(f"테이블 {table}이 존재하지 않습니다")
                    
        except Exception as e:
            logger.error(f"중복 데이터 검출 실패: {e}")
            results['errors'].append(str(e))
            
        logger.info(
            f"중복 데이터 제거 완료 - "
            f"거래: {results['duplicate_trades']}, "
            f"주문: {results['duplicate_orders']}, "
            f"가격: {results['duplicate_prices']}, "
            f"총: {results['removed_total']}"
        )
        
        return results
    
    async def verify_referential_integrity(self) -> Dict[str, Any]:
        """참조 무결성 검증"""
        logger.info("참조 무결성 검증 시작")
        
        results = {
            'orphan_trades': 0,
            'invalid_symbols': 0,
            'invalid_conids': 0,
            'integrity_issues': [],
            'errors': []
        }
        
        try:
            # trade_events의 orderId가 orders에 존재하는지 확인
            orphan_trades = await self.db.fetch("""
                SELECT DISTINCT t.orderId
                FROM trade_events t
                LEFT JOIN orders o ON t.orderId = o.orderId
                WHERE o.orderId IS NULL
                AND t.orderId IS NOT NULL
            """)
            
            results['orphan_trades'] = len(orphan_trades)
            if orphan_trades:
                logger.error(f"고아 거래 발견 (orderId가 orders에 없음): {len(orphan_trades)} 건")
                results['integrity_issues'].append({
                    'type': 'orphan_trades',
                    'count': len(orphan_trades),
                    'examples': [t['orderId'] for t in orphan_trades[:5]]
                })
            
            # orders의 symbol이 contracts에 존재하는지 확인
            invalid_symbols = await self.db.fetch("""
                SELECT DISTINCT o.symbol
                FROM orders o
                LEFT JOIN contracts c ON o.symbol = c.symbol
                WHERE c.symbol IS NULL
            """)
            
            results['invalid_symbols'] = len(invalid_symbols)
            if invalid_symbols:
                logger.error(f"잘못된 심볼 발견 (contracts에 없음): {len(invalid_symbols)} 건")
                results['integrity_issues'].append({
                    'type': 'invalid_symbols',
                    'count': len(invalid_symbols),
                    'examples': [s['symbol'] for s in invalid_symbols[:5]]
                })
            
            # price 데이터의 conId가 contracts에 존재하는지 확인
            price_tables = ['price_1min', 'price_5min', 'price_1hour', 'price_1day']
            
            for table in price_tables:
                try:
                    invalid_conids = await self.db.fetch(f"""
                        SELECT DISTINCT p.conId
                        FROM {table} p
                        LEFT JOIN contracts c ON p.conId = c.conId
                        WHERE c.conId IS NULL
                    """)
                    
                    if invalid_conids:
                        results['invalid_conids'] += len(invalid_conids)
                        logger.error(f"{table}에서 잘못된 conId 발견: {len(invalid_conids)} 건")
                        
                except asyncpg.UndefinedTableError:
                    pass
                    
        except Exception as e:
            logger.error(f"참조 무결성 검증 실패: {e}")
            results['errors'].append(str(e))
            
        # 검증 결과를 Redis에 캐시
        await self.redis.set(
            'data_integrity:last_check',
            {
                'timestamp': datetime.now().isoformat(),
                'results': results
            },
            expire=3600  # 1시간
        )
        
        logger.info(
            f"참조 무결성 검증 완료 - "
            f"고아 거래: {results['orphan_trades']}, "
            f"잘못된 심볼: {results['invalid_symbols']}, "
            f"잘못된 conId: {results['invalid_conids']}"
        )
        
        return results
    
    async def _recalculate_position(self, symbol: str) -> Dict[str, Any]:
        """심볼별 포지션 재계산"""
        trades = await self.db.fetch("""
            SELECT side, executed_qty, executed_price
            FROM trade_events
            WHERE symbol = $1
            ORDER BY time
        """, symbol)
        
        position = 0.0
        total_cost = 0.0
        
        for trade in trades:
            qty = float(trade['executed_qty'])
            price = float(trade['executed_price'])
            
            if trade['side'] == 'BUY':
                position += qty
                total_cost += qty * price
            else:  # SELL
                position -= qty
                total_cost -= qty * price
                
        avg_price = total_cost / position if position != 0 else 0
        
        return {
            'position': position,
            'avg_price': avg_price,
            'total_cost': total_cost
        }
    
    async def _correct_position(self, symbol: str, recalculated: Dict[str, Any]):
        """포지션 수정"""
        await self.db.execute("""
            UPDATE positions
            SET position = $2, avg_price = $3, updated_at = $4
            WHERE symbol = $1
        """, symbol, recalculated['position'], 
        recalculated['avg_price'], datetime.now())
        
        # 수정 로그 저장
        await self.db.execute("""
            INSERT INTO data_integrity_log 
            (check_type, symbol, issue_type, old_value, new_value, checked_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, 'POSITION', symbol, 'position_mismatch', 
        None, str(recalculated), datetime.now())
    
    async def _recalculate_pnl_fifo(self, trade: Dict[str, Any]) -> float:
        """FIFO 방식으로 손익 재계산"""
        symbol = trade['symbol']
        
        # 해당 거래 이전의 모든 거래 조회
        history = await self.db.fetch("""
            SELECT side, executed_qty, executed_price, time
            FROM trade_events
            WHERE symbol = $1 AND time < $2
            ORDER BY time
        """, symbol, trade['time'])
        
        # FIFO 큐 구성
        buy_queue = []
        
        for h in history:
            qty = float(h['executed_qty'])
            price = float(h['executed_price'])
            
            if h['side'] == 'BUY':
                buy_queue.append({'qty': qty, 'price': price})
            else:  # SELL
                # FIFO로 매도 처리
                remaining = qty
                while remaining > 0 and buy_queue:
                    if buy_queue[0]['qty'] <= remaining:
                        remaining -= buy_queue[0]['qty']
                        buy_queue.pop(0)
                    else:
                        buy_queue[0]['qty'] -= remaining
                        remaining = 0
        
        # 현재 거래의 손익 계산
        if trade['side'] == 'SELL':
            sell_qty = float(trade['executed_qty'])
            sell_price = float(trade['executed_price'])
            
            realized_pnl = 0.0
            remaining = sell_qty
            
            while remaining > 0 and buy_queue:
                if buy_queue[0]['qty'] <= remaining:
                    realized_pnl += buy_queue[0]['qty'] * (sell_price - buy_queue[0]['price'])
                    remaining -= buy_queue[0]['qty']
                    buy_queue.pop(0)
                else:
                    realized_pnl += remaining * (sell_price - buy_queue[0]['price'])
                    buy_queue[0]['qty'] -= remaining
                    remaining = 0
                    
            # 수수료 차감
            realized_pnl -= float(trade['commission'])
            
            return realized_pnl
        
        return 0.0
    
    async def _correct_pnl(self, exec_id: str, corrected_pnl: float):
        """손익 수정"""
        await self.db.execute("""
            UPDATE trade_events
            SET realizedPNL = $2
            WHERE execId = $1
        """, exec_id, corrected_pnl)
        
        # 수정 로그 저장
        await self.db.execute("""
            INSERT INTO data_integrity_log 
            (check_type, exec_id, issue_type, old_value, new_value, checked_at)
            VALUES ($1, $2, $3, $4, $5, $6)
        """, 'PNL', exec_id, 'pnl_mismatch', 
        None, str(corrected_pnl), datetime.now())


async def run_data_integrity_check(
    db_manager: DatabaseManager,
    ibkr_manager: Any,
    redis_manager: RedisManager
) -> Dict[str, Any]:
    """데이터 정합성 검증 실행"""
    checker = DataIntegrityChecker(db_manager, redis_manager)
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {}
    }
    
    # 1. 포지션 정합성 검증
    results['checks']['position_integrity'] = await checker.verify_position_integrity()
    
    # 2. 손익 재계산 및 검증
    results['checks']['pnl_calculation'] = await checker.verify_pnl_calculation()
    
    # 3. 중복 데이터 제거
    results['checks']['duplicate_removal'] = await checker.detect_and_remove_duplicates()
    
    # 4. 참조 무결성 검증
    results['checks']['referential_integrity'] = await checker.verify_referential_integrity()
    
    # 전체 요약
    summary = {
        'total_issues': sum(
            check.get('corrected_positions', 0) +
            check.get('corrected_pnl', 0) +
            check.get('removed_total', 0) +
            check.get('orphan_trades', 0) +
            check.get('invalid_symbols', 0) +
            check.get('invalid_conids', 0)
            for check in results['checks'].values()
        ),
        'total_errors': sum(
            len(check.get('errors', []))
            for check in results['checks'].values()
        )
    }
    
    results['summary'] = summary
    
    logger.info(f"데이터 정합성 검증 완료 - 총 {summary['total_issues']} 개 문제 발견 및 처리")
    
    return results
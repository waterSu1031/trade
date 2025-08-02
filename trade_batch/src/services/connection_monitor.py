"""
IBKR 연결 모니터링 서비스
- 연결 상태 모니터링
- 자동 재연결
- 연결 상태 알림
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from tradelib import IBKRManager, RedisManager

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """연결 상태"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class ConnectionMonitor:
    """IBKR 연결 모니터링 클래스"""
    
    def __init__(self, ibkr_manager: IBKRManager, redis_manager: RedisManager):
        self.ibkr = ibkr_manager
        self.redis = redis_manager
        
        # 모니터링 설정
        self.check_interval = 60  # 60초마다 체크
        self.max_reconnect_attempts = 3
        self.reconnect_delay = 30  # 재연결 시도 간격 (초)
        
        # 상태 추적
        self.reconnect_attempts = 0
        self.last_connected_time = None
        self.connection_lost_time = None
        self.monitoring_task = None
        
    async def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("모니터링이 이미 실행 중입니다")
            return
        
        logger.info("IBKR 연결 모니터링 시작")
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("IBKR 연결 모니터링 중지")
    
    async def _monitor_loop(self):
        """모니터링 루프"""
        while True:
            try:
                await self.check_connection()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"모니터링 중 오류 발생: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check_connection(self) -> Dict[str, Any]:
        """연결 상태 확인"""
        try:
            is_connected = self.ibkr.is_connected()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'is_connected': is_connected,
                'status': ConnectionStatus.CONNECTED.value if is_connected else ConnectionStatus.DISCONNECTED.value,
                'reconnect_attempts': self.reconnect_attempts,
                'client_id': self.ibkr.client_id if hasattr(self.ibkr, 'client_id') else None
            }
            
            if is_connected:
                # 연결 정상
                if self.reconnect_attempts > 0:
                    logger.info("IBKR 연결 복구됨")
                    await self._send_notification('connection_restored', status)
                
                self.reconnect_attempts = 0
                self.last_connected_time = datetime.now()
                self.connection_lost_time = None
                
                # 연결 정보 업데이트
                await self._update_connection_info(status)
                
            else:
                # 연결 끊김
                if self.connection_lost_time is None:
                    self.connection_lost_time = datetime.now()
                    logger.warning("IBKR 연결 끊김 감지")
                    await self._send_notification('connection_lost', status)
                
                # 재연결 시도
                await self.attempt_reconnection()
            
            # Redis에 상태 저장
            await self.redis.set(
                'ibkr:connection_status',
                status,
                expire=300  # 5분
            )
            
            return status
            
        except Exception as e:
            logger.error(f"연결 상태 확인 실패: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'is_connected': False,
                'status': ConnectionStatus.FAILED.value,
                'error': str(e)
            }
    
    async def attempt_reconnection(self) -> bool:
        """재연결 시도"""
        self.reconnect_attempts += 1
        
        if self.reconnect_attempts > self.max_reconnect_attempts:
            logger.error(
                f"최대 재연결 시도 횟수({self.max_reconnect_attempts}) 초과. "
                "수동 개입이 필요합니다."
            )
            
            await self._send_notification('max_reconnect_attempts_exceeded', {
                'attempts': self.reconnect_attempts,
                'connection_lost_time': self.connection_lost_time.isoformat() if self.connection_lost_time else None
            })
            
            return False
        
        logger.info(f"재연결 시도 {self.reconnect_attempts}/{self.max_reconnect_attempts}")
        
        try:
            # 기존 연결 정리
            if self.ibkr.is_connected():
                await self.ibkr.disconnect()
                await asyncio.sleep(2)  # 2초 대기
            
            # 재연결 시도
            await self.ibkr.connect(
                self.ibkr.host,
                self.ibkr.port,
                self.ibkr.client_id
            )
            
            # 연결 확인 (최대 10초 대기)
            for _ in range(100):
                if self.ibkr.is_connected():
                    logger.info("✅ 재연결 성공")
                    self.reconnect_attempts = 0
                    return True
                await asyncio.sleep(0.1)
            
            logger.error("❌ 재연결 실패")
            
            # 다음 재연결까지 대기
            if self.reconnect_attempts < self.max_reconnect_attempts:
                logger.info(f"{self.reconnect_delay}초 후 재시도")
                await asyncio.sleep(self.reconnect_delay)
            
            return False
            
        except Exception as e:
            logger.error(f"재연결 시도 중 오류: {e}")
            return False
    
    async def get_connection_statistics(self) -> Dict[str, Any]:
        """연결 통계 조회"""
        stats = {
            'current_status': await self.check_connection(),
            'uptime': None,
            'downtime': None,
            'total_reconnects': 0,
            'last_disconnection': None,
            'connection_quality': 'unknown'
        }
        
        # 업타임 계산
        if self.last_connected_time:
            uptime = datetime.now() - self.last_connected_time
            stats['uptime'] = str(uptime)
        
        # 다운타임 계산
        if self.connection_lost_time and not self.ibkr.is_connected():
            downtime = datetime.now() - self.connection_lost_time
            stats['downtime'] = str(downtime)
        
        # Redis에서 통계 조회
        reconnect_history = await self.redis.get('ibkr:reconnect_history') or []
        stats['total_reconnects'] = len(reconnect_history)
        
        if reconnect_history:
            stats['last_disconnection'] = reconnect_history[-1].get('timestamp')
        
        # 연결 품질 평가
        if stats['current_status']['is_connected']:
            if stats['total_reconnects'] == 0:
                stats['connection_quality'] = 'excellent'
            elif stats['total_reconnects'] < 5:
                stats['connection_quality'] = 'good'
            elif stats['total_reconnects'] < 10:
                stats['connection_quality'] = 'fair'
            else:
                stats['connection_quality'] = 'poor'
        
        return stats
    
    async def _update_connection_info(self, status: Dict[str, Any]):
        """연결 정보 업데이트"""
        try:
            # 계좌 정보 조회
            if hasattr(self.ibkr, 'ib') and self.ibkr.ib:
                accounts = self.ibkr.ib.accountValues()
                
                account_info = {
                    'account_id': self.ibkr.ib.accountCode() if hasattr(self.ibkr.ib, 'accountCode') else None,
                    'values': {av.tag: av.value for av in accounts[:10]}  # 상위 10개만
                }
                
                await self.redis.set(
                    'ibkr:account_info',
                    account_info,
                    expire=3600  # 1시간
                )
                
        except Exception as e:
            logger.error(f"연결 정보 업데이트 실패: {e}")
    
    async def _send_notification(self, event_type: str, data: Dict[str, Any]):
        """알림 전송"""
        notification = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'service': 'trade_batch',
            'data': data
        }
        
        # Redis 이벤트 발행
        await self.redis.publish('ibkr:connection_events', notification)
        
        # 재연결 이력 저장
        if event_type in ['connection_lost', 'connection_restored']:
            history = await self.redis.get('ibkr:reconnect_history') or []
            history.append(notification)
            
            # 최근 100개만 유지
            if len(history) > 100:
                history = history[-100:]
            
            await self.redis.set(
                'ibkr:reconnect_history',
                history,
                expire=86400 * 7  # 7일
            )
        
        # 중요 이벤트 로깅
        if event_type == 'max_reconnect_attempts_exceeded':
            logger.critical(f"IBKR 연결 복구 실패: {data}")
    
    def get_status_info(self) -> Dict[str, Any]:
        """현재 상태 정보 반환"""
        return {
            'monitoring_active': self.monitoring_task and not self.monitoring_task.done(),
            'reconnect_attempts': self.reconnect_attempts,
            'max_reconnect_attempts': self.max_reconnect_attempts,
            'last_connected_time': self.last_connected_time.isoformat() if self.last_connected_time else None,
            'connection_lost_time': self.connection_lost_time.isoformat() if self.connection_lost_time else None,
            'check_interval': self.check_interval,
            'reconnect_delay': self.reconnect_delay
        }


# 전역 모니터 인스턴스
monitor_instance: Optional[ConnectionMonitor] = None


async def initialize_connection_monitor(
    ibkr_manager: IBKRManager,
    redis_manager: RedisManager
) -> ConnectionMonitor:
    """연결 모니터 초기화"""
    global monitor_instance
    
    if monitor_instance is None:
        monitor_instance = ConnectionMonitor(ibkr_manager, redis_manager)
        await monitor_instance.start_monitoring()
    
    return monitor_instance


async def get_connection_monitor() -> Optional[ConnectionMonitor]:
    """연결 모니터 인스턴스 반환"""
    return monitor_instance
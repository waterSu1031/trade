"""
Redis 이벤트 소비자 서비스
- Redis pub/sub 이벤트 처리
- 이벤트 기반 작업 트리거
- 실시간 알림 처리
"""

import logging
import json
import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime

from tradelib import RedisManager, DatabaseManager

logger = logging.getLogger(__name__)


class RedisConsumer:
    """Redis 이벤트 소비자"""
    
    def __init__(
        self,
        redis_manager: RedisManager,
        db_manager: DatabaseManager
    ):
        self.redis = redis_manager
        self.db = db_manager
        
        # 이벤트 핸들러 등록
        self.event_handlers: Dict[str, List[Callable]] = {
            'trade_events': [],
            'connection_events': [],
            'alert_events': [],
            'batch_events': [],
            'system_events': []
        }
        
        # 소비자 상태
        self.is_running = False
        self.tasks = []
        self.processed_count = 0
        self.error_count = 0
        
        # 설정
        self.retry_delay = 5  # 재시도 지연 (초)
        self.max_retries = 3
    
    def register_handler(self, channel: str, handler: Callable):
        """이벤트 핸들러 등록"""
        if channel not in self.event_handlers:
            self.event_handlers[channel] = []
        
        self.event_handlers[channel].append(handler)
        logger.info(f"핸들러 등록: {channel} -> {handler.__name__}")
    
    async def start(self):
        """소비자 시작"""
        logger.info("Redis 이벤트 소비자 시작")
        self.is_running = True
        
        # 각 채널별 구독 시작
        for channel in self.event_handlers.keys():
            task = asyncio.create_task(self._consume_channel(channel))
            self.tasks.append(task)
        
        # 기본 이벤트 핸들러 등록
        self._register_default_handlers()
        
        logger.info(f"{len(self.event_handlers)} 채널 구독 시작됨")
    
    async def stop(self):
        """소비자 중지"""
        logger.info("Redis 이벤트 소비자 중지 중...")
        self.is_running = False
        
        # 모든 태스크 취소
        for task in self.tasks:
            task.cancel()
        
        # 태스크 완료 대기
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Redis 이벤트 소비자 중지됨")
    
    async def _consume_channel(self, channel: str):
        """특정 채널 소비"""
        retry_count = 0
        
        while self.is_running:
            try:
                # Redis pub/sub 구독
                async for message in self.redis.subscribe(channel):
                    if not self.is_running:
                        break
                    
                    # 메시지 처리
                    await self._process_message(channel, message)
                    retry_count = 0  # 성공시 재시도 카운트 리셋
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{channel} 채널 소비 중 오류: {e}")
                retry_count += 1
                
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * retry_count)
                else:
                    logger.error(f"{channel} 채널 최대 재시도 횟수 초과")
                    break
    
    async def _process_message(self, channel: str, message: Any):
        """메시지 처리"""
        try:
            # 메시지 파싱
            if isinstance(message, bytes):
                message = message.decode('utf-8')
            
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    data = {"raw_message": message}
            else:
                data = message
            
            # 메타데이터 추가
            data['_channel'] = channel
            data['_received_at'] = datetime.now().isoformat()
            
            # 핸들러 실행
            handlers = self.event_handlers.get(channel, [])
            for handler in handlers:
                try:
                    await handler(data)
                except Exception as e:
                    logger.error(f"핸들러 실행 오류 ({handler.__name__}): {e}")
                    self.error_count += 1
            
            self.processed_count += 1
            
            # 이벤트 로깅 (선택적)
            if channel in ['trade_events', 'alert_events']:
                await self._log_event(channel, data)
                
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}")
            self.error_count += 1
    
    async def _log_event(self, channel: str, data: Dict[str, Any]):
        """이벤트 로깅"""
        try:
            await self.db.execute("""
                INSERT INTO event_log (
                    channel, event_type, event_data, created_at
                ) VALUES ($1, $2, $3, $4)
            """, channel, data.get('event_type', 'unknown'), 
                json.dumps(data), datetime.now())
        except Exception as e:
            logger.error(f"이벤트 로깅 실패: {e}")
    
    def _register_default_handlers(self):
        """기본 이벤트 핸들러 등록"""
        # 거래 이벤트 핸들러
        self.register_handler('trade_events', self._handle_trade_event)
        
        # 연결 이벤트 핸들러
        self.register_handler('connection_events', self._handle_connection_event)
        
        # 알림 이벤트 핸들러
        self.register_handler('alert_events', self._handle_alert_event)
        
        # 배치 이벤트 핸들러
        self.register_handler('batch_events', self._handle_batch_event)
        
        # 시스템 이벤트 핸들러
        self.register_handler('system_events', self._handle_system_event)
    
    async def _handle_trade_event(self, data: Dict[str, Any]):
        """거래 이벤트 처리"""
        event_type = data.get('event_type')
        
        if event_type == 'ORDER_FILLED':
            logger.info(f"주문 체결: {data.get('order_id')} - {data.get('symbol')}")
            # 추가 처리 로직
            
        elif event_type == 'POSITION_CLOSED':
            logger.info(f"포지션 종료: {data.get('position_id')} - PnL: {data.get('pnl')}")
            # 통계 업데이트 등
            
        elif event_type == 'TRADE_ERROR':
            logger.error(f"거래 오류: {data.get('error_message')}")
            # 오류 알림 발송 등
    
    async def _handle_connection_event(self, data: Dict[str, Any]):
        """연결 이벤트 처리"""
        event = data.get('event')
        
        if event == 'CONNECTED':
            logger.info(f"IBKR 연결됨: {data.get('reason')}")
            # 연결 후 초기화 작업
            
        elif event == 'DISCONNECTED':
            logger.warning(f"IBKR 연결 해제됨: {data.get('reason')}")
            # 재연결 시도 또는 알림
            
        elif event == 'CONNECTION_LOST':
            logger.error("IBKR 연결 끊김")
            # 긴급 알림 발송
    
    async def _handle_alert_event(self, data: Dict[str, Any]):
        """알림 이벤트 처리"""
        alert_type = data.get('alert_type')
        severity = data.get('severity', 'INFO')
        
        logger.log(
            getattr(logging, severity, logging.INFO),
            f"알림 [{alert_type}]: {data.get('message')}"
        )
        
        # 심각도에 따른 처리
        if severity in ['ERROR', 'CRITICAL']:
            # 이메일/SMS 알림 발송
            pass
    
    async def _handle_batch_event(self, data: Dict[str, Any]):
        """배치 이벤트 처리"""
        job_name = data.get('job_name')
        status = data.get('status')
        
        if status == 'STARTED':
            logger.info(f"배치 작업 시작: {job_name}")
            
        elif status == 'COMPLETED':
            logger.info(f"배치 작업 완료: {job_name}")
            # 완료 통계 저장
            
        elif status == 'FAILED':
            logger.error(f"배치 작업 실패: {job_name} - {data.get('error')}")
            # 실패 알림 및 재시도
    
    async def _handle_system_event(self, data: Dict[str, Any]):
        """시스템 이벤트 처리"""
        event_type = data.get('event_type')
        
        if event_type == 'SHUTDOWN':
            logger.warning("시스템 종료 이벤트 수신")
            # 정리 작업 수행
            
        elif event_type == 'MAINTENANCE':
            logger.info(f"유지보수 모드: {data.get('duration')}분")
            # 유지보수 모드 설정
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]):
        """이벤트 발행 (헬퍼 메서드)"""
        event_data['timestamp'] = datetime.now().isoformat()
        await self.redis.publish(channel, event_data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보 반환"""
        return {
            "is_running": self.is_running,
            "channels_subscribed": list(self.event_handlers.keys()),
            "active_tasks": len([t for t in self.tasks if not t.done()]),
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "handlers_registered": {
                channel: len(handlers) 
                for channel, handlers in self.event_handlers.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        health = {
            "status": "healthy" if self.is_running else "stopped",
            "redis_connected": await self.redis.ping(),
            "active_channels": sum(
                1 for t in self.tasks if not t.done()
            ),
            "recent_errors": self.error_count > 0
        }
        
        if not health["redis_connected"]:
            health["status"] = "unhealthy"
        
        return health


# 전역 소비자 인스턴스
consumer_instance: Optional[RedisConsumer] = None


async def initialize_redis_consumer(
    redis_manager: RedisManager,
    db_manager: DatabaseManager
) -> RedisConsumer:
    """Redis 소비자 초기화"""
    global consumer_instance
    
    if consumer_instance is None:
        consumer_instance = RedisConsumer(redis_manager, db_manager)
        await consumer_instance.start()
    
    return consumer_instance


async def get_redis_consumer() -> Optional[RedisConsumer]:
    """Redis 소비자 인스턴스 반환"""
    return consumer_instance
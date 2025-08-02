"""
고급 설정 관리 서비스
- 동적 설정 관리
- 설정 버전 관리
- 설정 검증 및 적용
"""

import logging
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError

from tradelib import DatabaseManager, RedisManager

logger = logging.getLogger(__name__)


class ConfigSchema(BaseModel):
    """설정 스키마 정의"""
    
    class SchedulerConfig(BaseModel):
        """스케줄러 설정"""
        check_interval: int = 60
        max_concurrent_jobs: int = 5
        job_timeout: int = 3600
        retry_count: int = 3
        retry_delay: int = 300
    
    class ConnectionConfig(BaseModel):
        """연결 설정"""
        ibkr_host: str
        ibkr_port: int
        ibkr_client_id: int
        connection_timeout: int = 30
        heartbeat_interval: int = 10
        auto_reconnect: bool = True
        max_reconnect_attempts: int = 5
    
    class BatchConfig(BaseModel):
        """배치 작업 설정"""
        data_integrity_enabled: bool = True
        partition_days_ahead: int = 7
        compression_chunk_age_days: int = 30
        statistics_retention_days: int = 90
        sync_batch_size: int = 10000
    
    class MonitoringConfig(BaseModel):
        """모니터링 설정"""
        enable_alerts: bool = True
        alert_channels: List[str] = ["email", "slack"]
        health_check_interval: int = 300
        metrics_retention_days: int = 30
    
    scheduler: SchedulerConfig
    connection: ConnectionConfig
    batch: BatchConfig
    monitoring: MonitoringConfig
    
    class Config:
        extra = "allow"  # 추가 필드 허용


class ConfigurationManager:
    """고급 설정 관리자"""
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        redis_manager: RedisManager,
        config_file: str = "config/batch_config.yaml"
    ):
        self.db = db_manager
        self.redis = redis_manager
        self.config_file = Path(config_file)
        
        # 현재 설정
        self.current_config: Optional[ConfigSchema] = None
        self.config_version: int = 0
        
        # 설정 변경 리스너
        self.change_listeners: List[callable] = []
        
        # 설정 캐시
        self.config_cache: Dict[str, Any] = {}
        
        # 초기화
        self._load_initial_config()
    
    def _load_initial_config(self):
        """초기 설정 로드"""
        try:
            # 파일에서 로드
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    if self.config_file.suffix == '.yaml':
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                self.current_config = ConfigSchema(**config_data)
                logger.info(f"설정 파일 로드됨: {self.config_file}")
            else:
                # 기본 설정 사용
                self.current_config = self._get_default_config()
                logger.info("기본 설정 사용")
                
        except Exception as e:
            logger.error(f"설정 로드 실패: {e}")
            self.current_config = self._get_default_config()
    
    def _get_default_config(self) -> ConfigSchema:
        """기본 설정 반환"""
        return ConfigSchema(
            scheduler=ConfigSchema.SchedulerConfig(),
            connection=ConfigSchema.ConnectionConfig(
                ibkr_host="localhost",
                ibkr_port=4002,
                ibkr_client_id=3
            ),
            batch=ConfigSchema.BatchConfig(),
            monitoring=ConfigSchema.MonitoringConfig()
        )
    
    async def get_config(self, path: Optional[str] = None) -> Any:
        """설정 조회"""
        if path is None:
            return self.current_config.dict()
        
        # 캐시 확인
        if path in self.config_cache:
            return self.config_cache[path]
        
        # 경로로 설정 값 접근
        parts = path.split('.')
        value = self.current_config.dict()
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                raise KeyError(f"설정 경로를 찾을 수 없습니다: {path}")
        
        # 캐시에 저장
        self.config_cache[path] = value
        return value
    
    async def update_config(
        self,
        updates: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """설정 업데이트"""
        logger.info(f"설정 업데이트 요청: {list(updates.keys())}")
        
        # 현재 설정 복사
        current_dict = self.current_config.dict()
        
        # 업데이트 적용
        updated_dict = self._deep_update(current_dict, updates)
        
        # 검증
        if validate:
            try:
                new_config = ConfigSchema(**updated_dict)
            except ValidationError as e:
                logger.error(f"설정 검증 실패: {e}")
                raise ValueError(f"잘못된 설정: {e}")
        else:
            new_config = ConfigSchema.construct(**updated_dict)
        
        # 버전 증가
        self.config_version += 1
        
        # 이전 설정 백업
        await self._backup_config(self.current_config.dict())
        
        # 새 설정 적용
        old_config = self.current_config
        self.current_config = new_config
        
        # 캐시 초기화
        self.config_cache.clear()
        
        # 설정 저장
        await self._save_config()
        
        # 변경 알림
        await self._notify_changes(old_config.dict(), new_config.dict())
        
        return {
            'status': 'success',
            'version': self.config_version,
            'changes': self._get_changes(old_config.dict(), new_config.dict())
        }
    
    def _deep_update(self, base: Dict, updates: Dict) -> Dict:
        """딥 업데이트"""
        result = base.copy()
        
        for key, value in updates.items():
            if '.' in key:
                # 중첩된 키 처리
                parts = key.split('.')
                target = result
                
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                
                target[parts[-1]] = value
            else:
                if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                    result[key] = self._deep_update(result[key], value)
                else:
                    result[key] = value
        
        return result
    
    async def _backup_config(self, config: Dict[str, Any]):
        """설정 백업"""
        backup_data = {
            'version': self.config_version,
            'timestamp': datetime.now().isoformat(),
            'config': config
        }
        
        # DB에 저장
        await self.db.execute("""
            INSERT INTO config_history (
                version, timestamp, config_data, change_type
            ) VALUES ($1, $2, $3, 'UPDATE')
        """, self.config_version, datetime.now(), json.dumps(backup_data))
        
        # Redis에 최근 백업 저장
        await self.redis.set(
            f"config:backup:{self.config_version}",
            backup_data,
            expire=86400 * 7  # 7일
        )
    
    async def _save_config(self):
        """설정 파일 저장"""
        try:
            config_dict = self.current_config.dict()
            
            # 파일로 저장
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                if self.config_file.suffix == '.yaml':
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    json.dump(config_dict, f, indent=2)
            
            # Redis에도 저장
            await self.redis.set(
                "config:current",
                config_dict,
                expire=None  # 영구 저장
            )
            
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")
    
    async def _notify_changes(self, old_config: Dict, new_config: Dict):
        """설정 변경 알림"""
        changes = self._get_changes(old_config, new_config)
        
        if not changes:
            return
        
        # 리스너에게 알림
        for listener in self.change_listeners:
            try:
                await listener(changes)
            except Exception as e:
                logger.error(f"설정 변경 알림 실패: {e}")
        
        # Redis 이벤트 발행
        await self.redis.publish("config_events", {
            'event': 'CONFIG_UPDATED',
            'version': self.config_version,
            'changes': changes,
            'timestamp': datetime.now().isoformat()
        })
    
    def _get_changes(self, old: Dict, new: Dict, path: str = "") -> Dict[str, Any]:
        """변경 사항 추출"""
        changes = {}
        
        # 모든 키 확인
        all_keys = set(old.keys()) | set(new.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in old:
                changes[current_path] = {'action': 'added', 'value': new[key]}
            elif key not in new:
                changes[current_path] = {'action': 'removed', 'old_value': old[key]}
            elif isinstance(old[key], dict) and isinstance(new[key], dict):
                nested_changes = self._get_changes(old[key], new[key], current_path)
                changes.update(nested_changes)
            elif old[key] != new[key]:
                changes[current_path] = {
                    'action': 'modified',
                    'old_value': old[key],
                    'new_value': new[key]
                }
        
        return changes
    
    def register_change_listener(self, listener: callable):
        """변경 리스너 등록"""
        self.change_listeners.append(listener)
    
    async def rollback_config(self, version: int) -> Dict[str, Any]:
        """설정 롤백"""
        logger.info(f"설정 롤백 요청: version {version}")
        
        # 백업 조회
        backup = await self.redis.get(f"config:backup:{version}")
        
        if not backup:
            # DB에서 조회
            result = await self.db.fetchrow("""
                SELECT config_data FROM config_history
                WHERE version = $1
            """, version)
            
            if not result:
                raise ValueError(f"백업 버전을 찾을 수 없습니다: {version}")
            
            backup = json.loads(result['config_data'])
        
        # 롤백 적용
        return await self.update_config(backup['config'])
    
    async def validate_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """설정 검증"""
        try:
            # 스키마 검증
            test_config = ConfigSchema(**config_data)
            
            # 추가 비즈니스 규칙 검증
            errors = []
            
            # 예: 포트 범위 확인
            if not (1024 <= test_config.connection.ibkr_port <= 65535):
                errors.append("IBKR 포트는 1024-65535 범위여야 합니다")
            
            # 예: 타임아웃 값 확인
            if test_config.scheduler.job_timeout < 60:
                errors.append("작업 타임아웃은 최소 60초 이상이어야 합니다")
            
            if errors:
                return {
                    'valid': False,
                    'errors': errors
                }
            
            return {
                'valid': True,
                'config': test_config.dict()
            }
            
        except ValidationError as e:
            return {
                'valid': False,
                'errors': [str(err) for err in e.errors()]
            }
    
    async def export_config(self, format: str = 'yaml') -> str:
        """설정 내보내기"""
        config_dict = self.current_config.dict()
        
        if format == 'yaml':
            return yaml.dump(config_dict, default_flow_style=False)
        elif format == 'json':
            return json.dumps(config_dict, indent=2)
        else:
            raise ValueError(f"지원하지 않는 형식: {format}")
    
    async def import_config(self, config_str: str, format: str = 'yaml') -> Dict[str, Any]:
        """설정 가져오기"""
        try:
            if format == 'yaml':
                config_data = yaml.safe_load(config_str)
            elif format == 'json':
                config_data = json.loads(config_str)
            else:
                raise ValueError(f"지원하지 않는 형식: {format}")
            
            # 검증
            validation_result = await self.validate_config(config_data)
            
            if not validation_result['valid']:
                raise ValueError(f"설정 검증 실패: {validation_result['errors']}")
            
            # 적용
            return await self.update_config(config_data)
            
        except Exception as e:
            logger.error(f"설정 가져오기 실패: {e}")
            raise
    
    def get_config_info(self) -> Dict[str, Any]:
        """설정 정보 반환"""
        return {
            'version': self.config_version,
            'file_path': str(self.config_file),
            'last_modified': datetime.fromtimestamp(
                self.config_file.stat().st_mtime
            ).isoformat() if self.config_file.exists() else None,
            'listeners_count': len(self.change_listeners),
            'cache_size': len(self.config_cache)
        }


# 전역 설정 관리자 인스턴스
config_manager_instance: Optional[ConfigurationManager] = None


async def initialize_configuration_manager(
    db_manager: DatabaseManager,
    redis_manager: RedisManager,
    config_file: Optional[str] = None
) -> ConfigurationManager:
    """설정 관리자 초기화"""
    global config_manager_instance
    
    if config_manager_instance is None:
        config_manager_instance = ConfigurationManager(
            db_manager,
            redis_manager,
            config_file or "config/batch_config.yaml"
        )
    
    return config_manager_instance


async def get_configuration_manager() -> Optional[ConfigurationManager]:
    """설정 관리자 인스턴스 반환"""
    return config_manager_instance
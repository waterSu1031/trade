"""
데이터베이스 스키마 표준 정의
모든 서비스에서 공통으로 사용하는 데이터베이스 테이블명, 필드명, 데이터 타입 표준
"""

# 테이블명 표준 (복수형 사용)
TABLE_NAMES = {
    'contracts': 'contracts',
    'exchanges': 'exchanges', 
    'trades': 'trades',
    'positions': 'positions',
    'orders': 'orders',
    'accounts': 'accounts',
    'contract_details': 'contract_details',
    'contract_details_stock': 'contract_details_stock',
    'contract_details_future': 'contract_details_future',
    'contract_details_option': 'contract_details_option',
    'contract_details_index': 'contract_details_index',
    'exc_x_con': 'exc_x_con',
    'con_x_data': 'con_x_data',
    'price_time': 'price_time',
    'price_range': 'price_range',
    'price_volume': 'price_volume',
    'daily_statistics': 'daily_statistics',
    'trade_events': 'trade_events',
    'order_status_history': 'order_status_history'
}

# 필드명 표준 (snake_case 사용)
FIELD_NAMES = {
    # Contract 관련
    'contract_id': 'con_id',  # Primary key
    'symbol': 'symbol',
    'security_type': 'sec_type',
    'exchange': 'exchange',
    'currency': 'currency',
    'description': 'desc',  # 통일된 설명 필드
    'right_type': 'right_type',  # 옵션 권리 구분 (C/P)
    'strike': 'strike',
    'multiplier': 'multiplier',
    'local_symbol': 'local_symbol',
    'trading_class': 'trading_class',
    'primary_exchange': 'primary_exchange',
    
    # Contract Details 관련
    'market_name': 'market_name',
    'min_tick': 'min_tick',
    'price_magnifier': 'price_magnifier',
    'order_types': 'order_types',
    'valid_exchanges': 'valid_exchanges',
    'time_zone_id': 'time_zone_id',
    'trading_hours': 'trading_hours',
    'liquid_hours': 'liquid_hours',
    
    # Price 관련
    'timestamp': 'time',
    'open': 'open',
    'high': 'high', 
    'low': 'low',
    'close': 'close',
    'volume': 'volume',
    'vwap': 'vwap',
    'count': 'count',
    
    # Order 관련
    'order_id': 'order_id',
    'client_id': 'client_id',
    'perm_id': 'perm_id',
    'action': 'action',  # BUY/SELL
    'order_type': 'order_type',  # MKT/LMT/STP
    'quantity': 'quantity',
    'limit_price': 'lmt_price',
    'stop_price': 'aux_price',
    'status': 'status',
    'filled': 'filled',
    'remaining': 'remaining',
    'avg_fill_price': 'avg_fill_price',
    
    # Trade 관련
    'trade_id': 'trade_id',
    'exec_id': 'exec_id',
    'side': 'side',  # BOT/SLD
    'shares': 'shares',
    'price': 'price',
    'commission': 'commission',
    'realized_pnl': 'realized_pnl',
    
    # 공통 메타데이터
    'created_at': 'created_at',
    'updated_at': 'updated_at',
    'is_active': 'is_active'
}

# PostgreSQL 데이터 타입 표준
DATA_TYPES = {
    # 숫자형
    'id': 'INTEGER',
    'big_id': 'BIGINT',
    'price': 'DECIMAL(15,8)',
    'quantity': 'DECIMAL(15,8)',
    'money': 'DECIMAL(15,2)',
    'percentage': 'DECIMAL(5,2)',
    'count': 'INTEGER',
    
    # 문자열
    'symbol': 'VARCHAR(16)',
    'exchange': 'VARCHAR(16)',
    'currency': 'VARCHAR(8)',
    'description': 'VARCHAR(256)',
    'long_text': 'TEXT',
    'status': 'VARCHAR(20)',
    'type': 'VARCHAR(10)',
    
    # 날짜/시간
    'date': 'DATE',
    'timestamp': 'TIMESTAMP',
    'timestamp_tz': 'TIMESTAMPTZ',
    
    # 불린
    'boolean': 'BOOLEAN',
    
    # JSON (PostgreSQL 특화)
    'json': 'JSONB'
}

# 외래키 관계 정의
FOREIGN_KEYS = {
    'contract_details': {
        'con_id': 'contracts(con_id)'
    },
    'contract_details_stock': {
        'con_id': 'contracts(con_id)'
    },
    'contract_details_future': {
        'con_id': 'contracts(con_id)'
    },
    'contract_details_option': {
        'con_id': 'contracts(con_id)'
    },
    'contract_details_index': {
        'con_id': 'contracts(con_id)'
    },
    'orders': {
        'symbol': None  # 외래키 없음, 단순 참조
    },
    'trade_events': {
        'order_id': 'orders(order_id)'
    }
}

# 인덱스 정의
INDEXES = {
    'contracts': [
        'symbol',
        'exchange',
        'sec_type'
    ],
    'orders': [
        'symbol',
        'status',
        'place_time'
    ],
    'trade_events': [
        'symbol',
        'time',
        'order_id'
    ],
    'price_time': [
        'symbol',
        'time',
        'con_id'
    ]
}
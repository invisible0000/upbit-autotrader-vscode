#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
스키마 버전 레지스트리

다양한 스키마 버전을 정의하고 관리합니다.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

# 스키마 버전 정의
SCHEMA_VERSIONS = {
    "v0.0-empty": {
        "name": "Empty Schema",
        "description": "빈 데이터베이스",
        "release_date": "2024-01-01",
        "tables": [],
        "migration_from": None,
        "migration_to": ["v1.0-legacy"],
        "deprecated": False
    },
    
    "v1.0-legacy": {
        "name": "Legacy Strategy Schema", 
        "description": "기존 단순 전략 시스템",
        "release_date": "2024-06-01",
        "tables": [
            "strategy", "backtest", "portfolio", "trade", 
            "ohlcv", "orderbook", "trading_session"
        ],
        "migration_from": ["v0.0-empty"],
        "migration_to": ["v1.5-position-management", "v2.0-strategy-combination"],
        "deprecated": True,
        "deprecation_reason": "단순한 전략 구조로 복잡한 조합 불가능"
    },
    
    "v1.5-position-management": {
        "name": "Position Management Schema",
        "description": "포지션 관리 시스템 추가",
        "release_date": "2024-10-01", 
        "tables": [
            "strategy", "backtest", "portfolio", "trade", "ohlcv", "orderbook",
            "trading_session", "positions", "position_history"
        ],
        "migration_from": ["v1.0-legacy"],
        "migration_to": ["v2.0-strategy-combination"],
        "deprecated": False
    },
    
    "v2.0-strategy-combination": {
        "name": "Strategy Combination Schema",
        "description": "전략 조합 시스템 + 포지션 관리 + 백테스트 개선",
        "release_date": "2024-12-01",
        "tables": [
            # 기존 시장 데이터
            "ohlcv", "orderbook", "trade",
            
            # 새로운 전략 시스템
            "strategy_definitions", "strategy_configs", "strategy_combinations",
            "combination_management_strategies",
            
            # 포트폴리오 및 포지션
            "portfolios", "positions", "position_history", "portfolio_snapshots",
            
            # 백테스트 시스템
            "backtest_results", "trade_logs", "position_logs",
            
            # 최적화 시스템
            "optimization_jobs", "optimization_results",
            
            # 시스템 테이블
            "schema_migrations", "system_notifications"
        ],
        "migration_from": ["v1.0-legacy", "v1.5-position-management"],
        "migration_to": [],  # 최신 버전
        "deprecated": False,
        "features": [
            "전략 조합 시스템",
            "포지션 ID 관리", 
            "실시간 포트폴리오 추적",
            "매개변수 최적화",
            "충돌 해결 메커니즘"
        ]
    }
}

# 마이그레이션 규칙 정의
MIGRATION_RULES = {
    "v1.0_to_v2.0": {
        "name": "Legacy to Strategy Combination Migration",
        "description": "레거시 전략을 새로운 전략 조합 시스템으로 변환",
        "script_path": "scripts/v1_to_v2_migration.py",
        "data_transformations": {
            "strategy": {
                "source_table": "strategy",
                "target_table": "strategy_definitions",
                "field_mapping": {
                    "id": "id",
                    "name": "name",
                    "description": "description", 
                    "parameters": "default_parameters"
                },
                "default_values": {
                    "strategy_type": "entry",
                    "class_name": "LegacyStrategy"
                },
                "data_filters": {
                    "exclude_test_strategies": True
                }
            },
            "backtest": {
                "source_table": "backtest", 
                "target_table": "backtest_results",
                "field_mapping": {
                    "id": "backtest_id",
                    "strategy_id": "strategy_id",
                    "symbol": "symbol",
                    "start_date": "start_date",
                    "end_date": "end_date",
                    "initial_capital": "initial_capital",
                    "final_capital": "final_capital",
                    "total_return": "total_return",
                    "max_drawdown": "max_drawdown"
                },
                "calculated_fields": {
                    "portfolio_id": "NULL",  # 새 필드
                    "performance_metrics": "JSON.object()"  # 빈 JSON
                }
            }
        },
        "preserve_tables": [
            "ohlcv",       # 시장 데이터는 그대로 보존
            "orderbook",   # 호가 데이터 보존
            "trade"        # 거래 데이터 보존
        ],
        "archive_tables": [
            "trading_session"  # 구버전 테이블은 아카이브
        ]
    },
    
    "v1.5_to_v2.0": {
        "name": "Position Management to Strategy Combination Migration",
        "description": "포지션 관리에서 전략 조합 시스템으로 업그레이드",
        "script_path": "scripts/v15_to_v2_migration.py",
        "data_transformations": {
            "positions": {
                "source_table": "positions",
                "target_table": "positions", 
                "field_mapping": "1:1",  # 동일한 구조
                "schema_changes": {
                    "add_columns": ["combination_id", "entry_strategy_id"]
                }
            }
        },
        "preserve_tables": [
            "ohlcv", "orderbook", "trade", "positions", "position_history"
        ]
    }
}

# 데이터 검증 규칙
VALIDATION_RULES = {
    "schema_integrity": {
        "required_tables": {
            "v2.0-strategy-combination": [
                "strategy_definitions", "strategy_combinations", 
                "portfolios", "backtest_results"
            ]
        },
        "foreign_key_checks": {
            "strategy_configs.strategy_definition_id": "strategy_definitions.id",
            "strategy_combinations.entry_strategy_id": "strategy_configs.config_id",
            "positions.portfolio_id": "portfolios.portfolio_id"
        }
    },
    
    "data_consistency": {
        "non_empty_tables": ["strategy_definitions"],  # 최소한 하나의 전략은 있어야 함
        "valid_references": {
            "check_orphan_configs": "strategy_configs without strategy_definitions",
            "check_orphan_positions": "positions without portfolios"
        }
    },
    
    "performance_checks": {
        "max_table_scan_time": 30,  # 초
        "index_usage_verification": [
            "ohlcv.timestamp", "ohlcv.symbol", "positions.portfolio_id"
        ]
    }
}

class SchemaVersionRegistry:
    """스키마 버전 관리 클래스"""
    
    @classmethod
    def get_version_info(cls, version: str) -> Optional[Dict[str, Any]]:
        """특정 버전 정보 조회"""
        return SCHEMA_VERSIONS.get(version)
    
    @classmethod 
    def get_latest_version(cls) -> str:
        """최신 버전 조회"""
        non_deprecated = {k: v for k, v in SCHEMA_VERSIONS.items() 
                         if not v.get('deprecated', False)}
        
        if not non_deprecated:
            return list(SCHEMA_VERSIONS.keys())[-1]
        
        # release_date 기준으로 최신 버전 찾기
        latest = max(non_deprecated.items(), 
                    key=lambda x: datetime.strptime(x[1]['release_date'], '%Y-%m-%d'))
        return latest[0]
    
    @classmethod
    def get_migration_path(cls, from_version: str, to_version: str) -> Optional[str]:
        """두 버전 간의 마이그레이션 경로 조회"""
        if from_version == to_version:
            return None
            
        from_info = cls.get_version_info(from_version)
        if not from_info:
            return None
            
        # 직접 마이그레이션 가능한지 확인
        if to_version in from_info.get('migration_to', []):
            migration_key = f"{from_version.replace('-', '_').replace('.', '_')}_to_{to_version.replace('-', '_').replace('.', '_')}"
            return MIGRATION_RULES.get(migration_key, {}).get('script_path')
        
        return None
    
    @classmethod
    def get_migration_rules(cls, from_version: str, to_version: str) -> Optional[Dict[str, Any]]:
        """마이그레이션 규칙 조회"""
        migration_key = f"{from_version.replace('-', '_').replace('.', '_')}_to_{to_version.replace('-', '_').replace('.', '_')}"
        return MIGRATION_RULES.get(migration_key)
    
    @classmethod
    def validate_migration_path(cls, from_version: str, to_version: str) -> Dict[str, Any]:
        """마이그레이션 경로 유효성 검증"""
        result = {
            "valid": False,
            "path": [],
            "warnings": [],
            "errors": []
        }
        
        from_info = cls.get_version_info(from_version)
        to_info = cls.get_version_info(to_version)
        
        if not from_info:
            result["errors"].append(f"Unknown source version: {from_version}")
            return result
            
        if not to_info:
            result["errors"].append(f"Unknown target version: {to_version}")
            return result
        
        # 직접 마이그레이션 체크
        if to_version in from_info.get('migration_to', []):
            result["valid"] = True
            result["path"] = [from_version, to_version]
            
            # 경고 사항 체크
            if from_info.get('deprecated'):
                result["warnings"].append(f"Source version {from_version} is deprecated")
                
        else:
            result["errors"].append(f"No direct migration path from {from_version} to {to_version}")
        
        return result
    
    @classmethod
    def get_validation_rules(cls, version: str) -> Dict[str, Any]:
        """특정 버전의 검증 규칙 조회"""
        return VALIDATION_RULES
    
    @classmethod
    def list_all_versions(cls) -> List[Dict[str, Any]]:
        """모든 버전 목록 조회"""
        return [
            {
                "version": version,
                "name": info["name"],
                "description": info["description"],
                "release_date": info["release_date"],
                "deprecated": info.get("deprecated", False),
                "is_latest": version == cls.get_latest_version()
            }
            for version, info in SCHEMA_VERSIONS.items()
        ]


# 편의 함수들
def get_current_schema_version() -> str:
    """현재 권장 스키마 버전 반환"""
    return SchemaVersionRegistry.get_latest_version()

def is_migration_required(current_version: str) -> bool:
    """마이그레이션이 필요한지 확인"""
    latest = get_current_schema_version()
    return current_version != latest

def get_recommended_migration(current_version: str) -> Optional[str]:
    """권장 마이그레이션 대상 버전 반환"""
    if is_migration_required(current_version):
        return get_current_schema_version()
    return None

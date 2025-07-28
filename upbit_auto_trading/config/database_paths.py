#!/usr/bin/env python3
"""
데이터베이스 경로 상수 정의
TASK-20250728-01_Database_Structure_Unification Phase 4

통합된 데이터베이스 구조의 경로를 중앙에서 관리합니다.
"""

from pathlib import Path
import os

class DatabasePaths:
    """데이터베이스 경로 상수 클래스"""
    
    # 기본 경로 설정 (설치형 환경 최적화)
    BASE_DIR = Path(__file__).parent.parent  # upbit_auto_trading/config -> upbit_auto_trading -> project_root
    DATA_DIR = BASE_DIR / "upbit_auto_trading" / "data"
    
    # 새로운 통합 데이터베이스 경로 (설치형 환경 최적화됨)
    SETTINGS_DB = DATA_DIR / "settings.sqlite3"      # 설정 + 거래변수 통합
    STRATEGIES_DB = DATA_DIR / "strategies.sqlite3"   # 전략 + 거래 데이터
    MARKET_DATA_DB = DATA_DIR / "market_data.sqlite3" # 시장 데이터 (기존 유지)
    
    # 하위 호환성을 위한 레거시 경로 (deprecated)
    @classmethod
    def get_legacy_app_settings_path(cls) -> str:
        """
        레거시 app_settings.sqlite3 경로를 settings.sqlite3로 매핑
        @deprecated: 새 코드에서는 SETTINGS_DB 사용 권장
        """
        return str(cls.SETTINGS_DB)
    
    @classmethod 
    def get_legacy_upbit_auto_trading_path(cls) -> str:
        """
        레거시 upbit_auto_trading.sqlite3 경로를 strategies.sqlite3로 매핑
        @deprecated: 새 코드에서는 STRATEGIES_DB 사용 권장
        """
        return str(cls.STRATEGIES_DB)
    
    @classmethod
    def get_legacy_trading_variables_path(cls) -> str:
        """
        레거시 trading_variables.db 경로를 settings.sqlite3로 매핑
        @deprecated: 새 코드에서는 SETTINGS_DB 사용 권장
        """
        return str(cls.SETTINGS_DB)
    
    @classmethod
    def get_legacy_market_data_path(cls) -> str:
        """
        레거시 market_data.sqlite3 경로 (변경 없음)
        """
        return str(cls.MARKET_DATA_DB)


class TableMappings:
    """테이블 매핑 정보 클래스"""
    
    # Settings DB에 있는 테이블들 (app_settings.sqlite3 + trading_variables.db 통합)
    SETTINGS_TABLES = {
        # 원래 app_settings.sqlite3 테이블들
        'trading_conditions': 'settings.sqlite3',
        'strategies': 'settings.sqlite3', 
        'component_strategy': 'settings.sqlite3',
        'strategy_components': 'settings.sqlite3',
        'strategy_execution': 'settings.sqlite3',
        'chart_variables': 'settings.sqlite3',
        'chart_layout_templates': 'settings.sqlite3',
        'simulation_sessions': 'settings.sqlite3',
        'simulation_market_data': 'settings.sqlite3',
        'simulation_trades': 'settings.sqlite3',
        'system_settings': 'settings.sqlite3',
        'backup_info': 'settings.sqlite3',
        'variable_compatibility_rules': 'settings.sqlite3',
        'variable_usage_logs': 'settings.sqlite3',
        'execution_history': 'settings.sqlite3',
        'strategy_conditions': 'settings.sqlite3',
        
        # trading_variables.db 테이블들 (tv_ 접두사)
        'tv_trading_variables': 'settings.sqlite3',
        'tv_comparison_groups': 'settings.sqlite3', 
        'tv_schema_version': 'settings.sqlite3',
    }
    
    # Strategies DB에 있는 테이블들 (upbit_auto_trading.sqlite3)
    STRATEGIES_TABLES = {
        'market_data': 'strategies.sqlite3',  # 주의: 이름이 같지만 다른 DB
        'migration_info': 'strategies.sqlite3',
    }
    
    # Market Data DB에 있는 테이블들 (기존 유지)
    MARKET_DATA_TABLES = {
        'market_data': 'market_data.sqlite3',  # 메인 시장 데이터
        'atomic_strategies': 'market_data.sqlite3',
        'atomic_variables': 'market_data.sqlite3',
        'atomic_conditions': 'market_data.sqlite3',
        'atomic_actions': 'market_data.sqlite3',
        'atomic_rules': 'market_data.sqlite3',
        'backtest_results': 'market_data.sqlite3',
        'portfolios': 'market_data.sqlite3',
        'positions': 'market_data.sqlite3',
        'strategy_combinations': 'market_data.sqlite3',
        'strategy_configs': 'market_data.sqlite3',
        'strategy_definitions': 'market_data.sqlite3',
        'ohlcv_data': 'market_data.sqlite3',
        # ... 나머지 39개 테이블들
    }
    
    @classmethod
    def get_db_for_table(cls, table_name: str) -> str:
        """
        테이블명에 따라 적절한 데이터베이스 경로 반환
        
        Args:
            table_name: 테이블명
            
        Returns:
            str: 데이터베이스 파일 경로
        """
        if table_name in cls.SETTINGS_TABLES:
            return str(DatabasePaths.SETTINGS_DB)
        elif table_name in cls.STRATEGIES_TABLES:
            return str(DatabasePaths.STRATEGIES_DB)
        elif table_name in cls.MARKET_DATA_TABLES:
            return str(DatabasePaths.MARKET_DATA_DB)
        else:
            # 기본값: settings DB (대부분의 앱 테이블들)
            return str(DatabasePaths.SETTINGS_DB)


# 편의를 위한 전역 상수들
SETTINGS_DB_PATH = str(DatabasePaths.SETTINGS_DB)
STRATEGIES_DB_PATH = str(DatabasePaths.STRATEGIES_DB)  
MARKET_DATA_DB_PATH = str(DatabasePaths.MARKET_DATA_DB)

# 레거시 호환성 (점진적 마이그레이션용)
APP_SETTINGS_DB_PATH = DatabasePaths.get_legacy_app_settings_path()
UPBIT_AUTO_TRADING_DB_PATH = DatabasePaths.get_legacy_upbit_auto_trading_path()
TRADING_VARIABLES_DB_PATH = DatabasePaths.get_legacy_trading_variables_path()


def get_connection_string(table_name: str = None) -> str:
    """
    테이블명에 따라 적절한 DB 연결 문자열 반환
    
    Args:
        table_name: 테이블명 (선택사항)
        
    Returns:
        str: 데이터베이스 연결 경로
    """
    if table_name:
        return TableMappings.get_db_for_table(table_name)
    else:
        # 기본값: settings DB
        return SETTINGS_DB_PATH


def get_current_config() -> dict:
    """
    현재 데이터베이스 설정을 반환
    
    Returns:
        dict: 현재 DB 파일 경로들
    """
    try:
        # database_config.yaml 파일에서 user_defined 설정 확인
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "database_config.yaml")
        
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # user_defined 설정이 활성화되어 있으면 그 경로를 사용
                if config.get('user_defined', {}).get('active', False):
                    user_config = config['user_defined']
                    return {
                        'settings_db': user_config.get('settings_db', str(SETTINGS_DB_PATH)),
                        'strategies_db': user_config.get('strategies_db', str(STRATEGIES_DB_PATH)),
                        'market_data_db': user_config.get('market_data_db', str(MARKET_DATA_DB_PATH))
                    }
            except Exception:
                pass  # 오류 시 기본값 사용
    except Exception:
        pass  # 오류 시 기본값 사용
    
    # 기본값 반환
    return {
        'settings_db': str(SETTINGS_DB_PATH),
        'strategies_db': str(STRATEGIES_DB_PATH),
        'market_data_db': str(MARKET_DATA_DB_PATH)
    }


if __name__ == "__main__":
    # 테스트
    print("🔗 데이터베이스 경로 상수 테스트")
    print("=" * 50)
    
    print(f"📊 Settings DB: {SETTINGS_DB_PATH}")
    print(f"📊 Strategies DB: {STRATEGIES_DB_PATH}")
    print(f"📊 Market Data DB: {MARKET_DATA_DB_PATH}")
    
    print("\n🔍 테이블 매핑 테스트:")
    test_tables = ['trading_conditions', 'strategies', 'tv_trading_variables', 'market_data']
    for table in test_tables:
        db_path = TableMappings.get_db_for_table(table)
        print(f"  - {table} → {db_path}")
    
    print("\n✅ 경로 상수 로드 완료!")

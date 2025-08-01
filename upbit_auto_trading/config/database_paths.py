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
    BASE_DIR = Path(__file__).parent.parent.parent  # upbit_auto_trading/config -> upbit_auto_trading -> project_root
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
    """테이블 매핑 정보 클래스 - 3-Database 아키텍처 (2025-08-01)"""
    
    # Settings DB: 시스템 설정 + 변수 정의 (cfg_*, tv_*, sys_*)
    SETTINGS_TABLES = {
        # 시스템 설정 테이블들 (cfg_* 접두사)
        'cfg_app_settings': 'settings.sqlite3',
        'cfg_system_settings': 'settings.sqlite3',
        'cfg_chart_layout_templates': 'settings.sqlite3',
        
        # 시스템 관리 테이블들 (sys_* 접두사)
        'sys_backup_info': 'settings.sqlite3',
        
        # Trading Variables 시스템 (tv_* 접두사)
        'tv_trading_variables': 'settings.sqlite3',
        'tv_variable_parameters': 'settings.sqlite3',
        'tv_help_texts': 'settings.sqlite3',
        'tv_placeholder_texts': 'settings.sqlite3',
        'tv_indicator_categories': 'settings.sqlite3',
        'tv_parameter_types': 'settings.sqlite3',
        'tv_comparison_groups': 'settings.sqlite3',
        'tv_indicator_library': 'settings.sqlite3',
        'tv_schema_version': 'settings.sqlite3',
        'tv_workflow_guides': 'settings.sqlite3',
        'tv_chart_variables': 'settings.sqlite3',
        'tv_variable_compatibility_rules': 'settings.sqlite3',
        'tv_variable_usage_logs': 'settings.sqlite3',
        
        # 🔧 구조 정의는 settings에서 관리하지만 실제 데이터는 strategies DB에 있음
    }
    
    # Strategies DB: 사용자 생성 데이터 (strategies, strategy_*, user_*)
    STRATEGIES_TABLES = {
        # 메인 전략 테이블들
        'strategies': 'strategies.sqlite3',
        'strategy_components': 'strategies.sqlite3',
        'strategy_conditions': 'strategies.sqlite3',
        'strategy_execution': 'strategies.sqlite3',
        'strategy_alerts': 'strategies.sqlite3',
        'strategy_performance_metrics': 'strategies.sqlite3',
        
        # 🔧 현재 실제 사용자 트리거 데이터 (기존 마이그레이션된 데이터)
        'trading_conditions': 'strategies.sqlite3',  # 실제 사용자 생성 트리거들
        
        # 사용자 생성 데이터
        'user_strategies': 'strategies.sqlite3',
        'user_triggers': 'strategies.sqlite3',
        
        # 컴포넌트 시스템
        'component_strategy': 'strategies.sqlite3',
        
        # 실행 및 이력
        'execution_history': 'strategies.sqlite3',
        
        # 시뮬레이션 시스템
        'simulation_sessions': 'strategies.sqlite3',
        'simulation_trades': 'strategies.sqlite3',
        
        # 포지션 관리
        'current_positions': 'strategies.sqlite3',
        'portfolio_snapshots': 'strategies.sqlite3',
        
        # 기타
        'migration_info': 'strategies.sqlite3',
    }
    
    # Market Data DB: 시장 데이터 (candlestick_*, technical_*, real_time_*)
    MARKET_DATA_TABLES = {
        # 기본 시장 정보
        'market_symbols': 'market_data.sqlite3',
        
        # OHLCV 캔들 데이터
        'candlestick_data_1m': 'market_data.sqlite3',
        'candlestick_data_5m': 'market_data.sqlite3',
        'candlestick_data_1h': 'market_data.sqlite3',
        'candlestick_data_1d': 'market_data.sqlite3',
        
        # 기술적 지표
        'technical_indicators_1d': 'market_data.sqlite3',
        'technical_indicators_1h': 'market_data.sqlite3',
        
        # 실시간 데이터
        'real_time_quotes': 'market_data.sqlite3',
        'order_book_snapshots': 'market_data.sqlite3',
        
        # 시뮬레이션용 마켓 데이터
        'simulation_market_data': 'market_data.sqlite3',
        
        # 마켓 분석
        'daily_market_analysis': 'market_data.sqlite3',
        'screener_results': 'market_data.sqlite3',
        'market_state_summary': 'market_data.sqlite3',
        
        # 데이터 품질 관리
        'data_quality_logs': 'market_data.sqlite3',
        'data_collection_status': 'market_data.sqlite3',
        
        # 레거시 호환성
        'market_data': 'market_data.sqlite3',
        'ohlcv_data': 'market_data.sqlite3',
        'backtest_results': 'market_data.sqlite3',
        'portfolios': 'market_data.sqlite3',
        'positions': 'market_data.sqlite3',
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

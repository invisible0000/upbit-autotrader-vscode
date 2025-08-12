"""
컴포넌트 선택기 테스트용 데이터
DDD 아키텍처 기반 컴포넌트 계층 구조
"""

COMPONENT_TREE_DATA = {
    "🖥️ Presentation Layer": {
        "📱 Desktop UI": {
            "🏠 Main Window": "upbit_auto_trading.ui.desktop.main_window",
            "⚙️ Settings Screen": "upbit_auto_trading.ui.desktop.settings_screen",
            "📊 Trading Dashboard": "upbit_auto_trading.ui.desktop.trading_dashboard",
            "📈 Chart Viewer": "upbit_auto_trading.ui.desktop.chart_viewer",
        },
        "🧩 UI Components": {
            "🔢 Environment Profile": "upbit_auto_trading.ui.desktop.environment_profile",
            "📋 Logging Management": "upbit_auto_trading.ui.desktop.logging_management",
            "🗄️ Database Settings": "upbit_auto_trading.ui.desktop.database_settings",
            "🎨 Theme Manager": "upbit_auto_trading.ui.desktop.theme_manager",
        }
    },
    "🏗️ Application Layer": {
        "📋 Use Cases": {
            "💰 Trading Use Case": "upbit_auto_trading.application.trading_use_case",
            "📊 Market Analysis": "upbit_auto_trading.application.market_analysis",
            "📈 Strategy Management": "upbit_auto_trading.application.strategy_management",
            "⚙️ Configuration": "upbit_auto_trading.application.configuration",
        },
        "🔄 Services": {
            "📡 API Service": "upbit_auto_trading.application.api_service",
            "💾 Data Service": "upbit_auto_trading.application.data_service",
            "📬 Notification Service": "upbit_auto_trading.application.notification_service",
        }
    },
    "🎯 Domain Layer": {
        "🏪 Entities": {
            "💱 Trading Pair": "upbit_auto_trading.domain.entities.trading_pair",
            "📊 Market Data": "upbit_auto_trading.domain.entities.market_data",
            "🎯 Strategy": "upbit_auto_trading.domain.entities.strategy",
            "💼 Portfolio": "upbit_auto_trading.domain.entities.portfolio",
        },
        "🔧 Services": {
            "💹 Trading Engine": "upbit_auto_trading.domain.services.trading_engine",
            "🧮 Risk Calculator": "upbit_auto_trading.domain.services.risk_calculator",
            "📈 Indicator Calculator": "upbit_auto_trading.domain.services.indicator_calculator",
        }
    },
    "🔌 Infrastructure Layer": {
        "🗄️ Repositories": {
            "💾 Database Repository": "upbit_auto_trading.infrastructure.database_repository",
            "📁 File Repository": "upbit_auto_trading.infrastructure.file_repository",
            "💱 Market Repository": "upbit_auto_trading.infrastructure.market_repository",
        },
        "🌐 External APIs": {
            "🏛️ Upbit API": "upbit_auto_trading.infrastructure.upbit_api",
            "📊 Market Data API": "upbit_auto_trading.infrastructure.market_data_api",
        },
        "📝 Logging": {
            "🔍 Log Manager": "upbit_auto_trading.infrastructure.logging.log_manager",
            "📤 Log Formatter": "upbit_auto_trading.infrastructure.logging.formatter",
            "💾 Log Storage": "upbit_auto_trading.infrastructure.logging.storage",
        }
    }
}

def get_flat_component_list():
    """
    트리 구조를 평면 리스트로 변환
    각 항목은 (display_name, full_path) 튜플
    """
    flat_list = []

    def _flatten(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                # 중간 노드 (카테고리)
                current_prefix = f"{prefix}{key}" if prefix else key
                flat_list.append((current_prefix, ""))  # 카테고리는 경로 없음
                _flatten(value, f"{current_prefix} > ")
            else:
                # 말단 노드 (실제 컴포넌트)
                display_name = f"{prefix}{key}"
                flat_list.append((display_name, value))

    _flatten(COMPONENT_TREE_DATA)
    return flat_list

def search_components(query):
    """
    컴포넌트 검색 기능
    """
    query = query.lower()
    flat_list = get_flat_component_list()

    results = []
    for display_name, path in flat_list:
        if path and (query in display_name.lower() or query in path.lower()):
            results.append((display_name, path))

    return results

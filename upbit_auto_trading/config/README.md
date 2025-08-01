# 🔧 Config Directory - 구성 설정 관리

이 폴더는 **upbit-autotrader-vscode 프로젝트의 핵심 구성 설정**을 관리합니다.

## 📁 폴더 개요

**Purpose**: 시스템 전반의 설정, 데이터베이스 경로, 로깅 구성 등 핵심 설정 파일들을 중앙 집중 관리

**Architecture Role**: 
- 3-Database 아키텍처의 경로 정의 및 테이블 매핑
- 시스템 구성 파라미터 표준화
- 개발/운영 환경별 설정 분리

---

## 📋 주요 파일 구성

### 🗄️ database_paths.py ⭐ **핵심 파일**
**목적**: 3-Database 아키텍처 경로 및 테이블 매핑 중앙 관리

#### 주요 클래스
```python
class DatabasePaths:
    """데이터베이스 경로 상수 클래스"""
    SETTINGS_DB = "upbit_auto_trading/data/settings.sqlite3"    # 시스템 설정 + 변수 정의
    STRATEGIES_DB = "upbit_auto_trading/data/strategies.sqlite3" # 사용자 생성 데이터
    MARKET_DATA_DB = "upbit_auto_trading/data/market_data.sqlite3" # 시장 데이터

class TableMappings:
    """테이블 매핑 정보 클래스 - 53개 테이블 정의"""
    SETTINGS_TABLES = {...}    # 17개 테이블 (cfg_*, tv_*, sys_*)
    STRATEGIES_TABLES = {...}  # 16개 테이블 (strategies, trading_conditions 등)
    MARKET_DATA_TABLES = {...} # 20개 테이블 (candlestick_*, technical_*, real_time_*)
```

#### 핵심 기능
- **🎯 3-Database 분리**: Settings/Strategies/Market Data 역할별 분리
- **🗂️ 테이블 매핑**: 53개 테이블의 정확한 DB 할당
- **🔄 레거시 호환성**: 기존 경로에서 새 구조로 점진적 마이그레이션 지원
- **📍 중앙 집중**: 모든 DB 경로를 한 곳에서 관리

#### 사용 방법
```python
# 기본 사용법
from upbit_auto_trading.config.database_paths import (
    SETTINGS_DB_PATH, STRATEGIES_DB_PATH, MARKET_DATA_DB_PATH,
    TableMappings
)

# 특정 테이블의 DB 경로 조회
db_path = TableMappings.get_db_for_table('trading_conditions')
# → "upbit_auto_trading/data/strategies.sqlite3"

# 연결 문자열 생성
connection_string = get_connection_string('tv_trading_variables')
# → "upbit_auto_trading/data/settings.sqlite3"
```

#### 테이블 분류 원칙
```markdown
📊 Settings DB (settings.sqlite3):
- cfg_*: 앱 설정 (cfg_app_settings, cfg_system_settings)
- tv_*: Trading Variables 시스템 (tv_trading_variables, tv_variable_parameters)
- sys_*: 시스템 관리 (sys_backup_info)

📈 Strategies DB (strategies.sqlite3):
- 사용자 생성 데이터 (trading_conditions, strategies, user_*)
- 실행 이력 (execution_history, simulation_*)
- 포지션 관리 (current_positions, portfolio_snapshots)

📉 Market Data DB (market_data.sqlite3):
- 시장 데이터 (candlestick_*, technical_*, real_time_*)
- 분석 결과 (screener_results, daily_market_analysis)
- 데이터 품질 (data_quality_logs, data_collection_status)
```

---

### 📄 config.yaml
**목적**: 기본 시스템 설정 및 환경 변수

```yaml
# 시스템 설정
system:
  version: "0.1.0-alpha"
  environment: "development"
  
# 데이터베이스 설정
database:
  auto_backup: true
  backup_interval: 24h
  
# UI 설정
ui:
  theme: "dark"
  chart_library: "matplotlib"
```

### 📊 database_config_legacy.yaml
**목적**: 레거시 데이터베이스 설정 (하위 호환성)

**Status**: Deprecated - `database_paths.py`로 이전됨
**유지 이유**: 기존 코드와의 호환성 보장

### 📝 logging_config.yaml
**목적**: 로깅 시스템 구성

```yaml
version: 1
formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
handlers:
  file:
    class: logging.FileHandler
    filename: logs/upbit_auto_trading.log
    formatter: standard
    
loggers:
  upbit_auto_trading:
    level: DEBUG
    handlers: [file]
```

### 🔧 Development Tools

#### mypy.ini
**목적**: Type checking 설정
```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

#### pytest.ini
**목적**: 테스트 프레임워크 설정
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### requirements.txt
**목적**: Config 모듈 전용 의존성
```txt
PyYAML>=6.0
pathlib>=1.0
```

#### setup.py
**목적**: Config 모듈 패키징 설정

---

## 🔄 설정 관리 워크플로우

### 💼 개발자 사용법
1. **DB 경로 필요시**: `database_paths.py`에서 경로 상수 import
2. **새 테이블 추가시**: `TableMappings` 클래스에 매핑 추가
3. **환경 설정 변경시**: `config.yaml` 수정
4. **로그 레벨 조정시**: `logging_config.yaml` 수정

### 🧪 테스트 방법
```powershell
# 1. 기본 설정 검증
python -c "from upbit_auto_trading.config.database_paths import *; print('✅ 설정 로드 성공')"

# 2. 테이블 매핑 테스트
python upbit_auto_trading/config/database_paths.py

# 3. Super 도구로 종합 검증
python tools/super_db_debug_path_mapping.py
```

### ⚠️ 중요 사항

#### 🔒 보안 고려사항
- **민감 정보 제외**: API 키, 패스워드 등은 별도 보안 폴더에 저장
- **환경별 분리**: 개발/운영 환경 설정 명확히 구분
- **기본값 안전성**: 모든 설정에 안전한 기본값 제공

#### 📋 변경 관리 원칙
- **하위 호환성**: 기존 코드 영향 최소화
- **점진적 마이그레이션**: 레거시 → 신규 구조로 단계적 전환
- **중앙 집중화**: 분산된 설정을 config 폴더로 통합

#### 🔧 개발 가이드라인
- **새 설정 추가시**: 기본값, 타입 힌트, 문서화 필수
- **경로 변경시**: `TableMappings` 업데이트 및 영향도 분석
- **설정 삭제시**: Deprecated 표시 후 충분한 유예 기간 제공

---

## 🎯 Future Roadmap

### Phase 1: 완료 ✅
- 3-Database 아키텍처 경로 시스템 구축
- 53개 테이블 매핑 완성
- 레거시 호환성 지원

### Phase 2: 계획 중
- 환경별 설정 프로파일 시스템
- 동적 설정 변경 및 핫 리로드
- 설정 검증 및 자동 복구 시스템

### Phase 3: 확장 계획
- 클라우드 설정 동기화
- 설정 변경 이력 관리
- GUI 기반 설정 편집기

---

## 🚀 Quick Start

```python
# 1. 기본 임포트
from upbit_auto_trading.config.database_paths import (
    SETTINGS_DB_PATH, STRATEGIES_DB_PATH, MARKET_DATA_DB_PATH,
    TableMappings, get_connection_string
)

# 2. 테이블별 DB 경로 조회
trading_conditions_db = TableMappings.get_db_for_table('trading_conditions')
tv_variables_db = TableMappings.get_db_for_table('tv_trading_variables')

# 3. 연결 문자열 생성
conn_string = get_connection_string('strategies')

# 4. 현재 설정 확인
current_config = get_current_config()
print(f"Settings DB: {current_config['settings_db']}")
print(f"Strategies DB: {current_config['strategies_db']}")
print(f"Market Data DB: {current_config['market_data_db']}")
```

---

💡 **Config 시스템은 전체 프로젝트의 안정성과 확장성을 보장하는 핵심 인프라입니다!**

📅 **작성일**: 2025-08-01  
📝 **작성자**: Upbit Auto Trading Team  
🔄 **최종 업데이트**: database_paths.py 3-Database 아키텍처 완성

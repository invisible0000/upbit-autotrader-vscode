# 🔍 현재 아키텍처 분석 보고서

## 📋 분석 개요

본 문서는 업비트 자동매매 시스템의 현재 개발 상황을 폴더 구조, 코드 구조, 기능 연결성 관점에서 분석한 보고서입니다. 리팩토링 계획 수립을 위한 기초 자료로 활용됩니다.

**분석 일자**: 2025-08-03  
**분석 범위**: upbit_auto_trading 폴더 전체  
**주요 이슈**: UI 레이어에 비즈니스 로직과 데이터 접근 로직 혼재

## 🏗️ 현재 폴더 구조 분석

### 최상위 구조
```
upbit_auto_trading/
├── business_logic/     # ✅ 분리된 비즈니스 로직 (양호)
├── config/            # ✅ 설정 관리 (양호)
├── core/              # ⚠️ 핵심 유틸리티 (미흡)
├── data_layer/        # ✅ 데이터 접근 계층 (양호)
├── logging/           # ✅ 로깅 시스템 (양호)
├── tests/             # ✅ 테스트 코드 (양호)
├── ui/                # ❌ 모든 기능이 UI에 집중 (문제)
├── README.md
├── __init__.py
└── __main__.py
```

### UI 폴더 상세 구조 (문제 영역)
```
ui/
├── desktop/           # 데스크톱 UI 메인
│   ├── screens/       # 화면별 구현
│   │   ├── chart_view/              # 차트 뷰 화면
│   │   ├── live_trading/            # 실시간 거래 화면
│   │   ├── monitoring_alerts/       # 모니터링 알림 화면
│   │   ├── portfolio_configuration/ # 포트폴리오 설정 화면
│   │   ├── settings/               # 설정 화면
│   │   └── strategy_management/     # 전략 관리 화면 (핵심)
│   ├── common/        # 공통 UI 컴포넌트
│   ├── components/    # 재사용 UI 컴포넌트
│   ├── factories/     # UI 팩토리 패턴
│   ├── models/        # UI 모델 (데이터와 혼재)
│   └── utils/         # UI 유틸리티
├── cli/               # CLI 인터페이스
└── web/               # 웹 인터페이스 (미구현)
```

### Business Logic 폴더 구조 (양호)
```
business_logic/
├── backtester/        # 백테스팅 엔진
├── monitoring/        # 모니터링 로직
├── portfolio/         # 포트폴리오 관리
├── screener/          # 종목 스크리닝
├── strategy/          # 전략 실행 엔진
└── trader/            # 거래 실행 로직
```

### Data Layer 구조 (양호)
```
data_layer/
├── processors/        # 데이터 처리기
├── storage/          # 데이터 저장소
└── strategy_models.py # 전략 모델
```

## 🚨 주요 아키텍처 문제점

### 1. UI-Business Logic 혼재 (심각)

#### 문제 사례 1: Strategy Management
```python
# ❌ 문제: UI 컴포넌트에 비즈니스 로직 직접 구현
# 파일: ui/desktop/screens/strategy_management/strategy_maker/strategy_maker.py

class StrategyMaker(QWidget):
    def __init__(self):
        # UI 초기화와 비즈니스 로직이 혼재
        self.setup_ui()
        self.load_strategies()  # DB 접근
        self.init_validation() # 비즈니스 룰
        
    def save_strategy(self):
        # UI에서 직접 DB 저장 로직 수행
        # 검증 로직도 UI 레이어에서 처리
```

#### 문제 사례 2: Trigger Builder
```python
# ❌ 문제: 조건 생성 로직이 UI 컴포넌트에 직접 구현
# 파일: ui/desktop/screens/strategy_management/trigger_builder/

class TriggerBuilderScreen(QWidget):
    def create_condition(self):
        # 복잡한 비즈니스 로직이 UI에 위치
        # 호환성 검증, 조건 생성 등
```

#### 문제 사례 3: Chart View
```python
# ❌ 문제: 차트 데이터 처리 로직이 UI에 혼재
# 파일: ui/desktop/screens/chart_view/

class ChartViewScreen(QWidget):
    def update_chart(self):
        # 시장 데이터 가져오기
        # 지표 계산
        # 차트 렌더링
        # 모든 로직이 UI 컴포넌트에 집중
```

### 2. 데이터 접근 패턴 문제 (중간)

#### 직접 DB 접근
```python
# ❌ UI에서 직접 SQLite 접근
import sqlite3
conn = sqlite3.connect('data/strategies.sqlite3')
# UI 컴포넌트에서 직접 SQL 실행
```

#### Repository 패턴 미적용
- 데이터 접근 로직이 각 UI 컴포넌트에 분산
- 동일한 데이터 접근 코드 중복
- 데이터 소스 변경 시 영향 범위 광범위

### 3. 의존성 관리 문제 (중간)

#### 순환 의존성
```python
# UI → Business Logic → Data Layer → UI
# 일부 컴포넌트에서 순환 참조 발생
```

#### 하드 코딩된 의존성
```python
# ❌ 하드 코딩된 파일 경로
DATABASE_PATH = "data/strategies.sqlite3"
# ❌ 직접적인 클래스 의존성
from ui.desktop.components import SomeWidget
```

## 📊 현재 기능별 구현 현황

### ✅ 잘 분리된 기능들

#### 1. 로깅 시스템
```python
# ✅ 양호: 독립적인 로깅 시스템
logging/
├── smart_log_manager.py  # 스마트 로그 관리
└── __init__.py          # 통합 로거
```

#### 2. 설정 관리
```python
# ✅ 양호: 설정 파일 중앙 관리
config/
├── config.yaml
├── database_config.yaml
└── simple_paths.py
```

#### 3. 데이터 스토리지
```python
# ✅ 양호: 데이터 접근 계층 분리
data_layer/storage/
├── database_manager.py      # DB 관리자
├── market_data_storage.py   # 시장 데이터
└── migration_manager.py     # DB 마이그레이션
```

### ❌ 문제가 있는 기능들

#### 1. 전략 관리 (Strategy Management)
- **현재 위치**: `ui/desktop/screens/strategy_management/`
- **문제**: 전략 생성, 검증, 저장 로직이 UI에 혼재
- **영향도**: 높음 (핵심 기능)

#### 2. 트리거 빌더 (Trigger Builder)
- **현재 위치**: `ui/desktop/screens/strategy_management/trigger_builder/`
- **문제**: 조건 생성, 호환성 검증 로직이 UI 컴포넌트에 직접 구현
- **영향도**: 높음 (핵심 기능)

#### 3. 차트 뷰 (Chart View)
- **현재 위치**: `ui/desktop/screens/chart_view/`
- **문제**: 시장 데이터 처리, 지표 계산이 UI에서 수행
- **영향도**: 중간

#### 4. 실시간 거래 (Live Trading)
- **현재 위치**: `ui/desktop/screens/live_trading/`
- **문제**: 주문 실행 로직이 UI와 혼재
- **영향도**: 높음 (보안/안정성)

#### 5. 포트폴리오 관리
- **현재 위치**: `ui/desktop/screens/portfolio_configuration/`
- **문제**: 포트폴리오 계산 로직이 UI에 포함
- **영향도**: 중간

## 🔗 현재 컴포넌트 간 의존성 분석

### 의존성 매트릭스
```
           UI  BL  DL  Config  Core
UI         ●   ●   ●    ●      ●
BL         ●   ●   ●    ●      ●
DL         ×   ×   ●    ●      ●
Config     ×   ×   ×    ●      ×
Core       ×   ×   ×    ×      ●

● = 의존성 있음 (일부 문제)
× = 의존성 없음 (양호)
```

### 주요 의존성 문제
1. **UI → Business Logic**: 과도한 직접 호출
2. **Business Logic → UI**: 일부 콜백에서 UI 직접 참조
3. **UI → Data Layer**: Repository 패턴 없이 직접 접근

## 📈 코드 메트릭 분석

### 파일 수 통계
- **전체 Python 파일**: 410개 (대규모)
- **UI 레이어 파일**: 약 250개 (60%, 과도)
- **Business Logic 파일**: 약 80개 (20%, 부족)
- **Data Layer 파일**: 약 50개 (12%, 적정)
- **기타 (Config, Core, Tests)**: 약 30개 (8%, 적정)

### 코드 복잡도 이슈
- **평균 클래스 크기**: 200-500줄 (큰 편)
- **UI 컴포넌트 크기**: 일부 1000줄+ (과도)
- **함수당 평균 줄 수**: 20-50줄 (적정)

## 🎯 리팩토링 우선순위 분석

### 우선순위 1 (긴급): 핵심 비즈니스 로직 분리
1. **Strategy Management System**
   - 전략 생성/검증/저장 로직 분리
   - Service 레이어 신설

2. **Trigger Builder System**
   - 조건 생성 엔진 분리
   - 호환성 검증 서비스 분리

### 우선순위 2 (중요): 데이터 접근 패턴 개선
1. **Repository 패턴 도입**
   - 전략 Repository
   - 시장 데이터 Repository
   - 사용자 설정 Repository

2. **Service 레이어 구축**
   - 전략 서비스
   - 백테스팅 서비스
   - 거래 서비스

### 우선순위 3 (보통): UI 아키텍처 개선
1. **MVP/MVVM 패턴 도입**
2. **의존성 주입 시스템**
3. **이벤트 기반 통신**

## 💡 권장 해결 방향

### 1. 계층별 책임 재정의
```
├── Presentation Layer (UI)
│   ├── Views (현재 Screens)
│   ├── Presenters/ViewModels
│   └── UI Components
├── Application Layer (Services)
│   ├── Strategy Services
│   ├── Trading Services
│   └── Portfolio Services
├── Domain Layer (Business Logic)
│   ├── Entities
│   ├── Value Objects
│   └── Domain Services
└── Infrastructure Layer (Data)
    ├── Repositories
    ├── External APIs
    └── Database Access
```

### 2. 단계적 리팩토링 전략
1. **Phase 1**: 핵심 Service 레이어 구축
2. **Phase 2**: Repository 패턴 도입
3. **Phase 3**: UI 레이어 재구성
4. **Phase 4**: 의존성 주입 시스템 도입

## 📊 현재 상태 요약

### 강점
- ✅ 데이터 레이어 기본 구조 양호
- ✅ 로깅 시스템 잘 구성됨
- ✅ 설정 관리 체계적
- ✅ 기본 3-DB 아키텍처 적용

### 약점
- ❌ UI에 비즈니스 로직 과도 집중
- ❌ Repository 패턴 미적용
- ❌ 서비스 레이어 부재
- ❌ 순환 의존성 존재

### 기회
- 🎯 명확한 도메인 모델 존재
- 🎯 테스트 코드 기반 마련
- 🎯 문서화 체계 확립

### 위험
- ⚠️ 코드 복잡도 증가
- ⚠️ 유지보수성 저하
- ⚠️ 테스트 어려움 증가

---

**다음 문서**: [전문가 설계 문서 종합](02_EXPERT_DESIGN_SYNTHESIS.md)

# 🏗️ 프로젝트 아키텍처 개요

## 📋 핵심 아키텍처 원칙

**업비트 자동매매 시스템**은 **컴포넌트 기반 모듈러 아키텍처**를 기반으로 구축되었습니다.

### 🎯 설계 철학
- **컴포넌트 기반**: 재사용 가능한 독립적 모듈
- **계층 분리**: UI → 비즈니스 로직 → 데이터 레이어
- **테스트 중심**: 모든 컴포넌트는 단위 테스트 가능
- **에러 투명성**: 폴백 코드로 문제를 숨기지 않음

## 🏛️ 전체 구조

```
upbit_auto_trading/
├── 📁 core/                    # 핵심 유틸리티
│   ├── ensure_directory.py     # 디렉토리 관리
│   └── path_utils.py          # 경로 유틸리티
├── 📁 ui/desktop/             # PyQt6 GUI
│   ├── main_window.py         # 메인 윈도우
│   └── screens/               # 화면별 구현 (components 폴더로 UI 요소 관리)
├── 📁 business_logic/         # 비즈니스 로직 (분리 진행중)
├── 📁 data_layer/             # 데이터베이스 관리
└── 📁 logging/                # 스마트 로깅 v3.0
```

## 🎨 UI 아키텍처 (PyQt6)

### 메인 화면 구조
```
MainWindow
├── 📊 시장 분석 탭
├── ⚙️ 전략 관리 탭
│   ├── 트리거 빌더      # 조건 생성 시스템
│   ├── 전략 메이커      # 매매 전략 조합
│   └── 백테스팅        # 성능 검증
└── 🔧 설정 탭
    ├── API 키 관리
    ├── 데이터베이스 설정
    └── 로깅 설정
```

### 컴포넌트 통신 패턴
- **시그널/슬롯**: PyQt6 기본 통신 방식
- **이벤트 버스**: 전역 상태 관리
- **의존성 주입**: 테스트 가능한 설계

## 🗄️ 데이터베이스 아키텍처 (3-DB 구조)

### 1. `settings.sqlite3` - 구조 정의
- 트레이딩 변수 정의 (tv_trading_variables)
- 파라미터 스키마 (tv_variable_parameters)  
- 카테고리 분류 (tv_indicator_categories)
- 시스템 설정

### 2. `strategies.sqlite3` - 전략 인스턴스
- 사용자 생성 전략
- 조건 조합 규칙
- 백테스팅 결과

### 3. `market_data.sqlite3` - 시장 데이터
- 실시간 가격 데이터
- 기술적 지표 캐시
- 거래량 정보

**관리 방식**: `data_info/` 폴더의 .yaml 및 .sql 파일을 통해 스키마와 데이터 구조 관리

## 🧩 핵심 시스템 구성

### 트리거 빌더
- **목적**: 조건부 매매 신호 생성
- **특징**: 드래그앤드롭 UI, 3중 카테고리 시스템
- **호환성**: purpose_category, chart_category, comparison_group

### 전략 메이커  
- **진입 전략**: 6종 (이평선교차, RSI, 볼린저밴드 등)
- **관리 전략**: 6종 (물타기, 불타기, 트레일링스탑 등)
- **상태 관리**: 진입대기 ↔ 포지션관리

### 백테스팅 엔진
- **데이터**: 1년치 분봉 기준
- **성능**: 5분 내 처리 목표
- **지표**: 수익률, MDD, 샤프비율, 승률

**핵심 검증 기준**: [기본 7규칙 전략](basic_7_rule_strategy_guide.md)을 완전히 구현할 수 있어야 함

## 🔧 로깅 시스템 v3.0

### 환경변수 기반 제어
```python
# 로그 컨텍스트 설정
UPBIT_LOG_CONTEXT=strategy_maker,trigger_builder

# 로그 스코프 설정  
UPBIT_LOG_SCOPE=debug,performance
```

### 로그 범람 방지
- 동일 메시지 제한
- 컴포넌트별 선택적 로깅
- 성능 모니터링

## 🚀 배포 아키텍처

### 현재 지원 모드
- **개발모드**: `python run_desktop_ui.py`
- **Git Clone**: 소스코드 기반 설치

### 계획 중
- **CLI 모드**: 헤드리스 실행
- **포터블 모드**: 실행파일 배포

## 🔒 보안 아키텍처

### API 키 관리
- 환경변수 기반 저장
- 암호화된 로컬 캐시
- 하드코딩 절대 금지

### 데이터 보안
- `.gitignore`로 개인 데이터 보호
- 로그에서 민감 정보 마스킹
- 외부 API 호출 제한

## 📚 관련 문서

- [전략 시스템 명세](STRATEGY_SPECIFICATIONS.md)
- [데이터베이스 스키마](DB_SCHEMA.md)
- [개발 가이드](DEVELOPMENT_GUIDE.md)
- [트리거 빌더 상세](TRIGGER_BUILDER_GUIDE.md)

# 데이터베이스 설계 가이드

## 🗄️ DB 표준 규칙
- **확장자**: `.sqlite3` 필수
- **위치**: `data/` 폴더 내
- **구조**: 2개 DB 분리

## 📊 DB 구성
### `data/app_settings.sqlite3` (프로그램 설정)
#### 기본 설정 테이블
- `trading_conditions` - 거래 조건 (트리거 빌더 조건들)
- `component_strategy` - 전략 정보  
- `strategy_execution` - 실행 기록
- `system_settings` - 시스템 설정

#### 트리거 빌더 관련 테이블 (새로 추가) ⭐
- `trading_variables` - 트레이딩 변수 정의 (SMA, RSI, MACD 등)
- `variable_parameters` - 변수별 파라미터 정의 (period, source, multiplier 등)
- `variable_categories` - 변수 카테고리 정의 (purpose, chart, comparison)
- `compatibility_rules` - 변수 간 호환성 규칙
- `schema_version` - 스키마 버전 관리

#### 주요 특징
- **3중 카테고리 시스템**: purpose_category, chart_category, comparison_group
- **동적 파라미터 관리**: 변수별 맞춤형 파라미터 자동 생성
- **호환성 자동 검증**: 의미있는 변수 조합만 허용

### `data/market_data.sqlite3` (백테스팅 데이터)
- `candle_data` - 캔들 데이터
- `ticker_data` - 티커 정보
- `orderbook_data` - 호가 데이터

## 🔧 설정 화면 연결
메인 설정 화면의 "데이터베이스 경로"는 `app_settings.sqlite3`를 지정하세요.

## 📋 스키마 마이그레이션
새로운 트리거 빌더 시스템 사용 시 자동으로 스키마가 업데이트됩니다:
```sql
-- 자동 실행되는 스키마 생성
source: upbit_auto_trading/utils/trading_variables/schema.sql
```

## 🎯 트리거 빌더 DB 활용
- **조건 저장**: `trading_conditions` 테이블에 JSON 형태로 저장
- **변수 관리**: `trading_variables` 테이블에서 사용 가능한 지표 관리
- **파라미터 정의**: `variable_parameters` 테이블에서 변수별 파라미터 스키마 정의
- **호환성 검증**: 3중 카테고리 시스템으로 자동 호환성 검증

관련 문서: `.vscode/guides/trigger-builder-system.md`

# LLM 에이전트 연속 개발을 위한 프로젝트 지도

이 문서는 AI 에이전트가 중단 없이 개발을 이어가기 위한 핵심 정보를 제공합니다.

## 🎯 프로젝트 개요
**업비트 자동매매 시스템** - 컴포넌트 기반 암호화폐 자동거래 및 백테스팅 플랫폼

### � 주요 아키텍처 변경 (2025-07-22)
- **기존**: 고정된 전략 클래스 → **신규**: 아토믹 컴포넌트 시스템
- **핵심**: 14개 트리거 + 3개 액션의 조합형 전략 구성
- **UI**: 드래그&드롭 기반 전략 메이커 (PyQt6)
- **데이터**: 레거시/컴포넌트 분리 모델

## �📁 핵심 문서 위치

### 필수 문서 (우선순위 순)
1. **컴포넌트 시스템**: `upbit_auto_trading/component_system/`
2. **전략 메이커 UI**: `strategy_maker_ui.py`
3. **아키텍처 문서**: `docs/STRATEGY_ARCHITECTURE_OVERVIEW.md`
4. **DB 스키마**: `reference/02_database_schema_specification_erd.md`

### 개발 가이드
- **컴포넌트 가이드**: `docs/INDIVIDUAL_STRATEGY_GUIDE.md`
- **UI 개발**: `docs/UI_DEVELOPMENT_GUIDE.md`
- **전략 조합**: `docs/STRATEGY_COMBINATION_GUIDE.md`

## 🔧 현재 시스템 상태 (2025-07-22)

### ✅ 완료된 핵심 컴포넌트
1. **아토믹 컴포넌트 시스템**
   - 14개 트리거: price/indicator/time/volume 카테고리
   - 3개 액션: market_buy/market_sell/position_close
   - 태그 기반 포지션 관리: AUTO/MANUAL/HYBRID/LOCKED

2. **전략 메이커 UI**
   - PyQt6 기반 드래그&드롭 인터페이스
   - 컴포넌트 팔레트 + 전략 캔버스 + 설정 패널
   - 메인 UI 첫 번째 탭으로 통합 완료

3. **데이터베이스 모델**
   - 기존 Strategy → LegacyStrategy 분리
   - 새로운 ComponentStrategy 모델
   - 마이그레이션 스크립트 준비

4. **관리 시스템**
   - ComponentStrategyManager 클래스
   - 템플릿 기반 전략 생성
   - 실행 기록 추적

### 🚀 즉시 개발 가능한 다음 단계
1. **데이터베이스 마이그레이션 실행**
2. **백테스팅 탭 구현**
3. **전략 분석 탭 구현**
4. **실시간 거래 엔진 연동**

### 🔧 에이전트 상태 관리

#### 중요 파일들
- **컴포넌트 정의**: `upbit_auto_trading/component_system/triggers/__init__.py`
- **전략 매니저**: `upbit_auto_trading/business_logic/component_strategy_manager.py`
- **UI 통합**: `upbit_auto_trading/ui/desktop/screens/strategy_management/strategy_management_screen.py`

## ⚡ 빠른 시작 가이드

### 에이전트 재시작 시 필수 체크리스트
1. **현재 UI 상태 확인**: `python run_desktop_ui.py` 실행
2. **전략 메이커 접근**: 매매 전략 관리 → 🎯 전략 메이커 탭
3. **컴포넌트 시스템 확인**: `upbit_auto_trading/component_system/` 구조 파악
4. **데이터베이스 상태**: 마이그레이션 필요 시 `component_migration.py` 사용

### 개발 세션 시작 순서
1. README_FIRST.md (이 문서) 확인
2. 전략 메이커 UI 테스트 및 피드백
3. 다음 우선순위 기능 개발 (백테스팅/분석 탭)
4. 변경사항 커밋 및 문서 업데이트

## 🎯 개발 철학 & 아키텍처 원칙

### 컴포넌트 설계 원칙
- **아토믹**: 각 컴포넌트는 독립적 기능 수행
- **조합성**: 트리거 + 액션의 자유로운 조합
- **확장성**: 새로운 컴포넌트 쉽게 추가 가능
- **안전성**: 태그 기반 포지션 관리로 충돌 방지

### UI/UX 철학
- **직관성**: 드래그&드롭으로 누구나 쉽게 전략 생성
- **시각성**: 컴포넌트 연결 상태 명확히 표시
- **실시간성**: 즉시 설정 변경 및 미리보기
- **접근성**: 초보자도 고급 전략 구성 가능

---
**⚠️ 중요**: 모든 개발 세션은 이 문서를 먼저 읽고 시작하세요!

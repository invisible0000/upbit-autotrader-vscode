# LLM 에이전트 연속 개발을 위한 프로젝트 지도

이 문서는 AI 에이전트가 중단 없이 개발을 이어가기 위한 핵심 정보를 제공합니다.

## 🎯 프로젝트 개요
**업비트 자동매매 시스템** - 원자적 전략 빌더 기반 암호화폐 자동거래 플랫폼

### 🚀 최신 상태 (2025-07-23)
- **Phase 1 완료**: 원자적 전략 빌더 시스템 구현 ✅
- **핵심**: Variable → Condition → Action → Rule → Strategy 원자적 구조
- **UI**: PyQt6 드래그&드롭 전략 빌더 (`ui_prototypes/`)
- **예제**: 7규칙 전략 템플릿 완성 (5분 내 구현 가능)
- **문서**: 완전한 사용자 가이드 및 개발 로드맵

## �📁 핵심 문서 위치

### 필수 문서 (우선순위 순)

1. **전략 빌더 시스템**: `ui_prototypes/atomic_strategy_components.py`
2. **전략 빌더 UI**: `ui_prototypes/atomic_strategy_builder_ui.py`
3. **7규칙 전략 예제**: `ui_prototypes/seven_rule_strategy_example.py`
4. **사용자 가이드**: `ui_prototypes/basic_7_rule_strategy_guide.md`
5. **개발 로드맵**: `STRATEGY_BUILDER_ROADMAP.md`

### 레거시 시스템

- **기존 컴포넌트**: `upbit_auto_trading/component_system/`
- **기존 UI**: `strategy_maker_ui.py`
- **아키텍처 문서**: `docs/STRATEGY_ARCHITECTURE_OVERVIEW.md`

## 🔧 현재 시스템 상태 (2025-07-23)

### ✅ Phase 1 완료: 원자적 전략 빌더

1. **핵심 컴포넌트 시스템** (`ui_prototypes/atomic_strategy_components.py`)
   - Variable, Condition, Action, Rule, Strategy 클래스 완성
   - StrategyBuilder 로직 구현 및 검증 시스템

2. **드래그&드롭 UI** (`ui_prototypes/atomic_strategy_builder_ui.py`)
   - PyQt6 기반 ComponentPalette + StrategyCanvas
   - 실시간 유효성 검사 및 시각적 피드백

3. **7규칙 전략 템플릿** (`ui_prototypes/seven_rule_strategy_example.py`)
   - RSI 진입부터 급등 감지까지 완전한 예제
   - 5분 내 구현 가능한 검증된 워크플로우

4. **완전한 문서화**
   - 사용자 가이드 (`ui_prototypes/basic_7_rule_strategy_guide.md`)
   - 개발 로드맵 (`STRATEGY_BUILDER_ROADMAP.md`)

### 🚀 다음 우선순위 (Phase 2)

1. **DB 스키마 설계** - 전략 영속성
2. **UI-DB 연동 구현** - 저장/로드 기능
3. **기존 시스템 통합** - 매매 전략 관리 탭
4. **백테스트 엔진 연동** - 성과 검증

## ⚡ 빠른 시작 가이드

### 에이전트 재시작 시 체크리스트

1. **전략 빌더 테스트**: `python ui_prototypes/atomic_strategy_builder_ui.py`
2. **7규칙 예제 확인**: `python ui_prototypes/seven_rule_strategy_example.py`
3. **사용자 가이드 검토**: `ui_prototypes/basic_7_rule_strategy_guide.md`
4. **다음 단계 확인**: `STRATEGY_BUILDER_ROADMAP.md`

### 개발 세션 시작 순서

1. README_FIRST.md (이 문서) 확인
2. 전략 빌더 UI 테스트 및 피드백
3. Phase 2 우선순위 기능 개발 (DB 설계)
4. 변경사항 커밋 및 문서 업데이트

## 🎯 핵심 설계 원칙

### 원자적 컴포넌트 철학

- **독립성**: 각 컴포넌트는 독립적 기능 수행
- **조합성**: Variable → Condition → Action → Rule → Strategy
- **확장성**: 새로운 컴포넌트 쉽게 추가 가능
- **직관성**: 드래그&드롭으로 누구나 쉽게 전략 생성

---
**⚠️ 중요**: 모든 개발 세션은 이 문서를 먼저 읽고 시작하세요!

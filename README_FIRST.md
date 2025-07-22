# LLM 에이전트 연속 개발을 위한 프로젝트 지도

이 문서는 AI 에이전트가 중단 없이 개발을 이어가기 위한 핵심 정보를 제공합니다.

## 🎯 프로젝트 개요
**업비트 자동매매 시스템** - 전략 기반 암호화폐 자동거래 및 백테스팅 플랫폼

## 📁 핵심 문서 위치

### 필수 문서 (우선순위 순)
1. **요구 명세서**: `.kiro/specs/upbit-auto-trading/tasks.md`
2. **현재 진행 작업**: `tasks/active/`
3. **완료된 작업**: `tasks/completed/`
4. **계획된 작업**: `tasks/planned/`

### 개발 가이드
- **아키텍처 문서**: `docs/STRATEGY_ARCHITECTURE_OVERVIEW.md`
- **DB 스키마**: `reference/02_database_schema_specification_erd.md`
- **API 문서**: `reference/03_api_specification.md`

## 🔧 에이전트 상태 관리

### 연속성 파일들
- **에이전트 상태**: `agent_state.json` (생성 필요)
- **인간 피드백**: `feedback_to_agent.md` (생성 필요)
- **월별 로그**: `logs/agent_log_2025-07.md` (생성 필요)

### 현재 개발 상태 (2025-07-22)
- ✅ **완료**: DB 마이그레이션 시스템, 전략 조합 데이터 모델, 전략 조합 UI 탭
- 🚀 **다음 단계**: 백테스트 연동, 실시간 거래 시스템
- 📊 **테스트 상태**: 6/6 통과 (조합 시스템)

## ⚡ 빠른 시작 가이드

1. `tasks/active/` 폴더 확인 → 진행 중인 작업 파악
2. `.kiro/specs/upbit-auto-trading/tasks.md` 확인 → 전체 계획 파악  
3. `agent_state.json` 읽기 → 이전 세션 상태 복원
4. `feedback_to_agent.md` 확인 → 인간 개발자 지시사항

## 🎯 개발 철학
- **TDD 우선**: 테스트 작성 → 구현 → 검증
- **점진적 발전**: 작은 단위로 나누어 안정적 진행
- **문서화 병행**: 코드와 함께 문서 업데이트
- **사용자 중심**: 직관적이고 실용적인 UI/UX

---
**⚠️ 중요**: 모든 개발 세션은 이 문서를 먼저 읽고 시작하세요!

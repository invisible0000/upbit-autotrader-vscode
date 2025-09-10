# Implementation Plan: OverlapAnalyzer v5.0 Infrastructure 레이어 모델 재개발

**Branch**: `003-candledataprovider-infrastructure` | **Date**: 2025-09-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-candledataprovider-infrastructure/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
OverlapAnalyzer v5.0의 완전 호환성을 유지하면서 Infrastructure 레이어에 업비트 API 완전 호환 스키마와 frozen dataclass 기반의 불변 모델을 구현. SqliteCandleRepository와의 100% 연동을 보장하며 200개 청크 분할 최적화와 Infrastructure 로깅 시스템을 적용한 DDD 준수 설계.

## Technical Context
**Language/Version**: Python 3.13
**Primary Dependencies**: dataclasses, datetime, enum (표준 라이브러리만), sqlite3, decimal
**Storage**: SQLite3 (market_data.sqlite3)
**Testing**: pytest
**Target Platform**: Windows PowerShell 환경
**Project Type**: single (DDD Infrastructure 레이어 확장)
**Performance Goals**: 200개 청크 분할 최적화, 메모리 효율성 유지
**Constraints**: OverlapAnalyzer v5.0 코드 변경 최소화, Domain 계층 의존성 없음
**Scale/Scope**: 기존 SqliteCandleRepository와 100% 호환, Infrastructure 로깅 필수

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (Infrastructure 레이어 모델만)
- Using framework directly? (표준 라이브러리 + sqlite3 직접 사용)
- Single data model? (frozen dataclass 기반 불변 모델)
- Avoiding patterns? (Repository Pattern 기존 유지, 새로운 패턴 최소화)

**Architecture**:
- EVERY feature as library? (Infrastructure 레이어 컴포넌트로 구현)
- Libraries listed: CandleDataProvider Infrastructure 모델
- CLI per library: N/A (Infrastructure 레이어 컴포넌트)
- Library docs: 기존 DDD 문서 체계 준수

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? (테스트 우선 작성)
- Git commits show tests before implementation? (TDD 준수)
- Order: Contract→Integration→E2E→Unit strictly followed?
- Real dependencies used? (실제 SQLite DB 사용)
- Integration tests for: SqliteCandleRepository 연동, OverlapAnalyzer v5.0 호환성
- FORBIDDEN: Implementation before test, skipping RED phase

**Observability**:
- Structured logging included? (Infrastructure 로깅 필수: create_component_logger)
- Frontend logs → backend? (Infrastructure 레이어 로깅)
- Error context sufficient? (상세 에러 컨텍스트 포함)

**Versioning**:
- Version number assigned? (Infrastructure v5.0 호환)
- BUILD increments on every change? (패치 버전 관리)
- Breaking changes handled? (OverlapAnalyzer v5.0 완전 호환성 보장)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
### Source Code (repository root)
```
upbit_auto_trading/
├── infrastructure/
│   ├── data_models/
│   │   ├── candle/
│   │   │   ├── __init__.py
│   │   │   ├── upbit_candle_model.py      # 업비트 API 호환 모델
│   │   │   ├── candle_data_types.py       # 캔들 데이터 타입 정의
│   │   │   └── validation_rules.py        # 데이터 검증 규칙
│   │   └── __init__.py
│   ├── repositories/
│   │   └── sqlite_candle_repository.py    # 기존 Repository (변경 최소화)
│   └── logging/
└── tests/
    ├── infrastructure/
    │   ├── data_models/
    │   │   └── candle/
    │   └── repositories/
    └── integration/
        └── overlap_analyzer_compatibility/
```

**Structure Decision**: Option 1 (Single project) - 기존 DDD 구조 확장

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (data-model.md, contracts/, quickstart.md)
- OverlapAnalyzer v5.0 호환성 → integration test task
- 각 contract → contract test task [P]
- 각 entity (UpbitCandleModel, TimeChunk) → model creation task [P]
- Infrastructure 로깅 → logging integration task
- Quickstart 검증 시나리오 → validation test task

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Data models → Validation rules → Response models → Integration tests
- Mark [P] for parallel execution (independent files)
- Contract tests first: overlap_analyzer_compatibility, upbit_api_schema
- Model implementation: UpbitCandleModel → CandleDataTypes → ValidationRules
- Response models: CandleDataResponse → TimeChunk → Cache models

**Estimated Output**: 18-22 numbered, ordered tasks in tasks.md

**Task Categories**:
1. **Contract Tests (Tasks 1-3)**: 호환성 계약 검증 테스트 [P]
2. **Core Models (Tasks 4-8)**: 핵심 데이터 모델 구현 [P]
3. **Support Models (Tasks 9-12)**: 지원 모델 및 유틸리티 [P]
4. **Integration Tests (Tasks 13-16)**: OverlapAnalyzer v5.0 통합
5. **Performance & Validation (Tasks 17-20)**: 성능 최적화 및 검증

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) ✅ 2025-09-10
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*

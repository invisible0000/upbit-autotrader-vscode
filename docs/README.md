# 📚 업비트 자동매매 시스템 문서 가이드

## 🎯 핵심 문서 (12개)

### 필수 개발 기준 ⭐

1. **[PROJECT_SPECIFICATIONS.md](PROJECT_SPECIFICATIONS.md)** - 프로젝트 핵심 명세
2. **[BASIC_7_RULE_STRATEGY_GUIDE.md](BASIC_7_RULE_STRATEGY_GUIDE.md)** - 시스템 검증 기준
3. **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - 통합 개발 가이드 (NEW!)
4. **[COMPLEX_SYSTEM_TESTING_GUIDE.md](COMPLEX_SYSTEM_TESTING_GUIDE.md)** - 복잡한 백본 시스템 테스트 방법론 (NEW!)

### 시스템 설계

5. **[ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md)** - DDD 아키텍처 설계 (NEW!)
6. **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** - 전략 시스템 완전 가이드 (NEW!)
7. **[UI_GUIDE.md](UI_GUIDE.md)** - UI 시스템 완전 가이드 (NEW!)

### 핵심 기능

8. **[TRIGGER_BUILDER_GUIDE.md](TRIGGER_BUILDER_GUIDE.md)** - 트리거 빌더 시스템
9. **[DB_SCHEMA.md](DB_SCHEMA.md)** - 데이터베이스 스키마
10. **[UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)** - 통합 설정 관리

### 아키텍처 전문 문서 🏗️

1. **[DEPENDENCY_INJECTION_ARCHITECTURE.md](DEPENDENCY_INJECTION_ARCHITECTURE.md)** - 의존성 주입 아키텍처 완전 가이드 (NEW!)
2. **[DEPENDENCY_INJECTION_QUICK_GUIDE.md](DEPENDENCY_INJECTION_QUICK_GUIDE.md)** - 의존성 주입 실용 가이드 (NEW!)
3. **[QASYNC_EVENT_ARCHITECTURE.md](QASYNC_EVENT_ARCHITECTURE.md)** - QAsync 이벤트 기반 아키텍처 가이드 (NEW!)
4. **[QASYNC_EVENT_QUICK_GUIDE.md](QASYNC_EVENT_QUICK_GUIDE.md)** - QAsync 이벤트 실용 가이드 (NEW!)

### 기여 가이드

1. **[CONTRIBUTING.md](CONTRIBUTING.md)** - 기여 방법 및 규칙
2. **api_key_secure/** - API 키 보안 관리

## 🚀 빠른 시작

### 개발자

```powershell
# 1. 애플리케이션 실행
python run_desktop_ui.py

# 2. 기본 7규칙 전략 검증
# → 전략 관리 → 트리거 빌더에서 7규칙 구성 테스트

# 3. 개발 시작
# → DEVELOPMENT_GUIDE.md 체크리스트 확인
```

### 시스템 이해

1. **ARCHITECTURE_GUIDE.md** - 전체 시스템 구조
2. **STRATEGY_GUIDE.md** - 매매 전략 시스템
3. **UI_GUIDE.md** - 사용자 인터페이스

## 📋 작업별 문서 참조

### 매매 전략 개발

- STRATEGY_GUIDE.md → BASIC_7_RULE_STRATEGY_GUIDE.md → TRIGGER_BUILDER_GUIDE.md

### UI 개발

- UI_GUIDE.md → ARCHITECTURE_GUIDE.md → DEVELOPMENT_GUIDE.md

### 설정/구성 관리

- UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md → DB_SCHEMA.md

### 아키텍처 개발

- **DEPENDENCY_INJECTION_ARCHITECTURE.md** → **DEPENDENCY_INJECTION_QUICK_GUIDE.md**
- **QASYNC_EVENT_ARCHITECTURE.md** → **QASYNC_EVENT_QUICK_GUIDE.md**

### 마켓 데이터 백본 개발 ⚡

- **[market_data_backbone_v2/](market_data_backbone_v2/)** - MarketDataBackbone V2 + UnifiedAPI 완전 구현 (NEW! 🔥)
  - Phase 1.1~1.3 완료 (62/62 테스트) + Phase 2.1 UnifiedAPI 완료 (19/19 테스트)
  - 총 **81개 테스트 모두 통과** ✅
  - SmartChannelRouter, FieldMapper, ErrorUnifier 통합
  - 검증: `python demonstrate_phase_2_1_unified_api.py`

---

## 📝 아키텍처 문서 작성 가이드라인 (표준 패턴)

### 🎯 문서 구조 표준

모든 아키텍처 구조 관련 문서는 다음 패턴을 따라 작성:

#### 상세 가이드 문서 (`*_ARCHITECTURE.md`)

1. **개요** - 비개발자 친화적 설명 + 기술적 개요
2. **방법론 비교** - 다양한 접근법과 우리의 선택 이유
3. **구축 개요** - 파일 구조와 핵심 구성 요소
4. **적용 상황 가이드** - 필요/불필요 판단 기준
5. **체크포인트와 체크리스트** - 실용적 작업 가이드
6. **패턴 가이드** - 코드 템플릿과 표준 패턴
7. **전문가 조언** - 성공 요인, 안티패턴 회피, 장기 관점

#### 실용 가이드 문서 (`*_QUICK_GUIDE.md`)

1. **빠른 판단 체크리스트** - 필요/불필요 즉시 판단
2. **3단계 적용 패턴** - 최소 구현 단계
3. **계층별 적용 가이드** - 아키텍처 계층별 적용법
4. **즉시 적용 템플릿** - 복사 붙여넣기 가능한 코드
5. **문제 해결 가이드** - 흔한 오류와 해결책
6. **안티패턴 회피** - 절대 하지 말아야 할 것들
7. **성공 기준** - 올바른 구현 검증법

### 📋 작성 규칙

#### 상세 문서 규칙

- **길이**: 1000줄 이하 (에러 방지)
- **비개발자 설명**: "스마트 부품 상자" 같은 비유 활용
- **Mermaid 다이어그램**: 복잡한 구조는 시각화
- **코드 예시**: 올바른/잘못된 패턴 대비
- **참고 파일**: 실제 구현 파일 경로 명시

#### 실용 가이드 규칙

- **길이**: 300줄 이하 (빠른 참조)
- **LLM 최적화**: 적은 콘텍스트로 완벽한 판단 가능
- **체크리스트 중심**: [ ] 형태의 실행 가능한 항목
- **템플릿 제공**: 즉시 사용 가능한 코드 블록
- **핵심 원칙**: 마지막에 한 줄 핵심 메시지

### 🔄 업데이트 주기

- **새로운 아키텍처 패턴 도입시**: 상세+실용 가이드 쌍으로 작성
- **기존 패턴 변경시**: 두 문서 동시 업데이트
- **분기별 리뷰**: 실제 사용 패턴과 문서 일치성 검증

---

**🎯 성공 기준**: 기본 7규칙 전략이 트리거 빌더에서 완벽하게 동작!

**🔥 최신 성과**: MarketDataBackbone V2 + UnifiedAPI 통합 완성 (81/81 테스트 통과)

**💡 개발 철학**: DDD 아키텍처 + 에러 투명성 + 사용자 중심 UI + TDD 방법론

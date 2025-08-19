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

### 기여 가이드
11. **[CONTRIBUTING.md](CONTRIBUTING.md)** - 기여 방법 및 규칙
12. **api_key_secure/** - API 키 보안 관리

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

### 마켓 데이터 백본 개발 ⚡
- **[market_data_backbone_v2/](market_data_backbone_v2/)** - MarketDataBackbone V2 + UnifiedAPI 완전 구현 (NEW! 🔥)
  - Phase 1.1~1.3 완료 (62/62 테스트) + Phase 2.1 UnifiedAPI 완료 (19/19 테스트)
  - 총 **81개 테스트 모두 통과** ✅
  - SmartChannelRouter, FieldMapper, ErrorUnifier 통합
  - 검증: `python demonstrate_phase_2_1_unified_api.py`

---

**🎯 성공 기준**: 기본 7규칙 전략이 트리거 빌더에서 완벽하게 동작!

**🔥 최신 성과**: MarketDataBackbone V2 + UnifiedAPI 통합 완성 (81/81 테스트 통과)

**💡 개발 철학**: DDD 아키텍처 + 에러 투명성 + 사용자 중심 UI + TDD 방법론

# 📚 업비트 자동매매 시스템 문서 가이드

## 🎯 핵심 문서 (12개)

### 필수 개발 기준 ⭐
1. **[PROJECT_SPECIFICATIONS.md](PROJECT_SPECIFICATIONS.md)** - 프로젝트 핵심 명세
2. **[BASIC_7_RULE_STRATEGY_GUIDE.md](BASIC_7_RULE_STRATEGY_GUIDE.md)** - 시스템 검증 기준
3. **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - 통합 개발 가이드 (NEW!)

### 시스템 설계
4. **[ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md)** - DDD 아키텍처 설계 (NEW!)
5. **[STRATEGY_GUIDE.md](STRATEGY_GUIDE.md)** - 전략 시스템 완전 가이드 (NEW!)
6. **[UI_GUIDE.md](UI_GUIDE.md)** - UI 시스템 완전 가이드 (NEW!)

### 핵심 기능
7. **[TRIGGER_BUILDER_GUIDE.md](TRIGGER_BUILDER_GUIDE.md)** - 트리거 빌더 시스템
8. **[DB_SCHEMA.md](DB_SCHEMA.md)** - 데이터베이스 스키마
9. **[UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md](UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)** - 통합 설정 관리

### 기여 가이드
10. **[CONTRIBUTING.md](CONTRIBUTING.md)** - 기여 방법 및 규칙
11. **api_key_secure/** - API 키 보안 관리

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

---

**🎯 성공 기준**: 기본 7규칙 전략이 트리거 빌더에서 완벽하게 동작!

**💡 개발 철학**: DDD 아키텍처 + 에러 투명성 + 사용자 중심 UI

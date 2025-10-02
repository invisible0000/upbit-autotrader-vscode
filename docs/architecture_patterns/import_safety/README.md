# 🛡️ Import Safety Patterns

> Python/PyQt6 애플리케이션에서 안전한 Import 관리를 위한 아키텍처 패턴들

## 📋 **포함된 패턴**

### 🔄 [Lazy Loading + Dynamic Tab Replacement](./LAZY_LOADING_IMPORT_CHAIN_SAFETY.md)

- **목적**: Import 체인 의존성으로부터 컴포넌트 보호
- **핵심**: 탭 클릭시까지 Import 지연 + 동적 위젯 교체
- **발견**: TASK_20250930_01에서 API 키 설정 탭만 정상 동작한 이유 분석
- **적용**: PyQt6 탭 기반 UI, Presenter 계층 이동시

## 🎯 **패턴 적용 시나리오**

### ✅ **권장 상황**

- Presenter/Controller 레이어 리팩터링 시
- 대규모 Import 체인이 있는 모듈 구조 변경 시
- 탭/페이지 기반 UI에서 컴포넌트별 격리 필요시
- Legacy 코드와 신규 코드의 점진적 마이그레이션

### ⚠️ **주의 상황**

- 앱 시작시 즉시 로드가 필요한 핵심 컴포넌트
- 컴포넌트간 강한 의존성이 있는 구조
- 실시간 데이터 동기화가 필수인 경우

## 🔗 **관련 패턴**

- **[Factory Pattern](../factory_pattern/)**: 안전한 컴포넌트 생성
- **[MVP Assembly](../MVP_ASSEMBLY_GUIDE.md)**: MVP 구조 조립 가이드
- **[DDD Layer Design](../GUIDE_DDD레이어별설계패턴.md)**: 계층별 설계 패턴

---

**업데이트**: 2025년 9월 30일
**기여자**: GitHub Copilot Assistant
**프로젝트**: 업비트 자동매매 시스템

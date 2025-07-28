# 📊 TASK-20250728-02_Trading_Variables_Schema_Compatibility

## 🎯 태스크 개요
**태스크명**: 거래 변수 스키마 호환성 문제 해결  
**생성일**: 2025.07.28  
**우선순위**: 🟡 중간 (기능 제한적 영향)  
**예상 소요시간**: 2-3시간  
**의존성**: TASK-20250728-01 (데이터베이스 구조 통합) 완료 후

## 📋 문제 상황

### 🚨 발견된 문제
database structure unification 과정에서 거래 변수 관련 도구들의 스키마 호환성 문제 발견:

1. **trading_variables_cli.py 실행 시 오류**:
   ```
   ERROR: no such column: purpose_category
   ERROR: no such column: is_active
   ```

2. **원인 분석**:
   - 기존 `trading_variables.db` 스키마와 통합된 `settings.sqlite3`의 `tv_*` 테이블 스키마 차이
   - variable_manager.py가 원래 테이블 구조를 기대하지만 통합 DB에서는 `tv_` 접두사 사용
   - 일부 컬럼명이나 구조가 마이그레이션 과정에서 변경됨

## 🔍 영향 범위 분석

### 📁 영향받는 파일들
- `tools/trading_variables_cli.py` - 통계 기능 동작 불가
- `upbit_auto_trading/utils/trading_variables/variable_manager.py` - 스키마 불일치
- `upbit_auto_trading/utils/trading_variables/parameter_manager.py` - 의존성 문제
- `upbit_auto_trading/utils/trading_variables/cached_variable_manager.py` - 캐시 기능 문제

### 🎯 기능 영향도
- **🔴 높음**: CLI 도구 통계 기능 완전 중단
- **🟡 중간**: 거래 변수 관리 기능 일부 제한
- **🟢 낮음**: 메인 트레이딩 시스템은 정상 동작 (별도 시스템)

## 🚀 해결 방안 계획

### 📋 Phase 1: 스키마 분석 및 매핑
- [ ] 1.1. 기존 trading_variables.db 스키마 상세 분석
- [ ] 1.2. 통합 settings.sqlite3의 tv_* 테이블 스키마 분석
- [ ] 1.3. 스키마 차이점 문서화 및 매핑 테이블 작성
- [ ] 1.4. 필요한 컬럼 추가/수정 계획 수립

### 📋 Phase 2: 호환성 레이어 구현
- [ ] 2.1. 스키마 어댑터 클래스 설계
- [ ] 2.2. 테이블명/컬럼명 매핑 로직 구현
- [ ] 2.3. 레거시 호환성 유지 레이어 추가
- [ ] 2.4. 자동 스키마 마이그레이션 기능 구현

### 📋 Phase 3: 코드 수정 및 테스트
- [ ] 3.1. variable_manager.py 스키마 호환성 추가
- [ ] 3.2. trading_variables_cli.py 수정
- [ ] 3.3. 관련 매니저 클래스들 업데이트
- [ ] 3.4. 기능 테스트 및 검증

### 📋 Phase 4: 문서화 및 마이그레이션 가이드
- [ ] 4.1. 스키마 변경 내역 문서화
- [ ] 4.2. 호환성 가이드 작성
- [ ] 4.3. 트러블슈팅 가이드 추가

## 🎯 성공 기준

### ✅ 필수 목표
- trading_variables_cli.py stats 명령 정상 동작
- 기존 거래 변수 데이터 모두 접근 가능
- 새로운 통합 DB 구조에서 모든 기능 동작

### 🚀 추가 목표
- 레거시 DB와 신규 DB 간 자동 변환 기능
- 스키마 버전 관리 시스템 구축
- 향후 스키마 변경 시 호환성 보장 메커니즘

## ⚠️ 주의사항

### 🚨 리스크
- 거래 변수 데이터 손실 위험
- 기존 사용자 설정 호환성 문제
- 성능 영향 (어댑터 레이어로 인한)

### 🛡️ 완화 방안
- 작업 전 거래 변수 데이터 별도 백업
- 단계별 테스트로 기능 검증
- 롤백 계획 수립

## 📝 메모

이 문제는 데이터베이스 통합 작업의 부작용으로, 메인 트레이딩 시스템에는 영향이 없지만 관리 도구들의 완전한 기능을 위해서는 해결이 필요합니다.

우선순위는 메인 데이터베이스 구조 통합 완료 후로 설정하여, 핵심 기능 안정화를 먼저 완료하는 것이 좋겠습니다.

---

**생성일**: 2025.07.28  
**관련 태스크**: TASK-20250728-01_Database_Structure_Unification  
**담당자**: GitHub Copilot  

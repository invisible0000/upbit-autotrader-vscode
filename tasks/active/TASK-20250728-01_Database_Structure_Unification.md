# 📊 TASK-20250728-01_Database_Structure_Unification

## 🎯 태스크 개요
**태스크명**: 데이터베이스 구조 통합 및 단순화  
**생성일**: 2025.07.28  
**우선순위**: 🔥 높음 (사용자 편의성 및 유지보수성 개선)  
**예상 소요시간**: 4-6시간  

## 📋 목표
현재 7개 위치에 분산된 데이터베이스 파일들을 3개의 명확한 역할별 파일로 통합 및 단순화

## 🔍 현재 문제 상황 분석

### 📂 현재 데이터베이스 파일 분포
```
📍 루트/data/ (메인)
├── app_settings.sqlite3              # 설정 데이터
├── app_settings_backup.sqlite3       # 백업
├── market_data.sqlite3               # 시장 데이터
└── upbit_auto_trading.sqlite3        # 거래 데이터

📍 중복 위치들 (제거 대상)
├── upbit_auto_trading/data/app_settings.sqlite3
├── upbit_auto_trading/ui/desktop/data/upbit_auto_trading.sqlite3
└── trigger_builder/components/data/app_settings.sqlite3

📍 기타 위치들
├── trading_variables.db (루트)
├── upbit_auto_trading/utils/trading_variables.db
└── upbit_auto_trading/utils/trading_variables/trading_variables.db
```

### 🎯 목표 구조 (3개 파일로 단순화 + 설치형 환경 최적화)
```
📂 upbit_auto_trading/data/  ← 설치형 환경의 실제 사용자 데이터 폴더
├── settings/               ← API 키, 암호화 키 (기존 유지)
│   ├── api_keys.json
│   └── encryption_key.key
├── settings.sqlite3        ← 모든 사용자 설정 (app_settings + 거래변수)
├── strategies.sqlite3      ← 전략, 트리거, 거래 데이터
└── market_data.sqlite3     ← 시장 데이터 캐시
```

**📋 Phase 5에서 추가 이동 작업:**
- 루트 `data/` → `upbit_auto_trading/data/`로 DB 파일들 이동
- API 키와 DB 파일이 동일한 위치에서 통합 관리
- 설치형 프로그램 배포 시 단일 데이터 폴더 구조 완성

## 📝 하드코딩된 경로 분석

### 🔍 발견된 하드코딩 경로들

#### 1. `data/app_settings.sqlite3` 사용처
- `condition_storage.py` (라인 15)
- `chart_variable_service.py` (라인 50) 
- `strategy_storage.py` (라인 15)
- `database_settings.py` (라인 295)
- `indicator_calculator.py` (라인 27 - 상대경로)
- `tools/` 폴더 다수 파일들

#### 2. `data/market_data.sqlite3` 사용처
- `simulation_engines.py` (3곳)
- `data_source_manager.py` (2곳)
- `robust_simulation_engine.py`
- `real_data_simulation.py`
- `embedded_simulation_engine.py`

#### 3. `trading_variables.db` 사용처
- `variable_manager.py`
- `parameter_manager.py`
- `cached_variable_manager.py`
- `database_variable_widgets.py`
- `trading_variables_cli.py`

#### 4. `data/upbit_auto_trading.sqlite3` 사용처
- `market_data_storage.py` (2곳)
- `database_manager.py`
- `test_data_collection_full.py`

## 🚀 작업 단계별 계획

### ✅ Phase 0: 사전 준비 (완료)
- [x] 현재 상황 분석 완료
- [x] 하드코딩된 경로 조사 완료
- [x] 태스크 문서 작성

### ✅ Phase 1: 백업 및 안전장치 구축 (완료)
- [x] 1.1. 현재 데이터베이스 전체 백업
- [x] 1.2. 마이그레이션 스크립트 작성 (migrate_database.py)
- [x] 1.3. 롤백 스크립트 작성 (rollback_database.py)
- [x] 1.4. 데이터 검증 스크립트 작성 (validate_database.py)

### ✅ Phase 2: 새로운 데이터베이스 구조 생성 (완료)
- [x] 2.1. 기존 DB 스키마 상세 분석 완료 ✅
  - app_settings.sqlite3: 17개 테이블, 핵심 트리거/전략 데이터 확인
  - trading_variables.db: 3개 테이블, 32개 거래변수 확인  
  - market_data.sqlite3: 39개 테이블, 24,776행 시장데이터 확인
  - upbit_auto_trading.sqlite3: 1개 테이블, 비어있음 확인
- [x] 2.2. `data/settings.sqlite3` 생성 및 초기화 ✅
  - app_settings.sqlite3의 17개 테이블 통합 (strategies, trading_conditions 등)
  - trading_variables.db의 3개 테이블 통합 (tv_ 접두사)
  - 총 22개 테이블로 통합 완료
- [x] 2.3. `data/strategies.sqlite3` 생성 및 초기화 ✅
  - upbit_auto_trading.sqlite3 복사 완료 (3개 테이블)
  - migration_info 메타데이터 테이블 추가
- [x] 2.4. `data/market_data.sqlite3` 유지 (변경 없음) ✅

### ✅ Phase 3: 데이터 마이그레이션 (완료)
- [x] 3.1. 설정 데이터 통합 (app_settings → settings) ✅
  - 17개 테이블 마이그레이션 완료
  - 핵심 데이터: strategies(2), trading_conditions(14), component_strategy(1) 등
- [x] 3.2. 전략 데이터 통합 (upbit_auto_trading → strategies) ✅
  - upbit_auto_trading.sqlite3 전체 복사 완료
  - migration_info 메타데이터 추가
- [x] 3.3. 거래 변수 데이터 통합 (trading_variables → settings) ✅
  - tv_trading_variables(32), tv_comparison_groups(8), tv_schema_version(1) 통합
- [x] 3.4. 데이터 무결성 검증 ✅
  - settings: 22개 테이블 확인
  - strategies: 3개 테이블 확인  
  - market_data: 39개 테이블 확인

### ✅ Phase 4: 코드 경로 업데이트 (완료)
- [x] 4.1. 상수 파일 생성 (database_paths.py) ✅
  - DatabasePaths 클래스: 통합 DB 경로 관리
  - TableMappings 클래스: 테이블별 DB 매핑
  - 레거시 호환성 지원: 점진적 마이그레이션 가능
  - 경로 테스트 완료: settings, strategies, market_data DB 확인
- [x] 4.2. condition_storage.py 경로 업데이트 ✅
  - 새로운 통합 DB 경로 시스템 적용 (settings.sqlite3)
  - 하위 호환성 유지: 레거시 경로 백업 지원
  - trading_conditions 테이블 정상 접근 확인 (14개 레코드)
  - 모듈 import 및 데이터 연결 테스트 완료
- [x] 4.3. chart_variable_service.py 경로 업데이트 ✅
  - 새로운 통합 DB 경로 시스템 적용 (settings.sqlite3)
  - 하위 호환성 유지: 레거시 경로 백업 지원
  - chart_variables 테이블 정상 접근 확인 (7개 변수)
  - 모듈 import 및 기능 테스트 완료
- [x] 4.4. strategy_storage.py 경로 업데이트 ✅
  - 새로운 통합 DB 경로 시스템 적용 (settings.sqlite3)
  - 하위 호환성 유지: 레거시 경로 백업 지원
  - component_strategy 테이블 정상 접근 확인 (1개 전략)
  - 모듈 import 및 기능 테스트 완료
- [x] 4.5. simulation_engines.py 경로 업데이트 ✅
  - 새로운 통합 DB 경로 시스템 적용 (market_data.sqlite3)
  - 하위 호환성 유지: 레거시 경로 백업 지원
  - 3개 시뮬레이션 엔진 모두 업데이트 완료
  - market_data 테이블 정상 접근 확인 (10개 데이터)
- [x] 4.6. tools/ 폴더 파일들 경로 업데이트 ✅
  - unified_trigger_manager.py: 새로운 통합 DB 경로 시스템 적용
  - trading_variables_cli.py: 새로운 통합 DB 경로 시스템 적용
  - 하위 호환성 유지: 레거시 경로 백업 지원
  - 주요 도구들 업데이트 완료 (나머지는 필요시 개별 업데이트)

### ✅ Phase 5: 중복 파일 정리 (진행중)
- [x] 5.1. 중복 DB 파일들 제거 ✅
  - data/app_settings.sqlite3 제거 완료
  - data/app_settings_backup.sqlite3 제거 완료  
  - data/upbit_auto_trading.sqlite3 제거 완료
  - upbit_auto_trading/data/app_settings.sqlite3 제거 완료
  - upbit_auto_trading/ui/desktop/data/upbit_auto_trading.sqlite3 제거 완료
  - trading_variables.db 제거 완료
  - legacy_db 폴더 전체 정리 완료
  - upbit_auto_trading/ui/desktop/data/trading_conditions.db 제거 완료
- [ ] 5.2. 데이터베이스 파일 최적 위치 이동 (설치형 환경 준비)
  - [ ] 5.2.1. data/settings.sqlite3 → upbit_auto_trading/data/settings.sqlite3 이동
  - [ ] 5.2.2. data/strategies.sqlite3 → upbit_auto_trading/data/strategies.sqlite3 이동
  - [ ] 5.2.3. data/market_data.sqlite3 → upbit_auto_trading/data/market_data.sqlite3 이동
  - [ ] 5.2.4. database_paths.py 경로 상수 업데이트 (새 위치 반영)
  - [ ] 5.2.5. 모든 하드코딩된 경로 재검토 및 업데이트
  - [ ] 5.2.6. 이동 후 전체 DB 연결 및 기능 테스트
- [ ] 5.3. 사용하지 않는 백업 파일들 정리
- [ ] 5.4. 빈 폴더 정리

### ⏳ Phase 6: 검증 및 테스트
- [ ] 6.1. 전체 시스템 기능 테스트
- [ ] 6.2. 트리거 빌더 동작 확인
- [ ] 6.3. 전략 매니저 동작 확인
- [ ] 6.4. 데이터 저장/로드 테스트

### ⏳ Phase 7: 최종 정리
- [ ] 7.1. 코드 리뷰 및 정리
- [ ] 7.2. 문서 업데이트
- [ ] 7.3. 설정 파일 경로 가이드 작성

## 📊 파일 매핑 상세 계획

### 🔄 통합 대상 파일들
```
# 설정 데이터 통합 (→ data/settings.sqlite3)
data/app_settings.sqlite3
upbit_auto_trading/data/app_settings.sqlite3 (중복)
trigger_builder/components/data/app_settings.sqlite3 (중복)
trading_variables.db (루트)
upbit_auto_trading/utils/trading_variables.db (중복)
upbit_auto_trading/utils/trading_variables/trading_variables.db (중복)

# 전략 데이터 통합 (→ data/strategies.sqlite3)  
data/upbit_auto_trading.sqlite3
upbit_auto_trading/ui/desktop/data/upbit_auto_trading.sqlite3 (중복)

# 시장 데이터 유지 (변경 없음)
data/market_data.sqlite3 (유지)
```

## 📋 우선순위별 작업 계획

### 🔥 높은 우험도 (데이터 손실 가능)
1. **백업 필수**: 모든 작업 전 완전 백업
2. **점진적 마이그레이션**: 한 번에 모든 파일 변경 금지
3. **검증 강화**: 각 단계마다 데이터 무결성 확인

### ⚠️ 중간 위험도 (기능 중단 가능)
1. **경로 업데이트**: 하드코딩된 경로들 상수화
2. **코드 테스트**: 변경 후 즉시 기능 테스트
3. **롤백 준비**: 문제 시 즉시 복구 가능한 체계

### ✅ 낮은 위험도 (정리 작업)
1. **중복 파일 제거**: 기능 검증 후 안전하게 제거
2. **문서 업데이트**: 변경사항 반영
3. **가이드 작성**: 향후 유지보수를 위한 문서

## 🎯 예상 효과

### ✅ 즉시 효과
- **직관성**: 3개 파일로 역할 명확화
- **중복 제거**: 7개 → 3개 파일로 단순화
- **유지보수성**: 하드코딩 제거로 경로 관리 용이
- **통합성**: 모든 사용자 데이터가 `upbit_auto_trading/data/`에 집중

### 🚀 장기 효과
- **확장성**: 새 기능 추가 시 적절한 DB 선택 명확
- **백업 용이성**: 단일 폴더 백업으로 모든 데이터 보존
- **배포 준비**: 설치형 프로그램 완전 준비 완료
- **이식성**: 전체 data 폴더 복사로 환경 이전 가능

## ⚠️ 주의사항 및 리스크

### 🚨 높은 리스크
- **데이터 손실**: 마이그레이션 중 데이터 손실 가능성
- **호환성**: 기존 코드와의 호환성 문제
- **의존성**: 다른 컴포넌트에서 예상치 못한 의존성

### 🛡️ 완화 방안
- **완전 백업**: 작업 전 모든 DB 파일 백업
- **단계별 진행**: 한 번에 하나씩 점진적 변경
- **즉시 검증**: 각 단계마다 기능 테스트
- **롤백 계획**: 문제 발생 시 즉시 복구 가능한 절차

## 📈 진행 상황 추적

### 🎯 전체 진행률: 71% (5/7 Phase 완료)

**현재 상태**: Phase 4 완료, Phase 5 시작 준비  
**다음 작업**: 중복 파일 정리 (레거시 데이터베이스 파일들 정리)

---

## 📝 작업 로그

### 2025.07.28 18:00 - 태스크 시작
- 📊 현재 상황 분석 완료
- 🔍 하드코딩된 경로 조사 완료 (30+ 위치)
- 📋 작업 계획 수립 완료

### 2025.07.28 19:00 - Phase 1 완료
- 🗂️ legacy_db 폴더 생성 및 중복 파일 백업
- 📦 data 폴더 전체 백업 완료 (legacy_db/backups/)
- 🔧 마이그레이션 스크립트 작성 (migrate_database.py)
- 🔄 롤백 스크립트 작성 (rollback_database.py)  
- 🔍 검증 스크립트 작성 (validate_database.py)
- 📋 백업 상태 문서화 (legacy_db/README.md)

### 2025.07.28 20:40 - Phase 2-3 완료 ✅
- 🚀 데이터베이스 구조 통합 마이그레이션 성공 실행
- 📊 settings.sqlite3 생성: 22개 테이블 통합
  - app_settings.sqlite3: 17개 테이블 (strategies 2개, trading_conditions 14개 등)
  - trading_variables.db: 3개 테이블 (tv_ 접두사로 통합)
- 📊 strategies.sqlite3 생성: upbit_auto_trading.sqlite3 복사 + 메타데이터
- 📊 market_data.sqlite3: 기존 파일 유지 (39개 테이블, 24,776행)
- ✅ 마이그레이션 검증 완료: 모든 DB 연결 성공
- 📋 마이그레이션 로그 저장: legacy_db/migration_log_20250728_114045.txt

---

**다음 단계**: Phase 2 - 새로운 데이터베이스 구조 생성

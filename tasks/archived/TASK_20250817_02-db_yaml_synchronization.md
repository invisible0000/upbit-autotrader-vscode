# 📋 TASK_20250817_02-db_yaml_synchronization: DB-YAML 완전 동기화 시스템 구축

## 🎯 태스크 목표
DB를 원천(Single Source of Truth)으로 하여 YAML과의 완전한 동기화 시스템을 구축하고, 7규칙 전략이 완벽 동작하도록 데이터 일관성을 확보

## 📊 현재 상황 분석

### 핵심 문제점
1. **DB 불완전성**: 모든 tv_ 테이블 (tv_trading_variables, tv_variable_parameters, tv_* 전체)에 일부 변수 정보 누락
2. **YAML 불일치**: 형식 이상, 내용 누락, 구조적 불일치
3. **동기화 부재**: DB ↔ YAML 간 일관성 보장 메커니즘 없음
4. **메타변수 표시 실패**: 트리거 빌더에서 META_PYRAMID_TARGET, META_TRAILING_STOP 파라미터 미표시

### 사용 가능한 리소스
- **DB**: `settings.sqlite3` (tv_trading_variables, tv_variable_parameters)
- **원본 YAML**: `data_info/trading_variables/` (고품질, 보존됨)
- **수정 YAML**: `data_info/trading_variables_test/` (구문 정상, 활용 가능)

## 🔄 체계적 작업 절차 (필수 준수)

### 작업 진행 원칙
- **차분하고 신중한 접근**: 주위를 살펴보고 천천히 차근차근 진행
- **단계별 검증**: 각 단계마다 철저한 검토와 확인
- **안전성 우선**: 모든 변경사항에 대한 백업 및 롤백 준비

### 8단계 작업 절차 (모든 작업 항목에 적용)
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해하여 계획 수립
3. **🔄 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 코딩/분석/구현 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 문제 없으면 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 상세 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인 대기

### 작업 상태 마커 규칙
- **[ ]**: 미완료 (미시작 상태)
- **[-]**: 진행 중 (현재 작업 중)
- **[x]**: 완료 (작업 완료)

## 🏗️ 4단계 동기화 전략

### Phase 1: DB 현황 정밀 진단 [즉시 시작]
- [-] **1.1 DB 스키마 분석**
  - [x] 모든 tv_ 테이블 목록 완전 파악 (tv_trading_variables, tv_variable_parameters, tv_* 전체)
    **✅ 완료**: 6개 tv_ 테이블 발견 및 분석 완료
    - tv_trading_variables: 22개 변수 (완전 등록됨)
    - tv_variable_parameters: 30개 파라미터 (10개 변수에 분산)
    - tv_help_texts: 29개 도움말
    - tv_placeholder_texts: 27개 플레이스홀더
    - tv_variable_help_documents: 93개 문서
    - tv_schema_version: 1개 스키마 버전

  **🎯 핵심 발견**: 메타변수 완전 등록 상태
    - META_PYRAMID_TARGET: 4개 파라미터 (calculation_method, value, trail_direction, max_count)
    - META_TRAILING_STOP: 3개 파라미터 (calculation_method, value, trail_direction)

  **📊 변수 분류 현황**:
    - 목적별: price(4), state(4), capital(3), momentum(3), dynamic_management(2), trend(2), volatility(2), volume(2)
    - 차트별: subplot(13), overlay(7), adaptive(2)
    - 비교그룹별: price_comparable(8), capital_comparable(4), percentage_comparable(3), dynamic_target(2) 등

  - [x] 각 tv_ 테이블 구조 및 데이터 상태 상세 확인
    **✅ 완료**: 6개 TV 테이블 구조 완전 분석

    **🔧 테이블별 상세 정보**:
    - tv_trading_variables: 22개 변수, 완벽한 인덱스, 외래키 없음
    - tv_variable_parameters: 30개 파라미터, variable_id 외래키로 연결
    - tv_help_texts: 29개 도움말, variable_id 외래키로 연결
    - tv_placeholder_texts: 27개 플레이스홀더, variable_id 외래키로 연결
    - tv_variable_help_documents: 93개 문서, variable_id 외래키로 연결
    - tv_schema_version: 1개 스키마 버전 (1.0.0)

    **🔗 관계 분석**: 모든 테이블이 variable_id로 적절히 연결됨
    **⚠️ 데이터 일관성**: ✅ 문제 없음 (고아 레코드, 누락 참조 등 없음)

    **🎯 메타변수 완전성 확인**:
    - META_PYRAMID_TARGET: 4 파라미터 + 5 도움말 + 4 플레이스홀더 + 6 문서
    - META_TRAILING_STOP: 3 파라미터 + 4 도움말 + 3 플레이스홀더 + 6 문서

  - [x] 테이블 간 관계 및 외래키 분석
    **✅ 완료**: 외래키 및 관계 구조 완전 분석

    **🔗 외래키 관계**:
    - tv_variable_parameters.variable_id → tv_trading_variables.variable_id
    - tv_help_texts.variable_id → tv_trading_variables.variable_id
    - tv_placeholder_texts.variable_id → tv_trading_variables.variable_id
    - tv_variable_help_documents.variable_id → tv_trading_variables.variable_id

    **📊 관계 무결성**: 모든 외래키 참조가 유효함 (고아 레코드 없음)
    **🎯 중심 테이블**: tv_trading_variables가 허브 역할로 다른 모든 테이블과 연결

  - [x] 누락된 변수 및 파라미터 식별
    **✅ 완료**: DB-YAML 정밀 매핑 분석으로 핵심 문제 발견!

    **🎯 DB-YAML 매핑 관계 (사용자 제안 채택)**:
    - tv_trading_variables ↔ definition.yaml
    - tv_variable_parameters ↔ parameters.yaml
    - tv_placeholder_texts ↔ placeholders.yaml
    - tv_help_texts ↔ help_texts.yaml
    - tv_variable_help_documents ↔ help_guide.yaml

    **📊 정밀 분석 결과**:
    - ✅ 완전매핑: 10개 (ATR, BOLLINGER_BAND, EMA, MACD, META_PYRAMID_TARGET, META_TRAILING_STOP, RSI, SMA, STOCHASTIC, VOLUME_SMA)
    - ⚠️ 불완전매핑: 12개 (AVG_BUY_PRICE, CASH_BALANCE, COIN_BALANCE, CURRENT_PRICE, HIGH_PRICE, LOW_PRICE, OPEN_PRICE, POSITION_SIZE, PROFIT_AMOUNT, PROFIT_PERCENT, TOTAL_BALANCE, VOLUME)
    - 🔵 DB만존재: 0개
    - 🟡 YAML만존재: 0개

    **🚨 핵심 발견**: 12개 변수가 DB의 파라미터/플레이스홀더/도움말 테이블에서 누락!
    이것이 트리거 빌더 문제의 근본 원인일 가능성 높음

  - [x] 데이터 품질 문제 파악
    **✅ 완료**: 신중한 개별 검증으로 DB 설계 철학 이해

    **🔍 AVG_BUY_PRICE 상세 검증 결과**:
    - ✅ YAML 파일 모두 존재 (definition.yaml, parameters.yaml, help_texts.yaml, placeholders.yaml, help_guide.yaml)
    - ✅ definition.yaml: DB와 완벽 일치, 프로그램 방향성 적합
    - ✅ parameter_required: false (정확함 - 계산값이므로 파라미터 불필요)
    - ⚠️ help_texts.yaml & placeholders.yaml: 템플릿 수준 내용 (실제 도움말 없음)

    **💡 중요한 깨달음**:
    DB 설계가 올바름을 확인. 불완전 매핑 12개 변수들은 모두 parameter_required: false
    - 실시간 값: CURRENT_PRICE, VOLUME, HIGH_PRICE, LOW_PRICE, OPEN_PRICE
    - 계산 값: AVG_BUY_PRICE, PROFIT_AMOUNT, PROFIT_PERCENT
    - 상태 값: CASH_BALANCE, COIN_BALANCE, POSITION_SIZE, TOTAL_BALANCE

    **🎯 실제 문제 재정의**:
    "누락"이 아닌 "시스템 일관성" 문제. 트리거 빌더가 모든 변수에 동일한 메타데이터 구조를 기대하는지 확인 필요

- [x] **1.2 DB-YAML 매핑 분석**
  **✅ 완료**: 메타변수 파라미터 표시 문제 해결로 새로운 차원의 문제 발견!

  **🎯 핵심 발견**: ChartCategory enum 및 파라미터 파싱 문제 해결
  - ChartCategory.ADAPTIVE 추가로 메타변수 정상 로드
  - ast.literal_eval() 사용으로 enum 파싱 문제 해결
  - 메타변수 파라미터 한국어 표시명 매핑 완료

  **🚨 새로운 중요 문제 발견**: 파라미터 설계 논리 불일치
  - VOLUME, OPEN_PRICE, HIGH_PRICE, LOW_PRICE가 parameter_required=false
  - 하지만 이들은 타임프레임에 의존적인 값들임
  - 논리적으로 timeframe 파라미터가 필요함

  **📊 변수 논리성 재분류**:
  - ✅ 파라미터 불필요 (8개): CURRENT_PRICE, CASH_BALANCE, COIN_BALANCE, TOTAL_BALANCE, PROFIT_PERCENT, PROFIT_AMOUNT, POSITION_SIZE, AVG_BUY_PRICE
  - ❌ 파라미터 필요 (4개): VOLUME, OPEN_PRICE, HIGH_PRICE, LOW_PRICE (timeframe 의존적)

  **🔄 새로운 태스크 방향성**:
  1. 파라미터 없는 변수의 YAML 처리 방안
  2. DB 기준 YAML 올바른 추출
  3. YAML 기준 DB 무결성 업데이트
  4. 타임프레임 의존 변수들의 파라미터 설계 개선

- [x] **1.3 변수 파라미터 논리성 검토**
  **✅ 완료**: 프로그램 전체 논리에 맞는 파라미터 설계 개선 완료!

  **📊 파라미터 없는 변수들 (12개) 논리적 분석 완료**:

  **✅ 파라미터 불필요 (논리적으로 정당한 8개)**:
  - `CURRENT_PRICE` (현재가): 실시간 최신값, 타임프레임 무관
  - `CASH_BALANCE` (현금 잔고): 계좌 현재 상태, 타임프레임 무관
  - `COIN_BALANCE` (코인 잔고): 계좌 현재 상태, 타임프레임 무관
  - `TOTAL_BALANCE` (총 잔고): 계좌 현재 상태, 타임프레임 무관
  - `PROFIT_PERCENT` (현재 수익률): 포지션 기준 계산값, 타임프레임 무관
  - `PROFIT_AMOUNT` (현재 수익 금액): 포지션 기준 계산값, 타임프레임 무관
  - `POSITION_SIZE` (포지션 크기): 현재 포지션 상태, 타임프레임 무관
  - `AVG_BUY_PRICE` (평균 매수가): 포지션 기준 계산값, 타임프레임 무관

  **✅ 파라미터 추가 완료 (4개 변수)**:
  - `VOLUME` (거래량): timeframe 파라미터 추가 완료
  - `OPEN_PRICE` (시가): timeframe 파라미터 추가 완료
  - `HIGH_PRICE` (고가): timeframe 파라미터 추가 완료
  - `LOW_PRICE` (저가): timeframe 파라미터 추가 완료

  **🔧 적용된 timeframe 파라미터 표준**:
  - 파라미터명: `timeframe` (타임프레임)
  - 타입: `enum`, 기본값: `position_follow`
  - 선택옵션: `["position_follow", "1m", "3m", "5m", "10m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"]`
  - 기존 변수들과 완전히 동일한 표준 적용

- [x] **1.4 변수명 사용성 개선**
  **✅ 완료**: 기술적 지표 변수명에 영문 약어 추가로 사용자 인식성 향상

  **🎯 개선된 변수명**:
  - `ATR`: "평균실제범위" → **"평균실제범위 (ATR)"**
  - `SMA`: "단순이동평균" → **"단순이동평균 (SMA)"**
  - `EMA`: "지수이동평균" → **"지수이동평균 (EMA)"**
  - `BOLLINGER_BAND`: "볼린저 밴드" → **"볼린저 밴드 (BB)"**
  - `STOCHASTIC`: "스토캐스틱" → **"스토캐스틱 (STOCH)"**
  - `VOLUME_SMA`: "거래량 이동평균" → **"거래량 이동평균 (Vol SMA)"**

  **📈 사용성 개선 원칙**:
  - 어려운 한글 표현: 영문 약어 추가
  - 직관적인 한글: 그대로 유지 (현재가, 시가, 고가, 저가 등)
  - 이미 약어 포함: 변경 없음 (RSI 지표, MACD 지표)
  - `HIGH_PRICE` (고가): **타임프레임 의존적** (해당 기간의 최고가)
  - `LOW_PRICE` (저가): **타임프레임 의존적** (해당 기간의 최저가)

  **🔧 필요한 수정사항**:
  1. 4개 변수의 parameter_required를 true로 변경
  2. timeframe 파라미터 추가 (1m, 5m, 15m, 1h, 4h, 1d)
  3. 해당 변수들의 YAML 파일 구조 재설계

### Phase 2: DB 기준 YAML 표준화 [Phase 1 완료 후]
- [ ] **2.1 DB 우선 정리 전략**
  - [ ] DB에 존재하지 않는 YAML 변수 처리 방침 결정
  - [ ] DB 기준 YAML 형식 표준 템플릿 설계
  - [ ] 메타변수 vs 일반변수 형식 통일 방안 수립

- [ ] **2.2 YAML 구조 정규화**
  - [ ] DB 스키마에 맞는 YAML 필드 매핑 정의
  - [ ] 누락된 YAML 필드 자동 생성 스크립트 개발
  - [ ] 형식 불일치 자동 수정 도구 개발

### Phase 3: 상호 보완 및 업데이트 [Phase 2 완료 후]
- [ ] **3.1 DB 누락 정보 보충**
  - [ ] YAML에서 DB로 누락 정보 식별 및 추출
  - [ ] DB 테이블 안전한 업데이트 스크립트 개발
  - [ ] 하나씩 검증하며 보수적 업데이트 실행

- [ ] **3.2 YAML 완성도 향상**
  - [ ] DB 기준으로 YAML 누락 내용 보충
  - [ ] 메타변수 파라미터 완전성 확보
  - [ ] 전체 YAML 구조적 일관성 달성

### Phase 4: 완전 동기화 시스템 구축 [Phase 3 완료 후]
- [ ] **4.1 양방향 동기화 도구 개발**
  - [ ] **YAML → DB 업데이트 도구**: 완전 검증 및 안전 업데이트
  - [ ] **DB → YAML 생성 도구**: 표준 형식으로 YAML 자동 생성
  - [ ] 동기화 상태 검증 및 불일치 탐지 도구

- [ ] **4.2 최종 통합 검증**
  - [ ] 트리거 빌더에서 모든 변수 정상 표시 확인
  - [ ] 7규칙 전략 완전 구성 가능 검증
  - [ ] 데이터 일관성 최종 검증

## 🔧 개발할 핵심 도구

### 진단 도구
- `db_comprehensive_analyzer.py`: DB 완전 분석 도구
- `db_yaml_mapping_analyzer.py`: DB-YAML 매핑 분석 도구
- `meta_variable_diagnostic.py`: 메타변수 전용 진단 도구

### 동기화 도구
- `yaml_to_db_updater.py`: YAML → DB 안전 업데이트 도구
- `db_to_yaml_generator.py`: DB → YAML 표준 생성 도구
- `sync_state_validator.py`: 동기화 상태 검증 도구

### 검증 도구
- `data_consistency_checker.py`: 전체 데이터 일관성 검증
- `trigger_builder_tester.py`: 트리거 빌더 동작 테스트

## 🎯 성공 기준

### 단계별 체크포인트
1. **Phase 1 완료**: DB 상태 완전 파악, 문제점 정확한 식별
2. **Phase 2 완료**: 모든 YAML 파일이 DB 기준 표준 형식
3. **Phase 3 완료**: DB와 YAML 간 모든 정보 완전 동기화
4. **Phase 4 완료**: 양방향 동기화 도구 완성 및 검증 통과

### 최종 검증 기준
- ✅ 트리거 빌더에서 모든 변수 (메타변수 포함) 정상 표시
- ✅ 7규칙 전략 완전 구성 가능
- ✅ DB ↔ YAML 완전 일치 상태
- ✅ 지속 가능한 동기화 시스템 완성

## 💡 작업 시 주의사항

### 안전성 우선 원칙
- **원본 보존**: `data_info/trading_variables/` 절대 직접 수정 금지
- **백업 필수**: 각 단계별 DB 백업 생성
- **검증 우선**: 모든 변경사항 단계별 검증
- **롤백 준비**: 문제 발생시 즉시 복구 가능한 상태 유지

### DB 작업 가이드라인
- **보수적 접근**: 하나씩 검증하며 업데이트
- **트랜잭션 사용**: 모든 DB 변경사항 트랜잭션으로 처리
- **로깅 필수**: 모든 변경사항 상세 로그 기록
- **검증 단계**: 변경 → 검증 → 확정 절차 준수

## 🚀 즉시 시작할 첫 번째 작업

### 1단계: DB 상태 완전 분석
```powershell
# DB 테이블 구조 및 데이터 확인
python tools/super_db_table_viewer.py settings

# 새로운 종합 분석 도구 개발 필요
python db_comprehensive_analyzer.py
```

### 2단계: 메타변수 문제 정확한 진단
```powershell
# 메타변수 전용 진단 도구 개발 및 실행
python meta_variable_diagnostic.py
```

### 3단계: DB-YAML 완전 매핑 분석
```powershell
# 완전한 매핑 분석 도구 개발
python db_yaml_mapping_analyzer.py
```

## 📋 Phase 1 상세 체크리스트

### DB 분석 [우선순위 1]
- [ ] 전체 tv_ 테이블 목록 파악 (settings.sqlite3 내 모든 tv_ 접두사 테이블)
- [ ] tv_trading_variables 테이블 스키마 분석
- [ ] tv_variable_parameters 테이블 스키마 분석
- [ ] 기타 tv_ 테이블들 (tv_*, 존재시) 스키마 분석
- [ ] 테이블 간 관계 및 외래키 구조 파악
- [ ] 현재 등록된 변수 목록 완전 추출
- [ ] 누락된 변수 식별 (특히 메타변수)
- [ ] 데이터 품질 문제 파악

### YAML 분석 [우선순위 2]
- [ ] 원본 YAML 구조 완전 분석
- [ ] 수정된 YAML 구조 비교 분석
- [ ] 변수별 파일 완성도 확인
- [ ] 메타변수 특별 구조 분석

### 매핑 분석 [우선순위 3]
- [ ] DB 변수 ↔ YAML 변수 완전 매핑
- [ ] 누락/불일치/중복 정확한 분류
- [ ] 각 변수별 데이터 품질 비교
- [ ] 메타변수 매핑 특별 분석

---
**🎯 성공을 위한 핵심**: DB를 중심으로 한 체계적이고 안전한 동기화 접근법
**다음 에이전트 시작점**: Phase 1.1 DB 스키마 분석부터 시작하세요!

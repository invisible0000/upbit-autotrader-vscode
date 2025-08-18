# TASK_20250817_03_db_fix_single_step.md
# DB 완성도 향상 - 단계별 보수적 접근법

## 🎯 목표
- 기존 `data_info/trading_variables` YAML을 활용해 DB 테이블 완성도 향상
- 하나의 변수, 하나의 컬럼씩 보수적으로 업데이트
- DB를 Single Source of Truth로 만들어 완전한 YAML 생성 가능

## 📊 현재 상태 분석

### DB 테이블 현황
- `tv_trading_variables`: 22 rows (기본 변수 정보)
- `tv_variable_parameters`: 34 rows (파라미터 정보, 일부 변수 누락)
- `tv_variable_help_documents`: 75 rows (도움말, 3-tab 구조 완성)
- `tv_help_texts`: 29 rows (헬프 텍스트, 불완전)
- `tv_placeholder_texts`: 27 rows (플레이스홀더, 불완전)

### 기존 YAML 구조
```
data_info/trading_variables/
├── trend/sma/
│   ├── definition.yaml
│   ├── parameters.yaml
│   ├── help_guide.yaml
│   ├── help_texts.yaml
│   └── placeholders.yaml
├── trend/ema/
├── momentum/rsi/
└── ... (기타 변수들)
```

## 🔍 Phase 1: 현황 파악 및 검증 (완료)

### [x] Step 1.1: DB 변수 목록 vs 기존 YAML 폴더 매핑 확인
- [x] TV_trading_variables에서 22개 variable_id 추출
- [x] 기존 YAML 폴더 구조에서 변수 목록 추출
- [x] 누락/추가 변수 식별 → **완전 일치 확인!**
- [x] 폴더명 vs variable_id 매핑 테이블 생성

### [x] Step 1.2: 각 변수별 데이터 완성도 체크
- [x] tv_variable_parameters 누락 확인
- [x] tv_help_texts 누락 확인
- [x] tv_placeholder_texts 누락 확인
- [x] 우선순위 변수 식별 → **완전: 10개, 부분: 4개, 빈값: 8개**

### [x] Step 1.3: 샘플 변수 선정 및 검증
- [x] 가장 완성도 높은 변수 1개 선정 → **SMA 선정**
- [x] SMA 변수의 현재 DB 상태 확인 → **완전한 데이터 확인**
- [ ] YAML → DB 마이그레이션 테스트 (SMA는 이미 완전하므로 스킵)
- [ ] DB → YAML 재생성 테스트
- [ ] 원본과 재생성 파일 비교 검증## 🛠️ Phase 2: 단계별 DB 업데이트 (대기)

### [ ] Step 2.1: tv_variable_parameters 보완
- [ ] 변수별로 parameters.yaml 확인
- [ ] 하나씩 DB INSERT/UPDATE 수행
- [ ] 각 단계마다 검증

### [ ] Step 2.2: tv_help_texts 보완
- [ ] 변수별로 help_texts.yaml 확인
- [ ] 하나씩 DB INSERT/UPDATE 수행
- [ ] 각 단계마다 검증

### [ ] Step 2.3: tv_placeholder_texts 보완
- [ ] 변수별로 placeholders.yaml 확인
- [ ] 하나씩 DB INSERT/UPDATE 수행
- [ ] 각 단계마다 검증

## 🔄 Phase 3: 표준 YAML 재생성 (대기)

### [ ] Step 3.1: db_to_yaml_tv_tables.py 개선
- [ ] 폴더명을 variable_id 대문자로 수정
- [ ] 빈 데이터 처리 로직 개선
- [ ] 메타데이터 보장 로직 추가

### [ ] Step 3.2: 새로운 표준 YAML 생성
- [ ] 완성된 DB에서 YAML 재생성
- [ ] 기존 구조와 비교 검증
- [ ] 필요시 기존 파일 백업 후 교체

## 📝 작업 로그

### 2025-08-17 초기 계획 수립
- [x] 문제점 분석 완료
- [x] 보수적 접근법 계획 수립
- [ ] Phase 1 작업 시작 예정

## 🚨 주의사항

1. **보수적 원칙**: 한 번에 하나의 변수, 하나의 컬럼만 수정
2. **백업 우선**: 모든 DB 변경 전 백업 생성
3. **검증 필수**: 각 단계마다 결과 검증
4. **롤백 준비**: 문제 발생시 즉시 롤백 가능하도록 준비
5. **로그 기록**: 모든 변경사항을 상세히 기록

## 🎯 성공 기준

- [ ] 모든 변수에 대해 완전한 메타데이터 보장
- [ ] DB에서 누락 없이 완전한 YAML 생성 가능
- [ ] 폴더명과 variable_id 일치
- [ ] 기존 데이터 무결성 유지

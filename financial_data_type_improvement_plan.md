# 금융 데이터 타입 개선 계획
# 분석 결과: 2025-01-14 22:35

## 🔍 발견된 REAL 타입 컬럼들

### Settings DB (6개)
1. `cfg_chart_layout_templates.main_chart_height_ratio` - UI 레이아웃 비율 (유지 가능)
2. `tv_chart_variables.scale_min` - 차트 스케일 최소값 (precision 필요할 수 있음)
3. `tv_chart_variables.scale_max` - 차트 스케일 최대값 (precision 필요할 수 있음)
4. `tv_chart_variables.subplot_height_ratio` - UI 레이아웃 비율 (유지 가능)
5. `tv_variable_compatibility_rules.min_value_constraint` - **금융 제약값 (개선 필요)**
6. `tv_variable_compatibility_rules.max_value_constraint` - **금융 제약값 (개선 필요)**

### Strategies DB (4개)
1. `event_processing_log.processing_time_ms` - 성능 메트릭 (유지 가능)
2. `execution_history.profit_loss` - **손익 계산 (개선 필요)**
3. `trading_conditions.success_rate` - 통계값 (유지 가능)
4. `user_strategies.position_size_value` - **포지션 크기 (개선 필요)**

## 🎯 우선순위 개선 대상

### HIGH PRIORITY (금융 정밀도 필수)
- `execution_history.profit_loss` → TEXT (Decimal 저장)
- `user_strategies.position_size_value` → TEXT (Decimal 저장)
- `tv_variable_compatibility_rules.min_value_constraint` → TEXT (Decimal 저장)
- `tv_variable_compatibility_rules.max_value_constraint` → TEXT (Decimal 저장)

### MEDIUM PRIORITY (차트/스케일 정밀도)
- `tv_chart_variables.scale_min` → TEXT (가격 스케일의 경우)
- `tv_chart_variables.scale_max` → TEXT (가격 스케일의 경우)

### LOW PRIORITY (유지 가능)
- UI 레이아웃 비율들 (main_chart_height_ratio, subplot_height_ratio)
- 성능 메트릭 (processing_time_ms)
- 통계값 (success_rate)

## 📋 안전한 마이그레이션 전략

1. **백업 완료** ✅
   - 스키마: upbit_autotrading_unified_schema_now_20250814_223241.sql
   - 데이터: data/ 폴더 백업 완료

2. **단계적 접근**
   - Phase 1: 새 컬럼 추가 (TEXT 타입)
   - Phase 2: 데이터 변환 및 검증
   - Phase 3: 기존 컬럼 제거
   - Phase 4: 인덱스 재생성

3. **검증 포인트**
   - 데이터 무결성 확인
   - 정밀도 테스트
   - 성능 영향 측정

## 🛡️ 안전 장치

- 롤백 스크립트 준비
- 데이터 변환 검증 로직
- 단위 테스트 추가
- 실제 거래 전 dry-run 테스트

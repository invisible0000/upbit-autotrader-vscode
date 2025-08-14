-- 개선된 스키마: 금융 데이터 정밀도 향상
-- 생성일: 2025-01-14 22:36
-- 기준: upbit_autotrading_unified_schema_now_20250814_223241.sql

-- =============================================================================
-- STRATEGIES DATABASE 개선사항
-- =============================================================================

-- 1. execution_history 테이블 개선
-- BEFORE: profit_loss REAL
-- AFTER: profit_loss TEXT (Decimal 문자열 저장)
CREATE TABLE execution_history_improved (
    id INTEGER PRIMARY KEY,
    strategy_id INTEGER,
    symbol TEXT,
    action TEXT,
    quantity TEXT,  -- Decimal 저장
    price TEXT,     -- Decimal 저장
    profit_loss TEXT,  -- 🔥 REAL → TEXT 개선
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (strategy_id) REFERENCES user_strategies(id)
);

-- 2. user_strategies 테이블 개선
-- BEFORE: position_size_value REAL DEFAULT 100000
-- AFTER: position_size_value TEXT DEFAULT '100000'
CREATE TABLE user_strategies_improved (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 0,
    position_size_type TEXT DEFAULT 'fixed',
    position_size_value TEXT DEFAULT '100000',  -- 🔥 REAL → TEXT 개선
    stop_loss_enabled BOOLEAN DEFAULT 0,
    take_profit_enabled BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SETTINGS DATABASE 개선사항
-- =============================================================================

-- 3. tv_variable_compatibility_rules 테이블 개선
-- BEFORE: min_value_constraint REAL, max_value_constraint REAL
-- AFTER: min_value_constraint TEXT, max_value_constraint TEXT
CREATE TABLE tv_variable_compatibility_rules_improved (
    id INTEGER PRIMARY KEY,
    variable_group TEXT NOT NULL,
    constraint_type TEXT NOT NULL,
    min_value_constraint TEXT,  -- 🔥 REAL → TEXT 개선
    max_value_constraint TEXT,  -- 🔥 REAL → TEXT 개선
    validation_rule TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. tv_chart_variables 테이블 개선 (가격 스케일의 경우)
-- BEFORE: scale_min REAL, scale_max REAL
-- AFTER: scale_min TEXT, scale_max TEXT (Decimal 지원)
CREATE TABLE tv_chart_variables_improved (
    id INTEGER PRIMARY KEY,
    variable_name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    description TEXT,
    purpose_category TEXT NOT NULL,
    chart_category TEXT NOT NULL DEFAULT 'overlay',
    comparison_group TEXT NOT NULL,
    scale_min TEXT,     -- 🔥 REAL → TEXT 개선 (가격 스케일)
    scale_max TEXT,     -- 🔥 REAL → TEXT 개선 (가격 스케일)
    subplot_height_ratio REAL DEFAULT 0.3,  -- UI 비율은 REAL 유지
    default_visible BOOLEAN DEFAULT 1,
    supports_comparison BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- 마이그레이션 헬퍼 뷰
-- =============================================================================

-- 금융 데이터 정밀도 검증을 위한 뷰
CREATE VIEW financial_precision_audit AS
SELECT
    'execution_history' as table_name,
    'profit_loss' as column_name,
    profit_loss as current_value,
    CASE
        WHEN typeof(profit_loss) = 'real' THEN '⚠️  REAL 타입 (정밀도 이슈 가능)'
        WHEN typeof(profit_loss) = 'text' THEN '✅ TEXT 타입 (Decimal 안전)'
        ELSE '❓ 알 수 없는 타입'
    END as precision_status
FROM execution_history
WHERE profit_loss IS NOT NULL

UNION ALL

SELECT
    'user_strategies' as table_name,
    'position_size_value' as column_name,
    position_size_value as current_value,
    CASE
        WHEN typeof(position_size_value) = 'real' THEN '⚠️  REAL 타입 (정밀도 이슈 가능)'
        WHEN typeof(position_size_value) = 'text' THEN '✅ TEXT 타입 (Decimal 안전)'
        ELSE '❓ 알 수 없는 타입'
    END as precision_status
FROM user_strategies
WHERE position_size_value IS NOT NULL;

-- =============================================================================
-- 마이그레이션 안전 검증 쿼리
-- =============================================================================

-- 1. 데이터 타입 검증
-- SELECT typeof(column_name) FROM table_name;

-- 2. 정밀도 손실 검증
-- SELECT
--     original_value,
--     CAST(original_value AS TEXT) as text_conversion,
--     CAST(CAST(original_value AS TEXT) AS REAL) as round_trip,
--     CASE WHEN original_value = CAST(CAST(original_value AS TEXT) AS REAL)
--          THEN '✅ 정밀도 유지'
--          ELSE '⚠️  정밀도 손실' END as precision_check
-- FROM table_name;

-- 3. Decimal 호환성 검증 (Python에서)
-- from decimal import Decimal
-- try:
--     decimal_value = Decimal(text_value)
--     print(f"✅ Decimal 변환 성공: {decimal_value}")
-- except Exception as e:
--     print(f"❌ Decimal 변환 실패: {e}")

-- =============================================================================
-- 코멘트: 안전한 금융 데이터 처리
-- =============================================================================

/*
🎯 목표: 암호화폐 거래의 정밀도 보장

💰 금융 데이터 정밀도가 중요한 이유:
1. 거래소 수수료 계산 정확성
2. 손익 계산 정확성
3. 포지션 크기 정확성
4. 규제 요구사항 준수

📊 TEXT 타입 선택 이유:
- SQLite의 REAL은 IEEE 754 부동소수점 (정밀도 제한)
- TEXT로 Decimal 문자열 저장하면 임의 정밀도 지원
- Python Decimal과 완벽 호환
- 금융 업계 표준 접근법

🛡️ 안전한 마이그레이션:
1. 기존 테이블 백업
2. _improved 테이블로 새 스키마 테스트
3. 데이터 변환 및 검증
4. 점진적 전환
5. 롤백 준비

⚡ 성능 고려사항:
- TEXT 저장은 REAL보다 약간 큰 저장 공간
- Decimal 연산은 float보다 느림
- 하지만 정확성이 성능보다 중요한 금융 도메인
*/

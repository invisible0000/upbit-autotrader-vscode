# 📋 데이터베이스 설계 및 관리 방침 문서

## 🎯 목적
이 문서는 `upbit-autotrader` 프로젝트의 settings.db 데이터베이스 설계 원칙과 향후 확장성을 고려한 관리 방침을 정의합니다. 누구나 DB를 보수/개선할 때 실수하지 않도록 명확한 가이드라인을 제공합니다.

---

## 🏗️ 테이블 명명 규칙 (Naming Convention)

### 1. 접두사(Prefix) 시스템

모든 테이블은 **기능별 접두사**를 사용하여 명명합니다:

```sql
-- 형식: {모듈명}_{테이블명}
-- 예시:
tv_trading_variables    -- Trading Variables 모듈
tv_variable_parameters  -- Trading Variables 모듈  
tv_comparison_groups    -- Trading Variables 모듈
```

### 2. 현재 정의된 접두사

| 접두사 | 모듈명 | 설명 | 예시 테이블 |
|--------|--------|------|-------------|
| `tv_` | Trading Variables | 트레이딩 지표 변수 관리 | `tv_trading_variables` |
| `auth_` | Authentication | 사용자 인증 (향후 예정) | `auth_users`, `auth_roles` |
| `chart_` | Chart Settings | 차트 설정 (향후 예정) | `chart_layouts`, `chart_themes` |
| `strategy_` | Strategy Management | 전략 관리 (향후 예정) | `strategy_rules`, `strategy_backtest` |
| `trade_` | Trading Engine | 실제 거래 실행 (향후 예정) | `trade_orders`, `trade_history` |
| `config_` | System Configuration | 시스템 설정 (향후 예정) | `config_app`, `config_api` |

### 3. 접두사 사용 이유

1. **📂 모듈 그룹화**: 관련 테이블들을 논리적으로 그룹화
2. **💥 이름 충돌 방지**: SQLite 예약어 및 향후 테이블명 충돌 방지
3. **🔍 가독성 향상**: 테이블 이름만으로 소속 모듈 즉시 파악 가능
4. **⚡ 유지보수성**: 모듈별 독립적인 관리 및 수정 가능

---

## 📊 데이터 타입 및 제약 조건

### 1. 공통 컬럼 규칙

모든 테이블은 다음 공통 컬럼을 포함해야 합니다:

```sql
-- 메인 테이블 공통 컬럼
id_column TEXT PRIMARY KEY,                    -- 기본키 (의미있는 문자열 권장)
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 생성일시
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- 수정일시 (트리거로 자동 업데이트)
is_active BOOLEAN DEFAULT 1                     -- 활성화 상태 (소프트 삭제 지원)
```

### 2. 파라미터 저장 방식

설정값이나 파라미터는 **유연성**을 위해 TEXT 타입으로 저장하되, 애플리케이션에서 타입 검증을 수행합니다:

```sql
-- 파라미터 테이블 패턴
parameter_type TEXT NOT NULL,    -- 'integer', 'float', 'string', 'boolean', 'enum'
default_value TEXT,              -- 기본값 (문자열로 저장)
min_value TEXT,                  -- 최소값 (숫자형일 때)
max_value TEXT,                  -- 최대값 (숫자형일 때)
enum_values TEXT                 -- enum 값들 (JSON 배열)
```

⚠️ **중요**: Python 애플리케이션에서 반드시 타입 변환 및 범위 검증을 수행해야 합니다.

### 3. 다국어 지원 패턴

UI 표시 텍스트는 다국어를 고려하여 설계합니다:

```sql
display_name_ko TEXT NOT NULL,  -- 한국어 표시명 (필수)
display_name_en TEXT,           -- 영어 표시명 (선택)
description TEXT                -- 상세 설명 (한국어 기본)
```

---

## 🔄 버전 관리 시스템

### 1. 스키마 버전 테이블

각 모듈별로 버전 관리 테이블을 유지합니다:

```sql
CREATE TABLE IF NOT EXISTS {prefix}_schema_version (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);
```

### 2. 버전 번호 규칙

**SemVer(Semantic Versioning)** 방식을 사용합니다:

- `MAJOR.MINOR.PATCH` (예: 2.1.3)
- **MAJOR**: 호환성을 깨는 변경
- **MINOR**: 새로운 기능 추가 (하위 호환)
- **PATCH**: 버그 수정 및 소규모 개선

### 3. 마이그레이션 원칙

```sql
-- 올바른 마이그레이션 예시
-- 1. 기존 테이블 백업
CREATE TABLE tv_trading_variables_backup AS SELECT * FROM tv_trading_variables;

-- 2. 새 컬럼 추가 (기본값 설정)
ALTER TABLE tv_trading_variables ADD COLUMN new_field TEXT DEFAULT 'default_value';

-- 3. 데이터 업데이트
UPDATE tv_trading_variables SET new_field = '새로운값' WHERE 조건;

-- 4. 버전 기록
INSERT INTO tv_schema_version VALUES ('2.1.0', CURRENT_TIMESTAMP, '새 필드 추가 설명');
```

---

## 📈 확장성 고려사항

### 1. 새로운 모듈 추가 시

새 모듈을 추가할 때는 다음 단계를 따릅니다:

1. **접두사 정의**: 위 표에 새로운 접두사 등록
2. **스키마 설계**: 공통 컬럼 규칙 준수
3. **버전 테이블 생성**: `{prefix}_schema_version` 테이블 생성
4. **문서 업데이트**: 이 문서에 새 모듈 정보 추가

### 2. 성능 최적화

```sql
-- 필수 인덱스 생성 패턴
CREATE INDEX IF NOT EXISTS idx_{prefix}_{column} ON {table}({column});
CREATE INDEX IF NOT EXISTS idx_{prefix}_{table}_active ON {table}(is_active);
CREATE INDEX IF NOT EXISTS idx_{prefix}_{table}_created ON {table}(created_at);
```

### 3. 외래키 관리

```sql
-- 외래키 정의 패턴 (CASCADE 정책 주의)
FOREIGN KEY (parent_id) REFERENCES parent_table(id) ON DELETE CASCADE
FOREIGN KEY (reference_id) REFERENCES reference_table(id) ON DELETE SET NULL
```

---

## ⚠️ 주의사항 및 베스트 프랙티스

### 1. 절대 금지사항

- ❌ 기존 테이블명 변경 (호환성 파괴)
- ❌ 기존 컬럼 삭제 (데이터 손실 위험)  
- ❌ NOT NULL 제약조건 추가 (기본값 없이)
- ❌ 기본키 변경 (참조 무결성 파괴)

### 2. 권장사항

- ✅ 새 컬럼 추가 시 적절한 기본값 설정
- ✅ 인덱스 성능 영향 사전 검토
- ✅ 마이그레이션 전 반드시 백업
- ✅ 변경사항 상세 문서화

### 3. 데이터 무결성

```sql
-- 체크 제약조건 예시
CREATE TABLE example (
    status TEXT CHECK (status IN ('active', 'inactive', 'pending')),
    percentage REAL CHECK (percentage >= 0.0 AND percentage <= 100.0)
);
```

---

## 🔧 유지보수 가이드

### 1. 정기 점검 항목

- 인덱스 사용률 모니터링
- 테이블 크기 및 성능 확인
- 외래키 참조 무결성 검증
- 버전 히스토리 정리

### 2. 장애 대응

```sql
-- 데이터 복구를 위한 백업 쿼리
CREATE TABLE emergency_backup_YYYYMMDD AS 
SELECT * FROM original_table WHERE created_at >= '2025-01-01';
```

### 3. 성능 튜닝

```sql
-- 쿼리 성능 분석
EXPLAIN QUERY PLAN SELECT * FROM tv_trading_variables WHERE purpose_category = 'momentum';

-- 통계 정보 업데이트
ANALYZE tv_trading_variables;
```

---

## 📝 변경 기록

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 1.0.0 | 2025-07-30 | 최초 작성 - 기본 가이드라인 정의 | System |

---

## 📞 문의 및 개선사항

이 문서의 내용에 대한 문의나 개선사항이 있을 경우, 프로젝트 이슈 트래커에 등록하거나 개발팀에 직접 연락해 주세요.

**원칙**: "데이터는 소중하고, 호환성은 생명이다." 🛡️

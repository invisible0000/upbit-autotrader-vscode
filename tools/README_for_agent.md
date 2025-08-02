# 🤖 Super DB 도구 시스템 - LLM 에이전트용 가이드

## 0️⃣ 최우선 지침

당신은 이 프로젝트의 **DB 관리 전문 에이전트**입니다. 당신의 주요 책임은 다음과 같습니다:

1. **3-Database 아키텍처 보호**: `settings.sqlite3`, `strategies.sqlite3`, `market_data.sqlite3`의 무결성 유지
2. **Zero 데이터 손실**: 모든 작업 전 백업 체크포인트 생성 필수
3. **선제적 검증**: 작업 실행 전 영향도 분석 및 위험 평가 수행

## 1️⃣ 사전 준비: 도구 체계 이해

### 📌 도구 카테고리

1. **Core Tools (9개)**
   ```python
   DB_CORE_TOOLS = {
       "viewer": "super_db_table_viewer.py",           # v2.1
       "migrator": "super_db_migration_yaml_to_db.py", # v3.0
       "extractor": "super_db_extraction_db_to_yaml.py", # v2.3
       "merger": "super_db_yaml_merger.py",            # v2.5
       "generator": "super_db_structure_generator.py",  # v1.8
       "schema": "super_db_schema_extractor.py",       # v1.7
       "analyzer": "super_db_table_reference_code_analyzer.py", # v5.1
       "parameter": "super_db_analyze_parameter_table.py", # v1.2
       "editor": "super_db_yaml_editor_workflow.py"    # v1.5
   }
   ```

2. **Operation Tools (7개)**
   ```python
   DB_OPS_TOOLS = {
       "monitor": "super_db_health_monitor.py",        # v1.1 ✨
       "validator": "super_db_schema_validator.py",    # v1.0 ✨
       "rollback": "super_db_rollback_manager.py",    # v1.2 ✨
       "debugger": "super_db_debug_path_mapping.py",  # v1.0 ✨
       "migrator": "super_db_data_migrator.py"        # v1.0 ✨
   }
   ```

## 2️⃣ 핵심 워크플로우

### 🔄 표준 작업 순서

```python
WORKFLOW_STEPS = [
    {
        "step": 0,
        "name": "초기 진단",
        "tool": "super_db_debug_path_mapping.py",
        "args": "--quick"
    },
    {
        "step": 1,
        "name": "백업 생성",
        "tool": "super_db_rollback_manager.py",
        "args": "--create-checkpoint \"pre_task\" --verify"
    },
    {
        "step": 2,
        "name": "현황 파악",
        "tool": "super_db_table_viewer.py",
        "args": "--detailed"
    },
    {
        "step": 3,
        "name": "영향도 분석",
        "tool": "super_db_table_reference_code_analyzer.py",
        "args": "--analysis-depth deep"
    }
    # ... 이하 순서대로 진행
]
```

### 🎯 작업 유형별 접근 방법

1. **데이터 조회/분석**
   ```python
   QUERY_WORKFLOW = {
       "tool": "super_db_table_viewer.py",
       "options": ["--detailed", "--filter", "--table"],
       "output": ["테이블 구조", "레코드 수", "관계", "제약조건"],
       "risk_level": "LOW"  # 읽기 전용
   }
   ```

2. **스키마 변경**
   ```python
   SCHEMA_CHANGE_WORKFLOW = {
       "required_tools": [
           "super_db_rollback_manager.py",  # 백업 필수
           "super_db_table_reference_code_analyzer.py",  # 영향도 검사
           "super_db_schema_validator.py"  # 검증
       ],
       "risk_level": "HIGH",
       "verification_required": True
   }
   ```

3. **데이터 마이그레이션**
   ```python
   MIGRATION_WORKFLOW = {
       "steps": [
           {"tool": "super_db_rollback_manager.py", "purpose": "백업"},
           {"tool": "super_db_migration_yaml_to_db.py", "purpose": "마이그레이션"},
           {"tool": "super_db_schema_validator.py", "purpose": "검증"}
       ],
       "parallel_support": True,  # v3.0 신규
       "verification_required": True
   }
   ```

## 3️⃣ 도구별 상세 사용법

### 📊 분석 도구

1. **`super_db_table_viewer.py` (v2.1)**
   ```python
   VIEWER_COMMANDS = {
       "full_analysis": "--detailed",  # 전체 상세 분석
       "specific_table": "table [테이블명]",  # 특정 테이블 분석
       "pattern_filter": "--filter \"tv_*\"",  # 패턴 기반 필터링
       "health_score": True  # v2.1 신규: DB 건강도 점수
   }
   ```

2. **`super_db_table_reference_code_analyzer.py` (v5.1)**
   ```python
   ANALYZER_FEATURES = {
       "deep_analysis": "--analysis-depth deep",
       "risk_assessment": "--risk-threshold high",
       "exclude_patterns": "--ignore-files \"test_*.py\"",
       "target_specific": "--folder \"path/to/folder\"",
       "output_formats": ["json", "log", "report"]
   }
   ```

### 🔧 운영 도구

1. **`super_db_health_monitor.py` (v1.1)**
   ```python
   MONITOR_MODES = {
       "real_time": {
           "cmd": "--mode real-time --interval 30",
           "metrics": ["cpu", "memory", "io", "connections"],
           "alerts": {
               "threshold": 80,
               "channels": ["slack", "console"]
           }
       }
   }
   ```

2. **`super_db_schema_validator.py` (v1.0)**
   ```python
   VALIDATOR_CHECKS = {
       "naming_rules": "--check naming --all-dbs",
       "full_validation": "--check all --detailed",
       "migration_check": "--validate migration-completeness",
       "auto_fix": "--auto-fix naming --backup"
   }
   ```

## 4️⃣ 시스템 성능 지표

```python
SYSTEM_METRICS = {
    "schema_quality": 96.7,  # 목표: 95%
    "naming_rules": 94.4,    # 목표: 90%
    "relationship_integrity": 100.0,  # 필수
    "query_performance": "1000+ qps",
    "workflow_efficiency": "60% 시간 단축"
}
```

## 5️⃣ 에러 처리 프로토콜

```python
ERROR_HANDLING = {
    "backup_first": True,  # 모든 변경 작업 전 필수
    "verification_required": True,  # 모든 작업 후 필수
    "rollback_available": True,  # 문제 발생 시
    "monitoring_active": True  # 실시간 감시
}

RECOVERY_STEPS = [
    "super_db_rollback_manager.py --rollback [checkpoint]",
    "super_db_health_monitor.py --mode diagnose",
    "super_db_schema_validator.py --check all"
]
```

## 🔍 참고: 주요 데이터 구조

```python
DB_STRUCTURE = {
    "settings.sqlite3": {
        "purpose": "시스템 구조 및 설정",
        "tables": ["tv_trading_variables", "tv_variable_parameters", "tv_help_texts"],
        "priority": "HIGH"
    },
    "strategies.sqlite3": {
        "purpose": "전략 인스턴스",
        "tables": ["user_strategies", "strategy_templates"],
        "priority": "MEDIUM"
    },
    "market_data.sqlite3": {
        "purpose": "시장 데이터",
        "tables": ["market_symbols", "data_sources"],
        "priority": "LOW"
    }
}
```

---
*이 문서는 LLM 에이전트의 효율적인 작업을 위해 최적화되었습니다.*
*마지막 업데이트: 2025-08-02*

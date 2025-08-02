# 🤖 DB Migration Agent Protocol

## 1. 에이전트 스펙 (Agent Specification)

```python
AGENT_SPEC = {
    "domain": "데이터베이스 마이그레이션",
    "version": "2.0.0",
    "capabilities": ["구조 분석", "위험 평가", "마이그레이션 실행", "실시간 모니터링"],
    "supported_databases": ["settings.sqlite3", "strategies.sqlite3", "market_data.sqlite3"]
}
```

## 2. 도구 세트 (Tool Set)

```python
TOOLS = {
    "core": {
        "super_db_structure_generator.py": {
            "purpose": "DB 구조 생성",
            "usage_timing": "구조 변경 시",
            "required_params": ["target_db", "schema_definition"]
        },
        "super_data_migration_engine.py": {
            "purpose": "데이터 이관",
            "usage_timing": "데이터 전송 시",
            "required_params": ["source_db", "target_db", "mapping_rules"]
        },
        "super_rollback_manager.py": {
            "purpose": "백업/복구 관리",
            "usage_timing": "작업 전/오류 발생 시",
            "required_params": ["db_path", "backup_type"]
        }
    },
    "validation": {
        "super_schema_validator.py": {
            "purpose": "스키마 검증",
            "usage_timing": "구조 변경 전/후",
            "required_params": ["db_path", "expected_schema"]
        },
        "super_db_health_monitor.py": {
            "purpose": "DB 상태 모니터링",
            "usage_timing": "전체 과정",
            "required_params": ["db_path", "metrics_to_monitor"]
        }
    }
}
```

## 3. 작업 유형별 프로토콜 (Task-specific Protocols)

```python
MIGRATION_PROTOCOLS = {
    "basic_cleanup": {
        "detection": {
            "patterns": ["DB 정리", "테이블 구조 개선"],
            "conditions": {
                "table_count": "<20",
                "has_duplicates": True,
                "performance_issues": False
            }
        },
        "execution": {
            "tools": ["super_db_health_monitor.py", "super_rollback_manager.py"],
            "steps": [
                "상태_분석",
                "백업_생성",
                "구조_최적화",
                "검증_수행"
            ],
            "estimated_time": "30-60분",
            "risk_level": "LOW"
        }
    },
    "structure_instance_separation": {
        "detection": {
            "patterns": ["구조/인스턴스 분리", "DB 시스템 분리"],
            "conditions": {
                "current_state": "단일_DB",
                "has_user_data": True,
                "needs_scalability": True
            }
        },
        "execution": {
            "tools": ["super_schema_validator.py", "super_db_structure_generator.py"],
            "steps": [
                "구조_분석",
                "전체_백업",
                "설정DB_생성",
                "전략DB_생성",
                "데이터_이관",
                "무결성_검증",
                "성능_테스트"
            ],
            "estimated_time": "2-3시간",
            "risk_level": "MEDIUM"
        }
    },
    "large_scale_migration": {
        "detection": {
            "patterns": ["대량 데이터 이관", "레거시 데이터 마이그레이션"],
            "conditions": {
                "table_size": ">10MB",
                "record_count": ">10000",
                "requires_transformation": True
            }
        },
        "execution": {
            "tools": ["super_data_migration_engine.py", "super_db_health_monitor.py"],
            "steps": [
                "볼륨_분석",
                "백업_전략_수립",
                "호환성_검증",
                "점진적_이관",
                "실시간_모니터링"
            ],
            "estimated_time": "4-8시간",
            "risk_level": "HIGH"
        }
    }
}
```

## 4. 오류 대응 매트릭스 (Error Response Matrix)

```python
ERROR_HANDLING = {
    "validation_error": {
        "severity": "MEDIUM",
        "immediate_action": "작업_중단",
        "resolution_steps": [
            "스키마_재검증",
            "오류_로그_분석",
            "수정_계획_수립"
        ],
        "tool": "super_schema_validator.py"
    },
    "migration_failure": {
        "severity": "HIGH",
        "immediate_action": "롤백_시작",
        "resolution_steps": [
            "오류_지점_식별",
            "데이터_일관성_검사",
            "단계별_롤백"
        ],
        "tool": "super_rollback_manager.py"
    },
    "performance_degradation": {
        "severity": "LOW",
        "immediate_action": "모니터링_강화",
        "resolution_steps": [
            "병목점_분석",
            "최적화_수행",
            "성능_재측정"
        ],
        "tool": "super_db_health_monitor.py"
    }
}
```

## 5. 검증 프로토콜 (Validation Protocol)

```python
VALIDATION_STEPS = {
    "pre_migration": [
        "스키마_호환성_검사",
        "데이터_타입_검증",
        "제약조건_확인",
        "공간_요구사항_계산"
    ],
    "during_migration": [
        "데이터_무결성_검사",
        "성능_모니터링",
        "오류_발생_감시",
        "진행률_추적"
    ],
    "post_migration": [
        "전체_데이터_검증",
        "관계_무결성_확인",
        "성능_측정",
        "사용자_기능_테스트"
    ]
}
```

## 6. 성공 메트릭스 (Success Matrix)

```python
SUCCESS_CRITERIA = {
    "data_integrity": {
        "records_match": "100%",
        "constraints_preserved": True,
        "relationships_valid": True
    },
    "performance": {
        "query_time": "기존 대비 120% 이내",
        "index_effectiveness": "90% 이상",
        "resource_usage": "정상 범위 내"
    },
    "system_stability": {
        "error_rate": "<0.1%",
        "downtime": "계획된 시간 내",
        "recovery_point": "최신 백업 시점"
    }
}
```

---
*이 문서는 LLM 에이전트가 DB 마이그레이션 작업을 자동으로 수행할 수 있도록 구조화된 프로토콜을 정의합니다.*

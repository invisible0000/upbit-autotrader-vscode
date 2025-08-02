# 🤖 Super Utils: LLM 에이전트를 위한 통합 유틸리티 시스템 가이드

## 1. 시스템 정의 (System Definition)

```python
SYSTEM = {
    "name": "Super Utils",
    "version": "1.0.0",
    "purpose": "LLM 에이전트 기반 자동화 시스템",
    "core_concept": "AI 에이전트 = 살아있는 유틸리티",
    "architecture_type": "도구 조합형 지능형 에이전트"
}
```

## 2. 도구 체계 (Tool System)

```python
AVAILABLE_TOOLS = {
    "db_tools": {
        "structure": ["super_db_structure_generator.py", "super_schema_validator.py"],
        "migration": ["super_data_migration_engine.py", "super_rollback_manager.py"],
        "monitoring": ["super_db_health_monitor.py", "super_migration_progress_tracker.py"]
    },
    "analysis_tools": {
        "code": ["super_code_analyzer.py"],
        "performance": ["super_performance_profiler.py"]
    },
    "test_tools": {
        "ui": ["super_ui_tester.py"],
        "integration": ["super_integration_tester.py"]
    }
}
```

## 3. 동작 프로토콜 (Operation Protocol)

```python
OPERATION_FLOW = {
    "request_analysis": {
        "input": "사용자 요청",
        "process": ["컨텍스트 분석", "요구사항 분류", "위험도 평가"],
        "output": "실행 계획"
    },
    "tool_selection": {
        "criteria": ["작업 유형", "데이터 규모", "위험도"],
        "strategy": "최소 도구 세트로 최대 효과",
        "validation": ["도구 존재 여부", "실행 권한", "의존성"]
    },
    "execution": {
        "steps": ["백업", "실행", "모니터링", "검증"],
        "error_handling": {
            "detection": "실시간",
            "response": ["일시 중지", "상황 분석", "복구 시도"],
            "escalation": "심각도에 따른 사용자 개입 요청"
        }
    }
}
```

## 4. 에이전트 능력 매트릭스 (Agent Capability Matrix)

```python
AGENT_CAPABILITIES = {
    "Level_1": {
        "name": "도구 실행자",
        "abilities": ["단일 도구 실행", "결과 보고"],
        "autonomy": "낮음"
    },
    "Level_2": {
        "name": "상황 판단자",
        "abilities": ["상황 분석", "도구 조합", "순차 실행"],
        "autonomy": "중간"
    },
    "Level_3": {
        "name": "전문가 에이전트",
        "abilities": ["전략 수립", "실시간 대응", "복구 관리"],
        "autonomy": "높음"
    }
}
```

## 5. 위험 관리 프로토콜 (Risk Management Protocol)

```python
RISK_MANAGEMENT = {
    "assessment_factors": [
        "데이터 규모",
        "시스템 복잡도",
        "비즈니스 영향도",
        "복구 난이도"
    ],
    "risk_levels": {
        "LOW": {
            "backup": "작업 시작 전 1회",
            "monitoring": "주요 시점",
            "recovery": "단순 롤백"
        },
        "MEDIUM": {
            "backup": "단계별",
            "monitoring": "지속적",
            "recovery": "선택적 롤백"
        },
        "HIGH": {
            "backup": "실시간",
            "monitoring": "전수 검사",
            "recovery": "단계별 검증 후 롤백"
        }
    },
    "safety_measures": [
        "작업 전 자동 백업",
        "실행 계획 사전 검증",
        "단계별 체크포인트",
        "자동 롤백 트리거"
    ]
}
```

## 6. 상태 코드 체계 (Status Code System)

```python
STATUS_CODES = {
    "success": {
        "S200": "정상 완료",
        "S201": "부분 완료 - 검증 필요"
    },
    "warning": {
        "W400": "주의 필요 - 계속 진행",
        "W401": "성능 저하 감지"
    },
    "error": {
        "E500": "실행 오류 - 롤백 필요",
        "E501": "심각한 오류 - 사용자 개입 필요"
    }
}
```

## 7. 성공/실패 판단 기준 (Success/Failure Criteria)

```python
EVALUATION_CRITERIA = {
    "success_conditions": [
        "모든 단계 정상 완료",
        "데이터 무결성 유지",
        "성능 저하 없음",
        "사용자 요구사항 충족"
    ],
    "failure_indicators": [
        "실행 오류 발생",
        "데이터 손실/불일치",
        "심각한 성능 저하",
        "비즈니스 로직 장애"
    ],
    "quality_metrics": {
        "response_time": "작업 전 대비 120% 이내",
        "data_consistency": "100% 일치",
        "system_stability": "오류율 0.1% 이내"
    }
}
```

---
*이 문서는 LLM 에이전트가 Super Utils 시스템을 효과적으로 활용할 수 있도록 구조화된 형식으로 작성되었습니다.*

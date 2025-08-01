# 🔧 Super Util: DB Migrator Agent

## 📋 에이전트 정의

### 🎯 **전문 도메인**
데이터베이스 마이그레이션 및 구조 최적화

### 🧠 **핵심 역량**
- **위험 분석**: 마이그레이션 전 위험도 평가 및 대응 전략 수립
- **전략 수립**: 데이터 특성에 맞는 최적 마이그레이션 경로 설계  
- **실시간 대응**: 마이그레이션 중 문제 발생 시 즉시 판단 및 대응
- **구조/인스턴스 분리**: 설계도와 실제 데이터를 분리하여 관리

### 🛠️ **사용 도구 목록**
```yaml
핵심_도구:
  - super_db_structure_generator.py     # 구조 생성 및 스키마 설계
  - super_data_migration_engine.py      # 데이터 이관 및 변환
  - super_rollback_manager.py           # 백업 및 롤백 관리
  
검증_도구:
  - super_schema_validator.py           # 스키마 정합성 검증
  - super_db_health_monitor.py          # 성능 및 상태 모니터링
  
관리_도구:
  - super_migration_progress_tracker.py # 진행 상황 추적
```

---

## 🎭 에이전트 동작 모드

### Mode 1: **분석 모드** (Analysis Mode)
현재 DB 상태 파악 및 문제점 진단

### Mode 2: **계획 모드** (Planning Mode)  
최적 마이그레이션 전략 수립 및 위험도 평가

### Mode 3: **실행 모드** (Execution Mode)
단계별 마이그레이션 실행 및 실시간 모니터링

### Mode 4: **복구 모드** (Recovery Mode)
문제 발생 시 롤백 및 복구 작업

---

## 🎯 시나리오별 대응 전략

### 📊 **시나리오 1: 기본 DB 정리**
```yaml
요청_패턴: "DB 정리해줘", "테이블 구조 개선해줘"
판단_기준:
  - 테이블 수 < 20개
  - 중복/미사용 테이블 존재
  - 성능 이슈 없음
  
실행_계획:
  1. 현재 상태 분석 (super_db_health_monitor.py)
  2. 백업 생성 (super_rollback_manager.py) 
  3. 구조 최적화 (super_db_structure_generator.py)
  4. 검증 (super_schema_validator.py)
  
예상_소요시간: 30분 - 1시간
위험도: LOW
```

### 📊 **시나리오 2: 구조/인스턴스 분리 마이그레이션**  
```yaml
요청_패턴: "구조와 인스턴스 분리해줘", "2-DB 시스템으로 변경해줘"
판단_기준:
  - 현재 단일 DB에 구조+데이터 혼재
  - 사용자 생성 데이터 존재
  - 확장성 필요
  
실행_계획:
  1. 구조 분석 및 분리점 식별 (super_schema_validator.py)
  2. 전체 백업 (super_rollback_manager.py)
  3. settings.sqlite3 구조 생성 (super_db_structure_generator.py) 
  4. strategies.sqlite3 구조 생성 (super_db_structure_generator.py)
  5. 데이터 분류 및 이관 (super_data_migration_engine.py)
  6. 관계 무결성 검증 (super_schema_validator.py)
  7. 성능 테스트 (super_db_health_monitor.py)
  
예상_소요시간: 2-3시간
위험도: MEDIUM → LOW (백업 완료 시)
```

### 📊 **시나리오 3: 대용량 데이터 마이그레이션**
```yaml
요청_패턴: "trading_conditions 테이블 마이그레이션", "레거시 데이터 이관"
판단_기준:
  - 테이블 크기 > 10MB 또는 레코드 > 10,000개
  - 데이터 변환 필요
  - 비즈니스 로직 영향 존재
  
실행_계획:
  1. 데이터 볼륨 분석 (super_db_health_monitor.py)
  2. 단계별 백업 전략 수립 (super_rollback_manager.py)
  3. 스키마 호환성 검증 (super_schema_validator.py)
  4. 점진적 데이터 이관 (super_data_migration_engine.py)
     - 배치 단위: 1,000 레코드
     - 중간 검증점 설정
  5. 실시간 진행 모니터링 (super_migration_progress_tracker.py)
  6. 최종 무결성 검증 (super_schema_validator.py)
  
예상_소요시간: 4-6시간  
위험도: HIGH → MEDIUM (단계별 백업으로)
```

### 📊 **시나리오 4: 비상 복구**
```yaml
요청_패턴: "마이그레이션 실패", "원상복구해줘", "롤백해줘"
판단_기준:
  - 마이그레이션 중 오류 발생
  - 데이터 무결성 문제 발견
  - 성능 저하 심각
  
실행_계획:
  1. 즉시 현재 상태 분석 (super_db_health_monitor.py)
  2. 가장 최근 안전 체크포인트 식별 (super_rollback_manager.py)
  3. 자동 롤백 실행 (super_rollback_manager.py)
  4. 복구 검증 (super_schema_validator.py + super_db_health_monitor.py)
  5. 실패 원인 분석 보고서 생성
  
예상_소요시간: 15-30분
위험도: CRITICAL → LOW (롤백 완료 시)
```

---

## 🧠 에이전트 판단 로직

### 🔍 **1단계: 요청 분석**
```python
def analyze_user_request(user_input: str) -> RequestAnalysis:
    """사용자 요청을 분석하여 적절한 시나리오 매핑"""
    
    # 키워드 패턴 매칭
    patterns = {
        "basic_cleanup": ["정리", "개선", "최적화"],
        "structure_separation": ["분리", "2-DB", "구조", "인스턴스"],  
        "data_migration": ["마이그레이션", "이관", "테이블", "데이터"],
        "emergency_recovery": ["롤백", "복구", "실패", "원상복구"]
    }
    
    # 현재 DB 상태 고려
    current_state = analyze_current_db_state()
    
    # 위험도 평가
    risk_level = assess_risk_level(current_state, user_input)
    
    return RequestAnalysis(
        scenario=detected_scenario,
        risk_level=risk_level,
        estimated_time=calculate_time_estimate(),
        required_tools=determine_required_tools()
    )
```

### ⚖️ **2단계: 위험도 평가**
```python
def assess_migration_risk(db_state: DBState) -> RiskAssessment:
    """마이그레이션 위험도를 다각도로 평가"""
    
    risk_factors = {
        "data_volume": calculate_data_volume_risk(db_state),
        "table_complexity": analyze_table_relationships(db_state),
        "business_impact": assess_business_logic_impact(db_state),
        "backup_availability": check_backup_status(db_state),
        "system_stability": monitor_current_performance(db_state)
    }
    
    # 종합 위험도 계산
    overall_risk = calculate_weighted_risk(risk_factors)
    
    return RiskAssessment(
        level=overall_risk,  # LOW/MEDIUM/HIGH/CRITICAL
        factors=risk_factors,
        mitigation_strategies=generate_mitigation_plan(risk_factors),
        rollback_strategy=design_rollback_strategy(overall_risk)
    )
```

### 📋 **3단계: 실행 계획 수립**
```python
def generate_execution_plan(analysis: RequestAnalysis) -> ExecutionPlan:
    """분석 결과를 바탕으로 최적 실행 계획 생성"""
    
    # 시나리오별 기본 템플릿 로드
    base_plan = load_scenario_template(analysis.scenario)
    
    # 현재 상황에 맞게 계획 커스터마이징
    customized_plan = customize_plan(base_plan, analysis)
    
    # 안전장치 추가
    secured_plan = add_safety_measures(customized_plan, analysis.risk_level)
    
    return ExecutionPlan(
        phases=secured_plan.phases,
        tools=secured_plan.required_tools,
        checkpoints=secured_plan.checkpoints,
        rollback_points=secured_plan.rollback_points,
        estimated_duration=secured_plan.total_time
    )
```

---

## 🛡️ 안전장치 및 위험 관리

### 🎯 **체크포인트 전략**
```yaml
자동_백업_시점:
  - 마이그레이션 시작 전 (필수)
  - 각 Phase 완료 후 (선택적)
  - 오류 발생 직전 (자동)
  
백업_레벨:
  minimal: 스키마 구조만
  standard: 구조 + 중요 데이터
  full: 전체 시스템 백업
  
보관_정책:
  daily_backups: 7일간 보관
  milestone_backups: 영구 보관
  emergency_backups: 30일간 보관
```

### ⚡ **자동 롤백 조건**
```yaml
즉시_롤백_조건:
  - 데이터 손실 감지
  - Foreign Key 제약 위반  
  - 50% 이상 쿼리 실패
  - 메모리 사용량 90% 초과
  
경고_후_롤백_조건:
  - 성능 50% 이상 저하
  - 예상 시간 200% 초과
  - 데이터 불일치 발견
  
수동_개입_권장_조건:
  - 예상치 못한 스키마 차이 
  - 비즈니스 로직 영향 감지
  - 사용자 정의 함수 충돌
```

### 🚨 **실시간 모니터링 지표**
```yaml
핵심_지표:
  - 쿼리 응답 시간
  - 데이터 무결성 상태
  - 메모리/CPU 사용률
  - 진행률 vs 예상 시간
  
경고_임계값:
  query_timeout: 30초
  memory_usage: 80%
  error_rate: 5%
  progress_deviation: 50%
```

---

## 📊 에이전트 성과 지표

### ✅ **성공 기준**
```yaml
기능_성공:
  - 모든 계획된 단계 완료: 100%
  - 데이터 무결성 보장: 100%  
  - 롤백 가능성 유지: 항상
  
성능_기준:
  - 예상 시간 대비: ±20% 이내
  - 메모리 사용량: 기존 대비 150% 이내
  - 쿼리 성능: 기존 대비 120% 이내
  
사용자_만족:
  - 명확한 진행 상황 제공
  - 위험 요소 사전 알림
  - 문제 발생 시 즉시 대응
```

### 📈 **학습 및 개선**
```yaml
패턴_학습:
  - 성공한 전략 패턴 기록
  - 실패 원인 분석 및 개선
  - 사용자 피드백 반영
  
성능_최적화:
  - 도구 조합 효율성 분석
  - 병목 지점 식별 및 개선
  - 예측 정확도 향상
```

---

## 🎯 사용자 인터페이스

### 💬 **대화형 상호작용**
```markdown
사용자: "DB 마이그레이션 해줘"

에이전트: 
🔍 **현재 DB 상태 분석 중...**
- 테이블 수: 15개
- 총 데이터 크기: 45MB  
- 중복 테이블: 3개 발견
- 미사용 컬럼: 8개 발견

💡 **제안**: 구조/인스턴스 분리 + 정리 작업
- 예상 소요시간: 2시간 30분
- 위험도: MEDIUM → LOW (백업 완료 시)
- 백업 크기: 약 50MB

📋 **실행 계획**:
1. 전체 백업 생성 (15분)
2. settings.sqlite3 구조 생성 (30분)
3. strategies.sqlite3 구조 생성 (30분)  
4. 데이터 분류 및 이관 (60분)
5. 무결성 검증 (30분)
6. 성능 테스트 (15분)

🛡️ **안전장치**: 4개 체크포인트, 자동 롤백 지원

실행하시겠습니까? (y/n): 
```

### 📊 **실시간 진행 표시**
```markdown
🚀 **DB 마이그레이션 진행 중** (Phase 2/6)

├─ ✅ Phase 1: 백업 생성 완료 (15분)
├─ 🔄 Phase 2: settings.sqlite3 구조 생성 중... (진행률: 60%)
├─ ⏳ Phase 3: strategies.sqlite3 구조 생성 대기
├─ ⏳ Phase 4: 데이터 이관 대기  
├─ ⏳ Phase 5: 무결성 검증 대기
└─ ⏳ Phase 6: 성능 테스트 대기

⏱️ **예상 완료 시간**: 1시간 45분 후
🛡️ **최근 체크포인트**: Phase 1 완료 (15분 전)
📊 **시스템 상태**: 정상 (메모리: 45%, CPU: 20%)
```

---

## 🎉 에이전트 활용 가이드

### 🚀 **빠른 시작**
```markdown
1. 요청: "DB 마이그레이션 도움이 필요해요"
2. 분석: 에이전트가 현재 상태 파악
3. 계획: 맞춤형 실행 계획 제시
4. 승인: 계획 검토 후 실행 승인
5. 실행: 자동 실행 + 실시간 모니터링
6. 완료: 결과 보고 + 사후 관리 가이드
```

### 💡 **고급 활용법**
```markdown
# 특정 테이블만 마이그레이션
"trading_conditions 테이블을 user_triggers로 마이그레이션해줘"

# 성능 우선 마이그레이션  
"성능 저하 없이 DB 구조 개선해줘"

# 단계별 승인 모드
"각 단계마다 확인받고 진행해줘"

# 롤백 테스트
"마이그레이션 후 롤백이 잘 되는지 테스트해줘"
```

---

## 📚 관련 문서

### 🔗 **연관 가이드**
- `tools/planned_tools_blueprints.md` - 사용 도구 상세 명세
- `tasks/active/TASK-20250731-02_DB_Migration_Comprehensive_Safety_Plan.md` - 전체 마이그레이션 계획
- `.vscode/guides/database.md` - DB 설계 가이드

### 🛠️ **도구 사용법**
- 각 super_ 도구의 개별 사용법은 `tools/` 폴더 참조
- 도구 조합 전략은 에이전트가 자동 결정

---

**🎯 결론**: DB Migrator 에이전트는 복잡한 데이터베이스 작업을 **전문가 수준의 판단력**과 **자동화된 도구**로 안전하게 처리하는 지능형 시스템입니다.

---
**작성일**: 2025-08-01  
**버전**: 1.0  
**상태**: 설계 완료, 도구 연동 대기

# 🔍 디버깅 가이드

> **목적**: Clean Architecture에서 문제 추적 및 해결 방법  
> **대상**: LLM 에이전트, 개발자  
> **갱신**: 2025-08-03

## 🎯 디버깅 전략 개요

### 계층별 문제 진단 순서
```
1️⃣ 💎 Domain      ← 비즈니스 로직 오류 (가장 중요)
2️⃣ ⚙️ Application  ← 유스케이스 흐름 오류
3️⃣ 🔌 Infrastructure ← 외부 시스템 연동 오류
4️⃣ 🎨 Presentation ← UI 표시 문제 (가장 마지막)
```

### 문제 유형별 체크리스트
```python
DEBUGGING_CHECKLIST = {
    "기능 동작 안함": [
        "Domain: 비즈니스 규칙 검증",
        "Application: Command/Query 처리 확인", 
        "Infrastructure: DB/API 연결 상태",
        "Presentation: 사용자 입력 전달 확인"
    ],
    "데이터 저장 안됨": [
        "Domain: Entity 생성 실패?",
        "Application: 트랜잭션 문제?",
        "Infrastructure: Repository 오류?",
        "Presentation: 호출 누락?"
    ],
    "성능 저하": [
        "Domain: 알고리즘 복잡도",
        "Application: N+1 쿼리 문제",
        "Infrastructure: DB 인덱스",
        "Presentation: UI 렌더링"
    ]
}
```

## 💎 Domain Layer 디버깅

### 비즈니스 로직 디버깅
```python
class StrategyDebugger:
    """전략 Domain 로직 디버거"""
    
    def debug_rule_addition(self, strategy: Strategy, rule: TradingRule):
        """규칙 추가 과정 디버깅"""
        print(f"🔍 전략 '{strategy.name}' 규칙 추가 디버깅")
        print(f"  현재 규칙 수: {len(strategy.rules)}")
        print(f"  추가할 규칙: {rule.type}")
        
        try:
            # 비즈니스 규칙 검증 과정 추적
            if len(strategy.rules) >= 10:
                print("  ❌ 실패: 최대 규칙 수 초과")
                raise BusinessRuleViolationException("최대_규칙_제한", "10개 초과")
                
            if not self._is_compatible_rule(strategy, rule):
                print("  ❌ 실패: 호환되지 않는 규칙")
                raise IncompatibleVariableException(
                    strategy.rules[-1].variable_id if strategy.rules else "none",
                    rule.variable_id
                )
                
            strategy.rules.append(rule)
            print(f"  ✅ 성공: 규칙 추가 완료 (총 {len(strategy.rules)}개)")
            
        except Exception as e:
            print(f"  💥 예외 발생: {type(e).__name__}: {e}")
            raise
            
    def validate_strategy_state(self, strategy: Strategy):
        """전략 상태 검증"""
        issues = []
        
        if not strategy.name or strategy.name.strip() == "":
            issues.append("전략 이름이 비어있음")
            
        if len(strategy.rules) == 0:
            issues.append("규칙이 하나도 없음")
            
        if len(strategy.rules) > 10:
            issues.append(f"규칙 수 초과: {len(strategy.rules)}개 (최대 10개)")
            
        # 중복 규칙 검사
        rule_types = [rule.type for rule in strategy.rules]
        duplicates = [t for t in set(rule_types) if rule_types.count(t) > 1]
        if duplicates:
            issues.append(f"중복 규칙 발견: {duplicates}")
            
        if issues:
            print(f"⚠️ 전략 '{strategy.name}' 상태 이슈:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"✅ 전략 '{strategy.name}' 상태 정상")
            
        return len(issues) == 0
```

### Domain Event 추적
```python
class DomainEventTracker:
    """도메인 이벤트 추적기"""
    
    def __init__(self):
        self.event_log = []
        
    def track_entity_events(self, entity):
        """엔티티의 이벤트 추적"""
        if hasattr(entity, 'get_events'):
            events = entity.get_events()
            for event in events:
                self.event_log.append({
                    'timestamp': datetime.now(),
                    'entity_type': type(entity).__name__,
                    'entity_id': getattr(entity, 'id', 'unknown'),
                    'event_type': event.event_name,
                    'event_data': event.to_dict()
                })
                print(f"📅 이벤트 기록: {event.event_name} for {type(entity).__name__}")
                
    def print_event_history(self):
        """이벤트 히스토리 출력"""
        print("📜 도메인 이벤트 히스토리:")
        for i, event in enumerate(self.event_log, 1):
            print(f"  {i}. {event['timestamp'].strftime('%H:%M:%S')} - "
                  f"{event['event_type']} ({event['entity_type']})")
```

## ⚙️ Application Layer 디버깅

### Service 호출 추적
```python
import functools
import time

def debug_service_call(func):
    """서비스 호출 디버깅 데코레이터"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        service_name = self.__class__.__name__
        method_name = func.__name__
        
        print(f"🚀 서비스 호출: {service_name}.{method_name}")
        print(f"  인자: args={args}, kwargs={kwargs}")
        
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            execution_time = time.time() - start_time
            
            print(f"  ✅ 성공: {execution_time:.3f}초")
            print(f"  결과: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ 실패: {execution_time:.3f}초")
            print(f"  예외: {type(e).__name__}: {e}")
            raise
            
    return wrapper

class StrategyService:
    """디버깅이 적용된 전략 서비스"""
    
    @debug_service_call
    def create_strategy(self, command: CreateStrategyCommand) -> Result[str]:
        """전략 생성 서비스"""
        # 실제 구현...
        pass
        
    @debug_service_call
    def get_strategy(self, strategy_id: str) -> Result[Strategy]:
        """전략 조회 서비스"""
        # 실제 구현...
        pass
```

### Command/Query 처리 추적
```python
class CommandQueryDebugger:
    """Command/Query 처리 디버거"""
    
    def __init__(self):
        self.command_history = []
        self.query_history = []
        
    def debug_command(self, command):
        """Command 처리 디버깅"""
        command_info = {
            'timestamp': datetime.now(),
            'type': type(command).__name__,
            'data': vars(command)
        }
        self.command_history.append(command_info)
        
        print(f"📝 Command 처리: {command_info['type']}")
        for key, value in command_info['data'].items():
            print(f"  {key}: {value}")
            
    def debug_query(self, query, result):
        """Query 처리 디버깅"""
        query_info = {
            'timestamp': datetime.now(),
            'type': type(query).__name__,
            'result_type': type(result).__name__,
            'result_size': len(result) if hasattr(result, '__len__') else 'N/A'
        }
        self.query_history.append(query_info)
        
        print(f"🔍 Query 처리: {query_info['type']}")
        print(f"  결과 타입: {query_info['result_type']}")
        print(f"  결과 크기: {query_info['result_size']}")
        
    def print_command_summary(self):
        """Command 실행 요약"""
        print(f"📊 Command 실행 요약 (총 {len(self.command_history)}개):")
        command_counts = {}
        for cmd in self.command_history:
            cmd_type = cmd['type']
            command_counts[cmd_type] = command_counts.get(cmd_type, 0) + 1
            
        for cmd_type, count in command_counts.items():
            print(f"  {cmd_type}: {count}회")
```

## 🔌 Infrastructure Layer 디버깅

### Repository 디버깅
```python
class DebugRepository:
    """Repository 디버깅 래퍼"""
    
    def __init__(self, real_repository):
        self.real_repository = real_repository
        self.operation_log = []
        
    def save(self, entity):
        """저장 작업 디버깅"""
        print(f"💾 Repository 저장: {type(entity).__name__}")
        print(f"  Entity ID: {getattr(entity, 'id', 'unknown')}")
        
        start_time = time.time()
        try:
            result = self.real_repository.save(entity)
            execution_time = time.time() - start_time
            
            print(f"  ✅ 저장 성공: {execution_time:.3f}초")
            self._log_operation('save', entity, success=True, time=execution_time)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ 저장 실패: {execution_time:.3f}초")
            print(f"  오류: {e}")
            self._log_operation('save', entity, success=False, time=execution_time, error=e)
            raise
            
    def get_by_id(self, entity_id):
        """조회 작업 디버깅"""
        print(f"🔍 Repository 조회: ID={entity_id}")
        
        start_time = time.time()
        try:
            result = self.real_repository.get_by_id(entity_id)
            execution_time = time.time() - start_time
            
            print(f"  ✅ 조회 성공: {execution_time:.3f}초")
            print(f"  결과: {type(result).__name__}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ 조회 실패: {execution_time:.3f}초")
            print(f"  오류: {e}")
            raise
            
    def _log_operation(self, operation, entity, success, time, error=None):
        """작업 로그 기록"""
        self.operation_log.append({
            'timestamp': datetime.now(),
            'operation': operation,
            'entity_type': type(entity).__name__,
            'entity_id': getattr(entity, 'id', 'unknown'),
            'success': success,
            'execution_time': time,
            'error': str(error) if error else None
        })
```

### 데이터베이스 쿼리 분석
```python
class DatabaseQueryAnalyzer:
    """데이터베이스 쿼리 분석기"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.query_log = []
        
    def execute_with_analysis(self, query, params=None):
        """쿼리 실행 및 분석"""
        print(f"🗄️ SQL 실행: {query[:50]}...")
        if params:
            print(f"  파라미터: {params}")
            
        # 실행 계획 분석 (SQLite)
        explain_query = f"EXPLAIN QUERY PLAN {query}"
        explain_result = self.db.execute(explain_query, params or []).fetchall()
        
        print("  📊 실행 계획:")
        for row in explain_result:
            print(f"    {row}")
            
        # 실제 쿼리 실행
        start_time = time.time()
        try:
            result = self.db.execute(query, params or [])
            execution_time = time.time() - start_time
            
            if query.strip().upper().startswith('SELECT'):
                row_count = len(result.fetchall())
                print(f"  ✅ 조회 완료: {row_count}건, {execution_time:.3f}초")
            else:
                print(f"  ✅ 실행 완료: {execution_time:.3f}초")
                
            self._log_query(query, params, execution_time, success=True)
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"  ❌ 실행 실패: {execution_time:.3f}초")
            print(f"  오류: {e}")
            self._log_query(query, params, execution_time, success=False, error=e)
            raise
            
    def _log_query(self, query, params, time, success, error=None):
        """쿼리 실행 로그"""
        self.query_log.append({
            'timestamp': datetime.now(),
            'query': query,
            'params': params,
            'execution_time': time,
            'success': success,
            'error': str(error) if error else None
        })
        
    def get_slow_queries(self, threshold_seconds=1.0):
        """느린 쿼리 목록 반환"""
        slow_queries = [
            log for log in self.query_log 
            if log['execution_time'] > threshold_seconds
        ]
        
        print(f"🐌 느린 쿼리 ({len(slow_queries)}개):")
        for query_log in slow_queries:
            print(f"  {query_log['execution_time']:.3f}초: {query_log['query'][:50]}...")
            
        return slow_queries
```

## 🎨 Presentation Layer 디버깅

### UI 상태 추적
```python
class UIStateTracker:
    """UI 상태 추적기"""
    
    def __init__(self):
        self.state_history = []
        
    def track_state_change(self, widget_name, old_state, new_state):
        """UI 상태 변경 추적"""
        change = {
            'timestamp': datetime.now(),
            'widget': widget_name,
            'old_state': old_state,
            'new_state': new_state
        }
        self.state_history.append(change)
        
        print(f"🎨 UI 상태 변경: {widget_name}")
        print(f"  이전: {old_state}")
        print(f"  현재: {new_state}")
        
    def print_state_history(self):
        """상태 변경 히스토리 출력"""
        print("📜 UI 상태 변경 히스토리:")
        for i, change in enumerate(self.state_history[-10:], 1):  # 최근 10개만
            print(f"  {i}. {change['timestamp'].strftime('%H:%M:%S')} - "
                  f"{change['widget']}: {change['old_state']} → {change['new_state']}")

class DebugPresenter:
    """디버깅이 적용된 Presenter"""
    
    def __init__(self, view, service):
        self.view = view
        self.service = service
        self.state_tracker = UIStateTracker()
        
    def on_variable_selected(self, variable_id):
        """변수 선택 이벤트 디버깅"""
        print(f"🎯 Presenter: 변수 선택됨 - {variable_id}")
        
        try:
            # 1. 이전 상태 기록
            old_state = getattr(self, '_current_variable', None)
            self.state_tracker.track_state_change(
                'selected_variable', old_state, variable_id
            )
            
            # 2. 서비스 호출
            compatible_vars = self.service.get_compatible_variables(variable_id)
            print(f"  호환 변수 {len(compatible_vars)}개 발견")
            
            # 3. View 업데이트
            self.view.update_compatible_variables(compatible_vars)
            self._current_variable = variable_id
            
            print(f"  ✅ 변수 선택 처리 완료")
            
        except Exception as e:
            print(f"  ❌ 변수 선택 처리 실패: {e}")
            self.view.show_error_message("변수 선택 중 오류가 발생했습니다")
```

## 🚀 디버깅 도구 및 유틸리티

### 종합 디버거
```python
class CleanArchitectureDebugger:
    """Clean Architecture 종합 디버거"""
    
    def __init__(self):
        self.domain_debugger = StrategyDebugger()
        self.event_tracker = DomainEventTracker()
        self.command_debugger = CommandQueryDebugger()
        self.ui_tracker = UIStateTracker()
        
    def enable_full_debugging(self):
        """전체 계층 디버깅 활성화"""
        print("🔧 Clean Architecture 전체 디버깅 활성화")
        
        # 각 계층별 디버깅 설정
        self._setup_domain_debugging()
        self._setup_application_debugging()
        self._setup_infrastructure_debugging()
        self._setup_presentation_debugging()
        
    def generate_debug_report(self):
        """디버깅 종합 리포트 생성"""
        report = {
            'timestamp': datetime.now(),
            'domain_events': len(self.event_tracker.event_log),
            'commands_processed': len(self.command_debugger.command_history),
            'queries_processed': len(self.command_debugger.query_history),
            'ui_state_changes': len(self.ui_tracker.state_history)
        }
        
        print("📊 디버깅 종합 리포트:")
        for key, value in report.items():
            print(f"  {key}: {value}")
            
        return report
        
    def find_bottlenecks(self):
        """성능 병목점 분석"""
        print("🔍 성능 병목점 분석:")
        
        # 느린 쿼리 찾기
        # 긴 실행 시간의 서비스 호출 찾기
        # UI 응답 지연 찾기
        
        bottlenecks = []
        # 구체적 분석 로직...
        
        if not bottlenecks:
            print("  ✅ 발견된 병목점 없음")
        else:
            for bottleneck in bottlenecks:
                print(f"  ⚠️ {bottleneck}")
                
        return bottlenecks
```

### 로그 파일 분석
```python
class LogAnalyzer:
    """로그 파일 분석기"""
    
    def analyze_log_file(self, log_file_path):
        """로그 파일 분석"""
        error_patterns = [
            r'ERROR.*',
            r'Exception.*',
            r'Failed.*',
            r'❌.*'
        ]
        
        warning_patterns = [
            r'WARNING.*',
            r'⚠️.*'
        ]
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        errors = []
        warnings = []
        
        for line_num, line in enumerate(lines, 1):
            for pattern in error_patterns:
                if re.search(pattern, line):
                    errors.append((line_num, line.strip()))
                    break
                    
            for pattern in warning_patterns:
                if re.search(pattern, line):
                    warnings.append((line_num, line.strip()))
                    break
                    
        print(f"📋 로그 분석 결과 ({log_file_path}):")
        print(f"  총 라인 수: {len(lines)}")
        print(f"  에러: {len(errors)}개")
        print(f"  경고: {len(warnings)}개")
        
        if errors:
            print("\n❌ 발견된 에러들:")
            for line_num, error in errors[-5:]:  # 최근 5개
                print(f"  {line_num}: {error}")
                
        return {'errors': errors, 'warnings': warnings}
```

## 📚 관련 문서

- [시스템 개요](01_SYSTEM_OVERVIEW.md): 디버깅 대상 아키텍처
- [에러 처리](10_ERROR_HANDLING.md): 예외 상황 처리 방법
- [성능 최적화](09_PERFORMANCE_OPTIMIZATION.md): 성능 문제 해결
- [문제 해결](06_TROUBLESHOOTING.md): 일반적인 문제 해결책

---
**💡 핵심**: "각 계층의 책임에 맞는 디버깅 도구를 사용하여 문제를 체계적으로 추적하세요!"

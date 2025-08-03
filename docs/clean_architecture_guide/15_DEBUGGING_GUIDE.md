# 🔍 Clean Architecture 디버깅 가이드

> **목적**: Clean Architecture 시스템에서 발생하는 문제를 체계적으로 진단하고 해결하는 방법  
> **대상**: 개발자, 시스템 관리자  
> **예상 읽기 시간**: 18분

## 🎯 디버깅 전략 개요

### 📋 계층별 디버깅 접근법
1. **Presentation Layer**: UI 반응성, 사용자 입력 처리
2. **Application Layer**: 비즈니스 플로우, 유스케이스 실행
3. **Domain Layer**: 비즈니스 로직, 도메인 규칙
4. **Infrastructure Layer**: 데이터베이스, 외부 API, 파일 시스템
5. **Shared Layer**: 공통 유틸리티, 설정

### 🔧 디버깅 도구
- **로깅 시스템**: 계층별 상세 로그
- **성능 프로파일링**: 병목 지점 식별
- **단위 테스트**: 격리된 컴포넌트 검증
- **통합 테스트**: 계층 간 상호작용 검증

## 🎨 Presentation Layer 디버깅

### 1. UI 응답성 문제
```python
# presentation/debugging/ui_performance_debugger.py
import time
from functools import wraps
from typing import Dict, List
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

class UIPerformanceDebugger(QObject):
    """UI 성능 디버깅 도구"""
    
    performance_alert = pyqtSignal(str, float)  # 메서드명, 실행시간
    
    def __init__(self):
        super().__init__()
        self.performance_log: List[Dict] = []
        self.slow_operations_threshold = 100  # ms
    
    def monitor_method(self, threshold_ms: float = 100):
        """메서드 성능 모니터링 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # 성능 로그 기록
                    log_entry = {
                        'method': f"{func.__qualname__}",
                        'execution_time_ms': round(execution_time, 2),
                        'timestamp': time.time(),
                        'args_count': len(args),
                        'kwargs_count': len(kwargs)
                    }
                    self.performance_log.append(log_entry)
                    
                    # 임계값 초과 시 알림
                    if execution_time > threshold_ms:
                        self.performance_alert.emit(func.__qualname__, execution_time)
                        print(f"⚠️ 느린 UI 동작 감지: {func.__qualname__} - {execution_time:.2f}ms")
                    
                    return result
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    print(f"❌ UI 메서드 실행 오류: {func.__qualname__} - {str(e)}")
                    raise
            
            return wrapper
        return decorator
    
    def get_slow_operations(self, limit: int = 10) -> List[Dict]:
        """느린 동작 목록 조회"""
        slow_ops = [log for log in self.performance_log 
                   if log['execution_time_ms'] > self.slow_operations_threshold]
        
        return sorted(slow_ops, key=lambda x: x['execution_time_ms'], reverse=True)[:limit]
    
    def generate_performance_report(self) -> Dict:
        """성능 리포트 생성"""
        if not self.performance_log:
            return {'message': '성능 데이터 없음'}
        
        total_operations = len(self.performance_log)
        avg_time = sum(log['execution_time_ms'] for log in self.performance_log) / total_operations
        slow_operations = len([log for log in self.performance_log 
                              if log['execution_time_ms'] > self.slow_operations_threshold])
        
        # 가장 자주 호출되는 메서드
        method_calls = {}
        for log in self.performance_log:
            method_name = log['method']
            if method_name not in method_calls:
                method_calls[method_name] = {'count': 0, 'total_time': 0}
            method_calls[method_name]['count'] += 1
            method_calls[method_name]['total_time'] += log['execution_time_ms']
        
        most_called = sorted(method_calls.items(), 
                           key=lambda x: x[1]['count'], reverse=True)[:5]
        
        return {
            'total_operations': total_operations,
            'average_time_ms': round(avg_time, 2),
            'slow_operations_count': slow_operations,
            'slow_operations_rate': round(slow_operations / total_operations * 100, 2),
            'most_called_methods': most_called,
            'slowest_operations': self.get_slow_operations(5)
        }

# UI 이벤트 디버깅
class UIEventDebugger:
    """UI 이벤트 디버깅 도구"""
    
    def __init__(self):
        self.event_log: List[Dict] = []
        self.event_filters = []
    
    def log_event(self, event_type: str, widget_name: str, details: Dict = None):
        """이벤트 로깅"""
        log_entry = {
            'timestamp': time.time(),
            'event_type': event_type,
            'widget_name': widget_name,
            'details': details or {},
            'thread_id': threading.current_thread().ident
        }
        
        self.event_log.append(log_entry)
        
        # 필터링된 이벤트만 출력
        if self._should_log_event(event_type):
            print(f"🎯 UI 이벤트: {event_type} on {widget_name}")
            if details:
                for key, value in details.items():
                    print(f"   {key}: {value}")
    
    def _should_log_event(self, event_type: str) -> bool:
        """이벤트 로깅 여부 결정"""
        if not self.event_filters:
            return True  # 필터가 없으면 모든 이벤트 로깅
        
        return event_type in self.event_filters
    
    def set_event_filters(self, event_types: List[str]):
        """이벤트 필터 설정"""
        self.event_filters = event_types
    
    def get_recent_events(self, count: int = 20) -> List[Dict]:
        """최근 이벤트 조회"""
        return self.event_log[-count:] if self.event_log else []

# 실제 사용 예시
class DebuggedStrategyView(QWidget):
    """디버깅이 적용된 전략 뷰"""
    
    def __init__(self):
        super().__init__()
        self.performance_debugger = UIPerformanceDebugger()
        self.event_debugger = UIEventDebugger()
        self.setup_ui()
        self.setup_debugging()
    
    def setup_debugging(self):
        """디버깅 설정"""
        # 성능 알림 연결
        self.performance_debugger.performance_alert.connect(self.on_performance_alert)
        
        # 이벤트 필터 설정 (관심 있는 이벤트만)
        self.event_debugger.set_event_filters([
            'button_click', 'strategy_creation', 'backtest_start', 'data_load'
        ])
    
    @UIPerformanceDebugger().monitor_method(threshold_ms=50)
    def create_strategy(self, strategy_config: Dict):
        """전략 생성 (성능 모니터링 적용)"""
        self.event_debugger.log_event('strategy_creation', 'StrategyView', {
            'strategy_type': strategy_config.get('type'),
            'parameter_count': len(strategy_config)
        })
        
        # 실제 전략 생성 로직
        time.sleep(0.1)  # 시뮬레이션
        
        return "strategy_created"
    
    def on_performance_alert(self, method_name: str, execution_time: float):
        """성능 알림 처리"""
        if execution_time > 200:  # 200ms 이상
            QMessageBox.warning(
                self, 
                "성능 경고", 
                f"UI 동작이 느립니다:\n{method_name}\n실행 시간: {execution_time:.2f}ms"
            )
```

### 2. 사용자 입력 검증 디버깅
```python
# presentation/debugging/input_validation_debugger.py
class InputValidationDebugger:
    """입력 검증 디버깅 도구"""
    
    def __init__(self):
        self.validation_log: List[Dict] = []
    
    def debug_validation(self, field_name: str, value, validation_result: bool, 
                        error_message: str = None):
        """입력 검증 디버깅"""
        log_entry = {
            'timestamp': time.time(),
            'field_name': field_name,
            'value': str(value)[:100],  # 값이 너무 길면 자르기
            'value_type': type(value).__name__,
            'is_valid': validation_result,
            'error_message': error_message
        }
        
        self.validation_log.append(log_entry)
        
        if not validation_result:
            print(f"❌ 입력 검증 실패: {field_name}")
            print(f"   값: {value}")
            print(f"   오류: {error_message}")
    
    def get_validation_failures(self, hours: int = 1) -> List[Dict]:
        """최근 검증 실패 목록"""
        cutoff_time = time.time() - (hours * 3600)
        
        return [log for log in self.validation_log 
                if log['timestamp'] > cutoff_time and not log['is_valid']]
    
    def get_validation_stats(self) -> Dict:
        """검증 통계"""
        if not self.validation_log:
            return {'message': '검증 데이터 없음'}
        
        total_validations = len(self.validation_log)
        failed_validations = len([log for log in self.validation_log if not log['is_valid']])
        
        # 필드별 실패율
        field_failures = {}
        for log in self.validation_log:
            field_name = log['field_name']
            if field_name not in field_failures:
                field_failures[field_name] = {'total': 0, 'failed': 0}
            
            field_failures[field_name]['total'] += 1
            if not log['is_valid']:
                field_failures[field_name]['failed'] += 1
        
        # 실패율 계산
        for field_name, stats in field_failures.items():
            stats['failure_rate'] = (stats['failed'] / stats['total']) * 100
        
        return {
            'total_validations': total_validations,
            'failed_validations': failed_validations,
            'overall_failure_rate': round((failed_validations / total_validations) * 100, 2),
            'field_failure_rates': field_failures
        }
```

## ⚙️ Application Layer 디버깅

### 1. 유스케이스 실행 추적
```python
# application/debugging/usecase_tracer.py
class UseCaseTracer:
    """유스케이스 실행 추적기"""
    
    def __init__(self):
        self.execution_log: List[Dict] = []
        self.active_executions: Dict[str, Dict] = {}
    
    def trace_execution(self, usecase_name: str):
        """유스케이스 실행 추적 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                execution_id = f"{usecase_name}_{int(time.time() * 1000)}"
                
                # 실행 시작 기록
                start_time = time.time()
                self.active_executions[execution_id] = {
                    'usecase': usecase_name,
                    'start_time': start_time,
                    'status': 'running'
                }
                
                print(f"🚀 유스케이스 시작: {usecase_name} [{execution_id}]")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # 성공 기록
                    execution_time = time.time() - start_time
                    self._record_completion(execution_id, 'success', execution_time)
                    
                    print(f"✅ 유스케이스 완료: {usecase_name} ({execution_time:.3f}s)")
                    return result
                    
                except Exception as e:
                    # 실패 기록
                    execution_time = time.time() - start_time
                    self._record_completion(execution_id, 'failed', execution_time, str(e))
                    
                    print(f"❌ 유스케이스 실패: {usecase_name} - {str(e)}")
                    raise
                
                finally:
                    # 활성 실행 목록에서 제거
                    self.active_executions.pop(execution_id, None)
            
            return wrapper
        return decorator
    
    def _record_completion(self, execution_id: str, status: str, 
                          execution_time: float, error_message: str = None):
        """실행 완료 기록"""
        execution_info = self.active_executions.get(execution_id, {})
        
        log_entry = {
            'execution_id': execution_id,
            'usecase': execution_info.get('usecase'),
            'start_time': execution_info.get('start_time'),
            'execution_time': execution_time,
            'status': status,
            'error_message': error_message,
            'timestamp': time.time()
        }
        
        self.execution_log.append(log_entry)
    
    def get_active_executions(self) -> List[Dict]:
        """현재 실행 중인 유스케이스 목록"""
        current_time = time.time()
        
        active_list = []
        for execution_id, info in self.active_executions.items():
            running_time = current_time - info['start_time']
            active_list.append({
                'execution_id': execution_id,
                'usecase': info['usecase'],
                'running_time': round(running_time, 2),
                'status': info['status']
            })
        
        return active_list
    
    def get_execution_statistics(self, hours: int = 24) -> Dict:
        """실행 통계"""
        cutoff_time = time.time() - (hours * 3600)
        recent_executions = [log for log in self.execution_log 
                           if log['timestamp'] > cutoff_time]
        
        if not recent_executions:
            return {'message': f'최근 {hours}시간 동안 실행 기록 없음'}
        
        total_executions = len(recent_executions)
        successful_executions = len([log for log in recent_executions 
                                   if log['status'] == 'success'])
        failed_executions = total_executions - successful_executions
        
        # 평균 실행 시간
        avg_execution_time = sum(log['execution_time'] for log in recent_executions) / total_executions
        
        # 유스케이스별 통계
        usecase_stats = {}
        for log in recent_executions:
            usecase = log['usecase']
            if usecase not in usecase_stats:
                usecase_stats[usecase] = {
                    'total': 0, 'success': 0, 'failed': 0, 'total_time': 0
                }
            
            stats = usecase_stats[usecase]
            stats['total'] += 1
            stats['total_time'] += log['execution_time']
            
            if log['status'] == 'success':
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        # 성공률 및 평균 시간 계산
        for usecase, stats in usecase_stats.items():
            stats['success_rate'] = (stats['success'] / stats['total']) * 100
            stats['avg_time'] = stats['total_time'] / stats['total']
        
        return {
            'period_hours': hours,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'overall_success_rate': round((successful_executions / total_executions) * 100, 2),
            'average_execution_time': round(avg_execution_time, 3),
            'usecase_statistics': usecase_stats
        }

# 사용 예시
tracer = UseCaseTracer()

class CreateStrategyUseCase:
    """전략 생성 유스케이스 (디버깅 적용)"""
    
    @tracer.trace_execution("CreateStrategy")
    def execute(self, command: CreateStrategyCommand) -> CreateStrategyResult:
        """전략 생성 실행"""
        
        # 단계별 디버깅 로그
        print(f"🔍 전략 타입: {command.strategy_config.get('type')}")
        print(f"🔍 전략 이름: {command.strategy_config.get('name')}")
        
        # 검증 단계
        validation_result = self.strategy_validator.validate(command.strategy_config)
        if not validation_result.is_valid:
            print(f"❌ 검증 실패: {validation_result.error_message}")
            return CreateStrategyResult.failure(validation_result.error_message)
        
        print("✅ 전략 설정 검증 완료")
        
        # 전략 생성 단계
        try:
            strategy = self.strategy_factory.create_strategy(command.strategy_config)
            print(f"✅ 전략 객체 생성 완료: {strategy.id.value}")
        except Exception as e:
            print(f"❌ 전략 객체 생성 실패: {str(e)}")
            raise
        
        # 저장 단계
        try:
            saved_strategy = self.strategy_repository.save(strategy)
            print(f"✅ 전략 저장 완료: {saved_strategy.id.value}")
        except Exception as e:
            print(f"❌ 전략 저장 실패: {str(e)}")
            raise
        
        return CreateStrategyResult.success(saved_strategy.id.value)
```

### 2. 의존성 주입 디버깅
```python
# application/debugging/dependency_tracer.py
class DependencyTracer:
    """의존성 주입 추적기"""
    
    def __init__(self):
        self.injection_log: List[Dict] = []
        self.dependency_graph: Dict[str, List[str]] = {}
    
    def trace_injection(self, target_class: str, dependency_name: str, 
                       dependency_type: str):
        """의존성 주입 추적"""
        log_entry = {
            'timestamp': time.time(),
            'target_class': target_class,
            'dependency_name': dependency_name,
            'dependency_type': dependency_type
        }
        
        self.injection_log.append(log_entry)
        
        # 의존성 그래프 구성
        if target_class not in self.dependency_graph:
            self.dependency_graph[target_class] = []
        
        if dependency_name not in self.dependency_graph[target_class]:
            self.dependency_graph[target_class].append(dependency_name)
        
        print(f"🔗 의존성 주입: {target_class} <- {dependency_name} ({dependency_type})")
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """의존성 그래프 조회"""
        return self.dependency_graph
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """순환 의존성 탐지"""
        # 간단한 순환 의존성 탐지 알고리즘
        circular_deps = []
        
        def dfs(node: str, visited: set, path: List[str]):
            if node in visited:
                # 순환 발견
                cycle_start = path.index(node)
                circular_deps.append(path[cycle_start:] + [node])
                return
            
            visited.add(node)
            path.append(node)
            
            for dependency in self.dependency_graph.get(node, []):
                dfs(dependency, visited.copy(), path.copy())
        
        for start_node in self.dependency_graph:
            dfs(start_node, set(), [])
        
        return circular_deps
    
    def generate_dependency_report(self) -> Dict:
        """의존성 리포트 생성"""
        total_classes = len(self.dependency_graph)
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        
        # 가장 많은 의존성을 가진 클래스
        max_deps_class = max(self.dependency_graph.items(), 
                           key=lambda x: len(x[1]), default=('', []))
        
        # 순환 의존성 체크
        circular_deps = self.find_circular_dependencies()
        
        return {
            'total_classes': total_classes,
            'total_dependencies': total_dependencies,
            'average_dependencies_per_class': round(total_dependencies / total_classes, 2) if total_classes > 0 else 0,
            'class_with_most_dependencies': {
                'class_name': max_deps_class[0],
                'dependency_count': len(max_deps_class[1])
            },
            'circular_dependencies': circular_deps,
            'dependency_graph': self.dependency_graph
        }
```

## 💎 Domain Layer 디버깅

### 1. 도메인 이벤트 추적
```python
# domain/debugging/domain_event_tracer.py
class DomainEventTracer:
    """도메인 이벤트 추적기"""
    
    def __init__(self):
        self.event_log: List[Dict] = []
        self.event_handlers: Dict[str, List[str]] = {}
    
    def trace_event(self, event_name: str, event_data: Dict, 
                   aggregate_id: str = None):
        """도메인 이벤트 추적"""
        log_entry = {
            'timestamp': time.time(),
            'event_name': event_name,
            'event_data': event_data,
            'aggregate_id': aggregate_id,
            'event_id': f"evt_{int(time.time() * 1000)}"
        }
        
        self.event_log.append(log_entry)
        
        print(f"📡 도메인 이벤트: {event_name}")
        if aggregate_id:
            print(f"   Aggregate ID: {aggregate_id}")
        print(f"   데이터: {event_data}")
    
    def trace_event_handler(self, event_name: str, handler_name: str, 
                          execution_time: float, success: bool, 
                          error_message: str = None):
        """이벤트 핸들러 실행 추적"""
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
        
        handler_info = {
            'handler_name': handler_name,
            'execution_time': execution_time,
            'success': success,
            'error_message': error_message,
            'timestamp': time.time()
        }
        
        self.event_handlers[event_name].append(handler_info)
        
        status = "✅" if success else "❌"
        print(f"{status} 이벤트 핸들러: {handler_name} ({execution_time:.3f}s)")
        if not success and error_message:
            print(f"   오류: {error_message}")
    
    def get_event_statistics(self, hours: int = 24) -> Dict:
        """이벤트 통계"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [log for log in self.event_log 
                        if log['timestamp'] > cutoff_time]
        
        if not recent_events:
            return {'message': f'최근 {hours}시간 동안 도메인 이벤트 없음'}
        
        # 이벤트 타입별 통계
        event_counts = {}
        for event in recent_events:
            event_name = event['event_name']
            event_counts[event_name] = event_counts.get(event_name, 0) + 1
        
        # 핸들러 성능 통계
        handler_stats = {}
        for event_name, handlers in self.event_handlers.items():
            for handler in handlers:
                if handler['timestamp'] > cutoff_time:
                    handler_name = handler['handler_name']
                    if handler_name not in handler_stats:
                        handler_stats[handler_name] = {
                            'total_executions': 0,
                            'successful_executions': 0,
                            'total_time': 0,
                            'errors': []
                        }
                    
                    stats = handler_stats[handler_name]
                    stats['total_executions'] += 1
                    stats['total_time'] += handler['execution_time']
                    
                    if handler['success']:
                        stats['successful_executions'] += 1
                    else:
                        stats['errors'].append(handler['error_message'])
        
        # 평균 실행 시간 계산
        for handler_name, stats in handler_stats.items():
            stats['average_time'] = stats['total_time'] / stats['total_executions']
            stats['success_rate'] = (stats['successful_executions'] / stats['total_executions']) * 100
        
        return {
            'period_hours': hours,
            'total_events': len(recent_events),
            'event_type_counts': event_counts,
            'handler_performance': handler_stats
        }

# 사용 예시
event_tracer = DomainEventTracer()

class TrailingStopStrategy:
    """트레일링 스탑 전략 (이벤트 추적 적용)"""
    
    def update_trailing_stop(self, current_price: Decimal):
        """트레일링 스탑 업데이트"""
        old_stop_price = self.stop_price
        
        if current_price > self.highest_price:
            self.highest_price = current_price
            new_stop_price = current_price * (1 - self.trail_distance)
            
            if new_stop_price > self.stop_price:
                self.stop_price = new_stop_price
                
                # 도메인 이벤트 발생
                event_tracer.trace_event(
                    'TrailingStopUpdated',
                    {
                        'old_stop_price': float(old_stop_price),
                        'new_stop_price': float(new_stop_price),
                        'current_price': float(current_price),
                        'highest_price': float(self.highest_price)
                    },
                    aggregate_id=self.id.value
                )
```

## 🔌 Infrastructure Layer 디버깅

### 1. 데이터베이스 연결 및 쿼리 디버깅
```python
# infrastructure/debugging/database_debugger.py
class DatabaseDebugger:
    """데이터베이스 디버깅 도구"""
    
    def __init__(self):
        self.query_log: List[Dict] = []
        self.connection_log: List[Dict] = []
        self.slow_query_threshold = 100  # ms
    
    def trace_query(self, query: str, params: tuple = None):
        """쿼리 실행 추적 데코레이터"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # 쿼리 로그 기록
                    log_entry = {
                        'timestamp': time.time(),
                        'query': query[:200] + "..." if len(query) > 200 else query,
                        'params': str(params)[:100] if params else None,
                        'execution_time_ms': round(execution_time, 2),
                        'success': True,
                        'result_count': len(result) if isinstance(result, (list, tuple)) else 1
                    }
                    
                    self.query_log.append(log_entry)
                    
                    # 느린 쿼리 알림
                    if execution_time > self.slow_query_threshold:
                        print(f"🐌 느린 쿼리 감지: {execution_time:.2f}ms")
                        print(f"   쿼리: {query[:100]}...")
                    
                    return result
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    
                    # 실패 로그 기록
                    log_entry = {
                        'timestamp': time.time(),
                        'query': query[:200] + "..." if len(query) > 200 else query,
                        'params': str(params)[:100] if params else None,
                        'execution_time_ms': round(execution_time, 2),
                        'success': False,
                        'error_message': str(e)
                    }
                    
                    self.query_log.append(log_entry)
                    
                    print(f"❌ 쿼리 실행 실패: {str(e)}")
                    print(f"   쿼리: {query[:100]}...")
                    raise
            
            return wrapper
        return decorator
    
    def trace_connection(self, db_name: str, db_path: str):
        """데이터베이스 연결 추적"""
        connection_info = {
            'timestamp': time.time(),
            'db_name': db_name,
            'db_path': db_path,
            'status': 'attempting'
        }
        
        try:
            # 연결 테스트
            import sqlite3
            conn = sqlite3.connect(db_path, timeout=5.0)
            conn.execute("SELECT 1")
            conn.close()
            
            connection_info['status'] = 'success'
            print(f"✅ DB 연결 성공: {db_name}")
            
        except Exception as e:
            connection_info['status'] = 'failed'
            connection_info['error_message'] = str(e)
            print(f"❌ DB 연결 실패: {db_name} - {str(e)}")
        
        self.connection_log.append(connection_info)
        return connection_info['status'] == 'success'
    
    def get_slow_queries(self, limit: int = 10) -> List[Dict]:
        """느린 쿼리 목록"""
        slow_queries = [log for log in self.query_log 
                       if log['execution_time_ms'] > self.slow_query_threshold]
        
        return sorted(slow_queries, 
                     key=lambda x: x['execution_time_ms'], reverse=True)[:limit]
    
    def get_database_health_report(self) -> Dict:
        """데이터베이스 건강성 리포트"""
        if not self.query_log:
            return {'message': '쿼리 실행 기록 없음'}
        
        total_queries = len(self.query_log)
        successful_queries = len([log for log in self.query_log if log['success']])
        failed_queries = total_queries - successful_queries
        
        # 평균 실행 시간
        avg_execution_time = sum(log['execution_time_ms'] for log in self.query_log) / total_queries
        
        # 느린 쿼리 통계
        slow_queries = self.get_slow_queries()
        
        # 연결 통계
        connection_attempts = len(self.connection_log)
        successful_connections = len([log for log in self.connection_log 
                                    if log['status'] == 'success'])
        
        return {
            'query_statistics': {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'failed_queries': failed_queries,
                'success_rate': round((successful_queries / total_queries) * 100, 2),
                'average_execution_time_ms': round(avg_execution_time, 2),
                'slow_queries_count': len(slow_queries)
            },
            'connection_statistics': {
                'total_attempts': connection_attempts,
                'successful_connections': successful_connections,
                'connection_success_rate': round((successful_connections / connection_attempts) * 100, 2) if connection_attempts > 0 else 0
            },
            'slowest_queries': slow_queries[:5]
        }
```

## 🎯 통합 디버깅 대시보드

### 1. 종합 디버깅 매니저
```python
# debugging/integrated_debugger.py
class IntegratedDebuggingManager:
    """통합 디버깅 관리자"""
    
    def __init__(self):
        self.ui_debugger = UIPerformanceDebugger()
        self.usecase_tracer = UseCaseTracer()
        self.event_tracer = DomainEventTracer()
        self.db_debugger = DatabaseDebugger()
        self.dependency_tracer = DependencyTracer()
    
    def generate_comprehensive_report(self) -> Dict:
        """종합 디버깅 리포트 생성"""
        report = {
            'timestamp': time.time(),
            'system_health': {
                'ui_performance': self.ui_debugger.generate_performance_report(),
                'usecase_execution': self.usecase_tracer.get_execution_statistics(),
                'domain_events': self.event_tracer.get_event_statistics(),
                'database_health': self.db_debugger.get_database_health_report(),
                'dependency_analysis': self.dependency_tracer.generate_dependency_report()
            }
        }
        
        # 전반적인 건강성 점수 계산
        health_score = self._calculate_health_score(report['system_health'])
        report['overall_health_score'] = health_score
        
        return report
    
    def _calculate_health_score(self, health_data: Dict) -> int:
        """시스템 건강성 점수 계산 (0-100)"""
        score = 100
        
        # UI 성능 점수
        ui_perf = health_data.get('ui_performance', {})
        if 'slow_operations_rate' in ui_perf:
            slow_rate = ui_perf['slow_operations_rate']
            score -= min(slow_rate * 2, 20)  # 최대 20점 감점
        
        # 유스케이스 성공률 점수
        usecase_stats = health_data.get('usecase_execution', {})
        if 'overall_success_rate' in usecase_stats:
            success_rate = usecase_stats['overall_success_rate']
            score -= (100 - success_rate) * 0.3  # 실패율의 30%만큼 감점
        
        # 데이터베이스 건강성 점수
        db_health = health_data.get('database_health', {})
        if 'query_statistics' in db_health:
            query_success_rate = db_health['query_statistics'].get('success_rate', 100)
            score -= (100 - query_success_rate) * 0.5  # 실패율의 50%만큼 감점
        
        return max(0, min(100, int(score)))
    
    def print_health_summary(self):
        """건강성 요약 출력"""
        report = self.generate_comprehensive_report()
        health_score = report['overall_health_score']
        
        print(f"\n{'='*50}")
        print(f"🏥 시스템 건강성 리포트")
        print(f"{'='*50}")
        print(f"전체 건강성 점수: {health_score}/100")
        
        if health_score >= 90:
            print("🟢 시스템 상태: 매우 좋음")
        elif health_score >= 70:
            print("🟡 시스템 상태: 양호")
        elif health_score >= 50:
            print("🟠 시스템 상태: 주의 필요")
        else:
            print("🔴 시스템 상태: 심각한 문제")
        
        # 주요 이슈 요약
        issues = []
        
        health_data = report['system_health']
        
        # UI 성능 이슈
        ui_perf = health_data.get('ui_performance', {})
        if ui_perf.get('slow_operations_rate', 0) > 10:
            issues.append(f"UI 성능: 느린 동작 {ui_perf['slow_operations_rate']:.1f}%")
        
        # 유스케이스 실패 이슈
        usecase_stats = health_data.get('usecase_execution', {})
        if usecase_stats.get('overall_success_rate', 100) < 95:
            issues.append(f"유스케이스: 성공률 {usecase_stats['overall_success_rate']:.1f}%")
        
        # 데이터베이스 이슈
        db_health = health_data.get('database_health', {})
        if 'query_statistics' in db_health:
            query_success_rate = db_health['query_statistics'].get('success_rate', 100)
            if query_success_rate < 98:
                issues.append(f"데이터베이스: 쿼리 성공률 {query_success_rate:.1f}%")
        
        if issues:
            print(f"\n⚠️ 주요 이슈:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ 발견된 주요 이슈 없음")
        
        print(f"{'='*50}\n")

# 실제 사용
def main():
    """디버깅 매니저 사용 예시"""
    
    # 통합 디버깅 매니저 초기화
    debug_manager = IntegratedDebuggingManager()
    
    # 주기적 건강성 체크 (5분마다)
    import threading
    
    def periodic_health_check():
        while True:
            debug_manager.print_health_summary()
            time.sleep(300)  # 5분 대기
    
    # 백그라운드에서 건강성 체크 실행
    health_thread = threading.Thread(target=periodic_health_check, daemon=True)
    health_thread.start()
    
    print("🔍 통합 디버깅 시스템 시작됨")
    print("5분마다 시스템 건강성을 체크합니다...")

if __name__ == "__main__":
    main()
```

## 🔍 다음 단계

- **[테스팅 전략](16_TESTING_STRATEGY.md)**: 디버깅을 위한 체계적 테스트
- **[모니터링 전략](17_MONITORING_STRATEGY.md)**: 프로덕션 환경 모니터링

---
**💡 핵심**: "Clean Architecture에서 효과적인 디버깅은 각 계층의 책임을 명확히 이해하고, 계층별 특화된 디버깅 도구를 사용하는 것입니다!"

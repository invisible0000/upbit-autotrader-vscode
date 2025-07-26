"""
트레이딩 지표 변수 관리 시스템 - 성능 최적화 버전

캐싱, 인덱스 최적화, 대용량 데이터 처리를 지원하는 확장 버전입니다.
"""

import sqlite3
import time
import threading
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
import weakref
import sys
import os

# 절대 import를 위한 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from variable_manager import SimpleVariableManager
except ImportError:
    # 상대 import 시도
    from .variable_manager import SimpleVariableManager


@dataclass
class PerformanceMetrics:
    """성능 측정 클래스"""
    query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_query_time: float = 0.0
    total_query_time: float = 0.0
    memory_usage_mb: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """캐시 적중률 계산"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class CachedVariableManager(SimpleVariableManager):
    """
    캐싱 기능이 추가된 고성능 트레이딩 변수 관리 클래스
    
    주요 기능:
    1. 메모리 캐싱으로 DB 쿼리 최소화
    2. 인덱스 최적화로 빠른 검색
    3. 대용량 지표 처리 지원 (200개 이상)
    4. 성능 모니터링 및 메트릭 수집
    """
    
    def __init__(self, db_path: Optional[str] = None, cache_size: int = 1000):
        """
        Args:
            db_path: SQLite 데이터베이스 파일 경로
            cache_size: 최대 캐시 항목 수
        """
        # DB 경로가 없으면 기본 경로 설정
        if db_path is None:
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(current_dir, "trading_variables.db")
        
        super().__init__(db_path)
        
        # 캐시 설정
        self.cache_size = cache_size
        self._variable_cache: Dict[str, Any] = {}
        self._compatibility_cache: Dict[Tuple[str, str], bool] = {}
        self._category_cache: Dict[str, List[str]] = {}
        
        # 성능 모니터링
        self.metrics = PerformanceMetrics()
        self._lock = threading.RLock()
        
        # 약한 참조로 메모리 누수 방지
        self._weak_refs: Set[weakref.ref] = set()
        
        # 초기화 시 인덱스 최적화 적용
        self._optimize_database_indexes()
        
        # 자주 사용되는 데이터를 미리 캐싱
        self._warm_up_cache()
    
    def _optimize_database_indexes(self):
        """데이터베이스 인덱스 최적화"""
        optimization_queries = [
            # 복합 인덱스 추가 (성능 향상)
            "CREATE INDEX IF NOT EXISTS idx_variables_purpose_active ON trading_variables(purpose_category, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_variables_comparison_active ON trading_variables(comparison_group, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_variables_category_group ON trading_variables(purpose_category, comparison_group)",
            
            # 파라미터 테이블 인덱스
            "CREATE INDEX IF NOT EXISTS idx_parameters_variable_required ON variable_parameters(variable_id, is_required)",
            "CREATE INDEX IF NOT EXISTS idx_parameters_type_order ON variable_parameters(parameter_type, display_order)",
            
            # SQLite 최적화 설정
            "PRAGMA optimize",
            "PRAGMA analysis_limit=1000",
            "PRAGMA cache_size=10000",  # 10MB 캐시
        ]
        
        start_time = time.time()
        try:
            with sqlite3.connect(self.db_path) as conn:
                for query in optimization_queries:
                    conn.execute(query)
                conn.commit()
            
            optimization_time = time.time() - start_time
            print(f"🚀 DB 인덱스 최적화 완료 ({optimization_time:.3f}초)")
            
        except sqlite3.Error as e:
            print(f"⚠️ 인덱스 최적화 중 오류: {e}")
    
    def _warm_up_cache(self):
        """자주 사용되는 데이터를 미리 캐싱"""
        start_time = time.time()
        
        # 모든 활성 변수를 캐시에 로드
        variables = self.get_all_variables()
        for var in variables:
            self._variable_cache[var['variable_id']] = var
        
        # 카테고리별 변수 목록 캐싱
        categories = ['trend', 'momentum', 'volatility', 'volume', 'price']
        for category in categories:
            self._category_cache[category] = [
                var['variable_id'] for var in variables
                if var['purpose_category'] == category
            ]
        
        warmup_time = time.time() - start_time
        print(f"🔥 캐시 웜업 완료: {len(variables)}개 변수 로드 ({warmup_time:.3f}초)")
    
    def get_compatible_variables(self, variable_id: str) -> List[Dict[str, Any]]:
        """
        캐시된 호환 변수 조회 (오버라이드)
        """
        # 캐시에서 먼저 확인
        cache_key = f"compat_{variable_id}"
        if cache_key in self._variable_cache:
            self.metrics.cache_hits += 1
            return self._variable_cache[cache_key]
        
        # 캐시 미스 - DB에서 조회
        self.metrics.cache_misses += 1
        start_time = time.time()
        
        result = super().get_compatible_variables(variable_id)
        
        # 성능 메트릭 업데이트
        query_time = time.time() - start_time
        self.metrics.query_count += 1
        self.metrics.total_query_time += query_time
        self.metrics.avg_query_time = self.metrics.total_query_time / self.metrics.query_count
        
        # 결과 캐싱 (LRU 방식)
        if len(self._variable_cache) >= self.cache_size:
            # 가장 오래된 항목 제거
            oldest_key = next(iter(self._variable_cache))
            del self._variable_cache[oldest_key]
        
        self._variable_cache[cache_key] = result
        return result
    
    def check_compatibility(self, var1_id: str, var2_id: str) -> bool:
        """
        캐시된 호환성 검사 (오버라이드)
        """
        # 캐시 키 (순서 무관하게 일관성 유지)
        cache_key = tuple(sorted([var1_id, var2_id]))
        
        with self._lock:
            if cache_key in self._compatibility_cache:
                self.metrics.cache_hits += 1
                return self._compatibility_cache[cache_key]
            
            # 캐시 미스 - 실제 검사 수행
            self.metrics.cache_misses += 1
            start_time = time.time()
            
            result = super().check_compatibility(var1_id, var2_id)
            
            # 성능 메트릭 업데이트
            query_time = time.time() - start_time
            self.metrics.query_count += 1
            self.metrics.total_query_time += query_time
            self.metrics.avg_query_time = self.metrics.total_query_time / self.metrics.query_count
            
            # 결과 캐싱
            self._compatibility_cache[cache_key] = result
            
            return result
    
    def get_variables_by_category(self, category: str) -> List[str]:
        """
        카테고리별 변수 조회 (캐시 활용)
        """
        if category in self._category_cache:
            self.metrics.cache_hits += 1
            return self._category_cache[category].copy()
        
        # 캐시 미스 - DB에서 조회
        self.metrics.cache_misses += 1
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT variable_id FROM trading_variables 
                WHERE purpose_category = ? AND is_active = 1
                ORDER BY variable_id
            """, (category,))
            
            result = [row['variable_id'] for row in cursor.fetchall()]
            
        # 결과 캐싱
        self._category_cache[category] = result
        return result.copy()
    
    def batch_check_compatibility(self, variable_pairs: List[Tuple[str, str]]) -> Dict[Tuple[str, str], bool]:
        """
        대량 호환성 검사 (배치 처리로 성능 최적화)
        """
        results = {}
        uncached_pairs = []
        
        # 캐시에서 먼저 확인
        with self._lock:
            for pair in variable_pairs:
                cache_key = tuple(sorted(pair))
                if cache_key in self._compatibility_cache:
                    results[pair] = self._compatibility_cache[cache_key]
                    self.metrics.cache_hits += 1
                else:
                    uncached_pairs.append(pair)
                    self.metrics.cache_misses += 1
        
        # 캐시되지 않은 항목들을 배치로 처리
        if uncached_pairs:
            start_time = time.time()
            
            # SQL IN 절을 사용한 배치 쿼리로 최적화
            var_ids = set()
            for var1, var2 in uncached_pairs:
                var_ids.update([var1, var2])
            
            # 모든 관련 변수 정보를 한 번에 조회
            placeholders = ','.join('?' * len(var_ids))
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(f"""
                    SELECT variable_id, purpose_category, comparison_group 
                    FROM trading_variables 
                    WHERE variable_id IN ({placeholders}) AND is_active = 1
                """, list(var_ids))
                
                var_info = {row['variable_id']: row for row in cursor.fetchall()}
            
            # 호환성 검사 수행 및 캐싱
            for pair in uncached_pairs:
                var1_id, var2_id = pair
                
                if var1_id in var_info and var2_id in var_info:
                    var1_info = var_info[var1_id]
                    var2_info = var_info[var2_id]
                    
                    # 같은 카테고리이거나 같은 비교 그룹인 경우 호환
                    compatible = (
                        var1_info['purpose_category'] == var2_info['purpose_category'] or
                        var1_info['comparison_group'] == var2_info['comparison_group']
                    )
                else:
                    compatible = False
                
                results[pair] = compatible
                
                # 캐시에 저장
                cache_key = tuple(sorted(pair))
                self._compatibility_cache[cache_key] = compatible
            
            # 성능 메트릭 업데이트
            batch_time = time.time() - start_time
            self.metrics.query_count += 1
            self.metrics.total_query_time += batch_time
            self.metrics.avg_query_time = self.metrics.total_query_time / self.metrics.query_count
        
        return results
    
    def clear_cache(self):
        """캐시 초기화"""
        with self._lock:
            self._variable_cache.clear()
            self._compatibility_cache.clear()
            self._category_cache.clear()
            print("🧹 캐시가 초기화되었습니다.")
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """성능 메트릭 반환"""
        # 메모리 사용량 추정 (바이트 단위)
        cache_memory = (
            len(str(self._variable_cache)) + 
            len(str(self._compatibility_cache)) + 
            len(str(self._category_cache))
        )
        self.metrics.memory_usage_mb = cache_memory / (1024 * 1024)
        
        return self.metrics
    
    def performance_test(self, iterations: int = 1000) -> Dict[str, Any]:
        """
        성능 테스트 실행
        
        Args:
            iterations: 테스트 반복 횟수
            
        Returns:
            성능 테스트 결과
        """
        print(f"🏁 성능 테스트 시작 ({iterations}회 반복)")
        
        # 테스트용 변수 쌍 생성
        all_variables = [var['variable_id'] for var in self.get_all_variables()]
        if len(all_variables) < 2:
            return {"error": "테스트할 변수가 부족합니다."}
        
        test_pairs = []
        for i in range(min(iterations, len(all_variables) * (len(all_variables) - 1) // 2)):
            var1 = all_variables[i % len(all_variables)]
            var2 = all_variables[(i + 1) % len(all_variables)]
            if var1 != var2:
                test_pairs.append((var1, var2))
        
        # 캐시 초기화 후 테스트
        self.clear_cache()
        initial_metrics = self.get_performance_metrics()
        
        # 단일 호출 테스트
        start_time = time.time()
        for var1, var2 in test_pairs[:100]:  # 처음 100개만
            self.check_compatibility(var1, var2)
        single_call_time = time.time() - start_time
        
        # 배치 호출 테스트
        self.clear_cache()
        start_time = time.time()
        self.batch_check_compatibility(test_pairs[:100])
        batch_call_time = time.time() - start_time
        
        final_metrics = self.get_performance_metrics()
        
        return {
            "test_summary": {
                "iterations": len(test_pairs[:100]),
                "total_variables": len(all_variables),
                "single_call_time": round(single_call_time, 3),
                "batch_call_time": round(batch_call_time, 3),
                "performance_improvement": round((single_call_time / batch_call_time), 2) if batch_call_time > 0 else "N/A"
            },
            "cache_performance": {
                "hit_rate": round(final_metrics.cache_hit_rate, 2),
                "total_queries": final_metrics.query_count,
                "avg_query_time": round(final_metrics.avg_query_time * 1000, 3),  # ms
                "memory_usage_mb": round(final_metrics.memory_usage_mb, 3)
            }
        }


def stress_test_large_dataset(num_indicators: int = 200):
    """
    대용량 지표 데이터셋으로 스트레스 테스트
    
    Args:
        num_indicators: 테스트할 지표 수
    """
    print(f"💪 대용량 스트레스 테스트 시작 ({num_indicators}개 지표)")
    
    manager = CachedVariableManager()
    
    # 가상 지표 데이터 생성 및 추가
    categories = ['trend', 'momentum', 'volatility', 'volume', 'price']
    comparison_groups = ['price_comparable', 'percentage_comparable', 'centered_oscillator', 
                        'volatility_comparable', 'volume_comparable']
    
    start_time = time.time()
    
    # 대량 지표 추가
    for i in range(num_indicators):
        category = categories[i % len(categories)]
        comp_group = comparison_groups[i % len(comparison_groups)]
        
        success = manager.add_variable(
            variable_id=f"TEST_INDICATOR_{i:03d}",
            display_name_ko=f"테스트지표{i:03d}",
            purpose_category=category,
            chart_category='overlay' if category in ['trend', 'price'] else 'subplot',
            comparison_group=comp_group,
            description=f"스트레스 테스트용 지표 #{i}"
        )
        
        if not success:
            print(f"⚠️ 지표 {i} 추가 실패")
    
    add_time = time.time() - start_time
    
    # 성능 테스트 실행
    perf_results = manager.performance_test(1000)
    
    # 결과 출력
    total_variables = len(manager.get_all_variables())
    
    print("\n📊 스트레스 테스트 결과:")
    print(f"  🎯 총 지표 수: {total_variables}개")
    print(f"  ⏱️ 지표 추가 시간: {add_time:.3f}초")
    print(f"  🚀 성능 향상: {perf_results['test_summary']['performance_improvement']}배")
    print(f"  💾 캐시 적중률: {perf_results['cache_performance']['hit_rate']}%")
    print(f"  🧠 메모리 사용량: {perf_results['cache_performance']['memory_usage_mb']}MB")
    print(f"  ⚡ 평균 쿼리 시간: {perf_results['cache_performance']['avg_query_time']}ms")
    
    # 정리
    print("\n🧹 테스트 지표 정리 중...")
    with sqlite3.connect(manager.db_path) as conn:
        conn.execute("DELETE FROM trading_variables WHERE variable_id LIKE 'TEST_INDICATOR_%'")
        conn.commit()
    
    print("✅ 스트레스 테스트 완료!")
    
    return perf_results


def main():
    """성능 최적화 시스템 테스트"""
    print("🚀 성능 최적화 시스템 테스트")
    print("=" * 60)
    
    # 기본 성능 테스트
    manager = CachedVariableManager()
    
    print("📈 기본 성능 테스트:")
    basic_perf = manager.performance_test(100)
    
    print(f"  - 캐시 적중률: {basic_perf['cache_performance']['hit_rate']}%")
    print(f"  - 평균 쿼리 시간: {basic_perf['cache_performance']['avg_query_time']}ms")
    print(f"  - 성능 향상: {basic_perf['test_summary']['performance_improvement']}배")
    
    print("\n💪 대용량 스트레스 테스트 (200개 지표):")
    stress_test_large_dataset(200)
    
    print("\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    main()

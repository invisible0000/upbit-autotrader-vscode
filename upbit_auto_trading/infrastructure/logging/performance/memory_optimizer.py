"""
Memory Optimization System for LLM Agent Logging
메모리 사용량 최적화 및 누수 방지 시스템
"""
import gc
import psutil
import weakref
import time
import threading
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MemorySnapshot:
    """메모리 스냅샷"""
    timestamp: datetime
    process_memory_mb: float
    heap_size_mb: float
    gc_counts: Dict[int, int]
    object_counts: Dict[str, int]
    active_references: int


@dataclass
class MemoryAlert:
    """메모리 경고"""
    alert_type: str
    severity: str
    message: str
    memory_usage_mb: float
    threshold_mb: float
    timestamp: datetime
    suggestions: List[str]


class MemoryOptimizer:
    """메모리 최적화 관리자"""

    def __init__(self,
                 memory_threshold_mb: float = 500.0,
                 gc_threshold_factor: float = 2.0,
                 monitoring_interval: float = 30.0):

        self.memory_threshold_mb = memory_threshold_mb
        self.gc_threshold_factor = gc_threshold_factor
        self.monitoring_interval = monitoring_interval

        # 메모리 모니터링 상태
        self.is_monitoring = False
        self.monitoring_thread = None

        # 스냅샷 히스토리
        self.memory_snapshots: List[MemorySnapshot] = []
        self.max_snapshots = 100

        # 알림 시스템
        self.memory_alerts: List[MemoryAlert] = []
        self.max_alerts = 50

        # 참조 추적 (약한 참조 사용)
        self.tracked_objects: Set[weakref.ref] = set()

        # 캐시 관리
        self.cache_registries: List[weakref.ref] = []

        # 프로세스 정보
        self.process = psutil.Process()

    def start_monitoring(self):
        """메모리 모니터링 시작"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True,
            name="MemoryOptimizer"
        )
        self.monitoring_thread.start()
        print("🔍 메모리 모니터링 시작")

    def stop_monitoring(self):
        """메모리 모니터링 중지"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        print("🛑 메모리 모니터링 중지")

    def _monitoring_loop(self):
        """메모리 모니터링 루프"""
        while self.is_monitoring:
            try:
                # 메모리 스냅샷 생성
                snapshot = self._create_memory_snapshot()
                self._add_snapshot(snapshot)

                # 메모리 사용량 체크
                self._check_memory_usage(snapshot)

                # 참조 정리
                self._cleanup_weak_references()

                # 가비지 컬렉션 최적화
                self._optimize_garbage_collection()

                time.sleep(self.monitoring_interval)

            except Exception as e:
                print(f"❌ 메모리 모니터링 오류: {e}")
                time.sleep(5.0)

    def _create_memory_snapshot(self) -> MemorySnapshot:
        """현재 메모리 상태 스냅샷 생성"""
        # 프로세스 메모리 정보
        memory_info = self.process.memory_info()
        process_memory_mb = memory_info.rss / 1024 / 1024

        # 힙 크기 (RSS - 공유 메모리 등 제외한 실제 할당 메모리)
        try:
            heap_size_mb = memory_info.rss / 1024 / 1024
        except AttributeError:
            heap_size_mb = process_memory_mb

        # 가비지 컬렉터 통계
        gc_counts = {gen: count for gen, count in enumerate(gc.get_counts())}

        # 주요 객체 타입별 카운트
        object_counts = self._count_objects_by_type()

        # 활성 참조 수
        active_references = len([ref for ref in self.tracked_objects if ref() is not None])

        return MemorySnapshot(
            timestamp=datetime.now(),
            process_memory_mb=process_memory_mb,
            heap_size_mb=heap_size_mb,
            gc_counts=gc_counts,
            object_counts=object_counts,
            active_references=active_references
        )

    def _count_objects_by_type(self) -> Dict[str, int]:
        """타입별 객체 수 집계"""
        type_counts = {}

        # gc로 추적되는 객체들만 카운트
        for obj in gc.get_objects():
            obj_type = type(obj).__name__
            type_counts[obj_type] = type_counts.get(obj_type, 0) + 1

        # 상위 10개 타입만 반환
        sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_types[:10])

    def _add_snapshot(self, snapshot: MemorySnapshot):
        """스냅샷 추가 (크기 제한 적용)"""
        self.memory_snapshots.append(snapshot)

        # 최대 개수 초과 시 오래된 것 제거
        if len(self.memory_snapshots) > self.max_snapshots:
            self.memory_snapshots = self.memory_snapshots[-self.max_snapshots:]

    def _check_memory_usage(self, snapshot: MemorySnapshot):
        """메모리 사용량 체크 및 경고 생성"""
        memory_mb = snapshot.process_memory_mb

        # 임계값 초과 체크
        if memory_mb > self.memory_threshold_mb:
            severity = "HIGH" if memory_mb > self.memory_threshold_mb * 1.5 else "MEDIUM"

            alert = MemoryAlert(
                alert_type="MEMORY_THRESHOLD_EXCEEDED",
                severity=severity,
                message=f"메모리 사용량이 임계값을 초과했습니다: {memory_mb:.1f}MB",
                memory_usage_mb=memory_mb,
                threshold_mb=self.memory_threshold_mb,
                timestamp=datetime.now(),
                suggestions=self._generate_memory_suggestions(snapshot)
            )

            self._add_alert(alert)

        # 메모리 증가 패턴 체크
        self._check_memory_leak_pattern()

    def _generate_memory_suggestions(self, snapshot: MemorySnapshot) -> List[str]:
        """메모리 최적화 제안 생성"""
        suggestions = []

        # 객체 수가 많은 타입 체크
        object_counts = snapshot.object_counts
        if object_counts:
            max_type, max_count = max(object_counts.items(), key=lambda x: x[1])
            if max_count > 10000:
                suggestions.append(f"'{max_type}' 객체가 {max_count}개로 많습니다. 객체 재사용을 고려하세요.")

        # 가비지 컬렉션 체크
        gc_counts = snapshot.gc_counts
        if gc_counts.get(2, 0) > 100:
            suggestions.append("Generation 2 GC가 자주 발생합니다. 장기 참조 객체를 줄여보세요.")

        # 기본 제안들
        suggestions.extend([
            "gc.collect()를 호출하여 수동 가비지 컬렉션 실행",
            "캐시 크기 제한 및 만료 정책 검토",
            "대용량 객체의 약한 참조(weakref) 사용 고려"
        ])

        return suggestions[:3]  # 최대 3개 제안

    def _check_memory_leak_pattern(self):
        """메모리 누수 패턴 감지"""
        if len(self.memory_snapshots) < 5:
            return

        # 최근 5개 스냅샷의 메모리 증가 패턴
        recent_snapshots = self.memory_snapshots[-5:]
        memory_usages = [s.process_memory_mb for s in recent_snapshots]

        # 지속적인 증가 패턴 체크
        increasing_count = 0
        for i in range(1, len(memory_usages)):
            if memory_usages[i] > memory_usages[i-1] * 1.05:  # 5% 이상 증가
                increasing_count += 1

        if increasing_count >= 3:  # 3번 이상 연속 증가
            alert = MemoryAlert(
                alert_type="POTENTIAL_MEMORY_LEAK",
                severity="HIGH",
                message="메모리 누수 가능성이 감지되었습니다",
                memory_usage_mb=memory_usages[-1],
                threshold_mb=self.memory_threshold_mb,
                timestamp=datetime.now(),
                suggestions=[
                    "객체 참조 순환을 확인하세요",
                    "이벤트 리스너나 콜백 해제를 확인하세요",
                    "캐시나 컬렉션의 무제한 증가를 확인하세요"
                ]
            )
            self._add_alert(alert)

    def _add_alert(self, alert: MemoryAlert):
        """메모리 경고 추가"""
        self.memory_alerts.append(alert)

        # 최대 개수 초과 시 오래된 것 제거
        if len(self.memory_alerts) > self.max_alerts:
            self.memory_alerts = self.memory_alerts[-self.max_alerts:]

        # 콘솔 출력
        icon = "🚨" if alert.severity == "HIGH" else "⚠️"
        print(f"{icon} {alert.alert_type}: {alert.message}")

    def _cleanup_weak_references(self):
        """죽은 약한 참조 정리"""
        alive_refs = set()
        for ref in self.tracked_objects:
            if ref() is not None:
                alive_refs.add(ref)

        removed_count = len(self.tracked_objects) - len(alive_refs)
        self.tracked_objects = alive_refs

        if removed_count > 0:
            print(f"🗑️ {removed_count}개의 죽은 참조 정리됨")

    def _optimize_garbage_collection(self):
        """가비지 컬렉션 최적화"""
        # 현재 GC 임계값 확인
        thresholds = gc.get_threshold()

        # 메모리 사용량에 따라 GC 임계값 조정
        if self.memory_snapshots:
            current_memory = self.memory_snapshots[-1].process_memory_mb

            if current_memory > self.memory_threshold_mb:
                # 메모리 사용량이 높으면 GC를 더 자주 실행
                new_threshold = int(thresholds[0] / self.gc_threshold_factor)
                gc.set_threshold(new_threshold, thresholds[1], thresholds[2])
                print(f"🔄 GC 임계값 조정: {new_threshold}")

    def track_object(self, obj: Any) -> weakref.ref:
        """객체 추적 등록"""
        ref = weakref.ref(obj)
        self.tracked_objects.add(ref)
        return ref

    def register_cache(self, cache_obj: Any):
        """캐시 객체 등록"""
        ref = weakref.ref(cache_obj)
        self.cache_registries.append(ref)

    def force_garbage_collection(self) -> Dict[str, int]:
        """강제 가비지 컬렉션 실행"""
        collected_counts = {}

        for generation in range(3):
            collected = gc.collect(generation)
            collected_counts[f"generation_{generation}"] = collected

        total_collected = sum(collected_counts.values())
        print(f"🗑️ 가비지 컬렉션 완료: {total_collected}개 객체 정리됨")

        return collected_counts

    def clear_caches(self):
        """등록된 캐시들 정리"""
        cleared_count = 0

        for cache_ref in self.cache_registries[:]:
            cache = cache_ref()
            if cache is not None:
                if hasattr(cache, 'clear'):
                    cache.clear()
                    cleared_count += 1
            else:
                # 죽은 참조 제거
                self.cache_registries.remove(cache_ref)

        print(f"🗑️ {cleared_count}개 캐시 정리됨")

    def get_memory_stats(self) -> Dict[str, Any]:
        """메모리 통계 반환"""
        current_snapshot = self._create_memory_snapshot()

        return {
            "current_memory_mb": current_snapshot.process_memory_mb,
            "memory_threshold_mb": self.memory_threshold_mb,
            "usage_percentage": (current_snapshot.process_memory_mb / self.memory_threshold_mb) * 100,
            "tracked_objects": len(self.tracked_objects),
            "registered_caches": len(self.cache_registries),
            "total_alerts": len(self.memory_alerts),
            "high_severity_alerts": len([a for a in self.memory_alerts if a.severity == "HIGH"]),
            "gc_counts": current_snapshot.gc_counts,
            "top_object_types": current_snapshot.object_counts
        }

    def get_recent_alerts(self, hours: int = 1) -> List[MemoryAlert]:
        """최근 알림 조회"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.memory_alerts if alert.timestamp > cutoff_time]

    def cleanup(self):
        """리소스 정리"""
        self.stop_monitoring()
        self.clear_caches()
        self.force_garbage_collection()
        self.tracked_objects.clear()
        print("✅ MemoryOptimizer 정리 완료")

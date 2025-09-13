"""
업비트 Rate Limit 모니터링 시스템
- 429 에러 상세 추적 및 분석
- 일일/주간 통계 리포트 생성
- 패턴 분석을 통한 개선점 도출

Zero-429 정책 달성을 위한 핵심 모니터링 도구
"""
import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class Rate429Event:
    """429 에러 이벤트 상세 정보"""
    timestamp: float
    datetime_str: str
    endpoint: str
    method: str
    retry_after: Optional[float]
    attempt_number: int
    rate_limiter_type: str  # 'dynamic' or 'legacy'
    current_rate_ratio: Optional[float]  # 동적 리미터의 현재 비율
    response_headers: Dict[str, str]
    response_body: str
    context: Dict[str, Any]  # 추가 컨텍스트 정보


@dataclass
class HourlyStats:
    """시간대별 통계"""
    hour: int
    total_requests: int = 0
    error_429_count: int = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    rate_reductions: int = 0  # 동적 조정 발생 횟수


class RateLimitMonitor:
    """업비트 Rate Limit 모니터링 시스템"""

    def __init__(self, log_dir: str = "logs/rate_limit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 로깅
        self.logger = create_component_logger("RateLimitMonitor")

        # 이벤트 저장
        self.events: List[Rate429Event] = []
        self.hourly_stats: Dict[int, HourlyStats] = {}

        # 파일 경로
        self.events_file = self.log_dir / f"429_events_{datetime.now().strftime('%Y%m%d')}.json"
        self.daily_report_file = self.log_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"

        # 자동 저장 설정
        self._auto_save_interval = 300  # 5분마다 저장
        self._last_save_time = time.time()

        self.logger.info(f"🔍 Rate Limit 모니터링 시작 - 로그 디렉터리: {self.log_dir}")

    async def record_429_event(
        self,
        endpoint: str,
        method: str = 'GET',
        retry_after: Optional[float] = None,
        attempt_number: int = 1,
        rate_limiter_type: str = 'dynamic',
        current_rate_ratio: Optional[float] = None,
        response_headers: Optional[Dict[str, str]] = None,
        response_body: str = "",
        **context
    ) -> None:
        """429 이벤트 기록"""
        now = time.time()
        event = Rate429Event(
            timestamp=now,
            datetime_str=datetime.fromtimestamp(now).isoformat(),
            endpoint=endpoint,
            method=method,
            retry_after=retry_after,
            attempt_number=attempt_number,
            rate_limiter_type=rate_limiter_type,
            current_rate_ratio=current_rate_ratio,
            response_headers=response_headers or {},
            response_body=response_body[:500],  # 처음 500자만 저장
            context=context
        )

        self.events.append(event)

        # 🚨 즉시 알림 로깅
        self.logger.error("🚨 429 ERROR DETECTED!")
        self.logger.error(f"📍 엔드포인트: {method} {endpoint}")
        self.logger.error(f"⏰ 시간: {event.datetime_str}")
        self.logger.error(f"🔄 재시도: {attempt_number}회차")
        self.logger.error(f"📊 Rate Ratio: {current_rate_ratio}")
        self.logger.error(f"⌛ Retry-After: {retry_after}초")

        # 자동 저장 체크
        if now - self._last_save_time > self._auto_save_interval:
            await self.save_events()

    async def record_request_stats(
        self,
        endpoint: str,
        response_time_ms: float,
        success: bool = True
    ) -> None:
        """일반 요청 통계 기록"""
        current_hour = datetime.now().hour

        if current_hour not in self.hourly_stats:
            self.hourly_stats[current_hour] = HourlyStats(hour=current_hour)

        stats = self.hourly_stats[current_hour]
        stats.total_requests += 1

        if not success:
            stats.error_429_count += 1

        # 평균 응답 시간 업데이트 (지수 이동 평균)
        if stats.avg_response_time == 0:
            stats.avg_response_time = response_time_ms
        else:
            stats.avg_response_time = 0.9 * stats.avg_response_time + 0.1 * response_time_ms

        # 에러율 계산
        stats.error_rate = (stats.error_429_count / stats.total_requests) * 100

    async def record_rate_reduction(self, from_ratio: float, to_ratio: float) -> None:
        """동적 Rate Limit 감소 이벤트 기록"""
        current_hour = datetime.now().hour

        if current_hour not in self.hourly_stats:
            self.hourly_stats[current_hour] = HourlyStats(hour=current_hour)

        self.hourly_stats[current_hour].rate_reductions += 1

        self.logger.warning(f"📉 Rate Limit 감소 기록: {from_ratio:.1%} → {to_ratio:.1%}")

    async def save_events(self) -> None:
        """이벤트 저장"""
        try:
            events_data = [asdict(event) for event in self.events]

            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=2)

            self._last_save_time = time.time()
            self.logger.info(f"💾 429 이벤트 저장 완료: {len(self.events)}개 이벤트")

        except Exception as e:
            self.logger.error(f"❌ 이벤트 저장 실패: {e}")

    async def generate_daily_report(self) -> Dict[str, Any]:
        """일일 리포트 생성"""
        now = datetime.now()
        today_events = [
            event for event in self.events
            if datetime.fromtimestamp(event.timestamp).date() == now.date()
        ]

        # 기본 통계
        total_429_count = len(today_events)
        unique_endpoints = len(set(event.endpoint for event in today_events))

        # 시간대별 분포
        hourly_distribution = {}
        for event in today_events:
            hour = datetime.fromtimestamp(event.timestamp).hour
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1

        # 엔드포인트별 분포
        endpoint_distribution = {}
        for event in today_events:
            endpoint_distribution[event.endpoint] = endpoint_distribution.get(event.endpoint, 0) + 1

        # Rate Limiter 타입별 분포
        limiter_type_distribution = {}
        for event in today_events:
            limiter_type_distribution[event.rate_limiter_type] = limiter_type_distribution.get(event.rate_limiter_type, 0) + 1

        # 총 요청 수 추정 (hourly_stats 기반)
        total_requests = sum(stats.total_requests for stats in self.hourly_stats.values())
        error_rate = (total_429_count / total_requests * 100) if total_requests > 0 else 0

        report = {
            "date": now.strftime("%Y-%m-%d"),
            "generation_time": now.isoformat(),
            "summary": {
                "total_429_errors": total_429_count,
                "total_requests_estimated": total_requests,
                "error_rate_percentage": round(error_rate, 4),
                "unique_endpoints_affected": unique_endpoints,
                "zero_429_achieved": total_429_count == 0
            },
            "distributions": {
                "hourly": hourly_distribution,
                "endpoints": endpoint_distribution,
                "limiter_types": limiter_type_distribution
            },
            "hourly_stats": {
                str(hour): asdict(stats) for hour, stats in self.hourly_stats.items()
            },
            "recent_events": [
                asdict(event) for event in today_events[-10:]  # 최근 10개 이벤트
            ]
        }

        # 리포트 저장
        try:
            with open(self.daily_report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            self.logger.info(f"📊 일일 리포트 생성 완료: {self.daily_report_file}")

        except Exception as e:
            self.logger.error(f"❌ 일일 리포트 저장 실패: {e}")

        return report

    def get_current_stats(self) -> Dict[str, Any]:
        """현재 통계 조회"""
        today_events = [
            event for event in self.events
            if datetime.fromtimestamp(event.timestamp).date() == datetime.now().date()
        ]

        return {
            "today_429_count": len(today_events),
            "total_events_in_memory": len(self.events),
            "hourly_stats_count": len(self.hourly_stats),
            "last_429_time": today_events[-1].datetime_str if today_events else None,
            "zero_429_status": len(today_events) == 0
        }

    async def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """오래된 로그 파일 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for log_file in self.log_dir.glob("*.json"):
            try:
                # 파일명에서 날짜 추출
                date_str = log_file.stem.split('_')[-1]
                if len(date_str) == 8 and date_str.isdigit():
                    file_date = datetime.strptime(date_str, "%Y%m%d")

                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"🗑️  오래된 로그 파일 삭제: {log_file.name}")

            except Exception as e:
                self.logger.warning(f"⚠️ 로그 파일 정리 실패: {log_file.name}, {e}")


# 전역 모니터 인스턴스
_global_monitor: Optional[RateLimitMonitor] = None


def get_rate_limit_monitor() -> RateLimitMonitor:
    """전역 Rate Limit 모니터 인스턴스 획득"""
    global _global_monitor

    if _global_monitor is None:
        _global_monitor = RateLimitMonitor()

    return _global_monitor


# 편의 함수들
async def log_429_error(
    endpoint: str,
    method: str = 'GET',
    **kwargs
) -> None:
    """429 에러 간편 로깅"""
    monitor = get_rate_limit_monitor()
    await monitor.record_429_event(endpoint, method, **kwargs)


async def log_request_success(
    endpoint: str,
    response_time_ms: float
) -> None:
    """성공 요청 로깅"""
    monitor = get_rate_limit_monitor()
    await monitor.record_request_stats(endpoint, response_time_ms, success=True)


async def get_daily_429_report() -> Dict[str, Any]:
    """일일 429 리포트 조회"""
    monitor = get_rate_limit_monitor()
    return await monitor.generate_daily_report()

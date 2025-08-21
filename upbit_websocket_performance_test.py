"""
업비트 WebSocket 성능 테스트
RPS(Requests Per Second) 측정 및 압축 기능 테스트
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import statistics
import websockets
import logging

# 압축 지원을 위한 임포트
import gzip
import zlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """성능 측정 지표"""

    total_requests: int = 0
    total_responses: int = 0
    total_errors: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    compressed_bytes_received: int = 0

    response_times: List[float] = field(default_factory=list)
    throughput_history: List[float] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        """테스트 지속 시간 (초)"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def avg_response_time(self) -> float:
        """평균 응답 시간 (ms)"""
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def median_response_time(self) -> float:
        """중간값 응답 시간 (ms)"""
        return statistics.median(self.response_times) if self.response_times else 0.0

    @property
    def p95_response_time(self) -> float:
        """95퍼센타일 응답 시간 (ms)"""
        if self.response_times:
            sorted_times = sorted(self.response_times)
            index = int(len(sorted_times) * 0.95)
            return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]
        return 0.0

    @property
    def requests_per_second(self) -> float:
        """초당 요청 수 (RPS)"""
        return self.total_requests / self.duration_seconds if self.duration_seconds > 0 else 0.0

    @property
    def responses_per_second(self) -> float:
        """초당 응답 수"""
        return self.total_responses / self.duration_seconds if self.duration_seconds > 0 else 0.0

    @property
    def error_rate(self) -> float:
        """에러율 (%)"""
        return (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0.0

    @property
    def compression_ratio(self) -> float:
        """압축률 (%)"""
        if self.total_bytes_received > 0:
            return (1 - self.compressed_bytes_received / self.total_bytes_received) * 100
        return 0.0


class UpbitWebSocketPerformanceTester:
    """업비트 WebSocket 성능 테스터"""

    def __init__(self, url: str = "wss://api.upbit.com/websocket/v1"):
        self.url = url
        self.metrics = PerformanceMetrics()
        self.active_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self.message_counts: Dict[str, int] = {}
        self.is_running = False

    async def test_single_connection_performance(
        self,
        test_duration_seconds: int = 60,
        symbols: List[str] = None,
        data_types: List[str] = None,
        enable_compression: bool = True
    ) -> PerformanceMetrics:
        """단일 연결 성능 테스트"""

        if symbols is None:
            symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP"]
        if data_types is None:
            data_types = ["ticker", "trade", "orderbook"]

        logger.info(f"🚀 단일 연결 성능 테스트 시작: {test_duration_seconds}초")
        logger.info(f"📊 테스트 대상: {symbols} | 데이터 타입: {data_types}")
        logger.info(f"🗜️ 압축 기능: {'활성화' if enable_compression else '비활성화'}")

        self.metrics = PerformanceMetrics()
        self.metrics.start_time = datetime.now()

        try:
            # WebSocket 연결 (압축 옵션 포함)
            compression = "deflate" if enable_compression else None

            async with websockets.connect(
                self.url,
                compression=compression
            ) as websocket:                # 구독 요청 전송
                for data_type in data_types:
                    subscription_request = [
                        {"ticket": str(uuid.uuid4())},
                        {"type": data_type, "codes": symbols},
                        {"format": "SIMPLE"}  # 압축률 향상을 위해 SIMPLE 포맷 사용
                    ]

                    request_json = json.dumps(subscription_request)
                    request_start = time.time()

                    await websocket.send(request_json)
                    self.metrics.total_requests += 1
                    self.metrics.total_bytes_sent += len(request_json.encode('utf-8'))

                    logger.info(f"📤 구독 요청 전송: {data_type} ({len(symbols)}개 심볼)")

                # 메시지 수신 루프
                end_time = datetime.now() + timedelta(seconds=test_duration_seconds)
                message_count = 0
                last_report_time = time.time()

                while datetime.now() < end_time:
                    try:
                        # 1초 타임아웃으로 메시지 수신
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        receive_time = time.time()

                        # 메시지 처리
                        message_size = len(message)
                        if isinstance(message, bytes):
                            # 압축된 바이너리 데이터
                            self.metrics.compressed_bytes_received += message_size
                            try:
                                # 압축 해제 시도
                                decompressed = gzip.decompress(message)
                                actual_size = len(decompressed)
                            except:
                                actual_size = message_size
                        else:
                            # 텍스트 데이터
                            actual_size = len(message.encode('utf-8'))

                        self.metrics.total_responses += 1
                        self.metrics.total_bytes_received += actual_size
                        message_count += 1

                        # 응답 시간 기록 (첫 메시지 기준)
                        if message_count == 1:
                            response_time = (receive_time - request_start) * 1000  # ms
                            self.metrics.response_times.append(response_time)

                        # 1초마다 처리량 보고
                        if receive_time - last_report_time >= 1.0:
                            rps = message_count / (receive_time - last_report_time)
                            self.metrics.throughput_history.append(rps)
                            logger.info(f"📈 실시간 RPS: {rps:.2f} | 총 메시지: {message_count}")
                            message_count = 0
                            last_report_time = receive_time

                    except asyncio.TimeoutError:
                        # 타임아웃은 정상적인 상황 (메시지가 없을 수 있음)
                        continue
                    except Exception as e:
                        self.metrics.total_errors += 1
                        self.metrics.error_history.append(str(e))
                        logger.error(f"❌ 메시지 수신 오류: {e}")

        except Exception as e:
            self.metrics.total_errors += 1
            self.metrics.error_history.append(str(e))
            logger.error(f"❌ 연결 오류: {e}")

        self.metrics.end_time = datetime.now()
        return self.metrics

    async def test_multiple_connections_performance(
        self,
        connection_count: int = 5,
        test_duration_seconds: int = 30,
        requests_per_connection: int = 10
    ) -> Dict[str, PerformanceMetrics]:
        """다중 연결 성능 테스트"""

        logger.info(f"🔗 다중 연결 성능 테스트: {connection_count}개 연결")

        # 각 연결별 테스트 실행
        tasks = []
        for i in range(connection_count):
            symbols = [f"KRW-BTC"]  # 단순화
            data_types = ["ticker"]

            task = asyncio.create_task(
                self.test_single_connection_performance(
                    test_duration_seconds=test_duration_seconds,
                    symbols=symbols,
                    data_types=data_types
                )
            )
            tasks.append(task)

        # 모든 연결 테스트 완료 대기
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 정리
        connection_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 연결 {i+1} 실패: {result}")
                connection_results[f"connection_{i+1}"] = None
            else:
                connection_results[f"connection_{i+1}"] = result

        return connection_results

    async def test_rate_limits(self) -> Dict[str, Any]:
        """Rate Limit 테스트"""

        logger.info("🚦 Rate Limit 테스트 시작")

        rate_limit_results = {
            "websocket_connect_limit": None,
            "websocket_message_limit": None,
            "actual_limits_found": {}
        }

        # WebSocket 연결 제한 테스트 (공식: 초당 5회)
        logger.info("📊 WebSocket 연결 제한 테스트...")
        connect_start_time = time.time()
        successful_connections = 0
        connection_errors = []

        for i in range(10):  # 10번 연속 연결 시도
            try:
                async with websockets.connect(self.url, timeout=5) as ws:
                    successful_connections += 1
                    await asyncio.sleep(0.1)  # 짧은 대기
            except Exception as e:
                connection_errors.append(str(e))
                if "too many requests" in str(e).lower() or "429" in str(e):
                    break

        connect_duration = time.time() - connect_start_time
        connect_rps = successful_connections / connect_duration

        rate_limit_results["websocket_connect_limit"] = {
            "successful_connections": successful_connections,
            "errors": len(connection_errors),
            "actual_rps": connect_rps,
            "official_limit": 5,
            "test_duration": connect_duration
        }

        # WebSocket 메시지 제한 테스트 (공식: 초당 5회, 분당 100회)
        logger.info("📊 WebSocket 메시지 제한 테스트...")
        try:
            async with websockets.connect(self.url) as ws:
                message_start_time = time.time()
                successful_messages = 0
                message_errors = []

                # 빠른 속도로 메시지 전송
                for i in range(20):  # 20개 메시지 전송
                    try:
                        subscription_request = [
                            {"ticket": str(uuid.uuid4())},
                            {"type": "ticker", "codes": ["KRW-BTC"]},
                            {"format": "DEFAULT"}
                        ]
                        await ws.send(json.dumps(subscription_request))
                        successful_messages += 1
                        await asyncio.sleep(0.1)  # 0.1초 간격
                    except Exception as e:
                        message_errors.append(str(e))
                        break

                message_duration = time.time() - message_start_time
                message_rps = successful_messages / message_duration

                rate_limit_results["websocket_message_limit"] = {
                    "successful_messages": successful_messages,
                    "errors": len(message_errors),
                    "actual_rps": message_rps,
                    "official_limit": 5,
                    "test_duration": message_duration
                }

        except Exception as e:
            rate_limit_results["websocket_message_limit"] = {"error": str(e)}

        return rate_limit_results

    def print_performance_report(self, metrics: PerformanceMetrics, title: str = "성능 테스트 결과"):
        """성능 테스트 결과 출력"""

        print(f"\n{'='*60}")
        print(f"📊 {title}")
        print(f"{'='*60}")

        print(f"⏱️  테스트 지속 시간: {metrics.duration_seconds:.2f}초")
        print(f"📤 총 요청 수: {metrics.total_requests:,}")
        print(f"📥 총 응답 수: {metrics.total_responses:,}")
        print(f"❌ 총 에러 수: {metrics.total_errors:,}")
        print(f"📊 에러율: {metrics.error_rate:.2f}%")

        print(f"\n🚀 처리량 (Throughput)")
        print(f"   요청 RPS: {metrics.requests_per_second:.2f} req/sec")
        print(f"   응답 RPS: {metrics.responses_per_second:.2f} res/sec")

        if metrics.response_times:
            print(f"\n⚡ 응답 시간 (Response Time)")
            print(f"   평균: {metrics.avg_response_time:.2f}ms")
            print(f"   중간값: {metrics.median_response_time:.2f}ms")
            print(f"   95%: {metrics.p95_response_time:.2f}ms")

        print(f"\n💾 데이터 전송량")
        print(f"   송신: {metrics.total_bytes_sent:,} bytes")
        print(f"   수신: {metrics.total_bytes_received:,} bytes")
        if metrics.compressed_bytes_received > 0:
            print(f"   압축된 수신: {metrics.compressed_bytes_received:,} bytes")
            print(f"   압축률: {metrics.compression_ratio:.2f}%")

        if metrics.throughput_history:
            avg_throughput = statistics.mean(metrics.throughput_history)
            max_throughput = max(metrics.throughput_history)
            print(f"\n📈 처리량 통계")
            print(f"   평균 RPS: {avg_throughput:.2f}")
            print(f"   최대 RPS: {max_throughput:.2f}")


async def main():
    """메인 테스트 실행"""

    tester = UpbitWebSocketPerformanceTester()

    print("🔧 업비트 WebSocket 성능 테스트 시작")
    print("="*60)

    # 1. 단일 연결 성능 테스트 (압축 활성화)
    print("\n1️⃣ 단일 연결 성능 테스트 (압축 활성화)")
    metrics_compressed = await tester.test_single_connection_performance(
        test_duration_seconds=30,
        symbols=["KRW-BTC", "KRW-ETH"],
        data_types=["ticker", "trade"],
        enable_compression=True
    )
    tester.print_performance_report(metrics_compressed, "압축 활성화 테스트")

    # 2. 단일 연결 성능 테스트 (압축 비활성화)
    print("\n2️⃣ 단일 연결 성능 테스트 (압축 비활성화)")
    metrics_uncompressed = await tester.test_single_connection_performance(
        test_duration_seconds=30,
        symbols=["KRW-BTC", "KRW-ETH"],
        data_types=["ticker", "trade"],
        enable_compression=False
    )
    tester.print_performance_report(metrics_uncompressed, "압축 비활성화 테스트")

    # 3. Rate Limit 테스트
    print("\n3️⃣ Rate Limit 테스트")
    rate_limits = await tester.test_rate_limits()

    print(f"\n📊 Rate Limit 테스트 결과")
    print(f"{'='*40}")

    if rate_limits["websocket_connect_limit"]:
        connect_data = rate_limits["websocket_connect_limit"]
        print(f"🔗 연결 제한:")
        print(f"   성공한 연결: {connect_data['successful_connections']}")
        print(f"   실제 RPS: {connect_data['actual_rps']:.2f}")
        print(f"   공식 제한: {connect_data['official_limit']} req/sec")

    if rate_limits["websocket_message_limit"]:
        message_data = rate_limits["websocket_message_limit"]
        print(f"📨 메시지 제한:")
        print(f"   성공한 메시지: {message_data['successful_messages']}")
        print(f"   실제 RPS: {message_data['actual_rps']:.2f}")
        print(f"   공식 제한: {message_data['official_limit']} req/sec")

    # 4. 압축 효과 비교
    print(f"\n4️⃣ 압축 효과 비교")
    print(f"{'='*40}")

    if metrics_compressed.total_bytes_received > 0 and metrics_uncompressed.total_bytes_received > 0:
        compression_benefit = (
            1 - metrics_compressed.total_bytes_received / metrics_uncompressed.total_bytes_received
        ) * 100

        print(f"📊 데이터 절약:")
        print(f"   압축 전: {metrics_uncompressed.total_bytes_received:,} bytes")
        print(f"   압축 후: {metrics_compressed.total_bytes_received:,} bytes")
        print(f"   절약률: {compression_benefit:.2f}%")

        print(f"🚀 성능 비교:")
        print(f"   압축 활성화 RPS: {metrics_compressed.responses_per_second:.2f}")
        print(f"   압축 비활성화 RPS: {metrics_uncompressed.responses_per_second:.2f}")

    print(f"\n✅ 모든 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())

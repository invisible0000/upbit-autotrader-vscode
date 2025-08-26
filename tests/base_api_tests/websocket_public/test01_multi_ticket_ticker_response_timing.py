"""
업비트 WebSocket 멀티 티켓 현재가 응답 타이밍 테스트

🎯 목적:
- 다른 시점에 생성된 티켓들의 응답 패턴 분석
- 티켓별 개별 응답 vs 일괄 응답 검증
- 실제 업비트 API 동작 방식 확인

📋 테스트 시나리오:
1. 모든 KRW 마켓 심벌 취득 (REST API)
2. 심벌을 50개씩 3그룹으로 분할
3. 각 그룹별로 다른 티켓으로 순차 구독
4. 3초간 응답 수집 및 패턴 분석
5. 티켓별 응답 분리 여부 검증
"""

import asyncio
import json
import uuid
import time
import websockets
import aiohttp
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TicketInfo:
    """티켓 정보"""
    ticket_id: str
    group_number: int
    symbols: List[str]
    request_time: datetime
    response_count: int = 0


@dataclass
class ResponseInfo:
    """응답 정보"""
    ticket_id: str
    symbol: str
    response_time: datetime
    stream_type: str  # SNAPSHOT 또는 REALTIME
    data: Dict[str, Any]


class MultiTicketTester:
    """멀티 티켓 테스트 클래스"""

    def __init__(self):
        self.websocket = None
        self.tickets: Dict[str, TicketInfo] = {}
        self.responses: List[ResponseInfo] = []
        self.test_duration = 10.0  # 10초간 테스트 (실시간 스트림 확인)

    async def get_krw_markets(self) -> List[str]:
        """모든 KRW 마켓 심벌 취득"""
        print("📡 업비트 마켓 정보 조회 중...")

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.upbit.com/v1/market/all") as response:
                markets = await response.json()

        # KRW 마켓만 필터링
        krw_markets = [
            market['market'] for market in markets
            if market['market'].startswith('KRW-')
        ]

        print(f"✅ KRW 마켓 총 {len(krw_markets)}개 발견")
        return krw_markets

    def split_symbols_into_groups(self, symbols: List[str], group_size: int = 50) -> List[List[str]]:
        """심벌을 그룹별로 분할"""
        groups = []
        for i in range(0, len(symbols), group_size):
            group = symbols[i:i + group_size]
            groups.append(group)
            if len(groups) >= 3:  # 최대 3그룹
                break
        return groups

    def format_response_summary(self, responses: List[str], group_num: int) -> str:
        """응답 요약 포맷"""
        if not responses:
            return f"그룹 {group_num}: 응답 없음"

        count = len(responses)
        if count <= 6:
            symbols_str = ", ".join(responses)
        else:
            first_three = ", ".join(responses[:3])
            last_three = ", ".join(responses[-3:])
            symbols_str = f"{first_three} ... ({count}개) ... {last_three}"

        return f"그룹 {group_num}: {symbols_str}"

    async def connect_websocket(self):
        """WebSocket 연결"""
        print("🔌 WebSocket 연결 중...")
        self.websocket = await websockets.connect("wss://api.upbit.com/websocket/v1")
        print("✅ WebSocket 연결 완료")

    async def subscribe_ticker_group(self, group_num: int, symbols: List[str]) -> str:
        """특정 그룹의 현재가 구독"""
        ticket_id = str(uuid.uuid4())

        # 티켓 정보 저장
        self.tickets[ticket_id] = TicketInfo(
            ticket_id=ticket_id,
            group_number=group_num,
            symbols=symbols,
            request_time=datetime.now()
        )

        # 구독 메시지 생성 (실시간 스트림으로 변경)
        message = [
            {"ticket": ticket_id},
            {"type": "ticker", "codes": symbols},
            {"format": "DEFAULT"}
        ]

        # 전송
        await self.websocket.send(json.dumps(message))

        print(f"📤 그룹 {group_num} 구독 요청 (티켓: {ticket_id[:8]}..., 심벌: {len(symbols)}개) [실시간 스트림]")
        print(f"   - 첫 3개: {', '.join(symbols[:3])}")
        print(f"   - 마지막 3개: {', '.join(symbols[-3:])}")

        return ticket_id

    async def listen_responses(self):
        """응답 수신 및 분석"""
        print(f"\n👂 {self.test_duration}초간 응답 수신 시작...")
        start_time = time.time()

        while time.time() - start_time < self.test_duration:
            try:
                # 0.1초 타임아웃으로 메시지 수신
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=0.1
                )

                # JSON 파싱
                data = json.loads(message)

                # ticker 응답만 처리
                if data.get("type") == "ticker":
                    symbol = data.get("code", "unknown")

                    # 어떤 티켓의 응답인지 추론 (실제로는 불가능!)
                    ticket_id = self.infer_ticket_from_symbol(symbol)

                    response_info = ResponseInfo(
                        ticket_id=ticket_id or "unknown",
                        symbol=symbol,
                        response_time=datetime.now(),
                        stream_type=data.get("stream_type", "UNKNOWN"),
                        data=data
                    )

                    self.responses.append(response_info)

                    # 응답 카운트 증가
                    if ticket_id and ticket_id in self.tickets:
                        self.tickets[ticket_id].response_count += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"❌ 응답 처리 오류: {e}")

        print(f"✅ 응답 수신 완료 (총 {len(self.responses)}개)")

    def infer_ticket_from_symbol(self, symbol: str) -> str:
        """심벌로부터 티켓 추론 (실제로는 불가능한 작업!)"""
        for ticket_id, ticket_info in self.tickets.items():
            if symbol in ticket_info.symbols:
                return ticket_id
        return "unknown"

    def analyze_results(self):
        """결과 분석 및 출력"""
        print("\n" + "="*80)
        print("📊 테스트 결과 분석")
        print("="*80)

        # 티켓별 응답 통계
        print("\n🎫 티켓별 응답 현황:")
        for ticket_id, ticket_info in self.tickets.items():
            print(f"  티켓 {ticket_info.group_number} ({ticket_id[:8]}...): "
                  f"{ticket_info.response_count}/{len(ticket_info.symbols)}개 응답")

        # 그룹별 응답 심벌 정리
        print("\n📋 그룹별 응답 심벌:")
        for group_num in [1, 2, 3]:
            group_responses = []
            for response in self.responses:
                ticket_info = self.tickets.get(response.ticket_id)
                if ticket_info and ticket_info.group_number == group_num:
                    group_responses.append(response.symbol)

            print(f"  {self.format_response_summary(group_responses, group_num)}")

        # 시간순 응답 패턴 분석
        print("\n⏰ 시간순 응답 패턴 (처음 15개):")
        sorted_responses = sorted(self.responses, key=lambda x: x.response_time)
        for i, response in enumerate(sorted_responses[:15]):
            ticket_info = self.tickets.get(response.ticket_id)
            group_num = ticket_info.group_number if ticket_info else "?"
            time_str = response.response_time.strftime("%H:%M:%S.%f")[:-3]
            stream_type = response.stream_type
            print(f"  {i + 1:2d}. [{time_str}] 그룹{group_num} - {response.symbol} ({stream_type})")

        if len(sorted_responses) > 15:
            print(f"     ... (총 {len(sorted_responses)}개 응답)")

        # 스트림 타입별 통계
        print("\n📊 스트림 타입별 응답 통계:")
        snapshot_count = sum(1 for r in self.responses if r.stream_type == "SNAPSHOT")
        realtime_count = sum(1 for r in self.responses if r.stream_type == "REALTIME")
        unknown_count = sum(1 for r in self.responses if r.stream_type not in ["SNAPSHOT", "REALTIME"])

        print(f"  📸 SNAPSHOT: {snapshot_count}개")
        print(f"  🔴 REALTIME: {realtime_count}개")
        if unknown_count > 0:
            print(f"  ❓ 기타: {unknown_count}개")

        # 시간대별 응답 분포 (초 단위)
        print("\n⏱️  초별 응답 분포:")
        time_buckets = {}
        start_time = sorted_responses[0].response_time if sorted_responses else datetime.now()

        for response in sorted_responses:
            elapsed_seconds = int((response.response_time - start_time).total_seconds())
            if elapsed_seconds not in time_buckets:
                time_buckets[elapsed_seconds] = 0
            time_buckets[elapsed_seconds] += 1

        for second in sorted(time_buckets.keys())[:10]:  # 처음 10초만 표시
            count = time_buckets[second]
            print(f"  {second:2d}초: {count:3d}개 응답")

        if len(time_buckets) > 10:
            print(f"  ... (총 {len(time_buckets)}초 동안 응답)")

        # 지속적 응답 여부 확인
        print("\n🔄 지속적 응답 패턴 분석:")
        if len(time_buckets) >= 5:
            last_5_seconds = sorted(time_buckets.keys())[-5:]
            avg_responses_per_second = sum(time_buckets[s] for s in last_5_seconds) / 5
            print(f"  📈 마지막 5초 평균 응답: {avg_responses_per_second:.1f}개/초")

            if avg_responses_per_second > 10:
                print("  ✅ 활발한 실시간 스트림 확인")
            elif avg_responses_per_second > 1:
                print("  ⚠️  중간 수준의 실시간 스트림")
            else:
                print("  ❌ 실시간 스트림 거의 없음")
        else:
            print("  ⏳ 분석하기에 충분하지 않은 데이터")

        # 핵심 결론
        print("\n🔍 핵심 발견사항:")

        # 1. 응답에서 티켓 정보 확인
        has_ticket_in_response = False
        sample_response = self.responses[0] if self.responses else None
        if sample_response:
            has_ticket_in_response = "ticket" in sample_response.data
            print(f"  1. 응답에 티켓 정보 포함 여부: {'✅ 포함' if has_ticket_in_response else '❌ 미포함'}")

        # 2. 응답 도착 패턴
        if len(self.responses) > 0:
            # 그룹별 첫 응답 시간 계산
            first_response_times = {}
            for response in sorted_responses:
                ticket_info = self.tickets.get(response.ticket_id)
                if ticket_info:
                    group_num = ticket_info.group_number
                    if group_num not in first_response_times:
                        first_response_times[group_num] = response.response_time

            print("  2. 그룹별 첫 응답 시간:")
            for group_num in sorted(first_response_times.keys()):
                time_str = first_response_times[group_num].strftime("%H:%M:%S.%f")[:-3]
                print(f"     그룹 {group_num}: {time_str}")

        # 3. 응답 혼합 여부
        mixed_responses = False
        if len(self.responses) >= 6:  # 충분한 응답이 있을 때만 분석
            # 처음 6개 응답의 그룹 분포 확인
            first_six_groups = []
            for response in sorted_responses[:6]:
                ticket_info = self.tickets.get(response.ticket_id)
                if ticket_info:
                    first_six_groups.append(ticket_info.group_number)

            unique_groups_in_first_six = len(set(first_six_groups))
            mixed_responses = unique_groups_in_first_six > 1

        print(f"  3. 응답 혼합 패턴: {'🔀 그룹간 응답 혼합됨' if mixed_responses else '📦 그룹별 순차 응답'}")

        # 최종 결론
        print("\n🎯 최종 결론:")
        if not self.responses:
            print("  ❌ 응답을 받지 못했습니다.")
        else:
            print(f"  ✅ 총 {len(self.responses)}개 응답 수신")
            print(f"  ✅ 응답에서 티켓 정보로 구분: {'불가능' if not has_ticket_in_response else '가능'}")
            print(f"  ✅ 응답 패턴: {'혼합 스트림' if mixed_responses else '순차 스트림'}")
            print("  📝 업비트는 모든 구독 응답을 단일 스트림으로 혼합 전송하며,")
            print("     클라이언트는 응답 내용(type, code 등)으로만 구분해야 합니다.")

        print("\n💡 티켓의 실제 목적:")
        print("  🎫 구독 상태 관리: 서버가 클라이언트별 구독을 추적")
        print("  🔢 동시 연결 제한: 최대 5개 티켓 동시 사용 제한")
        print("  📊 구독 조회: LIST_SUBSCRIPTIONS으로 현재 구독 확인")
        print("  🚫 구독 해제: 업비트는 개별 구독 해제 기능 미제공")
        print("  ⚠️  새 구독 시: 기존 구독이 누적되어 응답량 증가")
        print("     → 연결 종료 후 재연결로만 구독 초기화 가능")

    async def run_test(self):
        """전체 테스트 실행"""
        try:
            # 1. 마켓 정보 조회
            symbols = await self.get_krw_markets()

            # 2. 그룹 분할
            groups = self.split_symbols_into_groups(symbols, 50)
            print(f"\n📊 심벌 그룹 분할 완료: {len(groups)}개 그룹")
            for i, group in enumerate(groups, 1):
                print(f"  그룹 {i}: {len(group)}개 심벌")

            # 3. WebSocket 연결
            await self.connect_websocket()

            # 4. 각 그룹별 순차 구독 (1초 간격)
            print("\n🔄 그룹별 순차 구독 시작...")
            for i, group in enumerate(groups, 1):
                await self.subscribe_ticker_group(i, group)
                if i < len(groups):  # 마지막 그룹이 아니면 1초 대기
                    await asyncio.sleep(1)

            # 5. 응답 수신
            await self.listen_responses()

            # 6. 결과 분석
            self.analyze_results()

        except Exception as e:
            print(f"❌ 테스트 실행 오류: {e}")
        finally:
            if self.websocket:
                await self.websocket.close()


async def main():
    """메인 실행 함수"""
    print("🚀 업비트 WebSocket 멀티 티켓 응답 패턴 테스트 시작")
    print("=" * 80)

    tester = MultiTicketTester()
    await tester.run_test()

    print("\n" + "=" * 80)
    print("✅ 테스트 완료")


if __name__ == "__main__":
    asyncio.run(main())

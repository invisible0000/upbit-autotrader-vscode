# d:\projects\upbit-autotrader-vscode\upbit_auto_trading\infrastructure\market_data_backbone\smart_router\core\batch_subscription_manager.py

import asyncio
import json
import time
from collections import defaultdict
from typing import Dict, List, Set, Callable, Any, Tuple

class BatchSubscriptionManager:
    """
    여러 요청을 단일 메시지로 일괄 처리하여 네트워크 오버헤드를 최소화하고
    API 제한을 준수하도록 WebSocket 구독을 관리합니다.
    """
    def __init__(self,
                 send_websocket_message_func: Callable[[str], None],
                 batch_interval_seconds: float = 0.1):
        """
        :param send_websocket_message_func: JSON 문자열을 받아 WebSocket 연결을 통해
                                            전송하는 호출 가능한 함수입니다.
        :param batch_interval_seconds: 전송하기 전에 구독 요청을 수집할 시간 창입니다.
        """
        self._send_websocket_message = send_websocket_message_func
        self.batch_interval_seconds = batch_interval_seconds
        self._pending_subscriptions: Set[Tuple[str, ...]] = set() # 고유한 구독 키를 저장합니다 (예: ('ticker', 'KRW-BTC'))
        self._active_subscriptions: Set[Tuple[str, ...]] = set() # 현재 활성 구독을 저장합니다.
        self._batch_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock() # 공유 상태를 보호하기 위한 락

    async def subscribe(self, data_type: str, symbols: List[str]):
        """
        대기 중인 일괄 처리에 구독 요청을 추가합니다.
        """
        # 구독을 위한 고유 키 생성
        sub_key = (data_type, *sorted(symbols))

        async with self._lock:
            if sub_key in self._active_subscriptions:
                # 이미 구독 중이므로 다시 구독할 필요가 없습니다.
                return

            if sub_key not in self._pending_subscriptions:
                self._pending_subscriptions.add(sub_key)
                if self._batch_task is None or self._batch_task.done():
                    self._batch_task = asyncio.create_task(self._send_batch_periodically())

    async def unsubscribe(self, data_type: str, symbols: List[str]):
        """
        구독을 제거합니다. 참고: 업비트 WebSocket API는 일반적으로 시장 데이터 스트림에 대한
        명시적인 구독 취소 메시지를 지원하지 않습니다. 이는 내부 상태 관리를 위한 것입니다.아
        명시적인 구독 취소가 필요한 경우, `send_websocket_message_func`가 이를 처리해야 합니다.
        """
        sub_key = (data_type, *sorted(symbols))
        async with self._lock:
            if sub_key in self._active_subscriptions:
                self._active_subscriptions.remove(sub_key)
                # 실제 시나리오에서는 API가 지원하고 해당 유형에 대한 마지막 구독인 경우
                # 여기에 구독 취소 메시지를 보낼 수 있습니다.
                print(f"정보: {sub_key}에서 내부적으로 구독 취소되었습니다. "
                      "참고: 업비트 시장 데이터 WS는 일반적으로 명시적인 구독 취소를 지원하지 않습니다.")

    async def _send_batch_periodically(self):
        """
        누적된 구독 요청을 주기적으로 전송합니다.
        """
        await asyncio.sleep(self.batch_interval_seconds) # 일괄 처리 시간 창을 기다립니다.

        async with self._lock:
            if not self._pending_subscriptions:
                return

            # 업비트 WebSocket 구독 메시지 구성
            # 예시: [{"ticket":"test"}, {"type":"ticker","codes":["KRW-BTC","KRW-ETH"]}]
            # 참고: 업비트 WS API는 심볼에 'codes'를 사용합니다.

            # 일괄 처리를 위해 대기 중인 구독을 data_type별로 그룹화합니다.
            grouped_subs: Dict[str, List[str]] = defaultdict(list)
            for sub_key in self._pending_subscriptions:
                data_type = sub_key[0]
                symbols = list(sub_key[1:])
                grouped_subs[data_type].extend(symbols)

            messages = []
            # 각 연결/세션에 대한 고유한 티켓
            ticket = {"ticket": f"smartrouter_{int(time.time() * 1000)}"}
            messages.append(ticket)

            for data_type, symbols_list in grouped_subs.items():
                # 업비트 WS API는 심볼에 'codes'를 사용합니다.
                message_payload = {"type": data_type, "codes": list(set(symbols_list))} # 심볼 중복 제거를 위해 set 사용
                messages.append(message_payload)

            # 대기 중인 것을 지우고 활성 상태로 이동
            self._active_subscriptions.update(self._pending_subscriptions)
            self._pending_subscriptions.clear()

            try:
                full_message = json.dumps(messages) # 이 줄을 try 안으로 이동
                # 일괄 처리된 메시지 전송
                await self._send_websocket_message(full_message)
                print(f"정보: 일괄 처리된 WS 구독 전송: {full_message}")
            except Exception as e:
                print(f"오류: 일괄 처리된 WS 메시지 전송 실패: {e}")
                # 실패 시, 대기 중인 것을 다시 이동하거나 재시도 고려
                self._pending_subscriptions.update(self._active_subscriptions.difference(self._pending_subscriptions))
                self._active_subscriptions.difference_update(self._pending_subscriptions)

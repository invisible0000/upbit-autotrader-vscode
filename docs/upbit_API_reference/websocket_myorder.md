# WebSocket 내 주문 및 체결 (MyOrder) API 명세

## 📋 개요

업비트 WebSocket MyOrder API는 사용자의 주문 및 체결 정보를 실시간으로 제공합니다. 주문 상태 변화, 체결 발생, 주문 취소 등의 이벤트를 즉시 수신하여 자동매매 시스템이나 포트폴리오 관리에 활용할 수 있습니다.

**엔드포인트**: `wss://api.upbit.com/websocket/v1`
**인증 필요**: ✅ API Key 필수

## 🎯 주요 특징

### 실시간 이벤트 기반
- **이벤트 조건**: 실제 주문/체결 발생시에만 데이터 전송
- **즉시 알림**: 주문 상태 변화 즉시 수신
- **미전송 정상**: 주문/체결이 없으면 데이터 미수신 (정상 동작)

### 자전거래 체결 방지 (SMP) 지원
- **SMP 타입**: `reduce`, `cancel_maker`, `cancel_taker`
- **체결 방지**: 동일 회원 간 메이커/테이커 체결 방지
- **신규 상태**: `prevented` (체결 방지) 상태 추가

### 고급 주문 조건
- **IOC**: Immediate or Cancel
- **FOK**: Fill or Kill
- **POST_ONLY**: 메이커 주문만 허용

## 📤 요청 메시지 형식

### 기본 구조
```json
[
  {
    "ticket": "unique-ticket-id"
  },
  {
    "type": "myOrder"
  }
]
```

### 특정 페어 구독
```json
[
  {
    "ticket": "myorder-specific"
  },
  {
    "type": "myOrder",
    "codes": ["KRW-BTC", "KRW-ETH"]
  }
]
```

### 요청 파라미터

| 필드 | 타입 | 설명 | 필수 여부 | 기본값 |
|------|------|------|-----------|--------|
| `type` | String | `myOrder` 고정값 | Required | - |
| `codes` | List\<String\> | 수신할 페어 목록 (대문자) | Optional | 전체 마켓 |

⚠️ **주의**: `codes`를 빈 배열로 설정하거나 생략하면 모든 마켓 정보를 수신합니다.

## 📥 응답 데이터 명세

### 응답 구조
```json
{
  "type": "myOrder",
  "code": "KRW-BTC",
  "uuid": "ac2dc2a3-fce9-40a2-a4f6-5987c25c438f",
  "ask_bid": "BID",
  "order_type": "limit",
  "state": "trade",
  "trade_uuid": "68315169-fba4-4175-ade3-aff14a616657",
  "price": 0.001453,
  "avg_price": 0.00145372,
  "volume": 30925891.29839369,
  "remaining_volume": 29968038.09235948,
  "executed_volume": 30925891.29839369,
  "trades_count": 1,
  "reserved_fee": 44.23943970238218,
  "remaining_fee": 21.77177967409916,
  "paid_fee": 22.467660028283017,
  "locked": 43565.33112787242,
  "executed_funds": 44935.32005656603,
  "time_in_force": null,
  "trade_fee": 22.467660028283017,
  "is_maker": true,
  "identifier": "test-1",
  "smp_type": "cancel_maker",
  "prevented_volume": 1.174291929,
  "prevented_locked": 0.001706246173,
  "trade_timestamp": 1710751590421,
  "order_timestamp": 1710751590000,
  "timestamp": 1710751597500,
  "stream_type": "REALTIME"
}
```

### 필드 상세 설명

#### 기본 주문 정보
| 필드 | 약칭 | 설명 | 타입 | 값 |
|------|------|------|------|-----|
| `type` | `ty` | 데이터 타입 | String | myOrder |
| `code` | `cd` | 페어 코드 | String | KRW-BTC |
| `uuid` | `uid` | 주문 고유 식별자 | String | - |
| `ask_bid` | `ab` | 매수/매도 구분 | String | ASK(매도), BID(매수) |
| `order_type` | `ot` | 주문 타입 | String | limit, price, market, best |

#### 주문 상태 정보
| 필드 | 약칭 | 설명 | 타입 | 값 |
|------|------|------|------|-----|
| `state` | `s` | 주문 상태 | String | wait, watch, trade, done, cancel, prevented |
| `trade_uuid` | `tuid` | 체결 고유 식별자 | String | - |
| `identifier` | `id` | 클라이언트 지정 식별자 | String | - |

##### 주문 상태 상세
- **`wait`**: 체결 대기 (일반 지정가 주문)
- **`watch`**: 예약 주문 대기 (조건부 주문)
- **`trade`**: 체결 발생 (부분 체결 포함)
- **`done`**: 전체 체결 완료
- **`cancel`**: 주문 취소
- **`prevented`**: 체결 방지 (SMP 기능으로 취소)

#### 가격 및 거래량 정보
| 필드 | 약칭 | 설명 | 타입 | 참고 |
|------|------|------|------|------|
| `price` | `p` | 주문가격 또는 체결가격 | Double | state=trade일 때 체결가격 |
| `avg_price` | `ap` | 평균 체결 가격 | Double | - |
| `volume` | `v` | 주문량 또는 체결량 | Double | state=trade일 때 체결량 |
| `remaining_volume` | `rv` | 체결 후 주문 잔량 | Double | - |
| `executed_volume` | `ev` | 체결된 총 수량 | Double | - |

#### 수수료 및 자금 정보
| 필드 | 약칭 | 설명 | 타입 | 참고 |
|------|------|------|------|------|
| `reserved_fee` | `rsf` | 수수료 예약 비용 | Double | - |
| `remaining_fee` | `rmf` | 남은 수수료 | Double | - |
| `paid_fee` | `pf` | 사용된 수수료 | Double | - |
| `trade_fee` | `tf` | 체결 시 발생 수수료 | Double | state≠trade시 null |
| `locked` | `l` | 거래 사용중 비용 | Double | - |
| `executed_funds` | `ef` | 체결된 총 금액 | Double | - |

#### 고급 주문 정보
| 필드 | 약칭 | 설명 | 타입 | 값 |
|------|------|------|------|-----|
| `time_in_force` | `tif` | 주문 조건 | String | ioc, fok, post_only |
| `is_maker` | `im` | 메이커/테이커 여부 | Boolean | true(메이커), false(테이커) |
| `trades_count` | `tc` | 해당 주문 체결 수 | Integer | - |

#### 자전거래 체결 방지 (SMP)
| 필드 | 약칭 | 설명 | 타입 | 값 |
|------|------|------|------|-----|
| `smp_type` | `smpt` | SMP 타입 | String | reduce, cancel_maker, cancel_taker |
| `prevented_volume` | `pv` | 체결 방지로 취소된 수량 | Double | - |
| `prevented_locked` | `pl` | 체결 방지로 취소된 금액/수량 | Double | 매수시 금액, 매도시 수량 |

#### 타임스탬프
| 필드 | 약칭 | 설명 | 타입 | 단위 |
|------|------|------|------|------|
| `trade_timestamp` | `ttms` | 체결 타임스탬프 | Long | ms |
| `order_timestamp` | `otms` | 주문 타임스탬프 | Long | ms |
| `timestamp` | `tms` | 이벤트 타임스탬프 | Long | ms |
| `stream_type` | `st` | 스트림 타입 | String | REALTIME, SNAPSHOT |

## 💡 활용 예시

### 1. 기본 주문 모니터링
```python
import asyncio
import websockets
import json
import jwt
import hashlib
import os

def create_auth_header():
    """업비트 WebSocket 인증 헤더 생성"""
    access_key = os.environ.get('UPBIT_ACCESS_KEY')
    secret_key = os.environ.get('UPBIT_SECRET_KEY')

    payload = {
        'access_key': access_key,
        'nonce': str(uuid.uuid4())
    }

    jwt_token = jwt.encode(payload, secret_key, algorithm='HS256')
    auth_header = f'Bearer {jwt_token}'
    return auth_header

async def monitor_my_orders():
    uri = "wss://api.upbit.com/websocket/v1"
    auth_header = create_auth_header()

    headers = {
        'Authorization': auth_header
    }

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        subscribe_message = [
            {"ticket": "myorder-monitor"},
            {"type": "myOrder"}
        ]

        await websocket.send(json.dumps(subscribe_message))

        while True:
            data = await websocket.recv()
            order = json.loads(data)

            # 주문 상태별 처리
            if order['state'] == 'trade':
                print(f"🎯 체결 발생: {order['code']} "
                      f"{order['ask_bid']} {order['volume']:,.8f} @ {order['price']:,}")
            elif order['state'] == 'done':
                print(f"✅ 주문 완료: {order['code']} "
                      f"총 체결량: {order['executed_volume']:,.8f}")
            elif order['state'] == 'cancel':
                print(f"❌ 주문 취소: {order['code']} {order['uuid']}")
```

### 2. 실시간 PnL 계산
```python
class RealTimePnLCalculator:
    def __init__(self):
        self.positions = {}  # 포지션 관리
        self.orders = {}     # 주문 관리

    def process_order_event(self, order_data):
        """주문 이벤트 처리"""
        code = order_data['code']
        uuid = order_data['uuid']

        # 주문 정보 업데이트
        self.orders[uuid] = order_data

        if order_data['state'] == 'trade':
            self.update_position(order_data)
        elif order_data['state'] == 'done':
            self.finalize_order(order_data)

    def update_position(self, order_data):
        """포지션 업데이트"""
        code = order_data['code']

        if code not in self.positions:
            self.positions[code] = {
                'volume': 0,
                'avg_price': 0,
                'total_cost': 0,
                'realized_pnl': 0
            }

        pos = self.positions[code]

        if order_data['ask_bid'] == 'BID':  # 매수
            # 평균 단가 업데이트
            new_volume = pos['volume'] + order_data['volume']
            new_cost = pos['total_cost'] + (order_data['volume'] * order_data['price'])

            pos['volume'] = new_volume
            pos['total_cost'] = new_cost
            pos['avg_price'] = new_cost / new_volume if new_volume > 0 else 0

        else:  # 매도
            # 실현 손익 계산
            sell_pnl = (order_data['price'] - pos['avg_price']) * order_data['volume']
            pos['realized_pnl'] += sell_pnl
            pos['volume'] -= order_data['volume']

            if pos['volume'] <= 0:
                pos['volume'] = 0
                pos['avg_price'] = 0
                pos['total_cost'] = 0

    def get_position_summary(self):
        """포지션 요약"""
        return {
            code: {
                'volume': pos['volume'],
                'avg_price': pos['avg_price'],
                'realized_pnl': pos['realized_pnl']
            }
            for code, pos in self.positions.items()
            if pos['volume'] > 0
        }
```

### 3. 주문 상태 추적 시스템
```python
class OrderTracker:
    def __init__(self):
        self.active_orders = {}
        self.completed_orders = {}
        self.order_history = []

    def track_order(self, order_data):
        """주문 추적"""
        uuid = order_data['uuid']
        state = order_data['state']

        # 주문 히스토리 추가
        self.order_history.append({
            'timestamp': order_data['timestamp'],
            'uuid': uuid,
            'state': state,
            'data': order_data
        })

        if state in ['wait', 'watch', 'trade']:
            # 활성 주문
            self.active_orders[uuid] = order_data
        elif state in ['done', 'cancel', 'prevented']:
            # 완료된 주문
            if uuid in self.active_orders:
                del self.active_orders[uuid]
            self.completed_orders[uuid] = order_data

    def get_order_status(self, uuid):
        """주문 상태 조회"""
        if uuid in self.active_orders:
            return self.active_orders[uuid]
        elif uuid in self.completed_orders:
            return self.completed_orders[uuid]
        else:
            return None

    def get_fill_rate(self, uuid):
        """체결률 계산"""
        order = self.get_order_status(uuid)
        if not order:
            return 0

        if order['volume'] == 0:
            return 100

        fill_rate = (order['executed_volume'] / order['volume']) * 100
        return fill_rate

    def analyze_execution_quality(self):
        """체결 품질 분석"""
        total_orders = len(self.completed_orders)
        if total_orders == 0:
            return {}

        filled_orders = 0
        partial_fills = 0
        cancelled_orders = 0

        for order in self.completed_orders.values():
            if order['state'] == 'done':
                if order['executed_volume'] == order['volume']:
                    filled_orders += 1
                else:
                    partial_fills += 1
            elif order['state'] == 'cancel':
                cancelled_orders += 1

        return {
            'total_orders': total_orders,
            'fill_rate': (filled_orders / total_orders) * 100,
            'partial_fill_rate': (partial_fills / total_orders) * 100,
            'cancel_rate': (cancelled_orders / total_orders) * 100
        }
```

### 4. SMP (자전거래 체결 방지) 모니터링
```python
def analyze_smp_events(order_data):
    """SMP 이벤트 분석"""
    if order_data.get('smp_type'):
        smp_info = {
            'type': order_data['smp_type'],
            'prevented_volume': order_data.get('prevented_volume', 0),
            'prevented_locked': order_data.get('prevented_locked', 0),
            'original_volume': order_data['volume']
        }

        print(f"🚫 SMP 발생: {order_data['code']}")
        print(f"   타입: {smp_info['type']}")
        print(f"   방지된 수량: {smp_info['prevented_volume']:,.8f}")
        print(f"   방지된 금액: {smp_info['prevented_locked']:,.2f}")

        return smp_info

    return None
```

## ⚠️ 주의사항

### 인증 요구사항
- **API Key 필수**: Access Key와 Secret Key 필요
- **JWT 토큰**: 모든 요청에 Bearer 토큰 포함
- **권한 확인**: 주문 조회 권한이 있는 API Key 사용

### 연결 유지
- **장시간 미전송**: 주문/체결이 없으면 데이터 미수신 (정상)
- **연결 유지**: WebSocket 연결 끊김 방지 로직 필요
- **재연결 처리**: 네트워크 장애시 자동 재연결 구현

### 데이터 처리
- **이벤트 기반**: 상태 변화시에만 데이터 전송
- **순서 보장**: 타임스탬프 기반 이벤트 순서 정렬
- **중복 처리**: 동일 이벤트 중복 수신 가능성 대비

### 성능 최적화
- **선별적 구독**: 필요한 페어만 구독하여 트래픽 절약
- **메모리 관리**: 주문 히스토리 적절한 크기로 제한
- **비동기 처리**: 높은 빈도의 체결 이벤트 대비

## 🔗 관련 API

- [REST 주문하기](https://docs.upbit.com/kr/reference/order-new)
- [REST 주문 취소](https://docs.upbit.com/kr/reference/order-cancel)
- [REST 주문 조회](https://docs.upbit.com/kr/reference/order-info)
- [WebSocket 내 자산](./websocket_myasset.md)

## 📚 추가 자료

- [업비트 WebSocket 인증](https://docs.upbit.com/kr/reference/auth)
- [자전거래 체결 방지 (SMP)](https://docs.upbit.com/docs/smp)
- [주문 타입 상세 가이드](https://docs.upbit.com/kr/docs/order-types)

---

**마지막 업데이트**: 2025년 1월
**API 버전**: v1
**문서 버전**: 1.0

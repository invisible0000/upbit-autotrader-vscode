# WebSocket 내 자산 (MyAsset) API 명세

## 📋 개요

업비트 WebSocket MyAsset API는 사용자의 자산 변동을 실시간으로 제공합니다. 거래 체결, 입출금, 수수료 차감 등으로 인한 자산 변화를 즉시 수신하여 포트폴리오 관리와 자산 추적에 활용할 수 있습니다.

**엔드포인트**: `wss://api.upbit.com/websocket/v1`
**인증 필요**: ✅ API Key 필수

## 🎯 주요 특징

### 실시간 자산 변동 감지
- **이벤트 조건**: 실제 자산 변동 발생시에만 데이터 전송
- **즉시 알림**: 거래, 입출금, 수수료 차감 즉시 수신
- **미전송 정상**: 자산 변동이 없으면 데이터 미수신 (정상 동작)

### 최초 연결 지연 현상
- **최초 이용시**: 수분간 데이터 수신이 지연될 수 있음
- **재연결시**: 최초 연결 이후 재연결에서는 즉시 수신
- **권장사항**: 최초 연결 후 재연결하여 정상 동작 확인

### 전체 자산 정보
- **모든 화폐**: KRW, BTC, 알트코인 등 보유 중인 모든 자산
- **잔고 구분**: 주문 가능 잔고와 주문 중 묶인 잔고 분리
- **고유 식별자**: 자산별 UUID 제공

## 📤 요청 메시지 형식

### 기본 구조
```json
[
  {
    "ticket": "unique-ticket-id"
  },
  {
    "type": "myAsset"
  }
]
```

### 요청 파라미터

| 필드 | 타입 | 설명 | 필수 여부 | 기본값 |
|------|------|------|-----------|--------|
| `type` | String | `myAsset` 고정값 | Required | - |

⚠️ **중요**: MyAsset 타입은 `codes` 파라미터를 지원하지 않습니다. 포함시 "WRONG_FORMAT" 오류가 발생합니다.

### 올바른 요청 예시
```json
[
  {
    "ticket": "myasset-monitor"
  },
  {
    "type": "myAsset"
  },
  {
    "format": "DEFAULT"
  }
]
```

### 잘못된 요청 예시 (오류 발생)
```json
[
  {
    "ticket": "myasset-error"
  },
  {
    "type": "myAsset",
    "codes": ["KRW-BTC"]  // ❌ 지원하지 않음
  }
]
```

## 📥 응답 데이터 명세

### 응답 구조
```json
{
  "type": "myAsset",
  "asset_uuid": "e635f223-1609-4969-8fb6-4376937baad6",
  "assets": [
    {
      "currency": "KRW",
      "balance": 1386929.37231066771348207123,
      "locked": 10329.670127489597585685
    },
    {
      "currency": "BTC",
      "balance": 0.12345678,
      "locked": 0.01000000
    }
  ],
  "asset_timestamp": 1710146517259,
  "timestamp": 1710146517267,
  "stream_type": "REALTIME"
}
```

### 필드 상세 설명

#### 자산 정보
| 필드 | 약칭 | 설명 | 타입 | 예시 |
|------|------|------|------|------|
| `type` | `ty` | 데이터 타입 | String | myAsset |
| `asset_uuid` | `astuid` | 자산 고유 식별자 | String | e635f223-1609-... |
| `assets` | `ast` | 자산 목록 | List of Objects | - |

#### 개별 자산 정보
| 필드 | 약칭 | 설명 | 타입 | 단위 |
|------|------|------|------|------|
| `assets.currency` | `ast.cu` | 화폐 코드 | String | KRW, BTC, ETH 등 |
| `assets.balance` | `ast.b` | 주문 가능 수량 | Double | 사용 가능한 잔고 |
| `assets.locked` | `ast.l` | 주문 중 묶인 수량 | Double | 거래 대기 중인 잔고 |

#### 타임스탬프
| 필드 | 약칭 | 설명 | 타입 | 단위 |
|------|------|------|------|------|
| `asset_timestamp` | `asttms` | 자산 변동 타임스탬프 | Long | ms |
| `timestamp` | `tms` | 이벤트 타임스탬프 | Long | ms |
| `stream_type` | `st` | 스트림 타입 | String | REALTIME |

### 자산 계산 공식
```
총 보유량 = balance + locked
사용 가능 금액 = balance
거래 중 금액 = locked
```

## 💡 활용 예시

### 1. 기본 자산 모니터링
```python
import asyncio
import websockets
import json
import jwt
import uuid
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
    return f'Bearer {jwt_token}'

async def monitor_my_assets():
    uri = "wss://api.upbit.com/websocket/v1"
    auth_header = create_auth_header()

    headers = {
        'Authorization': auth_header
    }

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        subscribe_message = [
            {"ticket": "myasset-monitor"},
            {"type": "myAsset"}
        ]

        await websocket.send(json.dumps(subscribe_message))

        while True:
            data = await websocket.recv()
            asset_data = json.loads(data)

            print(f"💰 자산 변동 감지: {asset_data['asset_timestamp']}")

            for asset in asset_data['assets']:
                currency = asset['currency']
                balance = asset['balance']
                locked = asset['locked']
                total = balance + locked

                if total > 0:  # 보유 중인 자산만 표시
                    print(f"   {currency}: 총 {total:,.8f} "
                          f"(가용: {balance:,.8f}, 거래중: {locked:,.8f})")
```

### 2. 포트폴리오 추적 시스템
```python
class PortfolioTracker:
    def __init__(self):
        self.asset_history = []
        self.previous_assets = {}
        self.total_value_history = []

    def update_assets(self, asset_data):
        """자산 업데이트"""
        current_assets = {}

        for asset in asset_data['assets']:
            currency = asset['currency']
            total_amount = asset['balance'] + asset['locked']

            current_assets[currency] = {
                'balance': asset['balance'],
                'locked': asset['locked'],
                'total': total_amount,
                'timestamp': asset_data['asset_timestamp']
            }

        # 변화 감지 및 기록
        changes = self.detect_changes(current_assets)

        if changes:
            self.asset_history.append({
                'timestamp': asset_data['asset_timestamp'],
                'assets': current_assets.copy(),
                'changes': changes
            })

        self.previous_assets = current_assets

        return changes

    def detect_changes(self, current_assets):
        """자산 변화 감지"""
        changes = {}

        # 모든 화폐 확인
        all_currencies = set(current_assets.keys()) | set(self.previous_assets.keys())

        for currency in all_currencies:
            current = current_assets.get(currency, {'total': 0, 'balance': 0, 'locked': 0})
            previous = self.previous_assets.get(currency, {'total': 0, 'balance': 0, 'locked': 0})

            total_change = current['total'] - previous['total']
            balance_change = current['balance'] - previous['balance']
            locked_change = current['locked'] - previous['locked']

            if abs(total_change) > 1e-8:  # 미세한 변화 제외
                changes[currency] = {
                    'total_change': total_change,
                    'balance_change': balance_change,
                    'locked_change': locked_change,
                    'current_total': current['total'],
                    'previous_total': previous['total']
                }

        return changes

    def analyze_transaction_pattern(self):
        """거래 패턴 분석"""
        if len(self.asset_history) < 2:
            return {}

        transaction_types = {
            'deposits': 0,    # 입금
            'withdrawals': 0, # 출금
            'trades': 0,      # 거래
            'fees': 0         # 수수료
        }

        for entry in self.asset_history:
            for currency, change in entry['changes'].items():
                total_change = change['total_change']

                if currency == 'KRW':
                    if total_change > 0:
                        transaction_types['deposits'] += 1
                    elif total_change < 0:
                        transaction_types['withdrawals'] += 1
                else:
                    if total_change != 0:
                        transaction_types['trades'] += 1

        return transaction_types

    def get_portfolio_summary(self):
        """포트폴리오 요약"""
        if not self.previous_assets:
            return {}

        summary = {
            'total_currencies': len([c for c, a in self.previous_assets.items() if a['total'] > 0]),
            'krw_balance': self.previous_assets.get('KRW', {}).get('total', 0),
            'crypto_holdings': {},
            'locked_ratio': 0
        }

        total_locked_value = 0
        total_balance_value = 0

        for currency, asset in self.previous_assets.items():
            if currency != 'KRW' and asset['total'] > 0:
                summary['crypto_holdings'][currency] = asset['total']

            # 잠김 비율 계산 (KRW 기준으로 근사)
            if currency == 'KRW':
                total_locked_value += asset['locked']
                total_balance_value += asset['balance']

        total_value = total_locked_value + total_balance_value
        if total_value > 0:
            summary['locked_ratio'] = (total_locked_value / total_value) * 100

        return summary
```

### 3. 실시간 손익 계산
```python
class RealTimePnLTracker:
    def __init__(self):
        self.initial_assets = {}
        self.current_prices = {}  # 현재가 정보 (별도 구독 필요)

    def set_initial_assets(self, asset_data):
        """초기 자산 설정"""
        for asset in asset_data['assets']:
            currency = asset['currency']
            total_amount = asset['balance'] + asset['locked']

            if total_amount > 0:
                self.initial_assets[currency] = total_amount

    def update_current_prices(self, ticker_data):
        """현재가 정보 업데이트 (Ticker WebSocket에서)"""
        if ticker_data['code'].startswith('KRW-'):
            currency = ticker_data['code'].split('-')[1]
            self.current_prices[currency] = ticker_data['trade_price']

    def calculate_pnl(self, current_asset_data):
        """손익 계산"""
        pnl_data = {
            'total_initial_value': 0,
            'total_current_value': 0,
            'currency_pnl': {}
        }

        current_assets = {}
        for asset in current_asset_data['assets']:
            currency = asset['currency']
            current_assets[currency] = asset['balance'] + asset['locked']

        # 각 화폐별 손익 계산
        all_currencies = set(self.initial_assets.keys()) | set(current_assets.keys())

        for currency in all_currencies:
            initial_amount = self.initial_assets.get(currency, 0)
            current_amount = current_assets.get(currency, 0)

            if currency == 'KRW':
                # KRW는 직접 계산
                initial_value = initial_amount
                current_value = current_amount
            else:
                # 암호화폐는 KRW 가격으로 환산
                price = self.current_prices.get(currency, 0)
                initial_value = initial_amount * price
                current_value = current_amount * price

            pnl = current_value - initial_value
            pnl_ratio = (pnl / initial_value * 100) if initial_value > 0 else 0

            pnl_data['currency_pnl'][currency] = {
                'initial_amount': initial_amount,
                'current_amount': current_amount,
                'initial_value': initial_value,
                'current_value': current_value,
                'pnl': pnl,
                'pnl_ratio': pnl_ratio
            }

            pnl_data['total_initial_value'] += initial_value
            pnl_data['total_current_value'] += current_value

        # 전체 손익
        total_pnl = pnl_data['total_current_value'] - pnl_data['total_initial_value']
        total_pnl_ratio = (total_pnl / pnl_data['total_initial_value'] * 100) if pnl_data['total_initial_value'] > 0 else 0

        pnl_data['total_pnl'] = total_pnl
        pnl_data['total_pnl_ratio'] = total_pnl_ratio

        return pnl_data
```

### 4. 자산 변동 알림 시스템
```python
class AssetAlertSystem:
    def __init__(self):
        self.alert_rules = []

    def add_alert_rule(self, currency, condition, threshold, message):
        """알림 규칙 추가"""
        self.alert_rules.append({
            'currency': currency,
            'condition': condition,  # 'increase', 'decrease', 'above', 'below'
            'threshold': threshold,
            'message': message
        })

    def check_alerts(self, asset_changes):
        """알림 규칙 확인"""
        alerts = []

        for rule in self.alert_rules:
            currency = rule['currency']

            if currency in asset_changes:
                change = asset_changes[currency]
                total_change = change['total_change']
                current_total = change['current_total']

                alert_triggered = False

                if rule['condition'] == 'increase' and total_change >= rule['threshold']:
                    alert_triggered = True
                elif rule['condition'] == 'decrease' and total_change <= -rule['threshold']:
                    alert_triggered = True
                elif rule['condition'] == 'above' and current_total >= rule['threshold']:
                    alert_triggered = True
                elif rule['condition'] == 'below' and current_total <= rule['threshold']:
                    alert_triggered = True

                if alert_triggered:
                    alerts.append({
                        'currency': currency,
                        'rule': rule,
                        'change': change,
                        'timestamp': time.time()
                    })

        return alerts

# 사용 예시
alert_system = AssetAlertSystem()
alert_system.add_alert_rule('KRW', 'decrease', 100000, 'KRW 잔고가 10만원 이상 감소했습니다')
alert_system.add_alert_rule('BTC', 'increase', 0.001, 'BTC 보유량이 0.001 이상 증가했습니다')
```

## ⚠️ 주의사항

### 최초 연결 지연
- **초기 설정**: 계정 최초 WebSocket 연결시 수분간 지연 가능
- **해결 방법**: 최초 연결 후 재연결하여 정상 동작 확인
- **예시**: 2025년 5월 1일 00:00 최초 연결 → 00:05분부터 정상 수신

### 인증 요구사항
- **API Key 필수**: 자산 조회 권한이 있는 API Key 필요
- **JWT 토큰**: 모든 요청에 Bearer 토큰 포함
- **보안 주의**: Secret Key 노출 방지

### 데이터 특성
- **이벤트 기반**: 자산 변동시에만 데이터 전송
- **전체 자산**: 변동 발생시 모든 자산 정보 전송
- **고정밀도**: Double 타입으로 소수점 이하 정밀도 유지

### 성능 고려사항
- **메모리 관리**: 자산 히스토리 적절한 크기로 제한
- **연결 유지**: 장시간 변동 없을 시 연결 끊김 방지
- **오류 처리**: 네트워크 장애시 재연결 로직 필요

## 🔗 관련 API

- [REST 전체 계좌 조회](https://docs.upbit.com/kr/reference/get-balance)
- [WebSocket 내 주문](./websocket_myorder.md)
- [WebSocket 현재가](./websocket_ticker.md)

## 📚 추가 자료

- [업비트 WebSocket 인증](https://docs.upbit.com/kr/reference/auth)
- [자산 관리 가이드](https://docs.upbit.com/kr/docs/asset-management)
- [포트폴리오 추적 방법](https://docs.upbit.com/kr/docs/portfolio-tracking)

---

**마지막 업데이트**: 2025년 1월
**API 버전**: v1
**문서 버전**: 1.0

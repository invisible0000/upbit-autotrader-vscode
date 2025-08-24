# 🔄 다중 거래소 지원을 위한 External APIs 구조 개선 방안

## 📊 현재 구조 문제점 분석

### 🚨 업비트 종속성 문제
1. **RateLimiter**: 업비트 전용 설정과 헤더 파싱
2. **UnifiedResponseConverter**: 업비트 데이터 구조 가정 (market 필드, KRW- 접두사)
3. **BaseApiClient**: 업비트 특화 파라미터명과 배치 처리

### 🎯 개선 목표
- 거래소 중립적인 Common 레이어 구현
- 각 거래소별 어댑터 패턴 적용
- 코드 중복 최소화하면서 확장성 확보

## 🏗️ 제안하는 새로운 구조

```
external_apis/
├── core/                          # 거래소 중립적 핵심 기능
│   ├── __init__.py
│   ├── base_client.py            # 추상 베이스 클라이언트
│   ├── rate_limiter.py           # 범용 Rate Limiter
│   ├── response_normalizer.py    # 거래소별 응답 정규화
│   └── data_models.py           # 공통 데이터 모델
├── adapters/                     # 거래소별 어댑터
│   ├── __init__.py
│   ├── upbit_adapter.py         # 업비트 전용 어댑터
│   ├── binance_adapter.py       # 바이낸스 어댑터 (예시)
│   └── base_adapter.py          # 어댑터 베이스
├── upbit/                        # 업비트 구현
│   ├── __init__.py
│   ├── upbit_public_client.py
│   ├── upbit_private_client.py
│   └── upbit_websocket_client.py
└── binance/                      # 바이낸스 구현 (미래)
    ├── __init__.py
    ├── binance_public_client.py
    └── binance_private_client.py
```

## 🔧 핵심 개선 사항

### 1. 거래소 중립적 Rate Limiter

```python
@dataclass
class ExchangeRateLimitConfig:
    requests_per_second: int
    requests_per_minute: int
    burst_limit: int
    headers_pattern: Dict[str, str]  # 각 거래소별 헤더 패턴

class UniversalRateLimiter:
    def __init__(self, exchange_config: ExchangeRateLimitConfig):
        # 거래소별 설정 적용

    def parse_server_headers(self, headers: Dict[str, str], exchange_type: str):
        # 거래소별 헤더 파싱 로직
```

### 2. 거래소별 어댑터 패턴

```python
class ExchangeAdapter(ABC):
    @abstractmethod
    def normalize_symbol_format(self, symbol: str) -> str:
        pass

    @abstractmethod
    def build_batch_params(self, symbols: List[str]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def parse_response(self, response: Any, data_type: str) -> Dict[str, Any]:
        pass

class UpbitAdapter(ExchangeAdapter):
    def normalize_symbol_format(self, symbol: str) -> str:
        return symbol  # KRW-BTC 형식 그대로

    def build_batch_params(self, symbols: List[str]) -> Dict[str, Any]:
        return {'markets': ','.join(symbols)}

    def parse_response(self, response: Any, data_type: str) -> Dict[str, Any]:
        # 업비트 특화 파싱 로직
        return response

class BinanceAdapter(ExchangeAdapter):
    def normalize_symbol_format(self, symbol: str) -> str:
        return symbol.replace('-', '')  # KRWBTC → BTCUSDT 형식 변환

    def build_batch_params(self, symbols: List[str]) -> Dict[str, Any]:
        return {'symbols': symbols}  # 바이낸스는 배열 형태
```

### 3. 통합 클라이언트 팩토리

```python
class ExchangeClientFactory:
    @staticmethod
    def create_public_client(exchange: str) -> BaseExchangeClient:
        if exchange.lower() == 'upbit':
            return UpbitPublicClient(UpbitAdapter())
        elif exchange.lower() == 'binance':
            return BinancePublicClient(BinanceAdapter())
        else:
            raise ValueError(f"지원하지 않는 거래소: {exchange}")
```

## 🎯 마이그레이션 전략

### Phase 1: Core 분리
- [ ] 현재 `common/` → `core/`로 이동
- [ ] 업비트 종속성 제거한 베이스 클래스 재작성
- [ ] 거래소 중립적 Rate Limiter 구현

### Phase 2: 어댑터 패턴 도입
- [ ] UpbitAdapter 구현으로 업비트 특화 로직 분리
- [ ] BaseExchangeClient와 어댑터 연동
- [ ] 기존 업비트 클라이언트를 새 구조로 마이그레이션

### Phase 3: 다중 거래소 지원
- [ ] BinanceAdapter 구현 (예시)
- [ ] ExchangeClientFactory 완성
- [ ] 통합 테스트 수행

## 💡 즉시 적용 가능한 개선사항

### 1. 현재 구조에서 최소 변경으로 개선
```python
# rate_limiter.py에서
class RateLimitConfig:
    @classmethod
    def for_exchange(cls, exchange: str, api_type: str) -> 'RateLimitConfig':
        configs = {
            'upbit': {
                'public': cls(10, 600, 50),
                'private': cls(8, 200, 30)
            },
            'binance': {
                'public': cls(20, 1200, 100),
                'private': cls(10, 600, 50)
            }
        }
        return configs[exchange][api_type]
```

### 2. 응답 변환기 개선
```python
# unified_response_converter.py에서
class UniversalResponseConverter:
    @staticmethod
    def convert_ticker_response(api_response: List[Dict],
                              exchange: str,
                              symbols: List[str]) -> Dict[str, Any]:
        if exchange == 'upbit':
            return UpbitResponseConverter.convert_ticker(api_response, symbols)
        elif exchange == 'binance':
            return BinanceResponseConverter.convert_ticker(api_response, symbols)
```

## 🔍 결론 및 권장사항

### ✅ 권장사항
1. **단계적 마이그레이션**: 기존 시스템 동작 보장하면서 점진적 개선
2. **어댑터 패턴 우선 적용**: 가장 큰 효과를 얻을 수 있는 핵심 개선
3. **Interface 표준화**: 모든 거래소가 동일한 인터페이스 제공

### ⚠️ 주의사항
- 현재 업비트 기능 무중단 보장 필요
- DDD 아키텍처 원칙 준수 (Infrastructure 계층 내 변경)
- 테스트 커버리지 확보 후 마이그레이션

### 🎯 우선순위
1. **High**: 어댑터 패턴 도입으로 업비트 종속성 분리
2. **Medium**: 범용 Rate Limiter 구현
3. **Low**: 실제 다중 거래소 클라이언트 구현

이러한 개선을 통해 확장 가능하고 유지보수가 용이한 다중 거래소 지원 아키텍처를 구축할 수 있습니다.

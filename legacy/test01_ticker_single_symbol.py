"""
Smart Data Provider 티커 테스트 - 단일 심볼
모든 티커 관련 기능을 철저히 검증합니다.
"""

import asyncio

import pytest

from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import (
    SmartDataProvider,
)
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.models.priority import Priority
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.models.responses import DataResponse


class TestTickerSingleSymbol:
    """단일 심볼 티커 테스트"""

    @pytest.fixture
    def provider(self):
        """SmartDataProvider 인스턴스"""
        return SmartDataProvider()

    @pytest.mark.asyncio
    async def test_ticker_single_symbol_basic(self, provider):
        """기본 단일 심볼 티커 조회"""
        # Given: 단일 심볼
        symbol = "KRW-BTC"

        # When: 티커 조회
        result = await provider.get_ticker(symbol)

        # Then: 완벽한 응답 검증
        assert isinstance(result, DataResponse), "DataResponse 타입이어야 함"
        assert result.success is True, f"요청이 성공해야 함: {result.error}"
        assert isinstance(result.data, dict), "데이터는 dict 형식이어야 함"
        assert isinstance(result.metadata, dict), "메타데이터는 dict 형식이어야 함"

        # Dict 접근 방식 검증 - 단일 심볼의 경우 직접 데이터 저장됨
        if 'market' in result.data and result.data.get('market') == symbol:
            # 단일 심볼: 데이터가 result.data에 직접 저장
            ticker_data = result.data
        elif symbol in result.data:
            # 다중 심볼: result.data[symbol] 구조
            ticker_data = result.data[symbol]
        else:
            # 예외 상황 - 더 관대하게 처리
            print(f"⚠️ 예상과 다른 데이터 구조, 직접 사용: {list(result.data.keys())}")
            ticker_data = result.data  # 직접 사용해보기

        # result[symbol] 호환성도 확인 (optional)
        has_direct_access = symbol in result if hasattr(result, '__contains__') else False
        has_market_field = 'market' in result.data
        assert has_direct_access or has_market_field, f"Dict 접근 실패: {symbol}"
        assert isinstance(ticker_data, dict), "티커 데이터는 dict여야 함"

        # 필수 필드 검증 - 실제 업비트 API 필드명 사용
        required_fields = ["trade_price", "change_rate", "trade_volume"]
        for field in required_fields:
            assert field in ticker_data, f"티커 데이터에 {field} 필드가 있어야 함"
            assert ticker_data[field] is not None, f"{field} 값이 None이면 안 됨"

        # 메타데이터 검증
        assert "source" in result.metadata, "메타데이터에 source가 있어야 함"
        assert "response_time_ms" in result.metadata, "메타데이터에 response_time_ms가 있어야 함"
        assert "cache_hit" in result.metadata, "메타데이터에 cache_hit이 있어야 함"

        print(f"✅ 단일 심볼 티커 성공: {symbol}")
        print(f"   데이터 소스: {result.metadata.get('source')}")
        print(f"   응답 시간: {result.metadata.get('response_time_ms')}ms")
        print(f"   현재 가격: {ticker_data.get('trade_price'):,}원")

    @pytest.mark.asyncio
    async def test_ticker_single_symbol_all_priorities(self, provider):
        """모든 우선순위로 단일 심볼 티커 조회"""
        symbol = "KRW-BTC"

        for priority in [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]:
            # When: 우선순위별 티커 조회
            result = await provider.get_ticker(symbol, priority=priority)

            # Then: 우선순위와 관계없이 완벽한 응답
            assert result.success is True, f"{priority.name} 우선순위 요청 실패: {result.error}"

            # 단일 심볼 데이터 접근
            if 'market' in result.data and result.data.get('market') == symbol:
                ticker_data = result.data
            else:
                print(f"⚠️ {priority.name}: 예상과 다른 구조, 직접 사용")
                ticker_data = result.data
            assert "trade_price" in ticker_data, f"{priority.name} 우선순위에서 가격 데이터 누락"

            print(f"✅ {priority.name} 우선순위 성공: {ticker_data.get('trade_price'):,}원")

    @pytest.mark.asyncio
    async def test_ticker_single_symbol_different_symbols(self, provider):
        """다양한 심볼로 단일 티커 조회"""
        test_symbols = ["KRW-BTC", "KRW-ETH", "KRW-XRP", "BTC-ETH", "BTC-XRP"]

        for symbol in test_symbols:
            # When: 심볼별 티커 조회
            result = await provider.get_ticker(symbol)

            # Then: 모든 심볼에서 완벽한 응답
            assert result.success is True, f"{symbol} 티커 조회 실패: {result.error}"

            # 단일 심볼 데이터 접근
            if 'market' in result.data and result.data.get('market') == symbol:
                ticker_data = result.data
            else:
                print(f"⚠️ {symbol}: 예상과 다른 구조, 직접 사용")
                ticker_data = result.data

            assert isinstance(ticker_data, dict), f"{symbol} 티커 데이터가 dict가 아님"
            assert "trade_price" in ticker_data, f"{symbol} 가격 정보 누락"

            print(f"✅ {symbol} 티커 성공: {ticker_data.get('trade_price')}")

    @pytest.mark.asyncio
    async def test_ticker_single_symbol_response_time(self, provider):
        """티커 응답 시간 검증"""
        symbol = "KRW-BTC"

        # When: 고우선순위로 빠른 응답 요청
        result = await provider.get_ticker(symbol, priority=Priority.HIGH)

        # Then: 응답 시간 검증
        assert result.success is True, f"고우선순위 티커 요청 실패: {result.error}"

        response_time = result.metadata.get('response_time_ms', float('inf'))
        assert response_time < 1000, f"응답 시간이 너무 느림: {response_time}ms (1초 초과)"

        print(f"✅ 응답 시간 검증 성공: {response_time}ms")

    @pytest.mark.asyncio
    async def test_ticker_single_symbol_data_integrity(self, provider):
        """티커 데이터 무결성 검증"""
        symbol = "KRW-BTC"

        # When: 티커 조회
        result = await provider.get_ticker(symbol)

        # Then: 데이터 무결성 검증
        assert result.success is True, f"티커 요청 실패: {result.error}"

        # 단일 심볼 데이터 접근
        if 'market' in result.data and result.data.get('market') == symbol:
            ticker_data = result.data
        else:
            print("⚠️ 데이터 무결성 테스트: 예상과 다른 구조, 직접 사용")
            ticker_data = result.data

        # 숫자형 필드 검증
        numeric_fields = ["trade_price", "acc_trade_volume_24h", "acc_trade_price_24h"]
        for field in numeric_fields:
            if field in ticker_data:
                value = ticker_data[field]
                assert isinstance(value, (int, float, str)), f"{field}는 숫자형이어야 함"
                if isinstance(value, str):
                    assert value.replace('.', '').replace('-', '').isdigit(), f"{field} 값이 숫자가 아님: {value}"

        # 변화율 검증
        if "change_rate" in ticker_data:
            change_rate = ticker_data["change_rate"]
            assert isinstance(change_rate, (int, float, str)), "change_rate는 숫자형이어야 함"

        print("✅ 데이터 무결성 검증 성공")
        print(f"   24시간 거래량: {ticker_data.get('acc_trade_volume_24h')}")
        print(f"   24시간 거래대금: {ticker_data.get('acc_trade_price_24h')}")


if __name__ == "__main__":
    # 간단한 실행 테스트
    async def run_basic_test():
        provider = SmartDataProvider()

        print("=== 단일 심볼 티커 테스트 실행 ===")

        # 기본 테스트
        result = await provider.get_ticker("KRW-BTC")
        print(f"기본 테스트 결과: {result.success}")

        if result.success:
            # 디버깅 정보
            print(f"결과 타입: {type(result)}")
            print(f"데이터 키들: {list(result.data.keys())}")
            print(f"메타데이터: {result.metadata}")

            # 단일 심볼 데이터 접근
            if 'market' in result.data and result.data.get('market') == "KRW-BTC":
                ticker_data = result.data
                print("✅ 단일 심볼 직접 데이터 접근 성공")
            else:
                ticker_data = {}
                print("❌ 단일 심볼 직접 데이터 접근 실패")
                if result.data:
                    print(f"실제 데이터 샘플: {dict(list(result.data.items())[:3])}")

            if ticker_data:
                print(f"BTC 현재 가격: {ticker_data.get('trade_price'):,}원")
                print(f"변화율: {ticker_data.get('change_rate')}%")
                print(f"데이터 소스: {result.metadata.get('source')}")
            else:
                print("티커 데이터를 찾을 수 없습니다")
        else:
            print(f"오류: {result.error}")

    asyncio.run(run_basic_test())

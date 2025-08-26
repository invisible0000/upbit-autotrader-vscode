"""
test01_single_ticker_single_request.py
====================================

SmartDataProvider 티커 기본 기능 테스트
- 단일 심볼, 단일 요청
- 기본적인 데이터 품질 검증
- 응답 시간 측정
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import SmartDataProvider


class TestSingleTickerSingleRequest:
    """단일 티커 단일 요청 테스트"""

    @pytest.fixture
    async def smart_provider(self):
        """SmartDataProvider 인스턴스 생성"""
        provider = SmartDataProvider()
        yield provider
        # cleanup if needed

    @pytest.mark.asyncio
    async def test_krw_btc_ticker_basic(self, smart_provider):
        """KRW-BTC 티커 기본 요청 테스트"""
        # Given
        symbol = "KRW-BTC"
        start_time = time.time()

        # When
        result = await smart_provider.get_ticker(symbol)
        response_time = (time.time() - start_time) * 1000

        # Then
        assert result.success is True, f"티커 조회 실패: {result.error}"
        assert result.data is not None, "티커 데이터가 None"
        assert isinstance(result.data, dict), f"티커 데이터가 dict가 아님: {type(result.data)}"

        # 응답 시간 검증 (첫 요청은 최대 2초)
        assert response_time < 2000, f"응답 시간 초과: {response_time:.1f}ms"

        # 메타데이터 검증
        assert hasattr(result, 'metadata'), "메타데이터 누락"
        assert result.metadata.get('source') in ['smart_router', 'upbit_rest_api'], "유효하지 않은 데이터 소스"

        print(f"✅ KRW-BTC 티커 성공 - 응답시간: {response_time:.1f}ms, 소스: {result.metadata.get('source')}")

    @pytest.mark.asyncio
    async def test_krw_eth_ticker_basic(self, smart_provider):
        """KRW-ETH 티커 기본 요청 테스트"""
        # Given
        symbol = "KRW-ETH"
        start_time = time.time()

        # When
        result = await smart_provider.get_ticker(symbol)
        response_time = (time.time() - start_time) * 1000

        # Then
        assert result.success is True, f"티커 조회 실패: {result.error}"
        assert result.data is not None, "티커 데이터가 None"

        # 응답 시간 검증
        assert response_time < 2000, f"응답 시간 초과: {response_time:.1f}ms"

        print(f"✅ KRW-ETH 티커 성공 - 응답시간: {response_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_btc_eth_ticker_basic(self, smart_provider):
        """BTC-ETH 티커 기본 요청 테스트 (BTC 마켓)"""
        # Given
        symbol = "BTC-ETH"
        start_time = time.time()

        # When
        result = await smart_provider.get_ticker(symbol)
        response_time = (time.time() - start_time) * 1000

        # Then
        assert result.success is True, f"티커 조회 실패: {result.error}"
        assert result.data is not None, "티커 데이터가 None"

        # 응답 시간 검증
        assert response_time < 2000, f"응답 시간 초과: {response_time:.1f}ms"

        print(f"✅ BTC-ETH 티커 성공 - 응답시간: {response_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_ticker_data_completeness(self, smart_provider):
        """티커 데이터 완전성 검증"""
        # Given
        symbol = "KRW-BTC"

        # When
        result = await smart_provider.get_ticker(symbol)

        # Then
        assert result.success is True
        data = result.data

        # 필수 필드 검증
        required_fields = [
            "market", "trade_price", "change_rate", "timestamp",
            "opening_price", "high_price", "low_price", "trade_volume"
        ]

        for field in required_fields:
            assert field in data, f"필수 필드 누락: {field}"
            assert data[field] is not None, f"필수 필드가 None: {field}"

        # 데이터 타입 검증
        assert isinstance(data["market"], str), "market 필드가 문자열이 아님"
        assert data["market"] == symbol, f"market 필드 불일치: {data['market']} != {symbol}"
        assert isinstance(data["trade_price"], (int, float)), "trade_price가 숫자가 아님"
        assert data["trade_price"] > 0, "trade_price가 0 이하"
        assert isinstance(data["timestamp"], int), "timestamp가 정수가 아님"
        assert data["timestamp"] > 0, "timestamp가 0 이하"

        print(f"✅ 데이터 완전성 검증 완료 - 필드 수: {len(data)}")

    @pytest.mark.asyncio
    async def test_ticker_field_coverage(self, smart_provider):
        """티커 필드 커버리지 검증 (업비트 공식 API 대비)"""
        # Given
        symbol = "KRW-BTC"

        # When
        result = await smart_provider.get_ticker(symbol)

        # Then
        assert result.success is True
        data = result.data

        # 업비트 공식 REST API 필드들
        official_fields = {
            "market", "trade_date", "trade_time", "trade_date_kst", "trade_time_kst",
            "trade_timestamp", "opening_price", "high_price", "low_price", "trade_price",
            "prev_closing_price", "change", "change_price", "change_rate",
            "signed_change_price", "signed_change_rate", "trade_volume",
            "acc_trade_price", "acc_trade_price_24h", "acc_trade_volume",
            "acc_trade_volume_24h", "highest_52_week_price", "highest_52_week_date",
            "lowest_52_week_price", "lowest_52_week_date", "timestamp"
        }

        # 실제 받은 필드들
        received_fields = set(field for field in data.keys() if not field.startswith('_'))

        # 커버리지 계산
        covered_fields = received_fields.intersection(official_fields)
        coverage_rate = len(covered_fields) / len(official_fields) * 100

        print(f"📊 필드 커버리지: {coverage_rate:.1f}% ({len(covered_fields)}/{len(official_fields)})")
        print(f"📊 전체 필드 수: {len(data)}")

        # 최소 커버리지 요구사항 (90% 이상)
        assert coverage_rate >= 90, f"필드 커버리지 부족: {coverage_rate:.1f}% < 90%"

        # 누락된 중요 필드 확인
        missing_critical = official_fields - received_fields
        if missing_critical:
            print(f"⚠️ 누락된 공식 필드: {sorted(missing_critical)}")

    @pytest.mark.asyncio
    async def test_ticker_response_metadata(self, smart_provider):
        """티커 응답 메타데이터 검증"""
        # Given
        symbol = "KRW-BTC"

        # When
        result = await smart_provider.get_ticker(symbol)

        # Then
        assert result.success is True

        # 메타데이터 필수 필드 검증
        metadata = result.metadata
        assert metadata is not None, "메타데이터가 None"

        required_metadata = ["source", "response_time_ms", "cache_hit", "priority_used"]
        for field in required_metadata:
            assert field in metadata, f"메타데이터 필수 필드 누락: {field}"

        # 메타데이터 값 검증
        assert metadata["source"] in ["smart_router", "upbit_rest_api", "memory_cache"], "유효하지 않은 소스"
        assert isinstance(metadata["response_time_ms"], (int, float)), "응답시간이 숫자가 아님"
        assert metadata["response_time_ms"] >= 0, "응답시간이 음수"
        assert isinstance(metadata["cache_hit"], bool), "cache_hit이 불린이 아님"

        print(f"✅ 메타데이터 검증 완료 - 소스: {metadata['source']}, 캐시: {metadata['cache_hit']}")

    @pytest.mark.asyncio
    async def test_invalid_symbol_handling(self, smart_provider):
        """잘못된 심볼 처리 테스트"""
        # Given
        invalid_symbol = "INVALID-SYMBOL"

        # When
        result = await smart_provider.get_ticker(invalid_symbol)

        # Then
        # 시스템이 실패를 우아하게 처리해야 함
        if not result.success:
            assert result.error is not None, "에러 메시지가 None"
            assert isinstance(result.error, str), "에러 메시지가 문자열이 아님"
            print(f"✅ 잘못된 심볼 우아한 처리: {result.error}")
        else:
            # 일부 시스템은 빈 데이터를 반환할 수 있음
            print(f"⚠️ 잘못된 심볼에 대해 성공 응답: {result.data}")


if __name__ == "__main__":
    # 개별 실행을 위한 간단한 테스트 러너
    async def run_tests():
        test_instance = TestSingleTickerSingleRequest()
        provider = SmartDataProvider()

        print("🧪 test01_single_ticker_single_request 시작...")

        try:
            await test_instance.test_krw_btc_ticker_basic(provider)
            await test_instance.test_krw_eth_ticker_basic(provider)
            await test_instance.test_btc_eth_ticker_basic(provider)
            await test_instance.test_ticker_data_completeness(provider)
            await test_instance.test_ticker_field_coverage(provider)
            await test_instance.test_ticker_response_metadata(provider)
            await test_instance.test_invalid_symbol_handling(provider)

            print("🎉 모든 테스트 통과!")

        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            raise

    # 실행
    asyncio.run(run_tests())

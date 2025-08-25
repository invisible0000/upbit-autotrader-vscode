"""
market 필드 수정 후 빠른 테스트
"""
import asyncio
import sys
import os

# 경로 추가
sys.path.insert(0, os.path.abspath('.'))

async def test_market_field():
    try:
        from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import SmartDataProvider

        print("SmartDataProvider 테스트 시작...")
        provider = SmartDataProvider()
        result = await provider.get_ticker("KRW-BTC")

        if result.success:
            market_value = result.data.get('market', '')
            print(f"✅ market 필드: '{market_value}'")
            print(f"✅ 필드 수: {len(result.data)}")

            # 핵심 필드들 확인
            critical_fields = ["market", "trade_price", "change_rate", "timestamp"]
            for field in critical_fields:
                value = result.data.get(field)
                print(f"  - {field}: {value}")

            return "PASS" if market_value else "FAIL"
        else:
            print(f"❌ 조회 실패: {result.error}")
            return "FAIL"

    except Exception as e:
        print(f"❌ 오류: {e}")
        return "ERROR"

if __name__ == "__main__":
    result = asyncio.run(test_market_field())
    print(f"\n최종 결과: {result}")

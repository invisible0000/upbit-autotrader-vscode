"""
KRW-BTC 1일봉 500개 데이터를 DB에 연속성 있게 준비하는 스크립트

Smart Data Provider를 통해 업비트 API에서 500개의 일봉 데이터를
가져와서 SQLite DB에 저장합니다.
"""

import asyncio
from datetime import datetime, timedelta
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import SmartDataProvider
from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.models.priority import Priority


async def prepare_btc_daily_candles_to_db():
    """KRW-BTC 1일봉 500개를 DB에 준비"""
    print("📊 KRW-BTC 1일봉 500개 데이터 DB 준비 시작")

    provider = SmartDataProvider()
    symbol = "KRW-BTC"
    timeframe = "1d"
    target_count = 500

    try:
        print(f"\n🎯 목표: {symbol} {timeframe} {target_count}개")
        print("=" * 60)

        # 현재 DB 상태 확인
        print("📋 현재 DB 상태 확인...")
        existing_result = await provider.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=10,  # 기존 데이터 확인용
            priority=Priority.NORMAL
        )

        existing_count = len(existing_result.data) if existing_result.data else 0
        print(f"   기존 데이터: {existing_count}개")
        print(f"   소스: {existing_result.metadata.source if existing_result.metadata else 'Unknown'}")

        # 500개 데이터 요청 (여러 번 나누어서)
        batch_size = 200  # 한 번에 200개씩
        total_collected = 0

        print(f"\n🔄 데이터 수집 시작 (배치 크기: {batch_size})")

        for batch_num in range(3):  # 3번에 나누어 수집 (200 + 200 + 100 = 500)
            batch_count = min(batch_size, target_count - total_collected)
            if batch_count <= 0:
                break

            print(f"\n📦 배치 {batch_num + 1}: {batch_count}개 요청")

            # 시작 시점 계산 (과거부터 연속으로)
            days_ago = total_collected
            end_time = datetime.now() - timedelta(days=days_ago)
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")

            result = await provider.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=batch_count,
                end_time=end_time_str,  # 시점 지정
                priority=Priority.HIGH  # 높은 우선순위
            )

            if result.success and result.data:
                batch_collected = len(result.data)
                total_collected += batch_collected

                print(f"   ✅ 수집 성공: {batch_collected}개")
                print(f"   🔗 소스: {result.metadata.source if result.metadata else 'Unknown'}")
                print(f"   ⚡ 응답시간: {result.metadata.response_time_ms if result.metadata else 0:.1f}ms")
                print(f"   📊 누적 수집: {total_collected}개")

                # 첫 번째와 마지막 캔들 시간 출력
                if isinstance(result.data, list) and len(result.data) > 0:
                    first_candle = result.data[0]
                    last_candle = result.data[-1]

                    if isinstance(first_candle, dict):
                        first_time = first_candle.get('candle_date_time_kst', 'Unknown')
                        last_time = last_candle.get('candle_date_time_kst', 'Unknown')
                        print(f"   📅 기간: {last_time} ~ {first_time}")

                # 잠시 대기 (API Rate Limit 고려)
                if batch_num < 2:  # 마지막 배치가 아니면
                    print("   ⏳ 1초 대기...")
                    await asyncio.sleep(1)

            else:
                print(f"   ❌ 수집 실패: {result.error if hasattr(result, 'error') else 'Unknown error'}")
                break

        print(f"\n🎉 데이터 수집 완료!")
        print(f"📊 총 수집된 데이터: {total_collected}개")

        # 최종 DB 상태 확인
        print(f"\n📋 최종 DB 상태 확인...")
        final_result = await provider.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=target_count,
            priority=Priority.NORMAL
        )

        if final_result.success:
            final_count = len(final_result.data) if final_result.data else 0
            print(f"   ✅ DB에 저장된 데이터: {final_count}개")
            print(f"   🔗 소스: {final_result.metadata.source if final_result.metadata else 'Unknown'}")

            if final_count >= target_count:
                print(f"   🎯 목표 달성! ({target_count}개 이상)")
            else:
                print(f"   ⚠️  목표 미달성: {target_count - final_count}개 부족")
        else:
            print(f"   ❌ DB 확인 실패: {final_result.error if hasattr(final_result, 'error') else 'Unknown'}")

    except Exception as e:
        print(f"🚨 예외 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n🔧 준비 완료")


if __name__ == "__main__":
    asyncio.run(prepare_btc_daily_candles_to_db())

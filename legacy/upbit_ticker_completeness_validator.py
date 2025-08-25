"""
업비트 티커 데이터 완전성 검증 도구

업비트 공식 문서와 실제 데이터를 비교하여 모든 필드가 올바르게 처리되는지 검증합니다.
"""

import asyncio
import logging
from typing import Dict, Any, Set
from datetime import datetime

from upbit_auto_trading.infrastructure.market_data_backbone.smart_data_provider.core.smart_data_provider import SmartDataProvider

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UpbitTickerValidator:
    """업비트 티커 데이터 완전성 검증기"""

    def __init__(self):
        # 업비트 공식 WebSocket 티커 필드 (docs.upbit.com 기준)
        self.official_websocket_fields = {
            # 필수 필드
            "type",           # 데이터 항목 (ticker)
            "code",           # 페어 코드 (KRW-BTC)
            "opening_price",  # 시가
            "high_price",     # 고가
            "low_price",      # 저가
            "trade_price",    # 현재가
            "prev_closing_price",  # 전일 종가
            "change",         # 전일 종가 대비 변동 방향
            "change_price",   # 전일 대비 가격 변동의 절대값
            "signed_change_price",  # 전일 대비 가격 변동 값
            "change_rate",    # 전일 대비 등락율의 절대값
            "signed_change_rate",   # 전일 대비 등락율
            "trade_volume",   # 가장 최근 거래량
            "acc_trade_volume",     # 누적 거래량(UTC 0시 기준)
            "acc_trade_volume_24h", # 24시간 누적 거래량
            "acc_trade_price",      # 누적 거래대금(UTC 0시 기준)
            "acc_trade_price_24h",  # 24시간 누적 거래대금
            "trade_date",     # 최근 거래 일자(UTC)
            "trade_time",     # 최근 거래 시각(UTC)
            "trade_timestamp",  # 체결 타임스탬프(ms)
            "ask_bid",        # 매수/매도 구분
            "acc_ask_volume", # 누적 매도량
            "acc_bid_volume", # 누적 매수량
            "highest_52_week_price",  # 52주 최고가
            "highest_52_week_date",   # 52주 최고가 달성일
            "lowest_52_week_price",   # 52주 최저가
            "lowest_52_week_date",    # 52주 최저가 달성일
            "market_state",   # 거래상태
            "is_trading_suspended",   # 거래 정지 여부 (Deprecated)
            "delisting_date", # 거래지원 종료일
            "market_warning", # 유의 종목 여부
            "timestamp",      # 타임스탬프 (ms)
            "stream_type"     # 스트림 타입
        }

        # 업비트 공식 REST API 티커 필드
        self.official_rest_fields = {
            "market",         # 페어 코드
            "trade_date",     # 최근 체결 일자 (UTC)
            "trade_time",     # 최근 체결 시각 (UTC)
            "trade_date_kst", # 최근 체결 일자 (KST)
            "trade_time_kst", # 최근 체결 시각 (KST)
            "trade_timestamp", # 체결 타임스탬프
            "opening_price",  # 시가
            "high_price",     # 고가
            "low_price",      # 저가
            "trade_price",    # 종가(현재가)
            "prev_closing_price",  # 전일 종가
            "change",         # 가격 변동 상태
            "change_price",   # 전일 종가 대비 가격 변화(절대값)
            "change_rate",    # 전일 종가 대비 가격 변화율(절대값)
            "signed_change_price",  # 전일 종가 대비 가격 변화
            "signed_change_rate",   # 전일 종가 대비 가격 변화율
            "trade_volume",   # 최근 거래 수량
            "acc_trade_price", # 누적 거래 금액 (UTC 0시 기준)
            "acc_trade_price_24h", # 24시간 누적 거래 금액
            "acc_trade_volume",    # 누적 거래량 (UTC 0시 기준)
            "acc_trade_volume_24h", # 24시간 누적 거래량
            "highest_52_week_price", # 52주 신고가
            "highest_52_week_date",  # 52주 신고가 달성일
            "lowest_52_week_price",  # 52주 신저가
            "lowest_52_week_date",   # 52주 신저가 달성일
            "timestamp"       # 현재가 정보 반영 시각 타임스탬프(ms)
        }

        # 핵심 비즈니스 필드 (필수 검증)
        self.critical_fields = {
            "trade_price",    # 현재가 - 가장 중요
            "change_rate",    # 변화율 - 매우 중요
            "trade_volume",   # 거래량 - 중요
            "acc_trade_volume_24h",  # 24시간 거래량 - 중요
            "acc_trade_price_24h",   # 24시간 거래대금 - 중요
            "opening_price",  # 시가 - 중요
            "high_price",     # 고가 - 중요
            "low_price",      # 저가 - 중요
            "timestamp",      # 타임스탬프 - 필수
            "market"          # 심볼 - 필수
        }

    async def validate_ticker_completeness(self, symbol: str = "KRW-BTC") -> Dict[str, Any]:
        """티커 데이터 완전성 검증"""
        print("\n" + "=" * 80)
        print("🔍 업비트 티커 데이터 완전성 검증")
        print("=" * 80)

        provider = SmartDataProvider()
        result = await provider.get_ticker(symbol)

        if not result.success:
            return {"error": f"데이터 조회 실패: {result.error}"}

        validation_results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "data_source": result.metadata.get('source'),
            "channel": result.metadata.get('channel'),
            "response_time_ms": result.metadata.get('response_time_ms'),
            "validation_results": {}
        }

        # 실제 받은 데이터 구조 분석
        received_fields = set(result.data.keys())
        print(f"📊 받은 필드 수: {len(received_fields)}")
        print(f"📊 데이터 소스: {result.metadata.get('source')}")

        # 1. 핵심 비즈니스 필드 검증
        print("\n🔥 핵심 비즈니스 필드 검증:")
        critical_validation = self._validate_critical_fields(result.data, received_fields)
        validation_results["validation_results"]["critical_fields"] = critical_validation

        # 2. 공식 API 필드와 비교
        print("\n📋 공식 API 필드 비교:")
        api_validation = self._validate_against_official_api(received_fields)
        validation_results["validation_results"]["api_comparison"] = api_validation

        # 3. 데이터 타입 및 값 검증
        print("\n🔢 데이터 타입 및 값 검증:")
        type_validation = self._validate_data_types(result.data)
        validation_results["validation_results"]["data_types"] = type_validation

        # 4. 메타데이터 검증
        print("\n🏷️ 메타데이터 검증:")
        metadata_validation = self._validate_metadata(result.data, result.metadata)
        validation_results["validation_results"]["metadata"] = metadata_validation

        # 5. 종합 점수 계산
        overall_score = self._calculate_overall_score(validation_results["validation_results"])
        validation_results["overall_score"] = overall_score

        print(f"\n🎯 종합 검증 점수: {overall_score}/100")

        if overall_score >= 95:
            print("✅ 우수: 실운영 시스템에 적합한 데이터 품질")
        elif overall_score >= 85:
            print("⚠️ 양호: 일부 개선 필요")
        else:
            print("❌ 부족: 추가 개발 필요")

        return validation_results

    def _validate_critical_fields(self, data: Dict[str, Any], received_fields: Set[str]) -> Dict[str, Any]:
        """핵심 비즈니스 필드 검증"""
        results = {
            "total_critical": len(self.critical_fields),
            "present_critical": 0,
            "missing_critical": [],
            "invalid_values": [],
            "field_details": {}
        }

        for field in self.critical_fields:
            if field in received_fields:
                results["present_critical"] += 1
                value = data.get(field)

                # 값 유효성 검증
                field_validation = self._validate_field_value(field, value)
                results["field_details"][field] = field_validation

                if field_validation["valid"]:
                    print(f"  ✅ {field}: {value} ({field_validation['type']})")
                else:
                    print(f"  ❌ {field}: {value} - {field_validation['issue']}")
                    results["invalid_values"].append({
                        "field": field,
                        "value": value,
                        "issue": field_validation["issue"]
                    })
            else:
                results["missing_critical"].append(field)
                print(f"  ❌ 누락: {field}")

        coverage = (results["present_critical"] / results["total_critical"]) * 100
        print(f"📊 핵심 필드 커버리지: {coverage:.1f}% ({results['present_critical']}/{results['total_critical']})")
        results["coverage_percent"] = coverage

        return results

    def _validate_against_official_api(self, received_fields: Set[str]) -> Dict[str, Any]:
        """공식 API 필드와 비교 검증"""

        # WebSocket vs REST 필드 매핑 고려
        websocket_to_rest_mapping = {
            "code": "market",  # WebSocket의 code는 REST의 market과 동일
        }

        # 받은 필드를 REST API 기준으로 정규화
        normalized_fields = set()
        for field in received_fields:
            if field in websocket_to_rest_mapping:
                normalized_fields.add(websocket_to_rest_mapping[field])
            else:
                normalized_fields.add(field)

        # REST API 필드와 비교
        present_official = normalized_fields.intersection(self.official_rest_fields)
        missing_official = self.official_rest_fields - normalized_fields
        extra_fields = normalized_fields - self.official_rest_fields

        # 메타데이터 필드 제외 (우리 시스템 고유)
        extra_fields = {f for f in extra_fields if not f.startswith('_')}

        results = {
            "total_official": len(self.official_rest_fields),
            "present_official": len(present_official),
            "missing_official": list(missing_official),
            "extra_fields": list(extra_fields),
            "coverage_percent": (len(present_official) / len(self.official_rest_fields)) * 100
        }

        print(f"📊 공식 필드 커버리지: {results['coverage_percent']:.1f}% ({len(present_official)}/{len(self.official_rest_fields)})")

        if missing_official:
            print(f"  ❌ 누락 필드 ({len(missing_official)}개): {', '.join(sorted(missing_official))}")

        if extra_fields:
            print(f"  ➕ 추가 필드 ({len(extra_fields)}개): {', '.join(sorted(extra_fields))}")

        return results

    def _validate_data_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """데이터 타입 및 값 검증"""
        results = {
            "total_fields": 0,
            "valid_types": 0,
            "invalid_types": [],
            "null_values": [],
            "type_details": {}
        }

        expected_types = {
            "trade_price": (int, float),
            "change_rate": (int, float),
            "trade_volume": (int, float),
            "acc_trade_volume_24h": (int, float),
            "acc_trade_price_24h": (int, float),
            "opening_price": (int, float),
            "high_price": (int, float),
            "low_price": (int, float),
            "timestamp": (int),
            "market": (str),
            "change": (str)
        }

        for field, value in data.items():
            if field.startswith('_'):  # 메타데이터 필드 스킵
                continue

            results["total_fields"] += 1

            if value is None:
                results["null_values"].append(field)
                print(f"  ⚠️ {field}: NULL 값")
                continue

            value_type = type(value)
            expected_type = expected_types.get(field)

            if expected_type:
                if isinstance(value, expected_type):
                    results["valid_types"] += 1
                    print(f"  ✅ {field}: {value_type.__name__} (예상: {expected_type})")
                else:
                    results["invalid_types"].append({
                        "field": field,
                        "actual_type": value_type.__name__,
                        "expected_type": str(expected_type),
                        "value": str(value)[:50]
                    })
                    print(f"  ❌ {field}: {value_type.__name__} (예상: {expected_type})")
            else:
                print(f"  📝 {field}: {value_type.__name__} (타입 미지정)")

            results["type_details"][field] = {
                "type": value_type.__name__,
                "value_sample": str(value)[:50]
            }

        return results

    def _validate_metadata(self, data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """메타데이터 검증"""
        results = {
            "metadata_fields": len(metadata),
            "internal_fields": 0,
            "issues": []
        }

        # 내부 메타데이터 필드 검증
        internal_fields = [f for f in data.keys() if f.startswith('_')]
        results["internal_fields"] = len(internal_fields)

        print(f"📊 메타데이터 필드: {len(metadata)}개")
        print(f"📊 내부 필드: {len(internal_fields)}개")

        # 필수 메타데이터 확인
        required_metadata = ['source', 'response_time_ms', 'cache_hit']
        for field in required_metadata:
            if field in metadata:
                print(f"  ✅ {field}: {metadata[field]}")
            else:
                results["issues"].append(f"필수 메타데이터 누락: {field}")
                print(f"  ❌ 누락: {field}")

        return results

    def _validate_field_value(self, field: str, value: Any) -> Dict[str, Any]:
        """개별 필드 값 유효성 검증"""
        validation = {
            "valid": True,
            "type": type(value).__name__,
            "issue": None
        }

        if value is None:
            validation["valid"] = False
            validation["issue"] = "NULL 값"
            return validation

        # 필드별 특수 검증
        if field == "trade_price":
            if not isinstance(value, (int, float)) or value <= 0:
                validation["valid"] = False
                validation["issue"] = "현재가는 양수여야 함"

        elif field == "change_rate":
            if not isinstance(value, (int, float)):
                validation["valid"] = False
                validation["issue"] = "변화율은 숫자여야 함"

        elif field == "timestamp":
            if not isinstance(value, int) or value <= 0:
                validation["valid"] = False
                validation["issue"] = "타임스탬프는 양의 정수여야 함"

        elif field == "market":
            if not isinstance(value, str) or not value:
                validation["valid"] = False
                validation["issue"] = "심볼은 비어있지 않은 문자열이어야 함"

        return validation

    def _calculate_overall_score(self, validation_results: Dict[str, Any]) -> int:
        """종합 검증 점수 계산 (100점 만점)"""
        score = 0

        # 핵심 필드 커버리지 (40점)
        critical = validation_results.get("critical_fields", {})
        critical_coverage = critical.get("coverage_percent", 0)
        score += (critical_coverage / 100) * 40

        # 공식 API 호환성 (30점)
        api = validation_results.get("api_comparison", {})
        api_coverage = api.get("coverage_percent", 0)
        score += (api_coverage / 100) * 30

        # 데이터 타입 정확성 (20점)
        types = validation_results.get("data_types", {})
        if types.get("total_fields", 0) > 0:
            type_accuracy = (types.get("valid_types", 0) / types.get("total_fields", 1)) * 100
            score += (type_accuracy / 100) * 20

        # 메타데이터 품질 (10점)
        metadata = validation_results.get("metadata", {})
        if len(metadata.get("issues", [])) == 0:
            score += 10
        else:
            score += max(0, 10 - len(metadata.get("issues", [])) * 2)

        return min(100, int(score))


async def main():
    """메인 검증 실행"""
    validator = UpbitTickerValidator()

    # 다양한 심볼로 검증
    test_symbols = ["KRW-BTC", "KRW-ETH", "BTC-ETH"]

    for symbol in test_symbols:
        print(f"\n{'='*20} {symbol} 검증 {'='*20}")
        try:
            result = await validator.validate_ticker_completeness(symbol)

            if "error" not in result:
                score = result.get("overall_score", 0)
                print(f"\n📊 {symbol} 최종 점수: {score}/100")
            else:
                print(f"\n❌ {symbol} 검증 실패: {result['error']}")

        except Exception as e:
            print(f"\n💥 {symbol} 검증 중 오류: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

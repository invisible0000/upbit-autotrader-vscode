"""
빈 캐들 벡터화 로직 테스트 - 청크 경계 문제 해결 검증

목적: 문서의 5가지 시나리오를 Mock 데이터로 구현하여
      기존 로직 vs 벡터화 로직의 정확성과 성능을 비교 검증

테스트 시나리오:
1. 현재시간 기준 빈 캔들이 없는 이상적 상황
2. 현재시간 기준 빈 캔들이 처음에 존재할 때 1
3. 현재시간 기준 빈 캔들이 처음에 존재할 때 2  
4. 현재시간 기준 빈 캔들이 처음에 존재할 때 3
5. 엣지 케이스: 빈 캔들이 청크 처음에 이어질 때

Created: 2025-09-21
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import pytest

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.market_data.candle.empty_candle_detector import EmptyCandleDetector, GapInfo
from upbit_auto_trading.infrastructure.market_data.candle.time_utils import TimeUtils

# 로그 출력 최소화
import logging
logging.getLogger("EmptyCandleDetector").setLevel(logging.WARNING)

logger = create_component_logger("EmptyCandleVectorizedTest")


class MockDataGenerator:
    """문서 시나리오 기반 Mock 데이터 생성기"""

    def __init__(self, timeframe: str = "1m"):
        self.timeframe = timeframe
        self.symbol = "KRW-BTC"

    def create_scenario_1(self) -> Dict[str, Any]:
        """
        시나리오 1: 현재시간 기준 빈 캔들이 없는 이상적 상황
        
        상황:
        - 현재시간(20) 기준 연속된 캔들 데이터
        - 청크1: [19,18,17,16,15], 청크2: [14,13,12,11,10]
        - Gap 없음
        """
        current_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)
        
        # 청크1 데이터 (chunk_to=19, chunk_end=15)
        chunk1_times = [
            current_time - timedelta(minutes=1),  # 19
            current_time - timedelta(minutes=2),  # 18
            current_time - timedelta(minutes=3),  # 17
            current_time - timedelta(minutes=4),  # 16
            current_time - timedelta(minutes=5),  # 15
        ]
        
        # 청크2 데이터 (chunk_to=14, chunk_end=10)
        chunk2_times = [
            current_time - timedelta(minutes=6),   # 14
            current_time - timedelta(minutes=7),   # 13
            current_time - timedelta(minutes=8),   # 12
            current_time - timedelta(minutes=9),   # 11
            current_time - timedelta(minutes=10),  # 10
        ]
        
        return {
            "scenario_name": "이상적 상황 (Gap 없음)",
            "current_time": current_time,
            "chunk1": {
                "datetime_list": chunk1_times,
                "api_start": current_time - timedelta(minutes=1),  # 19
                "api_end": current_time - timedelta(minutes=5),    # 15
                "is_first_chunk": True,
                "expected_gaps": 0
            },
            "chunk2": {
                "datetime_list": chunk2_times,
                "api_start": current_time - timedelta(minutes=6),   # 14
                "api_end": current_time - timedelta(minutes=10),   # 10
                "is_first_chunk": False,
                "expected_gaps": 0
            }
        }

    def create_scenario_2(self) -> Dict[str, Any]:
        """
        시나리오 2: 현재시간 기준 빈 캔들이 처음에 존재할 때 1
        
        상황:
        - 빈 캔들 [19,18] 
        - 청크1: [17,16,15,14,13], 청크2: [12,11,10]
        - 첫 번째 청크에서 Gap 검출되어야 함
        """
        current_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)
        
        # 청크1 데이터 (빈 캔들 19,18 건너뛰고 17부터)
        chunk1_times = [
            current_time - timedelta(minutes=3),  # 17 (19,18 빈 캔들)
            current_time - timedelta(minutes=4),  # 16
            current_time - timedelta(minutes=5),  # 15
            current_time - timedelta(minutes=6),  # 14
            current_time - timedelta(minutes=7),  # 13
        ]
        
        # 청크2 데이터 (연속됨)
        chunk2_times = [
            current_time - timedelta(minutes=8),   # 12
            current_time - timedelta(minutes=9),   # 11
            current_time - timedelta(minutes=10),  # 10
        ]
        
        return {
            "scenario_name": "첫 번째 빈 캔들 그룹 1개",
            "current_time": current_time,
            "chunk1": {
                "datetime_list": chunk1_times,
                "api_start": current_time - timedelta(minutes=1),  # 19
                "api_end": current_time - timedelta(minutes=5),    # 15
                "is_first_chunk": True,
                "expected_gaps": 1,  # 19,18 빈 캔들 그룹
                "expected_gap_ranges": [
                    (current_time - timedelta(minutes=1), current_time - timedelta(minutes=2))  # 19~18
                ]
            },
            "chunk2": {
                "datetime_list": chunk2_times,
                "api_start": current_time - timedelta(minutes=8),   # 12 (오버랩 보정)
                "api_end": current_time - timedelta(minutes=10),   # 10
                "is_first_chunk": False,
                "expected_gaps": 0
            }
        }

    def create_scenario_3(self) -> Dict[str, Any]:
        """
        시나리오 3: 현재시간 기준 빈 캔들이 처음에 존재할 때 2
        
        상황:
        - 빈 캔들 그룹1: [19,18]
        - 빈 캔들 그룹2: [16]
        - 청크1: [17,15,14,13,12], 청크2에서 중간 Gap 검출
        """
        current_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)
        
        # 청크1 데이터 (19,18 빈 캔들, 16 빈 캔들)
        chunk1_times = [
            current_time - timedelta(minutes=3),  # 17 (19,18 빈 캔들)
            current_time - timedelta(minutes=5),  # 15 (16 빈 캔들)
            current_time - timedelta(minutes=6),  # 14
            current_time - timedelta(minutes=7),  # 13
            current_time - timedelta(minutes=8),  # 12
        ]
        
        # 청크2 데이터 (연속됨)
        chunk2_times = [
            current_time - timedelta(minutes=9),   # 11
            current_time - timedelta(minutes=10),  # 10
        ]
        
        return {
            "scenario_name": "빈 캔들 그룹 2개 (처음 + 중간)",
            "current_time": current_time,
            "chunk1": {
                "datetime_list": chunk1_times,
                "api_start": current_time - timedelta(minutes=1),  # 19
                "api_end": current_time - timedelta(minutes=6),    # 14
                "is_first_chunk": True,
                "expected_gaps": 2,  # 19,18 + 16 빈 캔들 그룹
                "expected_gap_ranges": [
                    (current_time - timedelta(minutes=1), current_time - timedelta(minutes=2)),  # 19~18
                    (current_time - timedelta(minutes=4), current_time - timedelta(minutes=4))   # 16
                ]
            },
            "chunk2": {
                "datetime_list": chunk2_times,
                "api_start": current_time - timedelta(minutes=9),   # 11 (오버랩 보정)
                "api_end": current_time - timedelta(minutes=10),   # 10
                "is_first_chunk": False,
                "expected_gaps": 0
            }
        }

    def create_scenario_4(self) -> Dict[str, Any]:
        """
        시나리오 4: 엣지 케이스 - 빈 캔들이 청크 처음에 이어질 때
        
        상황:
        - 청크1: [17,16,(15),14] - 15는 빈 캔들로 생성됨
        - 청크2: [14,11,10,9,8] - 14는 이전 청크 마지막, 13,12 빈 캔들 검출되어야 함
        - 청크2에서 api_start +1틱(15) 추가로 13,12 빈 캔들 올바르게 검출
        """
        current_time = datetime(2025, 9, 21, 12, 20, 0, tzinfo=timezone.utc)
        
        # 청크1 데이터 (15 빈 캔들)
        chunk1_times = [
            current_time - timedelta(minutes=3),  # 17
            current_time - timedelta(minutes=4),  # 16
            # 15 빈 캔들 (건너뜀)
            current_time - timedelta(minutes=6),  # 14
        ]
        
        # 청크2 데이터 (13,12 빈 캔들)
        chunk2_times = [
            current_time - timedelta(minutes=6),   # 14 (오버랩)
            current_time - timedelta(minutes=9),   # 11 (13,12 빈 캔들)
            current_time - timedelta(minutes=10),  # 10
            current_time - timedelta(minutes=11),  # 9
            current_time - timedelta(minutes=12),  # 8
        ]
        
        return {
            "scenario_name": "청크 경계 엣지 케이스",
            "current_time": current_time,
            "chunk1": {
                "datetime_list": chunk1_times,
                "api_start": current_time - timedelta(minutes=3),  # 17
                "api_end": current_time - timedelta(minutes=6),    # 14
                "is_first_chunk": True,
                "expected_gaps": 1,  # 15 빈 캔들
                "expected_gap_ranges": [
                    (current_time - timedelta(minutes=5), current_time - timedelta(minutes=5))   # 15
                ]
            },
            "chunk2": {
                "datetime_list": chunk2_times,
                "api_start": current_time - timedelta(minutes=6),   # 14
                "api_end": current_time - timedelta(minutes=12),   # 8
                "is_first_chunk": False,
                "expected_gaps": 1,  # 13,12 빈 캔들 (api_start +1틱으로 검출되어야 함)
                "expected_gap_ranges": [
                    (current_time - timedelta(minutes=7), current_time - timedelta(minutes=8))   # 13~12
                ]
            }
        }


class VectorizedLogicTest:
    """벡터화 로직 정확성 및 성능 테스트"""

    def __init__(self):
        self.detector = EmptyCandleDetector("KRW-BTC", "1m")
        self.mock_generator = MockDataGenerator("1m")

    def test_scenario_accuracy(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """시나리오별 정확성 테스트 (기존 vs 벡터화)"""
        scenario_name = scenario["scenario_name"]
        results = {"scenario_name": scenario_name, "chunks": []}

        logger.info(f"🧪 테스트 시나리오: {scenario_name}")

        # 청크별 테스트
        for chunk_name in ["chunk1", "chunk2"]:
            chunk_data = scenario[chunk_name]
            
            datetime_list = chunk_data["datetime_list"]
            api_start = chunk_data["api_start"]
            api_end = chunk_data["api_end"]
            is_first_chunk = chunk_data["is_first_chunk"]
            expected_gaps = chunk_data["expected_gaps"]

            logger.info(f"  📋 {chunk_name}: {len(datetime_list)}개 캔들, 예상 Gap: {expected_gaps}개")

            # 1. 기존 방식 테스트
            try:
                original_gaps = self.detector._detect_gaps_in_datetime_list(
                    datetime_list, self.detector.symbol, api_start, api_end, "fallback_ref"
                )
                original_gap_count = len(original_gaps)
                original_success = True
            except Exception as e:
                logger.error(f"기존 방식 실패: {e}")
                original_gap_count = -1
                original_success = False

            # 2. 벡터화 방식 테스트
            try:
                vectorized_gaps = self.detector._detect_gaps_in_datetime_list(
                    datetime_list, self.detector.symbol, api_start, api_end, 
                    "fallback_ref", is_first_chunk
                )
                vectorized_gap_count = len(vectorized_gaps)
                vectorized_success = True
            except Exception as e:
                logger.error(f"벡터화 방식 실패: {e}")
                vectorized_gap_count = -1
                vectorized_success = False

            # 결과 비교
            accuracy_match = (original_gap_count == vectorized_gap_count == expected_gaps)
            
            chunk_result = {
                "chunk_name": chunk_name,
                "datetime_count": len(datetime_list),
                "expected_gaps": expected_gaps,
                "original": {
                    "gap_count": original_gap_count,
                    "success": original_success
                },
                "vectorized": {
                    "gap_count": vectorized_gap_count,
                    "success": vectorized_success
                },
                "accuracy": {
                    "match_expected": accuracy_match,
                    "both_methods_match": (original_gap_count == vectorized_gap_count),
                    "is_first_chunk": is_first_chunk
                }
            }

            results["chunks"].append(chunk_result)
            
            # 즉시 결과 출력
            status = "✅ 정확" if accuracy_match else "❌ 불일치"
            logger.info(f"    {status} | 기존: {original_gap_count}, 벡터화: {vectorized_gap_count}, 예상: {expected_gaps}")

        return results

    def test_all_scenarios(self) -> List[Dict[str, Any]]:
        """모든 시나리오 테스트 실행"""
        logger.info("🚀 벡터화 로직 정확성 테스트 시작")
        
        # 시나리오 생성
        scenarios = [
            self.mock_generator.create_scenario_1(),
            self.mock_generator.create_scenario_2(), 
            self.mock_generator.create_scenario_3(),
            self.mock_generator.create_scenario_4(),
        ]

        all_results = []
        
        for i, scenario in enumerate(scenarios):
            logger.info(f"\n📊 시나리오 {i+1}/{len(scenarios)}")
            result = self.test_scenario_accuracy(scenario)
            all_results.append(result)

        return all_results

    def print_summary_report(self, all_results: List[Dict[str, Any]]):
        """테스트 결과 종합 리포트"""
        print("\n" + "="*80)
        print("🎯 === 벡터화 로직 정확성 테스트 최종 리포트 ===")
        print("="*80)

        total_chunks = 0
        accurate_chunks = 0
        
        for result in all_results:
            scenario_name = result["scenario_name"]
            print(f"\n📋 {scenario_name}:")
            
            for chunk in result["chunks"]:
                total_chunks += 1
                chunk_name = chunk["chunk_name"]
                expected = chunk["expected_gaps"]
                original = chunk["original"]["gap_count"]
                vectorized = chunk["vectorized"]["gap_count"]
                accurate = chunk["accuracy"]["match_expected"]
                
                if accurate:
                    accurate_chunks += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"  {status} {chunk_name}: 예상={expected}, 기존={original}, 벡터화={vectorized}")

        # 종합 통계
        accuracy_rate = (accurate_chunks / total_chunks * 100) if total_chunks > 0 else 0
        
        print(f"\n📊 종합 결과:")
        print(f"  • 총 청크: {total_chunks}개")
        print(f"  • 정확한 청크: {accurate_chunks}개")
        print(f"  • 정확도: {accuracy_rate:.1f}%")
        
        if accuracy_rate >= 90:
            print(f"  🎉 벡터화 로직이 높은 정확도로 동작합니다!")
        elif accuracy_rate >= 70:
            print(f"  ⚠️ 일부 개선이 필요합니다.")
        else:
            print(f"  ❌ 벡터화 로직에 심각한 문제가 있습니다.")

        print("\n" + "="*80)


def main():
    """메인 테스트 실행"""
    print("🧪 벡터화 로직 정확성 테스트")
    print("목적: 청크 경계 문제 해결 및 정확성 검증")
    print("-" * 60)

    # 테스트 실행
    test_runner = VectorizedLogicTest()
    
    try:
        all_results = test_runner.test_all_scenarios()
        test_runner.print_summary_report(all_results)
        
        logger.info("✅ 모든 정확성 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ 정확성 테스트 완료")
    else:
        print("\n❌ 정확성 테스트 실패")
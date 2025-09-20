"""
CandleDataProvider v4.0 - Enhanced Domain Repository Interface
OverlapAnalyzer 지원 + 새로운 CandleData 모델 지원

설계 원칙:
- OverlapAnalyzer 기존 메서드 완전 호환 유지
- 새로운 CandleData 모델 지원 메서드 추가
- DDD Domain Layer 순수성 유지
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class DataRange:
    """기존 데이터 범위 (OverlapAnalyzer용)"""
    start_time: datetime
    end_time: datetime
    candle_count: int
    is_continuous: bool


class CandleRepositoryInterface(ABC):
    """캔들 데이터 Repository 인터페이스 - OverlapAnalyzer + CandleDataProvider v4.0 지원"""

    # === OverlapAnalyzer 전용 메서드들 (기존 호환성 보장) ===

    @abstractmethod
    async def get_data_ranges(self,
                              symbol: str,
                              timeframe: str,
                              start_time: datetime,
                              end_time: datetime) -> List[DataRange]:
        """지정 구간의 기존 데이터 범위 조회 (OverlapAnalyzer 겹침 분석용)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            List[DataRange]: 기존 데이터 범위 리스트
            - 데이터가 없으면 빈 리스트
            - 데이터가 있으면 연속된 구간별로 DataRange 객체 반환

        Note:
            - OverlapAnalyzer의 핵심 의존성
            - analyze_overlap() → _get_existing_data_ranges() → 이 메서드 호출
            - 겹침 상태 분석과 connected_end 찾기에 사용
        """
        pass

    @abstractmethod
    async def has_any_data_in_range(self,
                                    symbol: str,
                                    timeframe: str,
                                    start_time: datetime,
                                    end_time: datetime) -> bool:
        """지정 범위에 캔들 데이터 존재 여부 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            bool: 데이터 존재 여부 (1개라도 있으면 True)

        Note:
            - overlap_optimizer의 _check_start_overlap 로직 기반
            - 효율적인 LIMIT 1 쿼리 활용
        """
        pass

    @abstractmethod
    async def is_range_complete(self,
                                symbol: str,
                                timeframe: str,
                                start_time: datetime,
                                end_time: datetime,
                                expected_count: int) -> bool:
        """지정 범위의 데이터 완전성 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간
            expected_count: 예상 캔들 개수

        Returns:
            bool: 실제 개수 >= 예상 개수 여부

        Note:
            - overlap_optimizer의 _check_complete_overlap 로직 기반
            - 효율적인 COUNT 쿼리 활용
        """
        pass

    @abstractmethod
    async def find_last_continuous_time(self,
                                        symbol: str,
                                        timeframe: str,
                                        start_time: datetime,
                                        end_time: Optional[datetime] = None) -> Optional[datetime]:
        """시작점부터 연속된 데이터의 마지막 시점 조회

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 시작 시점
            end_time: 종료 시점 (선택적, None이면 무제한)

        Returns:
            Optional[datetime]: 연속된 데이터의 마지막 시점 (없으면 None)

        Note:
            - overlap_analyzer의 find_connected_end 단순화 버전
            - 효율적인 LEAD 윈도우 함수 활용 (309x 최적화)
            - end_time 제한으로 무한 추적 방지
        """
        pass

    @abstractmethod
    async def is_continue_till_end(self,
                                   symbol: str,
                                   timeframe: str,
                                   start_time: datetime,
                                   end_time: datetime) -> bool:
        """start_time부터 end_time까지 연속성 확인 (범위 제한)

        find_last_continuous_time과 달리 특정 범위 내에서만 연속성을 확인합니다.

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 연속성 확인 시작점 (포함)
            end_time: 연속성 확인 종료점 (포함) - 필수

        Returns:
            bool: True=완전 연속, False=Gap 존재 또는 데이터 부족

        Note:
            - OverlapAnalyzer의 is_continue_till_end 전용
            - 범위 제한으로 안전하고 명확한 연속성 판단
            - find_last_continuous_time과 명확히 구분된 목적
        """
        pass

    @abstractmethod
    async def has_data_at_time(self, symbol: str, timeframe: str, target_time: datetime) -> bool:
        """특정 시점에 캔들 데이터 존재 여부 확인

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            target_time: 확인할 특정 시점

        Returns:
            bool: 해당 시점에 데이터 존재 여부

        Note:
            - OverlapAnalyzer v5.0의 has_data_in_start용
            - PRIMARY KEY 점검색으로 최고 성능
        """
        pass

    @abstractmethod
    async def find_data_start_in_range(self, symbol: str, timeframe: str,
                                       start_time: datetime, end_time: datetime) -> Optional[datetime]:
        """범위 내 데이터 시작점 찾기

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.')
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            Optional[datetime]: 범위 내 가장 최신 데이터 시점 (없으면 None)

        Note:
            - OverlapAnalyzer v5.0의 중간 겹침 분석용
            - 업비트 서버 내림차순 특성: MAX가 '시작점'
            - PRIMARY KEY 인덱스 활용으로 빠른 성능
        """
        pass

    # === EmptyCandleDetector 빈 캔들 참조 지원 메서드 ===

    @abstractmethod
    async def find_reference_previous_chunks(
        self,
        symbol: str,
        timeframe: str,
        api_start: datetime,
        range_start: datetime,
        range_end: datetime
    ) -> Optional[str]:
        """수집된 청크 범위 내에서 api_start 이후 가장 가까운 참조 시간 찾기 (안전한 범위 제한)

        Args:
            symbol: 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 (예: '1m', '5m')
            api_start: 기준 시점 (이로부터 미래 방향으로 검색)
            range_start: 안전한 검색 범위 시작점 (첫 청크 시작)
            range_end: 안전한 검색 범위 종료점 (현재 청크 끝)

        Returns:
            참조할 수 있는 상태 (문자열) 또는 None (범위 내 데이터 없음)

        Note:
            - EmptyCandleDetector의 빈 캔들 생성 시 참조점 조회용
            - 수집하지 않은 구간을 건너서 잘못된 참조점을 찾는 엣지 케이스 방지
            - 확실히 수집한 청크 범위 내에서만 안전하게 참조점 조회
            - empty_copy_from_utc 체인 자동 처리로 빈 캔들 → 실제 캔들 추적
        """
        pass

    # === 미참조 빈 캔들 참조점 자동 업데이트 메서드들 ===

    @abstractmethod
    async def find_unreferenced_empty_candle_in_range(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[dict]:
        """범위 내 미참조 빈 캔들 중 가장 미래의 레코드 조회

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 검색 범위 시작점
            end_time: 검색 범위 종료점

        Returns:
            Optional[dict]: {
                'candle_date_time_utc': str,
                'empty_copy_from_utc': str  # 'none_xxxxxxxx' 형태
            } 또는 None (미참조 빈 캔들 없음)

        Note:
            - 오버랩 분석 완료 후 후처리용
            - 'none_'으로 시작하는 empty_copy_from_utc 레코드 탐지
            - 범위 기반 처리로 데이터 품질 일괄 향상
        """
        pass

    @abstractmethod
    async def get_record_by_time(
        self,
        symbol: str,
        timeframe: str,
        target_time: datetime
    ) -> Optional[dict]:
        """특정 시간의 레코드 조회 (참조점 업데이트용)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            target_time: 조회할 특정 시점

        Returns:
            Optional[dict]: {
                'candle_date_time_utc': str,
                'empty_copy_from_utc': Optional[str],
                # 기타 필요 필드들...
            } 또는 None (해당 시점 데이터 없음)

        Note:
            - 미참조 빈 캔들의 참조점 결정용
            - 현재 시점과 한 틱 미래 시점 조회에 활용
            - TimeUtils와 연동하여 정확한 시간 계산
        """
        pass

    @abstractmethod
    async def update_empty_copy_reference_by_group(
        self,
        symbol: str,
        timeframe: str,
        old_group_id: str,
        new_reference: str
    ) -> int:
        """특정 그룹의 empty_copy_from_utc 일괄 업데이트

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            old_group_id: 기존 그룹 ID (예: 'none_d1dea30f')
            new_reference: 새로운 참조 (시간 문자열 또는 참조 ID)

        Returns:
            int: 업데이트된 레코드 수

        Note:
            - 미참조 그룹 전체를 새 참조점으로 일괄 변경
            - 트랜잭션으로 데이터 일관성 보장
            - 성능 최적화: 단일 UPDATE 쿼리로 처리
        """
        pass

    # === CandleDataProvider v4.0 새로운 메서드들 ===

    @abstractmethod
    async def ensure_table_exists(self, symbol: str, timeframe: str) -> str:
        """캔들 테이블 생성 (새로운 스키마 적용)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)

        Returns:
            str: 생성된 테이블명

        Note:
            - 업비트 API 호환 스키마 적용
            - PRIMARY KEY (candle_date_time_utc) 사용
            - timeframe_specific_data JSON 컬럼 포함
        """
        pass

    @abstractmethod
    async def save_candle_chunk(self, symbol: str, timeframe: str, candles) -> int:
        """캔들 데이터 청크 저장

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            candles: CandleData 객체 리스트

        Returns:
            int: 저장된 캔들 개수

        Note:
            - 새로운 CandleData 모델 지원
            - INSERT OR IGNORE 방식으로 중복 처리 (중복시 삽입 무시)
            - UTC 시간 PRIMARY KEY + 업비트 데이터 불변성 활용
            - 배치 삽입으로 성능 최적화
        """
        pass

    @abstractmethod
    async def save_raw_api_data(self, symbol: str, timeframe: str, raw_data: List[dict]) -> int:
        """업비트 API 원시 데이터 직접 저장 (성능 최적화)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            raw_data: 업비트 API 원시 응답 데이터 (Dict 리스트)

        Returns:
            int: 저장된 캔들 개수

        Note:
            - Dict → CandleData 변환 생략으로 메모리 절약
            - 배치 INSERT로 고성능 저장
            - 업비트 API 필드 직접 매핑
            - INSERT OR IGNORE로 중복 처리
        """
        pass

    @abstractmethod
    async def get_latest_candle(self, symbol: str, timeframe: str):
        """최신 캔들 데이터 조회

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)

        Returns:
            CandleData: 최신 캔들 객체 또는 None (데이터 없음)

        Note:
            - Application 서비스 레이어에서 캐시 확인용으로 사용
            - PRIMARY KEY 역순 정렬로 최고 성능
            - CandleCache와 연동 예정
        """
        pass

    @abstractmethod
    async def count_candles_in_range(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """지정 범위의 캔들 개수 조회

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            int: 범위 내 캔들 개수

        Note:
            - 데이터 완전성 검증 및 진행률 계산용
            - COUNT 쿼리로 효율적 개수 조회
            - OverlapAnalyzer와 연계하여 데이터 품질 확인
        """
        pass

    @abstractmethod
    async def get_candles_by_range(self, symbol: str, timeframe: str, start_time: datetime, end_time: datetime) -> List:
        """지정 범위의 캔들 데이터 조회 (새로운 CandleData 모델 반환)

        Args:
            symbol: 거래 심볼 (예: 'KRW-BTC')
            timeframe: 타임프레임 ('1m', '5m', '15m', etc.)
            start_time: 조회 시작 시간
            end_time: 조회 종료 시간

        Returns:
            List[CandleData]: 새로운 CandleData 모델 리스트

        Note:
            - PRIMARY KEY 범위 스캔 활용
            - JSON 필드 파싱 포함
            - 시간순 정렬 보장 (ORDER BY 필수)
        """
        pass

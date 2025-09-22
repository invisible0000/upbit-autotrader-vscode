"""
candle_models.py 분할 계획 - 역할별 파일 분리

현재 상황:
- 총 1081줄, 16개 클래스
- 서로 다른 책임들이 하나의 파일에 혼재
- 유지보수 및 가독성 저하

목표:
- 역할별 파일 분리로 단일 책임 원칙 준수
- 각 파일 300-400줄 이하로 관리
- import 의존성 최소화
- 향후 확장성 확보

=== 🔄 분할 계획 ===

📁 1. candle_core_models.py (300줄)
역할: 핵심 도메인 모델
클래스:
- OverlapStatus, ChunkStatus (Enum)
- CandleData (업비트 API 호환 모델)
- CandleDataResponse (최종 응답)

특징:
- 가장 자주 사용되는 핵심 모델
- 외부 의존성 최소
- 안정적인 인터페이스

📁 2. candle_request_models.py (250줄)
역할: 요청/응답 관련 모델
클래스:
- CandleChunk (청크 단위)
- OverlapRequest, OverlapResult (겹침 분석)
- TimeChunk (시간 기반 청크)
- CollectionResult (수집 결과)

특징:
- API 요청과 분석 결과 모델
- OverlapAnalyzer와 밀접한 관계
- 비교적 안정적

📁 3. candle_cache_models.py (200줄)
역할: 캐시 관련 모델
클래스:
- CacheKey, CacheEntry, CacheStats

특징:
- 캐시 시스템 전용
- 완전히 독립적
- 필요시에만 import

📁 4. candle_collection_models.py (400줄)
역할: 수집 프로세스 관리 모델
클래스:
- CollectionState (개선된 버전)
- CollectionPlan
- RequestInfo
- ChunkInfo
- ProcessingStats

특징:
- CandleDataProvider 전용
- 가장 복잡하고 자주 변경됨
- 향후 개선 여지 많음

=== 📋 마이그레이션 순서 ===

1단계: 캐시 모델 분리 (가장 독립적)
2단계: 요청/응답 모델 분리
3단계: 수집 프로세스 모델 분리
4단계: 핵심 모델 정리

=== 🔗 Import 의존성 ===

candle_core_models.py
└── (의존성 없음)

candle_request_models.py
└── candle_core_models (CandleData, OverlapStatus)

candle_cache_models.py
└── candle_core_models (CandleData)

candle_collection_models.py
└── candle_core_models (CandleData)
└── candle_request_models (OverlapResult)

=== ⚡ 즉시 실행 가능한 작업 ===

현재 상황에서 바로 할 수 있는 것:
1. CollectionState v2.0 적용
2. 캐시 모델 분리 (완전 독립적)
3. 불필요한 유틸리티 함수들 정리

=== 🎯 우선순위 ===

High: CollectionState 개선
Medium: 캐시 모델 분리
Low: 전체 파일 분할

이유: CollectionState가 가장 많이 사용되고 문제가 많음
"""

# === 분할 예시: CacheModels 분리 ===

cache_models_content = '''
"""
Candle Cache Models - 캔들 데이터 캐시 관련 모델

분리 이유:
- 캐시 기능은 선택적 기능
- 완전히 독립적인 책임
- 다른 모델들과 의존성 없음
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from .candle_core_models import CandleData


@dataclass
class CacheKey:
    """캐시 키 구조화"""
    symbol: str
    timeframe: str
    start_time: datetime
    count: int

    def to_string(self) -> str:
        """캐시 키를 문자열로 변환"""
        return f"candles_{self.symbol}_{self.timeframe}_{self.start_time.isoformat()}_{self.count}"


@dataclass
class CacheEntry:
    """캐시 엔트리 (데이터 + 메타데이터)"""
    key: CacheKey
    candles: List[CandleData]
    created_at: datetime
    ttl_seconds: int
    data_size_bytes: int

    def is_expired(self, current_time: datetime) -> bool:
        """캐시 만료 여부 확인"""
        elapsed_seconds = (current_time - self.created_at).total_seconds()
        return elapsed_seconds > self.ttl_seconds


@dataclass
class CacheStats:
    """캐시 통계 정보"""
    total_entries: int
    total_memory_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    expired_count: int

    def get_hit_rate(self) -> float:
        """캐시 히트율 계산"""
        total_requests = self.hit_count + self.miss_count
        if total_requests == 0:
            return 0.0
        return self.hit_count / total_requests
'''

print("=== candle_models.py 분할 계획 완료 ===")
print(f"현재: {1081}줄 → 목표: 4개 파일(200~400줄)")
print("우선순위: CollectionState 개선 > 캐시 분리 > 전체 분할")

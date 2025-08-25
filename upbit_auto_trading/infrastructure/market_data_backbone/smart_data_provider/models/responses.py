"""
응답 모델 정의 - Dict 형식 통일 V3.0
Smart Data Provider의 응답 구조를 정의합니다.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime


@dataclass
class DataResponse:
    """
    데이터 응답 - Dict 기반 통일

    external_apis와 smart_routing과 완전히 호환되는 Dict 기반 응답 형식
    모든 데이터는 Dict[str, Any] 형태로 통일하여 일관성 보장
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def get(self, key: Optional[str] = None) -> Any:
        """키별 데이터 반환 또는 전체 Dict 반환"""
        if key:
            return self.data.get(key, {})
        return self.data

    def get_single(self, symbol: str) -> Dict[str, Any]:
        """단일 심볼 데이터 반환"""
        return self.data.get(symbol, {})

    def get_all(self) -> Dict[str, Any]:
        """전체 Dict 데이터 반환"""
        return self.data

    def get_list(self) -> list:
        """리스트 형태 데이터 반환 (캔들, 체결내역 등)"""
        if '_list_data' in self.data:
            return self.data['_list_data']
        elif isinstance(self.data, dict) and len(self.data) == 1:
            # 단일 키의 값이 리스트인 경우
            value = next(iter(self.data.values()))
            if isinstance(value, list):
                return value
        return []

    def keys(self):
        """Dict keys 반환"""
        return self.data.keys()

    def values(self):
        """Dict values 반환"""
        return self.data.values()

    def items(self):
        """Dict items 반환"""
        return self.data.items()

    def __getitem__(self, key: str):
        """Dict 스타일 접근 지원: response['KRW-BTC']"""
        return self.data[key]

    def __contains__(self, key: str):
        """in 연산자 지원: 'KRW-BTC' in response"""
        return key in self.data

    def __bool__(self):
        """boolean 컨텍스트 지원"""
        return self.success

    # 메타데이터 접근자 (하위 호환성)
    @property
    def is_cache_hit(self) -> bool:
        """캐시 히트 여부"""
        return self.metadata.get('cache_hit', False)

    @property
    def response_time_ms(self) -> float:
        """응답 시간 (밀리초)"""
        return self.metadata.get('response_time_ms', 0.0)

    @property
    def data_source(self) -> str:
        """데이터 소스"""
        return self.metadata.get('source', 'unknown')

    @property
    def records_count(self) -> int:
        """레코드 수"""
        return self.metadata.get('records_count', 0)

    @classmethod
    def create_success(cls, data: Union[Dict[str, Any], list],
                       source: str = "unknown",
                       response_time_ms: float = 0.0,
                       cache_hit: bool = False,
                       **extra_metadata) -> 'DataResponse':
        """성공 응답 생성 헬퍼"""
        # 리스트 데이터를 Dict로 래핑
        if isinstance(data, list):
            unified_data = {'_list_data': data}
            records_count = len(data)
        else:
            unified_data = data
            records_count = len(data) if isinstance(data, dict) else 1

        metadata = {
            'source': source,
            'response_time_ms': response_time_ms,
            'cache_hit': cache_hit,
            'records_count': records_count,
            'timestamp': datetime.now().isoformat(),
            **extra_metadata
        }

        return cls(success=True, data=unified_data, metadata=metadata)

    @classmethod
    def create_error(cls, error: str,
                     source: str = "error",
                     response_time_ms: float = 0.0,
                     **extra_metadata) -> 'DataResponse':
        """오류 응답 생성 헬퍼"""
        metadata = {
            'source': source,
            'response_time_ms': response_time_ms,
            'cache_hit': False,
            'records_count': 0,
            'timestamp': datetime.now().isoformat(),
            **extra_metadata
        }

        return cls(success=False, data={}, metadata=metadata, error=error)


# ResponseMetadata는 이제 Dict로 통일
ResponseMetadata = dict

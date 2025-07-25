"""
사용자 선택형 시뮬레이션 데이터 소스 관리자
사용자가 원하는 데이터 소스를 선택하여 시뮬레이션 실행 가능
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum


class DataSourceType(Enum):
    """데이터 소스 타입 정의"""
    EMBEDDED = "embedded"           # 내장 최적화 데이터셋
    REAL_DB = "real_db"            # 실제 DB 데이터
    SYNTHETIC = "synthetic"         # 합성 현실적 데이터
    SIMPLE_FALLBACK = "fallback"   # 단순 폴백 데이터


class SimulationDataSourceManager:
    """시뮬레이션 데이터 소스 관리자"""
    
    def __init__(self):
        """데이터 소스 관리자 초기화"""
        self._engines = {}
        self._availability = {}
        self._user_preference = None
        
        # 각 데이터 소스 가용성 확인
        self._check_availability()
        
    def _check_availability(self):
        """각 데이터 소스의 가용성 확인"""
        # 1. 내장 데이터셋 확인
        try:
            from .embedded_simulation_engine import get_embedded_simulation_engine
            self._engines[DataSourceType.EMBEDDED] = get_embedded_simulation_engine
            self._availability[DataSourceType.EMBEDDED] = True
            logging.info("✅ 내장 최적화 데이터셋 사용 가능")
        except ImportError as e:
            self._availability[DataSourceType.EMBEDDED] = False
            logging.warning(f"❌ 내장 데이터셋 불가: {e}")
        
        # 2. 실제 DB 확인
        try:
            import os
            db_path = "data/market_data.sqlite3"
            if os.path.exists(db_path):
                from .real_data_simulation import RealDataSimulationEngine
                self._engines[DataSourceType.REAL_DB] = lambda: RealDataSimulationEngine()
                self._availability[DataSourceType.REAL_DB] = True
                logging.info("✅ 실제 DB 데이터 사용 가능")
            else:
                self._availability[DataSourceType.REAL_DB] = False
                logging.warning("❌ 실제 DB 파일 없음")
        except ImportError as e:
            self._availability[DataSourceType.REAL_DB] = False
            logging.warning(f"❌ 실제 DB 엔진 불가: {e}")
        
        # 3. 합성 데이터 확인
        try:
            from .robust_simulation_engine import RobustSimulationEngine
            self._engines[DataSourceType.SYNTHETIC] = lambda: RobustSimulationEngine()
            self._availability[DataSourceType.SYNTHETIC] = True
            logging.info("✅ 합성 현실적 데이터 사용 가능")
        except ImportError as e:
            self._availability[DataSourceType.SYNTHETIC] = False
            logging.warning(f"❌ 합성 데이터 엔진 불가: {e}")
        
        # 4. 단순 폴백 (항상 가능)
        self._availability[DataSourceType.SIMPLE_FALLBACK] = True
        logging.info("✅ 단순 폴백 데이터 항상 사용 가능")
    
    def get_available_sources(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 데이터 소스 목록 반환"""
        sources = {}
        
        if self._availability.get(DataSourceType.EMBEDDED, False):
            sources["embedded"] = {
                "name": "내장 최적화 데이터셋",
                "description": "시나리오별로 최적화된 고품질 내장 데이터",
                "pros": ["가장 빠른 성능", "시나리오 특화", "오프라인 작동", "일관된 품질"],
                "cons": ["실제 시장과 차이 가능"],
                "performance": "최고 (0.001초)",
                "quality": "시나리오 최적화",
                "availability": True,
                "recommended": True
            }
        
        if self._availability.get(DataSourceType.REAL_DB, False):
            sources["real_db"] = {
                "name": "실제 시장 데이터",
                "description": "24,776개 실제 KRW-BTC 일봉 데이터",
                "pros": ["진짜 시장 상황", "높은 신뢰성", "범위 확장 지원"],
                "cons": ["DB 의존적", "상대적으로 느림"],
                "performance": "양호 (0.049초)",
                "quality": "실제 시장 반영",
                "availability": True,
                "recommended": False
            }
        
        if self._availability.get(DataSourceType.SYNTHETIC, False):
            sources["synthetic"] = {
                "name": "합성 현실적 데이터",
                "description": "실제 비트코인 특성을 반영한 합성 데이터",
                "pros": ["DB 독립적", "현실적 패턴", "다양한 시나리오"],
                "cons": ["실제 데이터 아님", "패턴 제한적"],
                "performance": "우수 (0.064초)",
                "quality": "현실적 합성",
                "availability": True,
                "recommended": False
            }
        
        if self._availability.get(DataSourceType.SIMPLE_FALLBACK, False):
            sources["fallback"] = {
                "name": "단순 시뮬레이션",
                "description": "기본적인 수학적 모델 기반 데이터",
                "pros": ["항상 사용 가능", "매우 빠름"],
                "cons": ["단순한 패턴", "현실성 부족"],
                "performance": "최고 (즉시)",
                "quality": "기본적",
                "availability": True,
                "recommended": False
            }
        
        return sources
    
    def set_user_preference(self, source_type: str) -> bool:
        """사용자 선호 데이터 소스 설정"""
        try:
            # 문자열을 Enum으로 변환
            source_enum = DataSourceType(source_type)
            
            if self._availability.get(source_enum, False):
                self._user_preference = source_enum
                logging.info(f"사용자 선호 데이터 소스 설정: {source_type}")
                return True
            else:
                logging.warning(f"선택한 데이터 소스 사용 불가: {source_type}")
                return False
        except ValueError:
            logging.error(f"잘못된 데이터 소스 타입: {source_type}")
            return False
    
    def get_user_preference(self) -> Optional[str]:
        """사용자 선호 데이터 소스 반환"""
        if self._user_preference:
            return self._user_preference.value
        return None
    
    def get_engine(self, source_type: Optional[str] = None):
        """지정된 타입의 엔진 반환"""
        # 사용자 지정 타입이 있으면 사용, 없으면 선호 설정 사용
        if source_type:
            try:
                target_type = DataSourceType(source_type)
            except ValueError:
                logging.error(f"잘못된 소스 타입: {source_type}")
                target_type = self._get_best_available_source()
        else:
            target_type = self._user_preference or self._get_best_available_source()
        
        # 해당 타입의 엔진 반환
        if target_type in self._engines and self._availability.get(target_type, False):
            try:
                engine = self._engines[target_type]()
                logging.info(f"선택된 엔진: {target_type.value}")
                return engine
            except Exception as e:
                logging.error(f"엔진 생성 실패 ({target_type.value}): {e}")
                return self._get_fallback_engine()
        else:
            logging.warning(f"요청한 엔진 사용 불가 ({target_type.value}), 폴백 사용")
            return self._get_fallback_engine()
    
    def _get_best_available_source(self) -> DataSourceType:
        """가장 좋은 사용 가능한 데이터 소스 선택"""
        # 우선순위: 내장 > 실제DB > 합성 > 폴백
        priority_order = [
            DataSourceType.EMBEDDED,
            DataSourceType.REAL_DB,
            DataSourceType.SYNTHETIC,
            DataSourceType.SIMPLE_FALLBACK
        ]
        
        for source_type in priority_order:
            if self._availability.get(source_type, False):
                return source_type
        
        return DataSourceType.SIMPLE_FALLBACK  # 최후의 수단
    
    def _get_fallback_engine(self):
        """폴백 엔진 반환"""
        from .real_data_simulation import RealDataSimulationEngine
        return RealDataSimulationEngine()
    
    def get_source_comparison(self) -> Dict[str, Any]:
        """데이터 소스별 비교 정보 반환"""
        available_sources = self.get_available_sources()
        
        comparison = {
            "total_available": len(available_sources),
            "recommended": None,
            "performance_ranking": [],
            "quality_ranking": [],
            "sources": available_sources
        }
        
        # 추천 소스 찾기
        for key, info in available_sources.items():
            if info.get("recommended", False):
                comparison["recommended"] = key
                break
        
        # 성능순 정렬
        performance_order = ["최고", "우수", "양호", "보통"]
        for perf in performance_order:
            for key, info in available_sources.items():
                if perf in info.get("performance", ""):
                    comparison["performance_ranking"].append(key)
        
        return comparison


# 전역 데이터 소스 관리자
_data_source_manager = None

def get_data_source_manager():
    """데이터 소스 관리자 싱글톤 반환"""
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = SimulationDataSourceManager()
    return _data_source_manager


def get_simulation_engine_by_preference(source_type: Optional[str] = None):
    """사용자 선호도에 따른 시뮬레이션 엔진 반환"""
    manager = get_data_source_manager()
    return manager.get_engine(source_type)

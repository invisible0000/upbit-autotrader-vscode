"""
향상된 시뮬레이션 데이터 소스 관리자
시나리오별 고품질 데이터 제공 및 미니차트 최적화
"""

import logging
from typing import Dict, List, Optional, Any
from enum import Enum


class DataSourceType(Enum):
    """데이터 소스 타입 정의"""
    EMBEDDED = "embedded"           # 내장 최적화 데이터셋 (시나리오별)
    REAL_DB = "real_db"            # 실제 DB 데이터 (세그먼테이션)
    SYNTHETIC = "synthetic"         # 합성 현실적 데이터
    SIMPLE_FALLBACK = "fallback"   # 단순 폴백 데이터


class EnhancedSimulationDataSourceManager:
    """향상된 시뮬레이션 데이터 소스 관리자"""
    
    def __init__(self):
        """데이터 소스 관리자 초기화"""
        self._engines = {}
        self._availability = {}
        self._user_preference = None
        
        # 각 데이터 소스 가용성 확인
        self._check_availability()
        
    def _check_availability(self):
        """각 데이터 소스의 가용성 확인"""
        # 1. 내장 최적화 데이터셋 확인
        try:
            from ..engines.embedded_simulation_engine import get_embedded_simulation_engine
            self._engines[DataSourceType.EMBEDDED] = get_embedded_simulation_engine
            self._availability[DataSourceType.EMBEDDED] = True
            logging.info("✅ 내장 최적화 데이터셋 사용 가능 (시나리오별)")
            print("✅✅✅ ENHANCED_DATA_SOURCE_MANAGER: 내장 최적화 데이터셋 사용 가능 - EMBEDDED 등록됨")
        except ImportError as e:
            self._availability[DataSourceType.EMBEDDED] = False
            logging.warning(f"❌ 내장 데이터셋 불가: {e}")
            print(f"❌❌❌ ENHANCED_DATA_SOURCE_MANAGER: 내장 데이터셋 불가: {e}")
        
        # 2. 실제 DB 확인 (시나리오별 세그먼테이션)
        try:
            import os
            # 샘플 데이터셋 경로
            db_path = os.path.join(os.path.dirname(__file__), "..", "components", "data", "sampled_market_data.sqlite3")
            print(f"🔍🔍🔍 ENHANCED_DATA_SOURCE_MANAGER DB 경로 확인: {db_path}")
            print(f"🔍🔍🔍 ENHANCED_DATA_SOURCE_MANAGER DB 파일 존재: {os.path.exists(db_path)}")
            
            if os.path.exists(db_path):
                from ..engines.real_data_simulation import RealDataSimulationEngine
                self._engines[DataSourceType.REAL_DB] = lambda: RealDataSimulationEngine()
                self._availability[DataSourceType.REAL_DB] = True
                logging.info("✅ 실제 DB 데이터 사용 가능 (시나리오별 세그먼테이션)")
                print("✅✅✅ ENHANCED_DATA_SOURCE_MANAGER: 실제 DB 데이터 사용 가능 - REAL_DB 등록됨")
            else:
                self._availability[DataSourceType.REAL_DB] = False
                logging.warning("❌ 실제 DB 파일 없음")
                print("❌❌❌ ENHANCED_DATA_SOURCE_MANAGER: 실제 DB 파일 없음")
        except ImportError as e:
            self._availability[DataSourceType.REAL_DB] = False
            logging.warning(f"❌ 실제 DB 엔진 불가: {e}")
        
        # 3. 합성 현실적 데이터 확인
        try:
            from ..engines.robust_simulation_engine import RobustSimulationEngine
            self._engines[DataSourceType.SYNTHETIC] = lambda: RobustSimulationEngine()
            self._availability[DataSourceType.SYNTHETIC] = True
            logging.info("✅ 합성 현실적 데이터 사용 가능")
            print("✅✅✅ ENHANCED_DATA_SOURCE_MANAGER: 합성 현실적 데이터 사용 가능 - SYNTHETIC 등록됨")
        except ImportError as e:
            self._availability[DataSourceType.SYNTHETIC] = False
            logging.warning(f"❌ 합성 데이터 엔진 불가: {e}")
            print(f"❌❌❌ ENHANCED_DATA_SOURCE_MANAGER: 합성 데이터 엔진 불가: {e}")
        
        # 4. 단순 폴백 (항상 가능)
        self._availability[DataSourceType.SIMPLE_FALLBACK] = True
        print("✅ 단순 폴백 데이터 항상 사용 가능 - SIMPLE_FALLBACK 등록됨")
        
        print(f"🔍 최종 데이터 소스 가용성: {self._availability}")
        print(f"🔍 사용 가능한 데이터 소스 개수: {sum(self._availability.values())}/{len(self._availability)}")
        
    def get_available_sources(self) -> List[str]:
        """사용 가능한 데이터 소스 목록 반환"""
        available = []
        print(f"🔍 get_available_sources 호출됨 - 가용성: {self._availability}")
        
        for source_type, available_flag in self._availability.items():
            if available_flag:
                available.append(source_type.value)
                print(f"📝 {source_type.value} 소스 추가됨")
        
        print(f"🔍 반환할 소스 목록: {available} (총 {len(available)}개)")
        return available
    
    def set_user_preference(self, source_type: str):
        """사용자 선호 데이터 소스 설정"""
        try:
            source_enum = DataSourceType(source_type)
            if self._availability.get(source_enum, False):
                self._user_preference = source_enum
                logging.info(f"사용자 선호 데이터 소스 설정: {source_type}")
                print(f"🎯 사용자 선호 데이터 소스 설정: {source_type}")
            else:
                logging.warning(f"사용할 수 없는 데이터 소스: {source_type}")
        except ValueError:
            logging.error(f"잘못된 데이터 소스 타입: {source_type}")
    
    def get_engine(self, source_type: str = None):
        """지정된 타입의 시뮬레이션 엔진 반환"""
        if source_type is None:
            source_type = self._user_preference or DataSourceType.EMBEDDED
        
        if isinstance(source_type, str):
            try:
                source_type = DataSourceType(source_type)
            except ValueError:
                logging.error(f"잘못된 데이터 소스 타입: {source_type}")
                source_type = DataSourceType.SIMPLE_FALLBACK
        
        if source_type in self._engines and self._availability.get(source_type, False):
            engine_factory = self._engines[source_type]
            if callable(engine_factory):
                return engine_factory()
            else:
                return engine_factory
        
        # 폴백: 사용 가능한 첫 번째 엔진
        for fallback_type, available in self._availability.items():
            if available and fallback_type in self._engines:
                logging.warning(f"폴백 엔진 사용: {fallback_type.value}")
                engine_factory = self._engines[fallback_type]
                if callable(engine_factory):
                    return engine_factory()
                else:
                    return engine_factory
        
        # 최후 폴백
        logging.error("사용 가능한 시뮬레이션 엔진이 없습니다")
        return None
    
    def get_scenario_data(self, scenario: str, source_type: str = None, length: int = 100) -> Dict[str, Any]:
        """시나리오별 데이터 반환 (미니차트 최적화)"""
        engine = self.get_engine(source_type)
        
        if engine is None:
            return self._generate_fallback_data(scenario, length)
        
        try:
            # 엔진별 시나리오 데이터 로딩
            if hasattr(engine, 'get_scenario_data'):
                # 내장 최적화 엔진 (시나리오별 특화)
                return engine.get_scenario_data(scenario, length)
            elif hasattr(engine, 'load_scenario_data'):
                # 실제 DB 엔진 (시나리오별 세그먼테이션)
                df = engine.load_scenario_data(scenario, length)
                if df is not None and not df.empty:
                    return {
                        'current_value': float(df['close'].iloc[-1]),
                        'price_data': df['close'].tolist(),
                        'scenario': scenario,
                        'data_source': 'real_db_segmented',
                        'period': f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
                        'base_value': float(df['close'].iloc[0]),
                        'change_percent': float((df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100)
                    }
            else:
                # 기본 데이터 로딩 후 시나리오 적용
                df = engine.load_market_data(length)
                if df is not None and not df.empty:
                    return self._apply_scenario_to_data(df, scenario)
        
        except Exception as e:
            logging.error(f"시나리오 데이터 로딩 실패: {e}")
        
        return self._generate_fallback_data(scenario, length)
    
    def _apply_scenario_to_data(self, df, scenario: str) -> Dict[str, Any]:
        """기본 데이터에 시나리오 패턴 적용"""
        try:
            # 시나리오별 데이터 변형
            price_data = df['close'].copy()
            
            if scenario == "상승 추세":
                trend = 1 + (range(len(price_data)) / len(price_data)) * 0.3
                price_data = price_data * trend
            elif scenario == "하락 추세":
                trend = 1 - (range(len(price_data)) / len(price_data)) * 0.2
                price_data = price_data * trend
            elif scenario == "횡보":
                # 평균 값 중심으로 수렴
                mean_price = price_data.mean()
                price_data = price_data * 0.7 + mean_price * 0.3
            
            return {
                'current_value': float(price_data.iloc[-1]),
                'price_data': price_data.tolist(),
                'scenario': scenario,
                'data_source': 'modified_real_data',
                'period': f"{df.index[0].strftime('%Y-%m-%d')} ~ {df.index[-1].strftime('%Y-%m-%d')}",
                'base_value': float(price_data.iloc[0]),
                'change_percent': float((price_data.iloc[-1] / price_data.iloc[0] - 1) * 100)
            }
        except Exception as e:
            logging.error(f"시나리오 패턴 적용 실패: {e}")
            return self._generate_fallback_data(scenario, len(df))
    
    def _generate_fallback_data(self, scenario: str, length: int) -> Dict[str, Any]:
        """폴백 시나리오 데이터 생성"""
        import numpy as np
        
        base_value = 50000000
        
        if scenario == "상승 추세":
            trend = np.linspace(0, base_value * 0.2, length)
        elif scenario == "하락 추세":
            trend = np.linspace(0, -base_value * 0.15, length)
        elif scenario == "급등":
            trend = np.concatenate([
                np.zeros(length//3),
                np.linspace(0, base_value * 0.4, length//3),
                np.full(length - 2*(length//3), base_value * 0.4)
            ])
        elif scenario == "급락":
            trend = np.concatenate([
                np.zeros(length//2),
                np.linspace(0, -base_value * 0.3, length//2)
            ])
        else:  # 횡보
            trend = np.sin(np.linspace(0, 4*np.pi, length)) * base_value * 0.05
        
        noise = np.random.randn(length) * base_value * 0.02
        price_data = base_value + trend + noise
        price_data = np.maximum(price_data, base_value * 0.1)
        
        return {
            'current_value': float(price_data[-1]),
            'price_data': price_data.tolist(),
            'scenario': scenario,
            'data_source': 'fallback_scenario',
            'period': 'generated_data',
            'base_value': base_value,
            'change_percent': (price_data[-1] / price_data[0] - 1) * 100
        }


# 전역 인스턴스
_enhanced_manager = None

def get_enhanced_data_source_manager():
    """향상된 데이터 소스 관리자 싱글톤 반환"""
    global _enhanced_manager
    if _enhanced_manager is None:
        _enhanced_manager = EnhancedSimulationDataSourceManager()
    return _enhanced_manager

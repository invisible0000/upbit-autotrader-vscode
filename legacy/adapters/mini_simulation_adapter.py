"""
TriggerBuilder 미니 시뮬레이션 어댑터

TriggerBuilder와 공통 미니시뮬레이션 시스템을 연결하는 어댑터 패턴 구현
기존 TriggerBuilder 특화 기능을 유지하면서 새로운 공통 컴포넌트 활용
"""

from typing import Dict, Any, Optional, List
import logging

# 공통 미니 시뮬레이션 시스템 import
try:
    from ...components.mini_simulation import (
        SimulationDataSourceManager
    )
    from ...components.mini_simulation.engines import (
        BaseSimulationEngine,
        get_embedded_simulation_engine,
        get_real_data_simulation_engine,
        get_robust_simulation_engine
    )
    COMMON_SYSTEM_AVAILABLE = True
    print("✅ 공통 미니 시뮬레이션 시스템 연결 성공")
except ImportError as e:
    # 폴백: 기존 시스템 사용
    COMMON_SYSTEM_AVAILABLE = False
    print(f"⚠️ 공통 시스템 연결 실패, 기존 시스템 사용: {e}")

# 기존 TriggerBuilder 컴포넌트들
from ..shared.simulation_engines import (
    get_embedded_simulation_engine as legacy_get_embedded,
    get_real_data_simulation_engine as legacy_get_real,
    get_robust_simulation_engine as legacy_get_robust
)


class TriggerBuilderMiniSimulationAdapter:
    """TriggerBuilder와 공통 미니시뮬레이션 시스템을 연결하는 어댑터"""
    
    def __init__(self):
        self.use_common_system = COMMON_SYSTEM_AVAILABLE
        self.data_source_manager = None
        self.current_engine = None
        
        if self.use_common_system:
            try:
                self.data_source_manager = SimulationDataSourceManager()
                logging.info("✅ 공통 데이터 소스 매니저 초기화")
            except Exception as e:
                logging.warning(f"⚠️ 공통 데이터 소스 매니저 초기화 실패, 폴백 사용: {e}")
                self.use_common_system = False
        
        if not self.use_common_system:
            logging.info("📦 기존 TriggerBuilder 시뮬레이션 시스템 사용")
    
    def get_simulation_engine(self, source_type: str = "embedded") -> BaseSimulationEngine:
        """
        데이터 소스 타입에 따른 시뮬레이션 엔진 반환
        
        Args:
            source_type: 데이터 소스 타입 ("embedded", "real_db", "synthetic", "fallback")
            
        Returns:
            BaseSimulationEngine: 시뮬레이션 엔진 인스턴스
        """
        if self.use_common_system:
            try:
                # 공통 시스템 사용
                if source_type == "embedded":
                    engine = get_embedded_simulation_engine()
                elif source_type == "real_db":
                    engine = get_real_data_simulation_engine()
                elif source_type in ["synthetic", "robust"]:
                    engine = get_robust_simulation_engine()
                else:  # fallback
                    engine = get_embedded_simulation_engine()
                
                self.current_engine = engine
                logging.info(f"✅ 공통 시스템에서 {source_type} 엔진 반환")
                return engine
                
            except Exception as e:
                logging.warning(f"⚠️ 공통 시스템 엔진 생성 실패, 레거시 사용: {e}")
                # 폴백: 기존 시스템
                return self._get_legacy_engine(source_type)
        else:
            # 기존 시스템 사용
            return self._get_legacy_engine(source_type)
    
    def _get_legacy_engine(self, source_type: str) -> BaseSimulationEngine:
        """기존 TriggerBuilder 엔진 반환 (폴백)"""
        if source_type == "embedded":
            engine = legacy_get_embedded()
        elif source_type == "real_db":
            engine = legacy_get_real()
        elif source_type in ["synthetic", "robust"]:
            engine = legacy_get_robust()
        else:  # fallback
            engine = legacy_get_embedded()
        
        self.current_engine = engine
        logging.info(f"📦 레거시 시스템에서 {source_type} 엔진 반환")
        return engine
    
    def run_trigger_simulation(self, trigger_data: Dict[str, Any], scenario: str,
                               source_type: str = "embedded") -> Dict[str, Any]:
        """
        트리거 시뮬레이션 실행 (TriggerBuilder 특화)
        
        Args:
            trigger_data: 트리거 설정 데이터
            scenario: 시뮬레이션 시나리오
            source_type: 데이터 소스 타입
            
        Returns:
            Dict: 시뮬레이션 결과
        """
        try:
            # 엔진 선택
            engine = self.get_simulation_engine(source_type)
            
            # 시장 데이터 로드
            market_data = engine.load_market_data(limit=100)
            if market_data is None or market_data.empty:
                return {
                    'success': False,
                    'error': '시장 데이터 로드 실패',
                    'engine_type': engine.name if hasattr(engine, 'name') else 'Unknown'
                }
            
            # 기술적 지표 계산
            market_data = engine.calculate_technical_indicators(market_data)
            
            # TriggerBuilder 특화 처리
            result = self._process_trigger_specific_logic(trigger_data, market_data, scenario)
            
            # 성공 결과 반환
            result.update({
                'success': True,
                'engine_type': engine.name if hasattr(engine, 'name') else 'Unknown',
                'data_source': source_type,
                'scenario': scenario,
                'data_points': len(market_data)
            })
            
            logging.info(f"✅ 트리거 시뮬레이션 완료: {scenario} ({source_type})")
            return result
            
        except Exception as e:
            logging.error(f"❌ 트리거 시뮬레이션 실패: {e}")
            return {
                'success': False,
                'error': str(e),
                'scenario': scenario,
                'data_source': source_type
            }
    
    def _process_trigger_specific_logic(self, trigger_data: Dict[str, Any], 
                                      market_data, scenario: str) -> Dict[str, Any]:
        """TriggerBuilder 특화 로직 처리"""
        # 현재는 기본 구현만 제공
        # 향후 TriggerBuilder의 특화 로직들을 여기에 구현
        
        # 기본 결과 구조
        return {
            'trigger_count': 0,
            'trigger_points': [],
            'price_data': market_data['close'].tolist() if 'close' in market_data.columns else [],
            'timestamps': market_data.index.tolist() if hasattr(market_data.index, 'tolist') else []
        }
    
    def get_available_data_sources(self) -> List[str]:
        """사용 가능한 데이터 소스 목록 반환"""
        if self.use_common_system and self.data_source_manager:
            try:
                sources = self.data_source_manager.get_available_sources()
                return [source.value for source in sources]
            except Exception as e:
                logging.warning(f"⚠️ 공통 시스템에서 데이터 소스 목록 가져오기 실패: {e}")
        
        # 기본 데이터 소스 목록
        return ["embedded", "real_db", "synthetic", "fallback"]
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """어댑터 상태 정보 반환"""
        return {
            'using_common_system': self.use_common_system,
            'current_engine': self.current_engine.name if self.current_engine and hasattr(self.current_engine, 'name') else None,
            'available_sources': self.get_available_data_sources(),
            'adapter_version': '1.0.0'
        }


# 싱글톤 인스턴스
_adapter_instance: Optional[TriggerBuilderMiniSimulationAdapter] = None


def get_trigger_builder_adapter() -> TriggerBuilderMiniSimulationAdapter:
    """TriggerBuilder 어댑터 싱글톤 인스턴스 반환"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = TriggerBuilderMiniSimulationAdapter()
    return _adapter_instance


def reset_adapter():
    """어댑터 인스턴스 리셋 (테스트용)"""
    global _adapter_instance
    _adapter_instance = None
    logging.info("🔄 TriggerBuilder 어댑터 리셋")

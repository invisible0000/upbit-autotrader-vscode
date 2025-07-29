"""
미니 시뮬레이션 통합 서비스

전략 메이커, 트리거 빌더 등에서 공통으로 사용할 수 있는
미니차트 시뮬레이션 서비스를 제공합니다.
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd

from ..engines.factory import (
    get_simulation_engine, 
    DataSourceType
)
from .data_source_manager import SimulationDataSourceManager


class MiniSimulationService:
    """미니차트 시뮬레이션 통합 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        self.data_source_manager = SimulationDataSourceManager()
        self.current_scenario = None
        self.current_data_source = DataSourceType.AUTO
        
        # 지원 시나리오 목록
        self.available_scenarios = [
            'bull_market',    # 상승 추세
            'bear_market',    # 하락 추세  
            'surge',          # 급등
            'crash',          # 급락
            'sideways',       # 횡보
            'ma_cross'        # MA 크로스
        ]
        
        print("🔗 MiniSimulationService 초기화 완료")
    
    def get_available_scenarios(self) -> List[str]:
        """사용 가능한 시나리오 목록 반환"""
        return self.available_scenarios.copy()
    
    def get_data_sources(self) -> List[str]:
        """사용 가능한 데이터 소스 목록 반환"""
        return [source.value for source in DataSourceType]
    
    def run_simulation(self, scenario: str, data_source: str = 'auto') -> Dict[str, Any]:
        """
        시나리오 시뮬레이션 실행
        
        Args:
            scenario: 시뮬레이션 시나리오 ('bull_market', 'bear_market' 등)
            data_source: 데이터 소스 ('auto', 'embedded', 'real_db' 등)
        
        Returns:
            시뮬레이션 결과 딕셔너리
        """
        try:
            # 데이터 소스 타입 변환
            if data_source == 'auto':
                source_type = DataSourceType.AUTO
            elif data_source == 'embedded':
                source_type = DataSourceType.EMBEDDED
            elif data_source == 'real_db':
                source_type = DataSourceType.REAL_DB
            elif data_source == 'synthetic':
                source_type = DataSourceType.SYNTHETIC
            else:
                source_type = DataSourceType.AUTO
            
            # 시뮬레이션 엔진 가져오기
            engine = get_simulation_engine(source_type)
            
            # 시나리오 데이터 생성
            data = engine.get_scenario_data(scenario)
            
            # 차트용 데이터 포맷팅
            chart_data = self._format_chart_data(data)
            
            # 결과 구성
            result = {
                'scenario': scenario,
                'data_source': data_source,
                'price_data': chart_data,
                'timestamp': datetime.now().isoformat(),
                'success': True
            }
            
            self.current_scenario = scenario
            self.current_data_source = source_type
            
            print(f"✅ 시뮬레이션 완료: {scenario} (source: {data_source})")
            return result
            
        except Exception as e:
            print(f"❌ 시뮬레이션 실패: {e}")
            return {
                'scenario': scenario,
                'data_source': data_source,
                'price_data': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
    
    def run_strategy_simulation(self, strategy_config: Dict[str, Any], scenario: str = 'bull_market') -> Dict[str, Any]:
        """
        전략 기반 시뮬레이션 실행 (StrategyMaker 전용)
        
        Args:
            strategy_config: 전략 설정 (진입/청산 조건 등)
            scenario: 시뮬레이션 시나리오
        
        Returns:
            전략 시뮬레이션 결과
        """
        try:
            # 기본 시뮬레이션 실행
            sim_result = self.run_simulation(scenario)
            
            if not sim_result['success']:
                return sim_result
            
            # 전략 적용 (간단한 버전)
            strategy_points = self._apply_strategy_logic(
                sim_result['price_data'], 
                strategy_config
            )
            
            # 결과에 전략 정보 추가
            sim_result.update({
                'strategy_config': strategy_config,
                'strategy_points': strategy_points,
                'entry_points': strategy_points.get('entries', []),
                'exit_points': strategy_points.get('exits', [])
            })
            
            print(f"✅ 전략 시뮬레이션 완료: {len(strategy_points.get('entries', []))}개 진입점")
            return sim_result
            
        except Exception as e:
            print(f"❌ 전략 시뮬레이션 실패: {e}")
            return {
                'scenario': scenario,
                'strategy_config': strategy_config,
                'error': str(e),
                'success': False
            }
    
    def _format_chart_data(self, raw_data: Any) -> List[Dict]:
        """원시 데이터를 차트용 포맷으로 변환"""
        try:
            chart_data = []
            
            if isinstance(raw_data, pd.DataFrame):
                # DataFrame인 경우
                for idx, row in raw_data.iterrows():
                    point = {
                        'timestamp': idx if hasattr(idx, 'isoformat') else str(idx),
                        'price': float(row.get('close', row.get('price', 0))),
                        'volume': float(row.get('volume', 0))
                    }
                    chart_data.append(point)
            
            elif isinstance(raw_data, list):
                # 리스트인 경우
                for i, item in enumerate(raw_data):
                    if isinstance(item, dict):
                        chart_data.append(item)
                    else:
                        chart_data.append({
                            'timestamp': i,
                            'price': float(item),
                            'volume': 1000
                        })
            
            else:
                # 기타 타입인 경우 기본값
                chart_data = [
                    {'timestamp': 0, 'price': 50000, 'volume': 1000}
                ]
            
            return chart_data
            
        except Exception as e:
            print(f"⚠️ 차트 데이터 포맷팅 실패: {e}")
            return [
                {'timestamp': 0, 'price': 50000, 'volume': 1000}
            ]
    
    def _apply_strategy_logic(self, price_data: List[Dict], strategy_config: Dict) -> Dict[str, List]:
        """
        전략 로직 적용 (간단한 버전)
        
        실제 구현에서는 더 복잡한 조건 분석이 필요합니다.
        """
        try:
            entries = []
            exits = []
            
            # 진입 조건 간단 체크
            entry_conditions = strategy_config.get('entry_conditions', [])
            if entry_conditions:
                # 가격 상승 시 진입 (예시)
                for i in range(1, len(price_data)):
                    prev_price = price_data[i-1]['price']
                    curr_price = price_data[i]['price']
                    
                    if curr_price > prev_price * 1.02:  # 2% 상승 시
                        entries.append({
                            'timestamp': price_data[i]['timestamp'],
                            'price': curr_price,
                            'reason': '2% 상승 진입'
                        })
            
            # 청산 조건 간단 체크
            exit_conditions = strategy_config.get('exit_conditions', [])
            if exit_conditions and entries:
                # 진입 후 일정 시간 후 청산 (예시)
                for entry in entries:
                    entry_idx = next(
                        (i for i, p in enumerate(price_data) 
                         if p['timestamp'] == entry['timestamp']), 
                        None
                    )
                    
                    if entry_idx and entry_idx + 5 < len(price_data):
                        exit_point = price_data[entry_idx + 5]
                        exits.append({
                            'timestamp': exit_point['timestamp'],
                            'price': exit_point['price'],
                            'reason': '시간 기반 청산'
                        })
            
            return {
                'entries': entries,
                'exits': exits
            }
            
        except Exception as e:
            print(f"⚠️ 전략 로직 적용 실패: {e}")
            return {'entries': [], 'exits': []}
    
    def get_current_state(self) -> Dict[str, Any]:
        """현재 시뮬레이션 상태 반환"""
        return {
            'current_scenario': self.current_scenario,
            'current_data_source': self.current_data_source.value if self.current_data_source else None,
            'available_scenarios': self.available_scenarios,
            'available_data_sources': self.get_data_sources()
        }

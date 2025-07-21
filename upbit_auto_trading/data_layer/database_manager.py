#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
데이터베이스 초기화 및 마이그레이션 스크립트

전략 조합 및 백테스트 관련 테이블을 생성하고 초기 데이터를 삽입합니다.
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 프로젝트 루트 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from upbit_auto_trading.data_layer.strategy_models import (
    Base, StrategyDefinition, StrategyCombination, StrategyConfig,
    CombinationManagementStrategy, BacktestResult, TradeLog, PositionLog,
    OptimizationJob, OptimizationResult, LiveTradingSession, LiveTrade
)


class DatabaseManager:
    """데이터베이스 관리 클래스"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # 기본 SQLite 데이터베이스 경로
            db_path = os.path.join(project_root, 'data', 'strategy_trading.sqlite3')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            database_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """모든 테이블 생성"""
        print("📊 데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=self.engine)
        print("✅ 테이블 생성 완료")
        
    def drop_tables(self):
        """모든 테이블 삭제"""
        print("🗑️ 기존 테이블 삭제 중...")
        Base.metadata.drop_all(bind=self.engine)
        print("✅ 테이블 삭제 완료")
        
    def reset_database(self):
        """데이터베이스 완전 초기화"""
        self.drop_tables()
        self.create_tables()
        
    def get_session(self):
        """데이터베이스 세션 반환"""
        return self.SessionLocal()
        
    def initialize_strategy_definitions(self):
        """기본 전략 정의 데이터 삽입"""
        print("🧬 기본 전략 정의 데이터 초기화 중...")
        
        session = self.get_session()
        try:
            # 진입 전략 정의
            entry_strategies = [
                {
                    'id': 'rsi_entry',
                    'name': 'RSI 과매수/과매도',
                    'description': 'RSI 지표를 이용한 과매수/과매도 구간 진입',
                    'strategy_type': 'entry',
                    'class_name': 'RSIEntry',
                    'default_parameters': {
                        'rsi_period': 14,
                        'oversold': 30,
                        'overbought': 70
                    },
                    'parameter_schema': {
                        'rsi_period': {'type': 'int', 'min': 5, 'max': 30},
                        'oversold': {'type': 'int', 'min': 10, 'max': 40},
                        'overbought': {'type': 'int', 'min': 60, 'max': 90}
                    }
                },
                {
                    'id': 'ma_cross_entry',
                    'name': '이동평균선 크로스',
                    'description': '단기/장기 이동평균선 교차 신호',
                    'strategy_type': 'entry',
                    'class_name': 'MovingAverageCrossEntry',
                    'default_parameters': {
                        'short_window': 20,
                        'long_window': 50
                    },
                    'parameter_schema': {
                        'short_window': {'type': 'int', 'min': 5, 'max': 50},
                        'long_window': {'type': 'int', 'min': 20, 'max': 200}
                    }
                },
                {
                    'id': 'bollinger_entry',
                    'name': '볼린저 밴드',
                    'description': '볼린저 밴드 돌파 및 반등 신호',
                    'strategy_type': 'entry',
                    'class_name': 'BollingerBandsEntry',
                    'default_parameters': {
                        'window': 20,
                        'num_std': 2.0
                    },
                    'parameter_schema': {
                        'window': {'type': 'int', 'min': 10, 'max': 50},
                        'num_std': {'type': 'float', 'min': 1.0, 'max': 3.0}
                    }
                },
                {
                    'id': 'macd_entry',
                    'name': 'MACD',
                    'description': 'MACD 신호선 교차 및 다이버전스',
                    'strategy_type': 'entry',
                    'class_name': 'MACDEntry',
                    'default_parameters': {
                        'fast_period': 12,
                        'slow_period': 26,
                        'signal_period': 9
                    },
                    'parameter_schema': {
                        'fast_period': {'type': 'int', 'min': 5, 'max': 20},
                        'slow_period': {'type': 'int', 'min': 15, 'max': 40},
                        'signal_period': {'type': 'int', 'min': 5, 'max': 15}
                    }
                },
                {
                    'id': 'volatility_entry',
                    'name': '변동성 돌파',
                    'description': '변동성 기반 가격 돌파 신호',
                    'strategy_type': 'entry',
                    'class_name': 'VolatilityBreakoutEntry',
                    'default_parameters': {
                        'lookback_period': 20,
                        'volatility_multiplier': 1.5
                    },
                    'parameter_schema': {
                        'lookback_period': {'type': 'int', 'min': 10, 'max': 50},
                        'volatility_multiplier': {'type': 'float', 'min': 1.0, 'max': 3.0}
                    }
                },
                {
                    'id': 'stochastic_entry',
                    'name': '스토캐스틱',
                    'description': '스토캐스틱 과매수/과매도 신호',
                    'strategy_type': 'entry',
                    'class_name': 'StochasticEntry',
                    'default_parameters': {
                        'k_period': 14,
                        'd_period': 3,
                        'oversold': 20,
                        'overbought': 80
                    },
                    'parameter_schema': {
                        'k_period': {'type': 'int', 'min': 5, 'max': 25},
                        'd_period': {'type': 'int', 'min': 1, 'max': 10},
                        'oversold': {'type': 'int', 'min': 10, 'max': 30},
                        'overbought': {'type': 'int', 'min': 70, 'max': 90}
                    }
                }
            ]
            
            # 관리 전략 정의
            management_strategies = [
                {
                    'id': 'averaging_down',
                    'name': '물타기',
                    'description': '하락 시 추가 매수를 통한 평균단가 하향',
                    'strategy_type': 'management',
                    'class_name': 'AveragingDownManagement',
                    'default_parameters': {
                        'drop_threshold': -0.05,  # 5% 하락 시
                        'max_additions': 3,
                        'addition_ratio': 0.5
                    },
                    'parameter_schema': {
                        'drop_threshold': {'type': 'float', 'min': -0.20, 'max': -0.02},
                        'max_additions': {'type': 'int', 'min': 1, 'max': 5},
                        'addition_ratio': {'type': 'float', 'min': 0.2, 'max': 1.0}
                    }
                },
                {
                    'id': 'pyramiding',
                    'name': '불타기',
                    'description': '상승 시 추가 매수를 통한 수익 극대화',
                    'strategy_type': 'management',
                    'class_name': 'PyramidingManagement',
                    'default_parameters': {
                        'profit_threshold': 0.03,  # 3% 상승 시
                        'max_additions': 2,
                        'addition_ratio': 0.3
                    },
                    'parameter_schema': {
                        'profit_threshold': {'type': 'float', 'min': 0.01, 'max': 0.10},
                        'max_additions': {'type': 'int', 'min': 1, 'max': 3},
                        'addition_ratio': {'type': 'float', 'min': 0.1, 'max': 0.5}
                    }
                },
                {
                    'id': 'trailing_stop',
                    'name': '트레일링 스탑',
                    'description': '수익 구간에서 동적 손절선 관리',
                    'strategy_type': 'management',
                    'class_name': 'TrailingStopManagement',
                    'default_parameters': {
                        'activation_profit': 0.02,  # 2% 수익 시 활성화
                        'trail_percent': 0.01       # 1% 트레일링
                    },
                    'parameter_schema': {
                        'activation_profit': {'type': 'float', 'min': 0.01, 'max': 0.05},
                        'trail_percent': {'type': 'float', 'min': 0.005, 'max': 0.03}
                    }
                },
                {
                    'id': 'fixed_target',
                    'name': '고정 목표가',
                    'description': '사전 설정된 목표 수익률 달성 시 매도',
                    'strategy_type': 'management',
                    'class_name': 'FixedTargetManagement',
                    'default_parameters': {
                        'target_profit': 0.10,  # 10% 목표 수익
                        'partial_exit': False
                    },
                    'parameter_schema': {
                        'target_profit': {'type': 'float', 'min': 0.02, 'max': 0.30},
                        'partial_exit': {'type': 'bool'}
                    }
                },
                {
                    'id': 'partial_exit',
                    'name': '분할 매도',
                    'description': '단계적 수익 실현 전략',
                    'strategy_type': 'management',
                    'class_name': 'PartialExitManagement',
                    'default_parameters': {
                        'exit_levels': [0.05, 0.10, 0.15],  # 5%, 10%, 15%
                        'exit_ratios': [0.3, 0.3, 0.4]       # 30%, 30%, 40%
                    },
                    'parameter_schema': {
                        'exit_levels': {'type': 'list', 'item_type': 'float', 'min_items': 1, 'max_items': 5},
                        'exit_ratios': {'type': 'list', 'item_type': 'float', 'min_items': 1, 'max_items': 5}
                    }
                },
                {
                    'id': 'time_based',
                    'name': '시간 기반 청산',
                    'description': '최대 보유 시간 기반 강제 청산',
                    'strategy_type': 'management',
                    'class_name': 'TimeBasedExitManagement',
                    'default_parameters': {
                        'max_holding_hours': 48,    # 48시간 최대 보유
                        'profit_threshold': 0.01    # 1% 수익 시에만 시간 청산
                    },
                    'parameter_schema': {
                        'max_holding_hours': {'type': 'int', 'min': 1, 'max': 168},  # 최대 1주일
                        'profit_threshold': {'type': 'float', 'min': -0.05, 'max': 0.10}
                    }
                }
            ]
            
            # 전략 정의 삽입
            all_strategies = entry_strategies + management_strategies
            for strategy_data in all_strategies:
                existing = session.query(StrategyDefinition).filter_by(id=strategy_data['id']).first()
                if not existing:
                    strategy = StrategyDefinition(**strategy_data)
                    session.add(strategy)
                    print(f"   ✅ {strategy_data['name']} 전략 정의 추가")
                else:
                    print(f"   ⏭️ {strategy_data['name']} 전략 정의 이미 존재")
            
            session.commit()
            print("✅ 전략 정의 초기화 완료")
            
        except Exception as e:
            session.rollback()
            print(f"❌ 전략 정의 초기화 실패: {e}")
            raise
        finally:
            session.close()
    
    def create_sample_strategy_combinations(self):
        """샘플 전략 조합 생성"""
        print("🎯 샘플 전략 조합 생성 중...")
        
        session = self.get_session()
        try:
            # 먼저 전략 설정들 생성
            sample_configs = [
                {
                    'config_id': 'rsi_config_1',
                    'strategy_definition_id': 'rsi_entry',
                    'strategy_name': 'RSI 과매수/과매도 (기본)',
                    'parameters': {'rsi_period': 14, 'oversold': 30, 'overbought': 70}
                },
                {
                    'config_id': 'rsi_config_2',
                    'strategy_definition_id': 'rsi_entry',
                    'strategy_name': 'RSI 과매수/과매도 (민감)',
                    'parameters': {'rsi_period': 12, 'oversold': 25, 'overbought': 75}
                },
                {
                    'config_id': 'ma_config_1',
                    'strategy_definition_id': 'ma_cross_entry',
                    'strategy_name': '이동평균 크로스 (20/50)',
                    'parameters': {'short_window': 20, 'long_window': 50}
                },
                {
                    'config_id': 'averaging_config_1',
                    'strategy_definition_id': 'averaging_down',
                    'strategy_name': '물타기 (보수적)',
                    'parameters': {'drop_threshold': -0.05, 'max_additions': 2, 'addition_ratio': 0.5}
                },
                {
                    'config_id': 'trailing_config_1',
                    'strategy_definition_id': 'trailing_stop',
                    'strategy_name': '트레일링 스탑 (기본)',
                    'parameters': {'activation_profit': 0.02, 'trail_percent': 0.01}
                },
                {
                    'config_id': 'pyramiding_config_1',
                    'strategy_definition_id': 'pyramiding',
                    'strategy_name': '불타기 (적극적)',
                    'parameters': {'profit_threshold': 0.03, 'max_additions': 2, 'addition_ratio': 0.3}
                }
            ]
            
            # 전략 설정 삽입
            for config_data in sample_configs:
                existing = session.query(StrategyConfig).filter_by(config_id=config_data['config_id']).first()
                if not existing:
                    config = StrategyConfig(**config_data)
                    session.add(config)
            
            session.commit()
            
            # 전략 조합 생성
            sample_combinations = [
                {
                    'combination_id': 'rsi_averaging_trailing',
                    'name': 'RSI + 물타기 + 트레일링',
                    'description': 'RSI 진입 + 물타기 관리 + 트레일링 스탑',
                    'entry_strategy_id': 'rsi_config_1',
                    'conflict_resolution': 'conservative',
                    'management_strategies': [
                        ('averaging_config_1', 1),  # (config_id, priority)
                        ('trailing_config_1', 2)
                    ]
                },
                {
                    'combination_id': 'rsi_pyramiding',
                    'name': 'RSI + 불타기',
                    'description': 'RSI 진입 + 불타기 전략',
                    'entry_strategy_id': 'rsi_config_2',
                    'conflict_resolution': 'priority',
                    'management_strategies': [
                        ('pyramiding_config_1', 1),
                        ('trailing_config_1', 2)
                    ]
                },
                {
                    'combination_id': 'ma_cross_conservative',
                    'name': '이동평균 크로스 (보수적)',
                    'description': '이동평균 크로스 + 보수적 관리',
                    'entry_strategy_id': 'ma_config_1',
                    'conflict_resolution': 'conservative',
                    'management_strategies': [
                        ('trailing_config_1', 1)
                    ]
                }
            ]
            
            # 전략 조합 삽입
            for combo_data in sample_combinations:
                existing = session.query(StrategyCombination).filter_by(
                    combination_id=combo_data['combination_id']
                ).first()
                
                if not existing:
                    # 조합 생성
                    combination = StrategyCombination(
                        combination_id=combo_data['combination_id'],
                        name=combo_data['name'],
                        description=combo_data['description'],
                        entry_strategy_id=combo_data['entry_strategy_id'],
                        conflict_resolution=combo_data['conflict_resolution']
                    )
                    session.add(combination)
                    session.flush()  # ID 생성을 위해
                    
                    # 관리 전략들 연결
                    for config_id, priority in combo_data['management_strategies']:
                        mgmt_link = CombinationManagementStrategy(
                            combination_id=combo_data['combination_id'],
                            strategy_config_id=config_id,
                            priority=priority
                        )
                        session.add(mgmt_link)
                    
                    print(f"   ✅ {combo_data['name']} 조합 생성")
                else:
                    print(f"   ⏭️ {combo_data['name']} 조합 이미 존재")
            
            session.commit()
            print("✅ 샘플 전략 조합 생성 완료")
            
        except Exception as e:
            session.rollback()
            print(f"❌ 샘플 조합 생성 실패: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self):
        """데이터베이스 통계 출력"""
        session = self.get_session()
        try:
            stats = {
                'strategy_definitions': session.query(StrategyDefinition).count(),
                'strategy_configs': session.query(StrategyConfig).count(),
                'strategy_combinations': session.query(StrategyCombination).count(),
                'backtest_results': session.query(BacktestResult).count(),
                'trade_logs': session.query(TradeLog).count(),
                'optimization_jobs': session.query(OptimizationJob).count(),
            }
            
            print("\n📊 데이터베이스 현황:")
            for table, count in stats.items():
                print(f"   {table}: {count}개")
            
            return stats
            
        finally:
            session.close()


def main():
    """메인 실행 함수"""
    print("🚀 전략 트레이딩 데이터베이스 초기화")
    print("=" * 50)
    
    # 데이터베이스 매니저 생성
    db_manager = DatabaseManager()
    
    try:
        # 테이블 생성
        db_manager.create_tables()
        
        # 기본 데이터 삽입
        db_manager.initialize_strategy_definitions()
        db_manager.create_sample_strategy_combinations()
        
        # 통계 출력
        db_manager.get_database_stats()
        
        print("\n🎉 데이터베이스 초기화 완료!")
        print("   🔗 백테스트 엔진과 연동 준비 완료")
        print("   🧬 매개변수 최적화 테이블 준비 완료")
        print("   📱 실시간 거래 테이블 준비 완료")
        
    except Exception as e:
        print(f"\n❌ 초기화 실패: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

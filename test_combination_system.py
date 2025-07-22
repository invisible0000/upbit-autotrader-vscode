#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
전략 조합 시스템 테스트 스크립트

CombinationManager와 데이터 모델을 테스트합니다.
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from upbit_auto_trading.data_layer.combination_manager import (
    CombinationManager, create_sample_strategy_definitions, create_sample_strategy_configs
)
from upbit_auto_trading.data_layer.strategy_models import Base
from upbit_auto_trading.data_layer.storage.database_manager import get_database_manager

def test_database_setup():
    """데이터베이스 스키마 생성 테스트"""
    print("🏗️ 데이터베이스 스키마 생성 테스트...")
    
    try:
        db_manager = get_database_manager()
        engine = db_manager.get_engine()
        
        # 모든 테이블 생성
        Base.metadata.create_all(engine)
        print("✅ 데이터베이스 스키마 생성 성공")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 스키마 생성 실패: {e}")
        return False

def test_sample_data_creation():
    """샘플 데이터 생성 테스트"""
    print("\n📦 샘플 데이터 생성 테스트...")
    
    try:
        # 1. 전략 정의 생성
        create_sample_strategy_definitions()
        
        # 2. 전략 설정 생성
        create_sample_strategy_configs()
        
        print("✅ 샘플 데이터 생성 성공")
        return True
        
    except Exception as e:
        print(f"❌ 샘플 데이터 생성 실패: {e}")
        return False

def test_combination_creation():
    """전략 조합 생성 테스트"""
    print("\n🎯 전략 조합 생성 테스트...")
    
    try:
        manager = CombinationManager()
        
        # 샘플 조합 생성
        combination = manager.create_combination(
            name="RSI 진입 + 손절/트레일링 조합",
            entry_strategy_config_id="rsi_entry_config_001",
            management_strategy_configs=[
                {"config_id": "fixed_stop_config_001", "priority": 1},
                {"config_id": "trailing_stop_config_001", "priority": 2}
            ],
            description="RSI 기반 진입과 이중 손절 관리 조합",
            conflict_resolution="priority"
        )
        
        print(f"✅ 전략 조합 생성 성공: {combination.combination_id}")
        return combination.combination_id
        
    except Exception as e:
        print(f"❌ 전략 조합 생성 실패: {e}")
        return None

def test_combination_validation(combination_id: str):
    """전략 조합 검증 테스트"""
    print(f"\n🔍 전략 조합 검증 테스트: {combination_id}")
    
    try:
        manager = CombinationManager()
        validation_result = manager.validate_combination(combination_id)
        
        print(f"검증 상태: {validation_result['status']}")
        
        if validation_result['warnings']:
            print(f"경고사항: {validation_result['warnings']}")
            
        if validation_result['errors']:
            print(f"오류사항: {validation_result['errors']}")
            
        print(f"상세정보: {validation_result['details']}")
        
        print("✅ 전략 조합 검증 완료")
        return validation_result
        
    except Exception as e:
        print(f"❌ 전략 조합 검증 실패: {e}")
        return None

def test_combination_details(combination_id: str):
    """전략 조합 상세 정보 조회 테스트"""
    print(f"\n📋 전략 조합 상세 정보 조회: {combination_id}")
    
    try:
        manager = CombinationManager()
        details = manager.get_combination_details(combination_id)
        
        if details:
            print(f"조합 이름: {details['name']}")
            print(f"설명: {details['description']}")
            print(f"충돌 해결: {details['conflict_resolution']}")
            print(f"진입 전략: {details['entry_strategy']['name']}")
            print(f"관리 전략 수: {len(details['management_strategies'])}")
            
            for i, mgmt in enumerate(details['management_strategies'], 1):
                print(f"  {i}. {mgmt['name']} (우선순위: {mgmt['priority']})")
            
            print("✅ 상세 정보 조회 성공")
            return details
        else:
            print("❌ 조합을 찾을 수 없음")
            return None
            
    except Exception as e:
        print(f"❌ 상세 정보 조회 실패: {e}")
        return None

def test_combination_list():
    """전략 조합 목록 조회 테스트"""
    print("\n📜 전략 조합 목록 조회 테스트...")
    
    try:
        manager = CombinationManager()
        combinations = manager.list_combinations(limit=10)
        
        print(f"조회된 조합 수: {len(combinations)}")
        
        for combo in combinations:
            print(f"  • {combo['name']} ({combo['combination_id'][:8]}...)")
            print(f"    진입: {combo['entry_strategy_name']}, 관리: {combo['management_strategy_count']}개")
        
        print("✅ 조합 목록 조회 성공")
        return combinations
        
    except Exception as e:
        print(f"❌ 조합 목록 조회 실패: {e}")
        return []

def main():
    """메인 테스트 함수"""
    print("🚀 전략 조합 시스템 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("데이터베이스 스키마 생성", test_database_setup),
        ("샘플 데이터 생성", test_sample_data_creation),
    ]
    
    passed = 0
    total = len(tests) + 4  # 추가 테스트들
    combination_id = None
    
    # 기본 테스트들
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 테스트 통과")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
    
    # 조합 생성 테스트
    try:
        combination_id = test_combination_creation()
        if combination_id:
            passed += 1
            print("✅ 전략 조합 생성 테스트 통과")
        else:
            print("❌ 전략 조합 생성 테스트 실패")
    except Exception as e:
        print(f"❌ 전략 조합 생성 테스트 오류: {e}")
    
    # 검증 테스트
    if combination_id:
        try:
            validation_result = test_combination_validation(combination_id)
            if validation_result:
                passed += 1
                print("✅ 전략 조합 검증 테스트 통과")
            else:
                print("❌ 전략 조합 검증 테스트 실패")
        except Exception as e:
            print(f"❌ 전략 조합 검증 테스트 오류: {e}")
        
        # 상세 정보 테스트
        try:
            details = test_combination_details(combination_id)
            if details:
                passed += 1
                print("✅ 상세 정보 조회 테스트 통과")
            else:
                print("❌ 상세 정보 조회 테스트 실패")
        except Exception as e:
            print(f"❌ 상세 정보 조회 테스트 오류: {e}")
    
    # 목록 조회 테스트
    try:
        combinations = test_combination_list()
        if combinations:
            passed += 1
            print("✅ 조합 목록 조회 테스트 통과")
        else:
            print("❌ 조합 목록 조회 테스트 실패")
    except Exception as e:
        print(f"❌ 조합 목록 조회 테스트 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트를 통과했습니다!")
        print("\n💡 다음 단계:")
        print("   1. UI 탭 개발 시작")
        print("   2. 백테스트 연동")
        print("   3. 실시간 거래 연동")
    else:
        print(f"⚠️ {total - passed}개 테스트가 실패했습니다.")
        if combination_id:
            print(f"🎯 생성된 테스트 조합 ID: {combination_id}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
케이스 시뮬레이션 현황 분석 스크립트
"""

import os
import sys

def main():
    print('🔍 케이스 시뮬레이션 현황 분석')
    print('=' * 60)
    
    # 현재 디렉토리 확인
    current_dir = os.getcwd()
    print(f'📂 현재 디렉토리: {current_dir}')
    
    # 프로젝트 루트 확인
    if not current_dir.endswith('upbit-autotrader-vscode'):
        print('❌ 프로젝트 루트가 아닙니다')
        return
    
    print('\n📋 파일 존재 여부 확인:')
    print('-' * 40)
    
    # 1. 루트의 integrated_condition_manager.py
    root_icm = 'integrated_condition_manager.py'
    if os.path.exists(root_icm):
        size = os.path.getsize(root_icm)
        print(f'✅ 루트/integrated_condition_manager.py ({size:,} bytes)')
        
        # 간단한 내용 확인
        with open(root_icm, 'r', encoding='utf-8') as f:
            content = f.read()
            has_sim_engine = 'enhanced_real_data_simulation_engine' in content
            print(f'   🔗 실제 시뮬레이션 엔진: {"연결됨" if has_sim_engine else "연결 안됨"}')
    else:
        print('❌ 루트/integrated_condition_manager.py 없음')
    
    # 2. UI 폴더의 integrated_condition_manager.py
    ui_icm = 'upbit_auto_trading/ui/desktop/screens/strategy_management/integrated_condition_manager.py'
    if os.path.exists(ui_icm):
        size = os.path.getsize(ui_icm)
        print(f'✅ UI/integrated_condition_manager.py ({size:,} bytes)')
        
        # 간단한 내용 확인
        with open(ui_icm, 'r', encoding='utf-8') as f:
            content = f.read()
            has_sim_engine = 'enhanced_real_data_simulation_engine' in content
            has_run_sim = 'def run_simulation' in content
            has_gen_data = 'generate_simulation_data' in content
            
            print(f'   🔗 실제 시뮬레이션 엔진: {"연결됨" if has_sim_engine else "연결 안됨"}')
            print(f'   🎮 run_simulation 메서드: {"있음" if has_run_sim else "없음"}')
            print(f'   📊 가상 데이터 생성: {"있음" if has_gen_data else "없음"}')
    else:
        print('❌ UI/integrated_condition_manager.py 없음')
    
    # 3. scripts/utility 폴더
    scripts_util = 'scripts/utility'
    if os.path.exists(scripts_util):
        py_files = [f for f in os.listdir(scripts_util) if f.endswith('.py')]
        print(f'✅ scripts/utility 폴더 ({len(py_files)}개 Python 파일)')
        for f in py_files:
            print(f'   📄 {f}')
    else:
        print('❌ scripts/utility 폴더 없음')
    
    print('\n📊 분석 결과:')
    print('-' * 40)
    
    # 실제 UI에서 사용되는 파일 확인
    if os.path.exists(ui_icm):
        with open(ui_icm, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'enhanced_real_data_simulation_engine' not in content:
            print('🔍 현재 UI는 실제 시뮬레이션 엔진을 사용하지 않음')
            print('   → 단순 랜덤 데이터 생성 방식으로 동작')
            print('   → scripts/utility의 엔진은 독립적으로 존재')
        else:
            print('✅ UI가 실제 시뮬레이션 엔진과 연결됨')
    
    print('\n🎯 권장사항:')
    print('-' * 40)
    print('1. UI의 케이스 시뮬레이션이 의미있는 결과를 제공하는지 검증 필요')
    print('2. 실제 트리거 조건과 시뮬레이션 결과가 일치하는지 확인')
    print('3. scripts/utility의 엔진이 실제로 활용되고 있는지 점검')

if __name__ == '__main__':
    main()

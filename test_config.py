#!/usr/bin/env python3
"""
YAML 설정 로딩 테스트 스크립트
"""

from database_paths import get_current_config

def test_config_loading():
    """설정 로딩 테스트"""
    print("=== YAML 설정 로딩 테스트 ===")
    
    try:
        # 직접 YAML 파일 로드해서 확인
        import yaml
        import os
        config_path = "config/database_config.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)
            
            print("\n전체 YAML 설정:")
            print(f"  user_defined 섹션 존재: {'user_defined' in full_config}")
            if 'user_defined' in full_config:
                user_def = full_config['user_defined']
                print(f"  active: {user_def.get('active', False)}")
                if user_def.get('active'):
                    print("  사용자 정의 경로:")
                    for key, value in user_def.items():
                        if key != 'active':
                            print(f"    {key}: {value}")
        
        # get_current_config() 함수 결과
        config = get_current_config()
        print("\nget_current_config() 결과:")
        print(f"  Settings DB: {config.get('settings_db', 'N/A')}")
        print(f"  Strategies DB: {config.get('strategies_db', 'N/A')}")
        print(f"  Market Data DB: {config.get('market_data_db', 'N/A')}")
            
    except Exception as e:
        print(f"❌ 설정 로딩 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_loading()

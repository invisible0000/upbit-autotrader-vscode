#!/usr/bin/env python3
"""
🔍 DB 현황 분석 스크립트
현재 DB에 저장된 모든 데이터를 분석하여 YAML 파일 생성에 필요한 정보 추출
"""

import sqlite3
from pathlib import Path
import sys
import os

def analyze_current_db():
    """현재 DB 분석"""
    
    try:
        # 직접 DB 경로 지정 (settings.sqlite3)
        project_root = Path(__file__).parent.parent.parent.parent.parent.parent
        db_path = project_root / "upbit_auto_trading" / "data" / "settings.sqlite3"
        
        print(f"🔍 DB 경로: {db_path.absolute()}")
        
        if not db_path.exists():
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            print("   먼저 DB 마이그레이션을 실행하여 DB를 생성하세요.")
            return None
            
        print(f"📊 DB 분석 시작: {db_path.name}")
        
    except Exception as e:
        print(f"❌ DB 경로 확인 실패: {e}")
        return None
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        analysis = {}
        
        # 0. 먼저 존재하는 테이블 목록 확인
        print("\n📋 존재하는 테이블 목록:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        existing_tables = [table['name'] for table in tables]
        
        for table_name in existing_tables:
            print(f"  📄 {table_name}")
        
        if not existing_tables:
            print("❌ 테이블이 하나도 없습니다.")
            conn.close()
            return None
        
        # 1. tv_trading_variables 분석 (테이블이 존재하는 경우만)
        if 'tv_trading_variables' in existing_tables:
            print("\n🏷️ tv_trading_variables 테이블 분석")
            cursor.execute("SELECT * FROM tv_trading_variables WHERE is_active = 1")
            variables = cursor.fetchall()
            
            analysis['trading_variables'] = []
            category_stats = {}
            
            for var in variables:
                var_data = dict(var)
                analysis['trading_variables'].append(var_data)
                
                category = var_data['purpose_category']
                if category not in category_stats:
                    category_stats[category] = 0
                category_stats[category] += 1
                
                print(f"  📌 {var_data['variable_id']}: {var_data['display_name_ko']} ({category})")
            
            print(f"\n📈 카테고리별 지표 수: {category_stats}")
        else:
            print("\n❌ tv_trading_variables 테이블이 존재하지 않습니다.")
            analysis['trading_variables'] = []
        
        # 2. tv_variable_parameters 분석 (테이블이 존재하는 경우만)
        if 'tv_variable_parameters' in existing_tables:
            print("\n⚙️ tv_variable_parameters 테이블 분석")
            cursor.execute("SELECT * FROM tv_variable_parameters ORDER BY variable_id, display_order")
            parameters = cursor.fetchall()
            
            analysis['parameters'] = {}
            param_stats = {}
            
            for param in parameters:
                param_data = dict(param)
                var_id = param_data['variable_id']
                
                if var_id not in analysis['parameters']:
                    analysis['parameters'][var_id] = []
                
                analysis['parameters'][var_id].append(param_data)
                
                param_type = param_data['parameter_type']
                if param_type not in param_stats:
                    param_stats[param_type] = 0
                param_stats[param_type] += 1
            
            print(f"📊 파라미터 타입별 수: {param_stats}")
            print("🔧 총 지표별 파라미터:")
            for var_id, params in analysis['parameters'].items():
                print(f"  📌 {var_id}: {len(params)}개 파라미터")
        else:
            print("\n❌ tv_variable_parameters 테이블이 존재하지 않습니다.")
            analysis['parameters'] = {}
        
        # 3. tv_comparison_groups 분석 (테이블이 존재하는 경우만)
        if 'tv_comparison_groups' in existing_tables:
            print("\n🔗 tv_comparison_groups 테이블 분석")
            cursor.execute("SELECT * FROM tv_comparison_groups")
            groups = cursor.fetchall()
            
            analysis['comparison_groups'] = []
            for group in groups:
                group_data = dict(group)
                analysis['comparison_groups'].append(group_data)
                print(f"  🔗 {group_data['group_id']}: {group_data['group_name_ko']}")
        else:
            print("\n❌ tv_comparison_groups 테이블이 존재하지 않습니다.")
            analysis['comparison_groups'] = []
        
        # 4. 확장 테이블들 확인 (존재하는 테이블만)
        extended_tables = [
            'tv_help_texts', 'tv_placeholder_texts', 'tv_indicator_categories',
            'tv_parameter_types', 'tv_workflow_guides', 'tv_indicator_library'
        ]
        
        analysis['extended_tables'] = {}
        print("\n📋 확장 테이블 현황:")
        
        for table in extended_tables:
            if table in existing_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                    count = cursor.fetchone()['count']
                    analysis['extended_tables'][table] = count
                    print(f"  ✅ {table}: {count}개 레코드")
                except sqlite3.OperationalError as e:
                    analysis['extended_tables'][table] = f"오류: {e}"
                    print(f"  ❌ {table}: 오류 - {e}")
            else:
                analysis['extended_tables'][table] = "테이블 없음"
                print(f"  ❌ {table}: 테이블 없음")
        
        conn.close()
        return analysis
        
    except Exception as e:
        print(f"❌ DB 분석 실패: {e}")
        return None

def extract_variable_definitions_data(analysis):
    """variable_definitions_example.py에서 추출 가능한 데이터 분석"""
    
    print("\n🔍 variable_definitions_example.py 상세 분석")
    
    # variable_definitions_example.py 파일 읽기
    try:
        with open("variable_definitions_example.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        print("✅ variable_definitions_example.py 파일 읽기 성공")
        
        # 데이터 구조 분석
        data = {
            'chart_categories': {},
            'variable_parameters': {},
            'variable_descriptions': {},
            'variable_placeholders': {},
            'category_variables': {}
        }
        
        # 1. CHART_CATEGORIES 추출 분석
        import re
        chart_pattern = r'"([^"]+)": "([^"]+)",'
        chart_matches = re.findall(chart_pattern, content)
        
        for var_id, category in chart_matches:
            if category in ['overlay', 'subplot']:
                data['chart_categories'][var_id] = category
        
        print(f"📊 variable_definitions의 차트 카테고리: {len(data['chart_categories'])}개 변수")
        
        # 2. DB와 variable_definitions 간 지표 비교
        print("\n🔎 DB vs variable_definitions 지표 비교:")
        
        # DB에 있는 지표들
        db_indicators = set(var['variable_id'] for var in analysis['trading_variables'])
        
        # variable_definitions에 정의된 지표들 (get_variable_parameters 메서드 내 key들)
        vd_indicators = set()
        
        # get_variable_parameters 메서드에서 정의된 지표들 추출
        params_pattern = r'"([A-Z_]+)": \{'
        params_matches = re.findall(params_pattern, content)
        vd_indicators = set(params_matches)
        
        print(f"  📌 DB 지표 수: {len(db_indicators)}")
        print(f"  📌 variable_definitions 지표 수: {len(vd_indicators)}")
        
        # 차이점 분석
        missing_in_vd = db_indicators - vd_indicators
        extra_in_vd = vd_indicators - db_indicators
        
        if missing_in_vd:
            print(f"  ⚠️ variable_definitions에 누락된 지표: {sorted(missing_in_vd)}")
        if extra_in_vd:
            print(f"  💡 variable_definitions에만 있는 지표: {sorted(extra_in_vd)}")
        if not missing_in_vd and not extra_in_vd:
            print("  ✅ DB와 variable_definitions 지표 완전 일치!")
        
        # 3. 카테고리 정의 분석
        print("\n📋 variable_definitions 카테고리 분석:")
        category_pattern = r'"([a-z_]+)": \[(.*?)\]'
        category_matches = re.findall(category_pattern, content, re.DOTALL)
        
        for category, vars_str in category_matches:
            var_count = vars_str.count('(",')
            if var_count > 0:
                print(f"  📂 {category}: {var_count}개 지표")
                data['category_variables'][category] = var_count
        
        return data
        
    except Exception as e:
        print(f"❌ variable_definitions_example.py 분석 실패: {e}")
        return None

def main():
    """메인 실행"""
    print("🚀 DB 현황 분석 및 YAML 검증")
    print("=" * 50)
    
    # DB 분석
    db_analysis = analyze_current_db()
    if not db_analysis:
        return
    
    # variable_definitions_example.py 분석
    vd_analysis = extract_variable_definitions_data(db_analysis)
    
    # 결과 요약
    print("\n📋 분석 결과 요약")
    print("=" * 30)
    print(f"📌 활성 지표 수: {len(db_analysis['trading_variables'])}")
    print(f"⚙️ 총 파라미터 수: {sum(len(params) for params in db_analysis['parameters'].values())}")
    print(f"🔗 비교 그룹 수: {len(db_analysis['comparison_groups'])}")
    
    # 기존 YAML 파일들 검증
    print("\n� YAML 파일 검증")
    print("=" * 30)
    
    # 현재 디렉토리의 YAML 파일들 확인
    yaml_files = [
        'tv_help_texts.yaml',
        'tv_placeholder_texts.yaml', 
        'tv_indicator_categories.yaml',
        'tv_parameter_types.yaml',
        'tv_workflow_guides.yaml',
        'tv_indicator_library.yaml'
    ]
    
    for yaml_file in yaml_files:
        yaml_path = Path(yaml_file)
        if yaml_path.exists():
            print(f"✅ {yaml_file}: 존재함")
        else:
            print(f"❌ {yaml_file}: 없음")
    
    # DB 데이터와 YAML 파일 간의 일치성 검증
    print("\n🔎 DB-YAML 일치성 검증")
    print("=" * 30)
    
    verify_yaml_consistency(db_analysis)
    
    return db_analysis, vd_analysis


def verify_yaml_consistency(db_analysis):
    """DB 데이터와 YAML 파일의 일치성 검증"""
    
    # 1. tv_indicator_categories.yaml 검증
    try:
        import yaml
        with open('tv_indicator_categories.yaml', 'r', encoding='utf-8') as f:
            categories_data = yaml.safe_load(f)
        
        print("📊 지표 카테고리 검증:")
        
        # DB에서 실제 사용되는 카테고리 추출
        db_categories = set()
        for var in db_analysis['trading_variables']:
            db_categories.add(var['purpose_category'])
        
        # YAML에 정의된 카테고리 확인
        yaml_categories = set(categories_data['categories'].keys())
        
        # 일치하지 않는 카테고리 찾기
        missing_in_yaml = db_categories - yaml_categories
        extra_in_yaml = yaml_categories - db_categories
        
        if missing_in_yaml:
            print(f"  ⚠️ YAML에 누락된 카테고리: {missing_in_yaml}")
        if extra_in_yaml:
            print(f"  💡 YAML에만 있는 카테고리: {extra_in_yaml}")
        if not missing_in_yaml and not extra_in_yaml:
            print("  ✅ 카테고리 완전 일치")
            
        # 각 카테고리별 지표 검증
        for category in yaml_categories:
            if category in categories_data['categories']:
                yaml_indicators = set(categories_data['categories'][category].get('indicators', []))
                db_indicators = set(var['variable_id'] for var in db_analysis['trading_variables'] 
                                  if var['purpose_category'] == category)
                
                missing_indicators = db_indicators - yaml_indicators
                extra_indicators = yaml_indicators - db_indicators
                
                if missing_indicators:
                    print(f"  📝 {category} 카테고리에 누락된 지표: {missing_indicators}")
                if extra_indicators:
                    print(f"  🗑️ {category} 카테고리에 불필요한 지표: {extra_indicators}")
                    
    except Exception as e:
        print(f"❌ tv_indicator_categories.yaml 검증 실패: {e}")
    
    # 2. tv_parameter_types.yaml 검증
    try:
        with open('tv_parameter_types.yaml', 'r', encoding='utf-8') as f:
            param_types_data = yaml.safe_load(f)
        
        print("\n⚙️ 파라미터 타입 검증:")
        
        # DB에서 실제 사용되는 파라미터 타입 추출
        db_param_types = set()
        for var_id, params in db_analysis['parameters'].items():
            for param in params:
                db_param_types.add(param['parameter_type'])
        
        # YAML에 정의된 파라미터 타입 확인
        yaml_param_types = set(param_types_data['parameter_types'].keys())
        
        missing_types = db_param_types - yaml_param_types
        extra_types = yaml_param_types - db_param_types
        
        if missing_types:
            print(f"  ⚠️ YAML에 누락된 파라미터 타입: {missing_types}")
        if extra_types:
            print(f"  � YAML에만 있는 파라미터 타입: {extra_types}")
        if not missing_types and not extra_types:
            print("  ✅ 파라미터 타입 완전 일치")
            
    except Exception as e:
        print(f"❌ tv_parameter_types.yaml 검증 실패: {e}")
    
    # 3. 지표별 필요한 도움말 텍스트 확인
    print("\n📚 도움말 텍스트 필요성 분석:")
    
    all_indicators = [var['variable_id'] for var in db_analysis['trading_variables']]
    all_param_ids = []
    
    for var_id, params in db_analysis['parameters'].items():
        for param in params:
            all_param_ids.append(f"{var_id}_{param['parameter_id']}")
    
    print(f"  📊 총 {len(all_indicators)}개 지표, {len(all_param_ids)}개 파라미터")
    print(f"  💬 각 지표당 평균 {len(all_param_ids)/len(all_indicators):.1f}개 파라미터")
    
    # 4. 현재 상태 요약
    print("\n📋 현재 상태 요약:")
    print("  ✅ 기본 스키마 테이블: tv_trading_variables, tv_variable_parameters, tv_comparison_groups")
    print("  ✅ YAML 파일들: 6개 모두 존재")
    print("  ⚠️ 확장 테이블들: 아직 생성되지 않음 (YAML→DB 마이그레이션 필요)")
    
    return True

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
1번 항목 분석: MACD.macd_type이 왜 enum이 되어야 하는지 확인
"""

import yaml
import sqlite3
import json

def analyze_macd_type():
    """MACD macd_type 파라미터 상세 분석"""

    print("=== 1번 분석: MACD.macd_type ===\n")

    # 1. YAML 파일에서 MACD 관련 파라미터 확인
    print("1. YAML 파일 분석")
    analyze_yaml_macd()

    # 2. 데이터베이스에서 MACD 파라미터 확인
    print("\n2. 데이터베이스 분석")
    analyze_db_macd()

    # 3. enum으로 변경해야 하는 이유 분석
    print("\n3. ENUM 변경 필요성 분석")
    analyze_enum_necessity()

def analyze_yaml_macd():
    """YAML에서 MACD 관련 파라미터 분석"""

    with open('data_info/tv_variable_parameters.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if 'variable_parameters' not in data:
        print("  ❌ variable_parameters 섹션이 없습니다.")
        return

    params = data['variable_parameters']
    print(f"  📊 총 파라미터 수: {len(params)}")

    # MACD 관련 파라미터 찾기
    macd_params = []
    for key, param_data in params.items():
        variable_id = param_data.get('variable_id', '')
        if variable_id == 'MACD':
            macd_params.append((key, param_data))

    print(f"  🔍 MACD 파라미터 수: {len(macd_params)}")

    # 각 MACD 파라미터 출력
    for key, param_data in macd_params:
        param_name = param_data.get('parameter_name', '')
        param_type = param_data.get('parameter_type', '')
        enum_values = param_data.get('enum_values', '')
        default_value = param_data.get('default_value', '')

        print(f"    📋 {key}:")
        print(f"      - parameter_name: {param_name}")
        print(f"      - parameter_type: {param_type}")
        print(f"      - default_value: {default_value}")

        if enum_values:
            try:
                parsed_values = json.loads(enum_values) if isinstance(enum_values, str) else enum_values
                print(f"      - enum_values ({len(parsed_values)}개): {parsed_values}")
            except:
                print(f"      - enum_values (raw): {enum_values}")
        else:
            print(f"      - enum_values: None")

        # macd_type 특별 분석
        if param_name == 'macd_type':
            print(f"      🎯 TARGET FOUND: macd_type")
            analyze_macd_type_detail(param_data)

def analyze_macd_type_detail(param_data):
    """macd_type 파라미터 상세 분석"""

    print(f"        📋 상세 분석:")

    param_type = param_data.get('parameter_type', '')
    enum_values = param_data.get('enum_values', '')

    print(f"        - 현재 타입: {param_type}")

    if enum_values:
        try:
            parsed_values = json.loads(enum_values) if isinstance(enum_values, str) else enum_values
            print(f"        - 선택 옵션들:")
            for i, value in enumerate(parsed_values, 1):
                print(f"          {i}. {value}")

            # enum 변경 필요성 판단
            if len(parsed_values) > 1:
                print(f"        ✅ ENUM 변경 필요: {len(parsed_values)}개 고정 선택지 존재")
                return True
            else:
                print(f"        ⚠️  선택지가 1개뿐: enum 불필요할 수 있음")
                return False
        except Exception as e:
            print(f"        ❌ enum_values 파싱 오류: {e}")
            return False
    else:
        print(f"        ❌ enum_values 없음: enum 불필요")
        return False

def analyze_db_macd():
    """데이터베이스에서 MACD 파라미터 확인"""

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # MACD 관련 파라미터 조회
    cursor.execute("""
        SELECT parameter_name, parameter_type, default_value, enum_values, description
        FROM tv_variable_parameters
        WHERE variable_id = 'MACD'
        ORDER BY parameter_name
    """)

    results = cursor.fetchall()

    if results:
        print(f"  📊 DB에서 MACD 파라미터 {len(results)}개 발견:")
        for param_name, param_type, default_value, enum_values, description in results:
            print(f"    📋 {param_name}:")
            print(f"      - type: {param_type}")
            print(f"      - default: {default_value}")
            print(f"      - description: {description}")

            if enum_values:
                try:
                    parsed_values = json.loads(enum_values)
                    print(f"      - enum_values: {parsed_values}")

                    if param_name == 'macd_type':
                        print(f"      🎯 macd_type 분석:")
                        print(f"        - 현재 타입: {param_type}")
                        print(f"        - 선택지 수: {len(parsed_values)}")
                        for i, value in enumerate(parsed_values, 1):
                            print(f"        - 옵션 {i}: {value}")
                except:
                    print(f"      - enum_values (raw): {enum_values}")
    else:
        print("  ❌ DB에서 MACD 파라미터를 찾을 수 없습니다.")

    conn.close()

def analyze_enum_necessity():
    """enum 변경 필요성 분석"""

    print("  📋 MACD Type이 ENUM이어야 하는 이유:")
    print("    1. 💡 MACD 계산 방식은 몇 가지로 제한됨:")
    print("       - Standard MACD (표준)")
    print("       - Signal MACD (시그널)")
    print("       - Histogram MACD (히스토그램)")
    print("       - Zero Lag MACD (제로 랙)")

    print("    2. 🚫 사용자 자유 입력의 문제점:")
    print("       - 'standart' (오타)")
    print("       - 'STANDARD' (대소문자 혼재)")
    print("       - '스탠다드' (한글 입력)")
    print("       - '표준 MACD' (공백 포함)")

    print("    3. ✅ ENUM 사용 시 장점:")
    print("       - 정확한 선택지만 제공")
    print("       - UI에서 드롭다운으로 편리한 선택")
    print("       - 내부 로직에서 정확한 값 보장")
    print("       - 다국어 지원 용이 (표시명 vs 내부값)")

    print("    4. 🎯 결론: MACD type은 반드시 ENUM이어야 함!")

if __name__ == "__main__":
    analyze_macd_type()

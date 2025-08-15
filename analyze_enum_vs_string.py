#!/usr/bin/env python3
"""
parameter_type: enum vs string 분석 및 개선 방안

현재 상황:
- timeframe 파라미터들이 parameter_type='string'으로 되어 있음
- enum_values는 있지만 UI에서 활용되지 않음
- QLineEdit으로 자유 입력 받고 있음

개선 방안 제시
"""

import sqlite3
import json
from pathlib import Path

def analyze_enum_vs_string():
    """enum vs string 타입 분석"""

    print("=== PARAMETER_TYPE: ENUM vs STRING 분석 ===\n")

    # 1. 현재 상황 분석
    print("1. 현재 상황")
    print("   - timeframe 파라미터: parameter_type='string'")
    print("   - enum_values 필드에 선택 옵션들이 있지만 UI에서 미활용")
    print("   - 사용자가 QLineEdit에 직접 입력 (오타 가능성)")

    # 2. 장단점 비교
    print("\n2. 타입별 장단점 비교")

    enum_pros = [
        "UI에서 QComboBox로 드롭다운 제공 → 사용자 편의성 ↑",
        "미리 정의된 값만 선택 가능 → 입력 오류 방지",
        "enum_values 필드 활용 → 데이터 일관성",
        "유효성 검증 자동화",
        "다국어 지원 용이 (표시명 vs 내부값 분리 가능)"
    ]

    enum_cons = [
        "새로운 값 추가 시 DB 업데이트 필요",
        "UI 구현이 약간 복잡해짐",
        "고정된 선택지만 제공"
    ]

    string_pros = [
        "자유로운 값 입력 가능",
        "새로운 timeframe 값 즉시 사용 가능",
        "UI 구현 단순 (QLineEdit)",
        "확장성 좋음"
    ]

    string_cons = [
        "사용자 입력 오류 가능성",
        "유효성 검증 별도 구현 필요",
        "enum_values 필드 미활용 → 데이터 불일치",
        "UI 사용성 떨어짐 (어떤 값을 입력해야 할지 모름)"
    ]

    print("\n   📊 ENUM 타입 장점:")
    for pro in enum_pros:
        print(f"     ✅ {pro}")

    print("\n   📊 ENUM 타입 단점:")
    for con in enum_cons:
        print(f"     ❌ {con}")

    print("\n   📊 STRING 타입 장점:")
    for pro in string_pros:
        print(f"     ✅ {pro}")

    print("\n   📊 STRING 타입 단점:")
    for con in string_cons:
        print(f"     ❌ {con}")

def check_current_enum_values():
    """현재 enum_values 데이터 확인"""

    print("\n3. 현재 ENUM_VALUES 데이터 분석")

    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # timeframe 파라미터들의 enum_values 확인
    cursor.execute("""
        SELECT variable_id, parameter_name, enum_values
        FROM tv_variable_parameters
        WHERE parameter_name = 'timeframe' AND enum_values IS NOT NULL
        ORDER BY variable_id
    """)

    results = cursor.fetchall()

    if results:
        print("   📋 현재 timeframe enum_values:")
        for var_id, param_name, enum_values_str in results:
            try:
                enum_values = json.loads(enum_values_str) if enum_values_str else []
                print(f"     {var_id}: {len(enum_values)}개 옵션")
                for i, value in enumerate(enum_values[:3]):  # 처음 3개만 표시
                    print(f"       {i+1}. {value}")
                if len(enum_values) > 3:
                    print(f"       ... 총 {len(enum_values)}개")
            except json.JSONDecodeError:
                print(f"     {var_id}: JSON 파싱 오류")

    conn.close()

def recommend_solution():
    """권장 해결 방안"""

    print("\n4. 권장 해결 방안")

    print("\n   🎯 결론: ENUM 타입 + UI 개선이 최적")

    print("\n   📋 구체적 개선 사항:")
    print("     1. parameter_type을 'enum'으로 변경")
    print("     2. parameter_input_widget.py에서 enum 타입 처리 추가:")
    print("        - QComboBox 위젯 생성")
    print("        - enum_values로 옵션 채우기")
    print("        - 기본값 설정")
    print("     3. 유효성 검증 로직 추가")
    print("     4. 사용자 정의 값 입력 옵션도 제공 (필요시)")

    print("\n   💡 하이브리드 접근법:")
    print("     - 기본적으로 QComboBox로 미리 정의된 옵션 제공")
    print("     - '직접 입력' 옵션 추가하여 사용자 정의 값도 허용")
    print("     - 최고의 사용성 + 유연성")

def generate_improvement_code():
    """개선된 파라미터 위젯 코드 예시 생성"""

    print("\n5. 개선된 UI 코드 예시")

    code_example = '''
def _create_input_widget_by_type(self, param_type: str, default_value: Any,
                                 min_value: Any = None, max_value: Any = None,
                                 enum_values: list = None) -> QWidget:
    """파라미터 타입에 따른 입력 위젯 생성 (개선된 버전)"""

    if param_type == 'enum':
        widget = QComboBox()

        # enum_values가 있으면 옵션 추가
        if enum_values:
            for value in enum_values:
                widget.addItem(value)

        # 기본값 설정
        if default_value and default_value in enum_values:
            widget.setCurrentText(default_value)

        # 사용자 정의 입력 허용 (선택사항)
        widget.setEditable(True)

        return widget

    # 기존 타입들은 그대로...
    '''

    print("   💻 핵심 코드:")
    print(code_example)

if __name__ == "__main__":
    analyze_enum_vs_string()
    check_current_enum_values()
    recommend_solution()
    generate_improvement_code()

    print("\n" + "="*60)
    print("🎯 최종 권장사항: timeframe을 enum 타입으로 변경 + UI 개선")
    print("   → 사용성 ↑, 오류 ↓, 데이터 일관성 ↑")
    print("="*60)

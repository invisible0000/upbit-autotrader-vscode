"""
QListWidget bool 값 문제 정밀 분석
"""

import sys
from PyQt6.QtWidgets import QApplication, QListWidget, QWidget

def analyze_bool_issue():
    """QListWidget의 bool 값 문제 분석"""
    print("=== QListWidget bool 값 문제 분석 ===")

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # 1. QWidget과 QListWidget 비교
    print("\n1. QWidget vs QListWidget bool 값 비교")

    widget = QWidget()
    print(f"QWidget:")
    print(f"  - is None: {widget is None}")
    print(f"  - bool(): {bool(widget)}")
    print(f"  - __bool__() 존재: {hasattr(widget, '__bool__')}")
    print(f"  - __len__() 존재: {hasattr(widget, '__len__')}")

    list_widget = QListWidget()
    print(f"QListWidget:")
    print(f"  - is None: {list_widget is None}")
    print(f"  - bool(): {bool(list_widget)}")
    print(f"  - __bool__() 존재: {hasattr(list_widget, '__bool__')}")
    print(f"  - __len__() 존재: {hasattr(list_widget, '__len__')}")

    # 2. QListWidget의 특별한 메서드들 확인
    print(f"\n2. QListWidget 특별 메서드 분석")
    print(f"  - count(): {list_widget.count()}")

    if hasattr(list_widget, '__len__'):
        try:
            len_result = len(list_widget)
            print(f"  - len(): {len_result}")
        except Exception as e:
            print(f"  - len() 오류: {e}")

    if hasattr(list_widget, '__bool__'):
        try:
            bool_result = list_widget.__bool__()
            print(f"  - __bool__(): {bool_result}")
        except Exception as e:
            print(f"  - __bool__() 오류: {e}")

    # 3. 조건문에서의 동작 테스트
    print(f"\n3. 조건문 테스트")

    if widget:
        print("  - QWidget: if 조건 True")
    else:
        print("  - QWidget: if 조건 False")

    if list_widget:
        print("  - QListWidget: if 조건 True")
    else:
        print("  - QListWidget: if 조건 False")

    # 4. 다른 방법으로 조건 체크
    print(f"\n4. 대안적 조건 체크")
    print(f"  - list_widget is not None: {list_widget is not None}")
    print(f"  - id(list_widget) != 0: {id(list_widget) != 0}")
    print(f"  - hasattr(list_widget, 'count'): {hasattr(list_widget, 'count')}")

    # 5. 아이템 추가 후 bool 값 변화
    print(f"\n5. 아이템 추가 후 bool 값 변화")
    print(f"  - 아이템 추가 전 bool(): {bool(list_widget)}")

    list_widget.addItem("테스트 아이템")
    print(f"  - 아이템 추가 후 bool(): {bool(list_widget)}")
    print(f"  - 아이템 추가 후 count(): {list_widget.count()}")

    return list_widget


def create_safe_conditional_check():
    """안전한 조건부 체크 함수"""
    print("\n=== 안전한 조건부 체크 방법 ===")

    list_widget = QListWidget()

    # 위험한 방법 (현재 문제가 되는 방법)
    if not list_widget:
        print("❌ 위험한 방법: list_widget이 False로 평가됨")
    else:
        print("✅ 위험한 방법: list_widget이 True로 평가됨")

    # 안전한 방법들
    if list_widget is None:
        print("❌ 안전한 방법 1: is None 체크 - None임")
    else:
        print("✅ 안전한 방법 1: is None 체크 - None 아님")

    if id(list_widget) == 0:
        print("❌ 안전한 방법 2: id 체크 - 0임")
    else:
        print("✅ 안전한 방법 2: id 체크 - 0 아님")

    if hasattr(list_widget, 'count'):
        print("✅ 안전한 방법 3: hasattr 체크 - count 메서드 존재")
    else:
        print("❌ 안전한 방법 3: hasattr 체크 - count 메서드 없음")

    return list_widget


if __name__ == "__main__":
    list_widget = analyze_bool_issue()
    create_safe_conditional_check()

    print("\n💡 결론:")
    print("1. QListWidget은 정상적으로 생성되지만 bool()이 False를 반환")
    print("2. 이는 빈 컨테이너의 특성으로 보임 (아이템이 없으면 False)")
    print("3. 'if not widget:' 조건 대신 'if widget is None:' 사용 권장")
    print("4. 또는 'if not hasattr(widget, 'count'):' 같은 안전한 체크 사용")

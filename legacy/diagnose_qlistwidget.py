"""
PyQt6 위젯 생성 근본 문제 진단
QListWidget이 생성 직후 None이 되는 현상 분석
"""

import sys
import gc
from PyQt6.QtWidgets import QApplication, QListWidget, QWidget

def diagnose_qlistwidget_creation():
    """QListWidget 생성 과정 상세 진단"""
    print("=== QListWidget 생성 진단 시작 ===")

    # 1. 기본 정보
    print(f"Python 버전: {sys.version}")
    print(f"시스템 참조 카운팅: {sys.getrefcount}")

    # 2. PyQt6 정보
    try:
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        print(f"Qt 버전: {QT_VERSION_STR}")
        print(f"PyQt6 버전: {PYQT_VERSION_STR}")
    except Exception as e:
        print(f"버전 정보 오류: {e}")

    # 3. QApplication 상태
    app = QApplication.instance()
    print(f"QApplication 존재: {app is not None}")
    if app:
        print(f"QApplication ID: {id(app)}")

    print("\n--- 단계별 위젯 생성 테스트 ---")

    # 4. 단계별 위젯 생성 테스트
    test_results = []

    # Test 1: 기본 QWidget
    try:
        print("Test 1: QWidget 생성")
        widget = QWidget()
        widget_id = id(widget)
        print(f"  생성 직후 ID: {widget_id}")
        print(f"  생성 직후 type: {type(widget)}")
        print(f"  생성 직후 None 체크: {widget is None}")
        print(f"  생성 직후 bool 체크: {bool(widget)}")

        # 변수 재할당 체크
        widget_ref = widget
        print(f"  참조 복사 후 원본: {widget is None}")
        print(f"  참조 복사 후 복사본: {widget_ref is None}")

        test_results.append(("QWidget", True, widget_id))
        del widget, widget_ref

    except Exception as e:
        print(f"  QWidget 생성 실패: {e}")
        test_results.append(("QWidget", False, str(e)))

    # Test 2: QListWidget - 직접 생성
    try:
        print("\nTest 2: QListWidget 직접 생성")
        list_widget = QListWidget()
        list_id = id(list_widget)
        print(f"  생성 직후 ID: {list_id}")
        print(f"  생성 직후 type: {type(list_widget)}")
        print(f"  생성 직후 None 체크: {list_widget is None}")
        print(f"  생성 직후 bool 체크: {bool(list_widget)}")

        # 메서드 호출 테스트
        try:
            count = list_widget.count()
            print(f"  count() 메서드 호출 성공: {count}")
        except Exception as e:
            print(f"  count() 메서드 호출 실패: {e}")

        # 변수 재할당 후 체크
        list_ref = list_widget
        print(f"  참조 복사 후 원본: {list_widget is None}")
        print(f"  참조 복사 후 복사본: {list_ref is None}")

        test_results.append(("QListWidget_direct", True, list_id))
        del list_widget, list_ref

    except Exception as e:
        print(f"  QListWidget 직접 생성 실패: {e}")
        test_results.append(("QListWidget_direct", False, str(e)))

    # Test 3: QListWidget - 클래스 내부에서 생성
    try:
        print("\nTest 3: 클래스 내부에서 QListWidget 생성")

        class TestContainer:
            def __init__(self):
                print("    TestContainer 초기화 시작")
                self.list_widget = None
                self._create_list_widget()
                print(f"    초기화 완료, list_widget: {self.list_widget is None}")

            def _create_list_widget(self):
                print("    QListWidget 생성 중...")
                self.list_widget = QListWidget()
                widget_id = id(self.list_widget)
                print(f"    생성 직후 ID: {widget_id}")
                print(f"    생성 직후 None 체크: {self.list_widget is None}")

                # 즉시 검증
                if self.list_widget is None:
                    print("    ❌ 생성 직후 None이 됨!")
                else:
                    print("    ✅ 생성 직후 정상")

                return widget_id

        container = TestContainer()
        final_check = container.list_widget is None
        print(f"  최종 체크: {final_check}")

        if final_check:
            test_results.append(("QListWidget_class", False, "생성 후 None이 됨"))
        else:
            test_results.append(("QListWidget_class", True, id(container.list_widget)))

        del container

    except Exception as e:
        print(f"  클래스 내부 생성 실패: {e}")
        import traceback
        print(f"  상세 오류: {traceback.format_exc()}")
        test_results.append(("QListWidget_class", False, str(e)))

    # Test 4: 메모리 및 참조 분석
    print("\nTest 4: 메모리 및 참조 분석")
    try:
        import weakref

        # 약한 참조로 테스트
        print("  약한 참조 테스트...")
        strong_list = QListWidget()
        weak_ref = weakref.ref(strong_list)

        print(f"  강한 참조 존재: {strong_list is not None}")
        print(f"  약한 참조 존재: {weak_ref() is not None}")

        # 강한 참조 제거
        strong_list = None
        gc.collect()

        print(f"  강한 참조 제거 후 약한 참조: {weak_ref() is not None}")

    except Exception as e:
        print(f"  메모리 분석 실패: {e}")

    # 결과 요약
    print("\n=== 진단 결과 요약 ===")
    for test_name, success, result in test_results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{test_name}: {status} - {result}")

    # 결론
    failed_tests = [name for name, success, _ in test_results if not success]
    if failed_tests:
        print(f"\n🚨 실패한 테스트: {', '.join(failed_tests)}")
        if "QListWidget_class" in failed_tests:
            print("💡 클래스 내부에서 QListWidget 생성 시 문제 발생!")
            print("💡 이는 self 속성 할당 과정에서의 참조 문제일 수 있습니다.")
    else:
        print("\n✅ 모든 테스트 통과")


if __name__ == "__main__":
    # QApplication 생성
    app = QApplication(sys.argv)

    # 진단 실행
    diagnose_qlistwidget_creation()

    print("\n프로그램 종료")

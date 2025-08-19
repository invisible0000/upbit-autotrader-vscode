# QAsync 문제 사례 조사 결과

`QAsync` 라이브러리의 문제 사례에 대해 블로그, 레딧, GitHub 등을 종합적으로 조사한 결과입니다. 라이브러리 자체는 안정적이지만, 몇 가지 특정 상황에서 발생하는 문제들과 해결책이 공유되고 있었습니다.

---

## QAsync 문제 사례 요약

조사 결과, 문제점들은 주로 **이벤트 루프의 생명주기 관리**, **특정 버전 호환성**, **에러 처리 방식**의 3가지 카테고리로 분류됩니다.

---

## **1. 이벤트 루프 관리 문제 🔄**

가장 흔하게 발견되는 문제 유형으로, 이벤트 루프를 잘못 초기화하거나 여러 스레드에서 사용할 때 발생합니다.

### **`RuntimeError: no running event loop` 에러**
* **원인**: `asyncio.create_task()`와 같은 함수가 호출될 때 현재 스레드에 `asyncio` 이벤트 루프가 설정되어 있지 않아서 발생합니다. 특히 메인 스레드가 아닌 별도의 `QThread`에서 `qasync` 이벤트 루프를 실행하려고 할 때 자주 발생합니다.
* **해결책**: 새로운 스레드 내에서 `qasync.QEventLoop` 인스턴스를 생성하고, `asyncio.set_event_loop()`를 통해 해당 스레드의 이벤트 루프로 명시적으로 지정해야 합니다.
* **관련 링크**: [Stack Overflow: How to set up a qasync event loop in another thread?](https://stackoverflow.com/questions/67979231/how-to-set-up-a-qasync-event-loop-in-another-thread)

### **애플리케이션 종료 시 멈춤(Hanging) 현상**
* **원인**: `qasync`의 이벤트 루프 종료(`close`) 방식이 기본 `asyncio`와 약간 다릅니다. 백그라운드 스레드에서 실행 중인 작업이 완전히 끝날 때까지 기다리면서, 특정 조건에서 프로그램이 종료되지 않고 멈추는 경우가 보고되었습니다.
* **해결책**: 프로그램 종료 시그널(`aboutToQuit`)을 명확하게 처리하고, 실행 중인 모든 비동기 태스크를 안전하게 취소하는 로직을 추가하는 것이 권장됩니다.
* **관련 링크**: [GitHub Issue #115: Differences between qasync.QEventLoop.close and asyncio.BaseEventLoop.close](https://github.com/CabbageDevelopment/qasync/issues/115)

### **`KeyboardInterrupt` (Ctrl+C) 처리 문제**
* **원인**: `qasync` 이벤트 루프가 실행 중일 때, 터미널에서 `Ctrl+C`로 프로그램을 종료하면 `core dumped`와 같은 비정상적인 종료가 발생할 수 있습니다.
* **해결책**: `asyncio.Event`를 사용하여 애플리케이션의 종료 이벤트를 관리하고, `run_until_complete`로 해당 이벤트가 설정될 때까지 기다리는 방식으로 구현하면 안전하게 종료할 수 있습니다.
* **관련 링크**: [GitHub Issue #127: How to handle KeyboardInterrupt?](https://github.com/CabbageDevelopment/qasync/issues/127)

---

## **2. 특정 버전 및 환경 호환성 문제 ⚙️**

라이브러리 버전이나 특정 Qt 컴포넌트와의 조합에서 발생하는 문제입니다.

### **`qasync` 특정 버전에서 태스크 생성 오류**
* **사례**: v0.24.0에서는 잘 작동하던 코드가 v0.24.2 이상으로 업데이트한 후 `__init__` 생성자에서 태스크를 만들 때 오류가 발생했다는 보고가 있습니다.
* **해결책**: 문제가 발생할 경우, 다른 버전으로 다운그레이드하거나 최신 버전의 릴리즈 노트를 확인하여 변경 사항을 적용해야 합니다.
* **관련 링크**: [GitHub Issue #116: creating task ... works fine in v0.24.0 but not with v0.24.2 and above](https://github.com/CabbageDevelopment/qasync/issues/116)

### **특정 Qt 위젯과의 충돌**
* **사례**: 코루틴(coroutine) 안에서 `QMediaPlayer` 객체를 생성할 때 프로그램이 충돌(crash)하는 사례가 보고되었습니다.
* **해결책**: 문제가 되는 Qt 객체는 코루틴 외부에서 생성하거나, Qt의 시그널-슬롯 메커니즘을 통해 메인 스레드에서 생성하도록 작업을 전달하는 방식으로 우회할 수 있습니다.
* **관련 링크**: [GitHub Issue #85: qasync will cause crash when construct QMediaPlayer in Coroutine](https://github.com/CabbageDevelopment/qasync/issues/85)

### **가상 환경(venv) 미사용 시 충돌**
* **사례**: 가상 환경 없이 시스템에 직접 설치된 파이썬/패키지를 사용할 때 예제 코드가 충돌하는 이슈가 있었습니다.
* **해결책**: 항상 프로젝트별로 가상 환경을 구성하여 패키지 충돌을 방지하는 것이 권장됩니다.
* **관련 링크**: [GitHub Issue #120: Basic example crashes when running without venv](https://github.com/CabbageDevelopment/qasync/issues/120)

---

## **3. 에러 및 예외 처리 문제 ⚠️**

비동기 작업에서 발생하는 예외를 처리하는 방식과 관련된 문제입니다.

### **`asyncio.CancelledError`가 잡히지 않는 문제**
* **원인**: 비동기 태스크가 취소될 때 발생하는 `CancelledError` 예외가 `@asyncSlot` 데코레이터의 에러 핸들러에서 제대로 처리되지 않는다는 보고가 있습니다.
* **해결책**: 해당 슬롯 내에서 직접 `try...except asyncio.CancelledError` 구문을 사용하여 예외를 명시적으로 처리해야 합니다.
* **관련 링크**: [GitHub Issue #126: asyncio.CancelledError not caught in asyncSlot error handler](https://github.com/CabbageDevelopment/qasync/issues/126)

---

## 🛠️ 안전한 QAsync 사용 패턴

### **권장 초기화 패턴**
```python
import asyncio
import sys
from qasync import QApplication, QEventLoop
from PyQt6.QtWidgets import QWidget

async def main():
    app = QApplication(sys.argv)

    # 애플리케이션 종료 이벤트 관리
    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    window = MainWindow()
    window.show()

    # 안전한 종료를 위한 이벤트 대기
    await app_close_event.wait()

if __name__ == "__main__":
    # Python 3.11+ 권장 방법
    asyncio.run(main(), loop_factory=QEventLoop)

    # Python 3.10 이하 호환성
    # import qasync
    # qasync.run(main())
```

### **스레드별 이벤트 루프 설정**
```python
import asyncio
import threading
from qasync import QEventLoop

def setup_qasync_in_thread():
    """별도 스레드에서 QAsync 이벤트 루프 설정"""
    loop = QEventLoop()
    asyncio.set_event_loop(loop)

    try:
        # 비동기 작업 실행
        loop.run_until_complete(async_task())
    finally:
        loop.close()

# 사용법
thread = threading.Thread(target=setup_qasync_in_thread)
thread.start()
```

### **안전한 예외 처리**
```python
from qasync import asyncSlot
import asyncio

@asyncSlot()
async def safe_async_slot(self):
    try:
        await some_async_operation()
    except asyncio.CancelledError:
        # 명시적으로 CancelledError 처리
        self.logger.info("작업이 취소되었습니다")
        return
    except Exception as e:
        self.logger.error(f"예상치 못한 오류: {e}")
        raise
```

---

## 📋 결론

`QAsync`는 `PyQt/PySide`와 `asyncio`를 통합하는 가장 강력하고 성숙한 솔루션입니다. 위에서 언급된 문제들은 대부분 **정확한 초기화 패턴을 따르거나**, **안전한 종료 로직을 추가**하고, **예외 처리를 명시적**으로 하는 것으로 해결할 수 있습니다. 특히 스레드와 관련된 부분은 `asyncio`와 Qt 스레딩 모델을 모두 이해해야 정확한 구현이 가능하므로 주의가 필요합니다.

### **핵심 권장사항**
1. ✅ **가상 환경 사용**: 패키지 충돌 방지
2. ✅ **안전한 초기화**: `asyncio.run(loop_factory=QEventLoop)` 사용
3. ✅ **명시적 종료 처리**: `aboutToQuit` 시그널 활용
4. ✅ **예외 처리**: `CancelledError` 명시적 처리
5. ✅ **스레드 격리**: 별도 스레드에서 이벤트 루프 명시적 설정

---

## 🔗 관련 문서
- `PyQt6_Asyncio_Integration_Patterns.md`: 전체 통합 패턴 가이드
- [QAsync GitHub Repository](https://github.com/CabbageDevelopment/qasync)
- [QAsync PyPI](https://pypi.org/project/qasync/)

---
*작성일: 2025-08-19*
*호가창 WebSocket QAsync 적용 전 위험 요소 분석*

# PyQt6 + Asyncio 통합 패턴 가이드

## 🚨 문제 상황
PyQt6 환경에서 `asyncio.create_task()` 사용 시 **"no running event loop"** 오류 발생

## 🎯 3가지 해결 방법

### 1️⃣ **QAsync 라이브러리 (권장)**
```bash
pip install qasync
```

```python
import asyncio
from qasync import QApplication, QEventLoop
from PyQt6.QtWidgets import QWidget

class MainWindow(QWidget):
    async def async_method(self):
        # 일반적인 asyncio 코드 그대로 사용 가능
        await asyncio.sleep(1)
        return "완료"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    # QAsync 이벤트 루프 사용
    asyncio.run(window.show(), loop_factory=QEventLoop)
```

**장점**:
- ✅ 기존 asyncio 코드 그대로 사용
- ✅ 업계 표준 (1.5k+ 프로젝트 사용)
- ✅ 가장 깔끔한 해결책

---

### 2️⃣ **격리 스레드 패턴 (안전한 방법)**
```python
import asyncio
import threading
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

class AsyncWorker(QObject):
    result_ready = pyqtSignal(object)

    def run_async_task(self, coro):
        def target():
            # 새로운 이벤트 루프에서 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                self.result_ready.emit(result)
            finally:
                loop.close()

        thread = threading.Thread(target=target)
        thread.start()

# 사용법
worker = AsyncWorker()
worker.result_ready.connect(self.handle_result)
worker.run_async_task(some_async_function())
```

**장점**:
- ✅ Qt 이벤트 루프와 완전 분리
- ✅ 기존 아키텍처 유지
- ✅ coin_list_widget.py에서 검증된 방법

---

### 3️⃣ **QThread + moveToThread 패턴 (전통적 방법)**
```python
from PyQt6.QtCore import QThread, QObject, pyqtSignal

class AsyncWorker(QObject):
    finished = pyqtSignal(object)

    def do_work(self):
        # 여기서 동기 작업 수행
        result = self.sync_version_of_async_work()
        self.finished.emit(result)

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.worker = AsyncWorker()

        # Worker를 별도 스레드로 이동
        self.worker.moveToThread(self.thread)

        # 시그널 연결
        self.thread.started.connect(self.worker.do_work)
        self.worker.finished.connect(self.handle_result)
        self.worker.finished.connect(self.thread.quit)

        self.thread.start()
```

**장점**:
- ✅ Qt 공식 권장 패턴
- ✅ 완전한 스레드 안전성
- ✅ 장기적으로 가장 안정적

---

## 📊 비교표

| 방법 | 구현 시간 | 복잡도 | 안정성 | 권장도 |
|------|-----------|---------|---------|---------|
| QAsync | 30분 | ⭐ | ⭐⭐⭐ | 🥇 |
| 격리 스레드 | 15분 | ⭐⭐ | ⭐⭐⭐ | 🥈 |
| QThread | 45분 | ⭐⭐⭐ | ⭐⭐⭐ | 🥉 |

## 🎯 권장사항

1. **신규 개발**: QAsync 사용
2. **기존 코드 유지**: 격리 스레드 패턴
3. **장기 안정성**: QThread 패턴

---

## 🔗 관련 문서
- `coin_list_widget.py`: 격리 스레드 패턴 구현 예시
- `PyQt6_Empty_Widget_Bool_Issue.md`: PyQt6 위젯 Bool 평가 문제
- [QAsync GitHub](https://github.com/CabbageDevelopment/qasync)

---
*작성일: 2025-08-19*
*호가창 WebSocket 자동 갱신 문제 해결 과정에서 정리*

# 🔧 실시간 로깅 관리 탭 설계 문서 (Design Document)

## 📋 개요

본 문서는 기존 환경&로깅 탭의 문제점을 해결하기 위한 새로운 **실시간 로깅 관리 탭**의 기술적 설계를 정의합니다. DDD 아키텍처와 MVP 패턴을 기반으로 Infrastructure Layer 로깅 시스템 v4.0과 완전히 통합된 전용 로깅 관리 UI를 구현합니다.

## 🎯 설계 목표

### 1. 핵심 목표
- **실시간 로그 뷰어**: QPlainTextEdit 기반 고성능 로그 스트림 표시
- **환경변수 통합 제어**: 로깅 시스템의 모든 환경변수 실시간 관리
- **탭 활성화 최적화**: 탭이 활성화될 때만 UI 업데이트 수행
- **LLM 브리핑 제거**: 불필요한 LLM 관련 기능 완전 제거

### 2. 성능 목표
- **로그 추가 지연**: < 10ms (QPlainTextEdit.appendPlainText 활용)
- **메모리 사용량**: 최대 50MB (setMaximumBlockCount로 제한)
- **UI 응답성**: 60 FPS 유지 (QTimer 기반 배치 업데이트)
- **스크롤 성능**: 자동 스크롤 시 끊김 없는 렌더링

## 🏗️ 아키텍처 설계

### 1. DDD 4계층 구조 적용

```
┌─────────────────────────────────────────────────┐
│               Presentation Layer                │
│  ├─ LoggingManagementView (MVP Passive View)    │
│  └─ LoggingManagementPresenter (MVP Presenter)  │
├─────────────────────────────────────────────────┤
│              Application Layer                  │
│  ├─ LoggingManagementUseCase                   │
│  └─ LogViewerService                           │
├─────────────────────────────────────────────────┤
│                Domain Layer                     │
│  ├─ LogEntry (Value Object)                    │
│  ├─ LogLevel (Enum)                            │
│  └─ LoggingConfiguration (Entity)              │
├─────────────────────────────────────────────────┤
│            Infrastructure Layer                 │
│  ├─ LoggingService v4.0 (기존)                 │
│  ├─ LogStreamCapture                           │
│  └─ EnvironmentVariableManager                 │
└─────────────────────────────────────────────────┘
```

### 2. MVP 패턴 적용

```python
# Passive View Pattern
class LoggingManagementView(QWidget):
    """MVP의 Passive View - 순수 UI 관심사만 담당"""

    def __init__(self):
        # UI 구성: 좌우 1:2 분할 레이아웃
        # QSplitter(Qt.Horizontal) 기반
        pass

    def update_log_display(self, log_entries: List[str]) -> None:
        """Presenter에서 호출하는 UI 업데이트 메서드"""
        pass

class LoggingManagementPresenter:
    """MVP의 Presenter - 비즈니스 로직과 UI 연결"""

    def __init__(self, view: LoggingManagementView, use_case: LoggingManagementUseCase):
        self.view = view
        self.use_case = use_case
        self._setup_event_handlers()

    def handle_environment_variable_change(self, var_name: str, value: str) -> None:
        """환경변수 변경 이벤트 처리"""
        pass
```

## 🎨 UI 컴포넌트 설계

### 1. 메인 레이아웃: 좌우 1:2 분할

```python
class LoggingManagementView(QWidget):
    def _setup_ui(self):
        # 메인 레이아웃: 수평 분할
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setSizes([300, 600])  # 1:2 비율

        # 좌측: 환경변수 제어 패널
        self.control_panel = self._create_control_panel()

        # 우측: 실시간 로그 뷰어
        self.log_viewer = self._create_log_viewer()

        self.main_splitter.addWidget(self.control_panel)
        self.main_splitter.addWidget(self.log_viewer)
```

### 2. 좌측 패널: 환경변수 제어

```python
def _create_control_panel(self) -> QWidget:
    """환경변수 제어 패널 생성"""
    panel = QWidget()
    layout = QVBoxLayout()

    # 1. 로그 레벨 제어
    log_level_group = QGroupBox("로그 레벨 제어")
    log_level_layout = QVBoxLayout()

    # UPBIT_LOG_LEVEL 제어
    self.log_level_combo = QComboBox()
    self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    log_level_layout.addWidget(QLabel("UPBIT_LOG_LEVEL:"))
    log_level_layout.addWidget(self.log_level_combo)

    log_level_group.setLayout(log_level_layout)
    layout.addWidget(log_level_group)

    # 2. 출력 제어
    output_group = QGroupBox("출력 제어")
    output_layout = QVBoxLayout()

    # UPBIT_CONSOLE_OUTPUT 제어
    self.console_output_checkbox = QCheckBox("콘솔 출력 활성화")
    output_layout.addWidget(self.console_output_checkbox)

    output_group.setLayout(output_layout)
    layout.addWidget(output_group)

    # 3. 스코프 제어
    scope_group = QGroupBox("로깅 스코프")
    scope_layout = QVBoxLayout()

    # UPBIT_LOG_SCOPE 제어
    self.log_scope_combo = QComboBox()
    self.log_scope_combo.addItems(["silent", "minimal", "normal", "verbose", "debug_all"])
    scope_layout.addWidget(QLabel("UPBIT_LOG_SCOPE:"))
    scope_layout.addWidget(self.log_scope_combo)

    scope_group.setLayout(scope_layout)
    layout.addWidget(scope_group)

    # 4. 컴포넌트 집중 모드
    focus_group = QGroupBox("컴포넌트 집중")
    focus_layout = QVBoxLayout()

    # UPBIT_COMPONENT_FOCUS 제어
    self.component_focus_edit = QLineEdit()
    self.component_focus_edit.setPlaceholderText("컴포넌트명 입력 (비어두면 모든 컴포넌트)")
    focus_layout.addWidget(QLabel("UPBIT_COMPONENT_FOCUS:"))
    focus_layout.addWidget(self.component_focus_edit)

    focus_group.setLayout(focus_layout)
    layout.addWidget(focus_group)

    # 5. 제어 버튼
    button_layout = QHBoxLayout()
    self.apply_btn = QPushButton("설정 적용")
    self.reset_btn = QPushButton("기본값 복원")
    button_layout.addWidget(self.apply_btn)
    button_layout.addWidget(self.reset_btn)
    layout.addLayout(button_layout)

    # 스트레치 추가 (하단 여백)
    layout.addStretch()

    panel.setLayout(layout)
    return panel
```

### 3. 우측 패널: 실시간 로그 뷰어

```python
def _create_log_viewer(self) -> QWidget:
    """실시간 로그 뷰어 생성"""
    viewer_widget = QWidget()
    layout = QVBoxLayout()

    # 툴바
    toolbar = QHBoxLayout()

    # 자동 스크롤 토글
    self.auto_scroll_checkbox = QCheckBox("자동 스크롤")
    self.auto_scroll_checkbox.setChecked(True)
    toolbar.addWidget(self.auto_scroll_checkbox)

    # 로그 필터
    self.filter_edit = QLineEdit()
    self.filter_edit.setPlaceholderText("로그 필터링 (정규식 지원)")
    toolbar.addWidget(QLabel("필터:"))
    toolbar.addWidget(self.filter_edit)

    # 로그 클리어
    self.clear_btn = QPushButton("로그 지우기")
    toolbar.addWidget(self.clear_btn)

    # 로그 저장
    self.save_btn = QPushButton("로그 저장")
    toolbar.addWidget(self.save_btn)

    toolbar.addStretch()
    layout.addLayout(toolbar)

    # 로그 텍스트 뷰어 (QPlainTextEdit)
    self.log_text_edit = QPlainTextEdit()
    self.log_text_edit.setReadOnly(True)
    self.log_text_edit.setMaximumBlockCount(10000)  # 메모리 제한: 최대 10,000줄
    self.log_text_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

    # 폰트 설정 (모노스페이스)
    font = QFont("Consolas, Monaco, monospace")
    font.setPointSize(9)
    self.log_text_edit.setFont(font)

    layout.addWidget(self.log_text_edit)

    # 상태바
    status_layout = QHBoxLayout()
    self.log_count_label = QLabel("로그 개수: 0")
    self.filter_count_label = QLabel("필터링됨: 0")
    status_layout.addWidget(self.log_count_label)
    status_layout.addWidget(self.filter_count_label)
    status_layout.addStretch()
    layout.addLayout(status_layout)

    viewer_widget.setLayout(layout)
    return viewer_widget
```

## 📡 실시간 로그 캡처 시스템

### 1. 로그 스트림 캡처

```python
class LogStreamCapture:
    """Infrastructure Layer의 로깅 시스템에서 로그를 실시간 캡처"""

    def __init__(self):
        self._handlers: List[Callable[[str], None]] = []
        self._setup_log_capture()

    def _setup_log_capture(self):
        """로깅 시스템에 커스텀 핸들러 추가"""
        # Infrastructure 로깅 시스템의 루트 로거에 핸들러 추가
        root_logger = logging.getLogger('upbit_auto_trading')
        self.custom_handler = self._create_stream_handler()
        root_logger.addHandler(self.custom_handler)

    def _create_stream_handler(self) -> logging.Handler:
        """스트림 캡처용 커스텀 핸들러 생성"""
        class StreamCaptureHandler(logging.Handler):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def emit(self, record):
                try:
                    log_entry = self.format(record)
                    self.callback(log_entry)
                except Exception:
                    pass  # 로깅 중 에러 발생 시 무시

        handler = StreamCaptureHandler(self._emit_to_handlers)

        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)

        return handler

    def _emit_to_handlers(self, log_entry: str):
        """캡처된 로그를 등록된 핸들러들에게 전달"""
        for handler in self._handlers:
            try:
                handler(log_entry)
            except Exception:
                pass  # 개별 핸들러 에러는 무시

    def add_handler(self, handler: Callable[[str], None]):
        """로그 핸들러 등록"""
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[str], None]):
        """로그 핸들러 제거"""
        if handler in self._handlers:
            self._handlers.remove(handler)
```

### 2. 배치 업데이트 시스템

```python
class BatchedLogUpdater:
    """성능 최적화를 위한 배치 로그 업데이트"""

    def __init__(self, update_callback: Callable[[List[str]], None]):
        self.update_callback = update_callback
        self._log_buffer: List[str] = []
        self._max_buffer_size = 100
        self._update_interval_ms = 100  # 100ms마다 업데이트

        # QTimer 설정
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._flush_buffer)
        self.update_timer.start(self._update_interval_ms)

    def add_log_entry(self, log_entry: str):
        """로그 엔트리 추가 (버퍼링)"""
        self._log_buffer.append(log_entry)

        # 버퍼가 가득 차면 즉시 플러시
        if len(self._log_buffer) >= self._max_buffer_size:
            self._flush_buffer()

    def _flush_buffer(self):
        """버퍼의 로그들을 UI에 업데이트"""
        if self._log_buffer:
            # 복사본 생성 후 버퍼 클리어
            logs_to_update = self._log_buffer.copy()
            self._log_buffer.clear()

            # UI 업데이트 콜백 호출
            self.update_callback(logs_to_update)

    def set_update_interval(self, interval_ms: int):
        """업데이트 간격 설정"""
        self._update_interval_ms = interval_ms
        self.update_timer.setInterval(interval_ms)

    def pause_updates(self):
        """업데이트 일시 정지"""
        self.update_timer.stop()

    def resume_updates(self):
        """업데이트 재개"""
        self.update_timer.start(self._update_interval_ms)
```

## 🎛️ 환경변수 관리 시스템

### 1. 환경변수 매니저

```python
import os
from typing import Dict, Optional, Callable

class EnvironmentVariableManager:
    """로깅 시스템의 환경변수 실시간 관리"""

    # 로깅 시스템이 사용하는 환경변수들
    LOGGING_ENV_VARS = {
        'UPBIT_LOG_LEVEL': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'UPBIT_CONSOLE_OUTPUT': ['true', 'false'],
        'UPBIT_LOG_SCOPE': ['silent', 'minimal', 'normal', 'verbose', 'debug_all'],
        'UPBIT_COMPONENT_FOCUS': None,  # 자유 입력
    }

    def __init__(self):
        self._change_callbacks: List[Callable[[str, str], None]] = []
        self._original_values: Dict[str, Optional[str]] = {}
        self._save_original_values()

    def _save_original_values(self):
        """원본 환경변수 값들 백업"""
        for var_name in self.LOGGING_ENV_VARS.keys():
            self._original_values[var_name] = os.environ.get(var_name)

    def get_current_values(self) -> Dict[str, Optional[str]]:
        """현재 환경변수 값들 조회"""
        return {
            var_name: os.environ.get(var_name)
            for var_name in self.LOGGING_ENV_VARS.keys()
        }

    def set_variable(self, var_name: str, value: str) -> bool:
        """환경변수 설정"""
        if var_name not in self.LOGGING_ENV_VARS:
            return False

        # 유효성 검사
        valid_values = self.LOGGING_ENV_VARS[var_name]
        if valid_values and value not in valid_values:
            return False

        # 환경변수 설정
        if value:
            os.environ[var_name] = value
        else:
            # 빈 값이면 환경변수 제거
            os.environ.pop(var_name, None)

        # 변경 알림
        self._notify_change(var_name, value)
        return True

    def reset_to_defaults(self):
        """기본값으로 복원"""
        for var_name in self.LOGGING_ENV_VARS.keys():
            original_value = self._original_values.get(var_name)
            if original_value:
                os.environ[var_name] = original_value
            else:
                os.environ.pop(var_name, None)

            self._notify_change(var_name, original_value or "")

    def add_change_callback(self, callback: Callable[[str, str], None]):
        """환경변수 변경 콜백 등록"""
        self._change_callbacks.append(callback)

    def _notify_change(self, var_name: str, new_value: str):
        """환경변수 변경 알림"""
        for callback in self._change_callbacks:
            try:
                callback(var_name, new_value)
            except Exception:
                pass  # 콜백 에러는 무시

    def get_default_values(self) -> Dict[str, str]:
        """기본 환경변수 값들 반환"""
        return {
            'UPBIT_LOG_LEVEL': 'INFO',
            'UPBIT_CONSOLE_OUTPUT': 'true',
            'UPBIT_LOG_SCOPE': 'normal',
            'UPBIT_COMPONENT_FOCUS': '',
        }
```

### 2. 환경변수 UI 바인딩

```python
class EnvironmentControlBinding:
    """환경변수와 UI 컨트롤 바인딩"""

    def __init__(self, view: LoggingManagementView, env_manager: EnvironmentVariableManager):
        self.view = view
        self.env_manager = env_manager
        self._setup_bindings()

    def _setup_bindings(self):
        """UI 컨트롤과 환경변수 바인딩 설정"""
        # 현재 값으로 UI 초기화
        self._update_ui_from_environment()

        # UI 변경 이벤트 연결
        self.view.log_level_combo.currentTextChanged.connect(
            lambda value: self._handle_env_change('UPBIT_LOG_LEVEL', value)
        )

        self.view.console_output_checkbox.toggled.connect(
            lambda checked: self._handle_env_change('UPBIT_CONSOLE_OUTPUT', 'true' if checked else 'false')
        )

        self.view.log_scope_combo.currentTextChanged.connect(
            lambda value: self._handle_env_change('UPBIT_LOG_SCOPE', value)
        )

        self.view.component_focus_edit.textChanged.connect(
            lambda text: self._handle_env_change('UPBIT_COMPONENT_FOCUS', text)
        )

        # 버튼 이벤트
        self.view.apply_btn.clicked.connect(self._apply_all_changes)
        self.view.reset_btn.clicked.connect(self._reset_to_defaults)

        # 환경변수 변경 알림 받기
        self.env_manager.add_change_callback(self._on_environment_changed)

    def _update_ui_from_environment(self):
        """현재 환경변수 값으로 UI 업데이트"""
        current_values = self.env_manager.get_current_values()

        # 로그 레벨
        log_level = current_values.get('UPBIT_LOG_LEVEL', 'INFO')
        index = self.view.log_level_combo.findText(log_level)
        if index >= 0:
            self.view.log_level_combo.setCurrentIndex(index)

        # 콘솔 출력
        console_output = current_values.get('UPBIT_CONSOLE_OUTPUT', 'true')
        self.view.console_output_checkbox.setChecked(console_output == 'true')

        # 로그 스코프
        log_scope = current_values.get('UPBIT_LOG_SCOPE', 'normal')
        index = self.view.log_scope_combo.findText(log_scope)
        if index >= 0:
            self.view.log_scope_combo.setCurrentIndex(index)

        # 컴포넌트 집중
        component_focus = current_values.get('UPBIT_COMPONENT_FOCUS', '')
        self.view.component_focus_edit.setText(component_focus)

    def _handle_env_change(self, var_name: str, value: str):
        """UI에서 환경변수 변경 시 처리"""
        success = self.env_manager.set_variable(var_name, value)
        if not success:
            # 유효하지 않은 값인 경우 UI 복원
            self._update_ui_from_environment()

    def _apply_all_changes(self):
        """모든 변경사항 적용"""
        # 현재 UI 값들로 환경변수 설정
        values = {
            'UPBIT_LOG_LEVEL': self.view.log_level_combo.currentText(),
            'UPBIT_CONSOLE_OUTPUT': 'true' if self.view.console_output_checkbox.isChecked() else 'false',
            'UPBIT_LOG_SCOPE': self.view.log_scope_combo.currentText(),
            'UPBIT_COMPONENT_FOCUS': self.view.component_focus_edit.text().strip(),
        }

        for var_name, value in values.items():
            self.env_manager.set_variable(var_name, value)

    def _reset_to_defaults(self):
        """기본값으로 복원"""
        self.env_manager.reset_to_defaults()
        self._update_ui_from_environment()

    def _on_environment_changed(self, var_name: str, new_value: str):
        """환경변수 외부 변경 시 UI 업데이트"""
        self._update_ui_from_environment()
```

## 🚀 성능 최적화 전략

### 1. QPlainTextEdit 최적화

```python
class OptimizedLogViewer(QPlainTextEdit):
    """성능 최적화된 로그 뷰어"""

    def __init__(self):
        super().__init__()
        self._setup_optimization()

    def _setup_optimization(self):
        """성능 최적화 설정"""
        # 1. 최대 블록 수 제한 (메모리 사용량 제한)
        self.setMaximumBlockCount(10000)

        # 2. 라인 래핑 모드 설정
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)

        # 3. 수직 스크롤바 정책
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # 4. 읽기 전용 모드
        self.setReadOnly(True)

        # 5. 배경 자동 채우기 비활성화 (성능 향상)
        self.setAutoFillBackground(False)

        # 6. 텍스트 상호작용 제한 (선택만 허용)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    def append_logs_batch(self, log_entries: List[str]):
        """배치로 로그 추가 (성능 최적화)"""
        if not log_entries:
            return

        # 현재 스크롤 위치 저장
        scroll_bar = self.verticalScrollBar()
        at_bottom = scroll_bar.value() == scroll_bar.maximum()

        # 배치로 텍스트 추가
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for log_entry in log_entries:
            cursor.insertText(log_entry + '\n')

        # 자동 스크롤 처리
        if at_bottom:
            self.ensureCursorVisible()

    def clear_logs(self):
        """로그 클리어"""
        self.clear()

    def get_log_count(self) -> int:
        """현재 로그 라인 수 반환"""
        return self.document().blockCount()
```

### 2. 탭 활성화 최적화

```python
class TabActivationOptimizer:
    """탭 활성화 상태 기반 업데이트 최적화"""

    def __init__(self, tab_widget: QTabWidget, tab_index: int):
        self.tab_widget = tab_widget
        self.tab_index = tab_index
        self._is_active = False
        self._pending_updates: List[str] = []

        # 탭 변경 이벤트 연결
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, current_index: int):
        """탭 변경 이벤트 처리"""
        was_active = self._is_active
        self._is_active = (current_index == self.tab_index)

        # 탭이 활성화된 경우 대기 중인 업데이트 처리
        if not was_active and self._is_active:
            self._process_pending_updates()

    def add_update(self, log_entry: str):
        """업데이트 추가 (탭 활성화 상태 고려)"""
        if self._is_active:
            # 탭이 활성화된 상태면 즉시 처리
            self._process_update(log_entry)
        else:
            # 탭이 비활성화된 상태면 대기열에 추가
            self._pending_updates.append(log_entry)

            # 대기열 크기 제한 (메모리 보호)
            if len(self._pending_updates) > 1000:
                self._pending_updates = self._pending_updates[-500:]  # 최근 500개만 유지

    def _process_pending_updates(self):
        """대기 중인 업데이트들 처리"""
        if self._pending_updates:
            # 배치로 처리
            self._process_updates_batch(self._pending_updates)
            self._pending_updates.clear()

    def _process_update(self, log_entry: str):
        """개별 업데이트 처리 (서브클래스에서 구현)"""
        raise NotImplementedError

    def _process_updates_batch(self, log_entries: List[str]):
        """배치 업데이트 처리 (서브클래스에서 구현)"""
        raise NotImplementedError

    def is_active(self) -> bool:
        """탭 활성화 상태 반환"""
        return self._is_active
```

## 🔌 Infrastructure 통합

### 1. LLM 브리핑 제거 과정

```python
class LLMBriefingRemover:
    """Infrastructure 로깅 시스템에서 LLM 브리핑 기능 제거"""

    def __init__(self, logging_service: LoggingService):
        self.logging_service = logging_service

    def remove_llm_features(self):
        """LLM 관련 기능들 제거"""

        # 1. LLM 브리핑 핸들러 제거
        self._remove_llm_handlers()

        # 2. LLM 관련 포맷터 제거
        self._remove_llm_formatters()

        # 3. LLM 관련 환경변수 정리
        self._cleanup_llm_env_vars()

        # 4. LLM 관련 설정 제거
        self._remove_llm_config()

    def _remove_llm_handlers(self):
        """LLM 브리핑 핸들러들 제거"""
        # 모든 로거에서 LLM 관련 핸들러 제거
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)

            # LLM 관련 핸들러 필터링
            handlers_to_remove = [
                handler for handler in logger.handlers
                if hasattr(handler, '__class__') and 'LLM' in handler.__class__.__name__
            ]

            for handler in handlers_to_remove:
                logger.removeHandler(handler)

    def _remove_llm_formatters(self):
        """LLM 관련 포맷터 제거"""
        # LLM 브리핑용 특수 포맷터들 제거
        pass  # 구체적인 구현은 기존 로깅 시스템 구조에 따라 결정

    def _cleanup_llm_env_vars(self):
        """LLM 관련 환경변수 정리"""
        llm_env_vars = [
            'UPBIT_LLM_BRIEFING_ENABLED',
            'UPBIT_LLM_BRIEFING_LEVEL',
            'UPBIT_LLM_CONTEXT_SIZE',
            # 추가 LLM 관련 환경변수들
        ]

        for var_name in llm_env_vars:
            os.environ.pop(var_name, None)

    def _remove_llm_config(self):
        """LLM 관련 설정 제거"""
        # 로깅 서비스의 LLM 관련 설정들 비활성화
        if hasattr(self.logging_service, '_llm_briefing_enabled'):
            self.logging_service._llm_briefing_enabled = False
```

### 2. 기존 로깅 시스템과의 통합

```python
class LoggingSystemIntegrator:
    """기존 Infrastructure 로깅 시스템과의 통합"""

    def __init__(self):
        self.logging_service = get_logging_service()
        self.stream_capture = LogStreamCapture()
        self.env_manager = EnvironmentVariableManager()

    def setup_integration(self) -> tuple[LogStreamCapture, EnvironmentVariableManager]:
        """로깅 시스템 통합 설정"""

        # 1. LLM 브리핑 기능 제거
        llm_remover = LLMBriefingRemover(self.logging_service)
        llm_remover.remove_llm_features()

        # 2. 스트림 캡처 설정
        self._setup_stream_capture()

        # 3. 환경변수 관리 연결
        self._setup_environment_integration()

        return self.stream_capture, self.env_manager

    def _setup_stream_capture(self):
        """스트림 캡처 설정"""
        # Infrastructure 로깅 시스템의 루트 로거에 연결
        root_logger = logging.getLogger('upbit_auto_trading')

        # 기존 핸들러들 확인
        existing_handlers = root_logger.handlers.copy()

        # 스트림 캡처 핸들러 추가
        capture_handler = self.stream_capture._create_stream_handler()
        root_logger.addHandler(capture_handler)

        # 로그 레벨 동기화
        self._sync_log_levels()

    def _setup_environment_integration(self):
        """환경변수 관리 통합"""
        # 환경변수 변경 시 로깅 시스템에 알림
        def on_env_change(var_name: str, new_value: str):
            if var_name == 'UPBIT_LOG_LEVEL':
                self._update_log_level(new_value)
            elif var_name == 'UPBIT_LOG_SCOPE':
                self._update_log_scope(new_value)
            elif var_name == 'UPBIT_COMPONENT_FOCUS':
                self._update_component_focus(new_value)

        self.env_manager.add_change_callback(on_env_change)

    def _sync_log_levels(self):
        """로그 레벨 동기화"""
        current_level = os.environ.get('UPBIT_LOG_LEVEL', 'INFO')
        self._update_log_level(current_level)

    def _update_log_level(self, level_name: str):
        """로그 레벨 업데이트"""
        level = getattr(logging, level_name.upper(), logging.INFO)

        # 모든 관련 로거 레벨 업데이트
        root_logger = logging.getLogger('upbit_auto_trading')
        root_logger.setLevel(level)

        # 서브 로거들도 업데이트
        for logger_name in logging.Logger.manager.loggerDict:
            if logger_name.startswith('upbit_auto_trading'):
                logger = logging.getLogger(logger_name)
                logger.setLevel(level)

    def _update_log_scope(self, scope_name: str):
        """로그 스코프 업데이트"""
        # LogScope enum 값으로 변환
        try:
            scope = LogScope(scope_name)
            self.logging_service.set_scope(scope)
        except ValueError:
            pass  # 유효하지 않은 스코프는 무시

    def _update_component_focus(self, component_name: str):
        """컴포넌트 집중 모드 업데이트"""
        # 특정 컴포넌트에만 집중하는 필터 설정
        if component_name:
            self._setup_component_filter(component_name)
        else:
            self._remove_component_filter()

    def _setup_component_filter(self, component_name: str):
        """컴포넌트 필터 설정"""
        class ComponentFilter(logging.Filter):
            def __init__(self, target_component: str):
                super().__init__()
                self.target_component = target_component

            def filter(self, record):
                return self.target_component in record.name

        # 기존 컴포넌트 필터 제거
        self._remove_component_filter()

        # 새 필터 추가
        component_filter = ComponentFilter(component_name)
        root_logger = logging.getLogger('upbit_auto_trading')

        for handler in root_logger.handlers:
            handler.addFilter(component_filter)

    def _remove_component_filter(self):
        """컴포넌트 필터 제거"""
        root_logger = logging.getLogger('upbit_auto_trading')

        for handler in root_logger.handlers:
            # ComponentFilter 타입의 필터들 제거
            filters_to_remove = [
                f for f in handler.filters
                if f.__class__.__name__ == 'ComponentFilter'
            ]

            for filter_obj in filters_to_remove:
                handler.removeFilter(filter_obj)
```

## 📋 Use Case 구현

```python
class LoggingManagementUseCase:
    """로깅 관리 탭의 비즈니스 로직"""

    def __init__(self):
        self.integrator = LoggingSystemIntegrator()
        self.stream_capture, self.env_manager = self.integrator.setup_integration()
        self._log_handlers: List[Callable[[List[str]], None]] = []

    def register_log_handler(self, handler: Callable[[List[str]], None]):
        """로그 핸들러 등록"""
        self._log_handlers.append(handler)

        # 스트림 캡처에 연결
        self.stream_capture.add_handler(self._handle_single_log)

    def _handle_single_log(self, log_entry: str):
        """단일 로그 엔트리 처리"""
        # 배치 처리를 위해 리스트로 감싸서 전달
        for handler in self._log_handlers:
            try:
                handler([log_entry])
            except Exception:
                pass  # 핸들러 에러는 무시

    def update_environment_variable(self, var_name: str, value: str) -> bool:
        """환경변수 업데이트"""
        return self.env_manager.set_variable(var_name, value)

    def get_current_environment_values(self) -> Dict[str, Optional[str]]:
        """현재 환경변수 값들 조회"""
        return self.env_manager.get_current_values()

    def reset_environment_to_defaults(self):
        """환경변수를 기본값으로 복원"""
        self.env_manager.reset_to_defaults()

    def get_log_statistics(self) -> Dict[str, Any]:
        """로깅 통계 정보"""
        return {
            'total_logs': 0,  # 구현 필요
            'log_levels': {},  # 레벨별 통계
            'memory_usage': 0,  # 메모리 사용량
            'active_components': []  # 활성 컴포넌트들
        }

    def save_logs_to_file(self, file_path: str, log_content: str) -> bool:
        """로그를 파일로 저장"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            return True
        except Exception:
            return False

    def apply_log_filter(self, filter_pattern: str, log_entries: List[str]) -> List[str]:
        """로그 필터링 적용"""
        if not filter_pattern:
            return log_entries

        try:
            import re
            pattern = re.compile(filter_pattern, re.IGNORECASE)
            return [entry for entry in log_entries if pattern.search(entry)]
        except re.error:
            # 유효하지 않은 정규식이면 단순 문자열 매칭
            return [entry for entry in log_entries if filter_pattern.lower() in entry.lower()]
```

## 🔗 최종 통합

```python
class LoggingManagementPresenter:
    """MVP 패턴의 Presenter - 최종 통합"""

    def __init__(self, view: LoggingManagementView):
        self.view = view
        self.use_case = LoggingManagementUseCase()

        # 성능 최적화 컴포넌트들
        self.batched_updater = BatchedLogUpdater(self._update_log_display)
        self.tab_optimizer = None  # 탭 위젯 설정 후 초기화

        # 환경변수 바인딩
        self.env_binding = EnvironmentControlBinding(self.view, self.use_case.env_manager)

        self._setup_event_handlers()
        self._initialize_ui()

    def set_tab_context(self, tab_widget: QTabWidget, tab_index: int):
        """탭 컨텍스트 설정"""
        self.tab_optimizer = LoggingTabOptimizer(
            tab_widget, tab_index, self.batched_updater
        )

        # Use Case에 로그 핸들러 등록
        self.use_case.register_log_handler(self.tab_optimizer.add_update)

    def _setup_event_handlers(self):
        """이벤트 핸들러 설정"""
        # 로그 뷰어 관련
        self.view.clear_btn.clicked.connect(self._clear_logs)
        self.view.save_btn.clicked.connect(self._save_logs)
        self.view.filter_edit.textChanged.connect(self._apply_filter)

        # 자동 스크롤 토글
        self.view.auto_scroll_checkbox.toggled.connect(
            self._toggle_auto_scroll
        )

    def _initialize_ui(self):
        """UI 초기화"""
        # 현재 환경변수 값으로 UI 초기화
        current_values = self.use_case.get_current_environment_values()
        self.env_binding._update_ui_from_environment()

        # 상태바 초기화
        self._update_status_display()

    def _update_log_display(self, log_entries: List[str]):
        """로그 디스플레이 업데이트"""
        if not log_entries:
            return

        # 필터 적용
        filtered_logs = self._apply_current_filter(log_entries)

        if filtered_logs:
            # 로그 뷰어에 추가
            self.view.log_text_edit.append_logs_batch(filtered_logs)

            # 상태 업데이트
            self._update_status_display()

    def _apply_current_filter(self, log_entries: List[str]) -> List[str]:
        """현재 필터 적용"""
        filter_text = self.view.filter_edit.text().strip()
        if not filter_text:
            return log_entries

        return self.use_case.apply_log_filter(filter_text, log_entries)

    def _clear_logs(self):
        """로그 클리어"""
        self.view.log_text_edit.clear_logs()
        self._update_status_display()

    def _save_logs(self):
        """로그 저장"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.view,
            "로그 저장",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text files (*.txt);;All files (*.*)"
        )

        if file_path:
            log_content = self.view.log_text_edit.toPlainText()
            success = self.use_case.save_logs_to_file(file_path, log_content)

            if success:
                # 성공 메시지 표시
                QMessageBox.information(self.view, "저장 완료", f"로그가 저장되었습니다:\n{file_path}")
            else:
                # 에러 메시지 표시
                QMessageBox.warning(self.view, "저장 실패", "로그 저장 중 오류가 발생했습니다.")

    def _apply_filter(self):
        """필터 적용 (실시간)"""
        # 현재 로그 내용 다시 필터링
        all_logs = self.view.log_text_edit.toPlainText().split('\n')
        filtered_logs = self._apply_current_filter(all_logs)

        # 뷰어 업데이트
        self.view.log_text_edit.clear_logs()
        if filtered_logs:
            self.view.log_text_edit.append_logs_batch(filtered_logs)

        self._update_status_display()

    def _toggle_auto_scroll(self, enabled: bool):
        """자동 스크롤 토글"""
        # 로그 뷰어의 자동 스크롤 설정
        if hasattr(self.view.log_text_edit, 'set_auto_scroll'):
            self.view.log_text_edit.set_auto_scroll(enabled)

    def _update_status_display(self):
        """상태 표시 업데이트"""
        log_count = self.view.log_text_edit.get_log_count()
        self.view.log_count_label.setText(f"로그 개수: {log_count}")

        # 필터링된 개수는 현재 표시된 개수로 계산
        # (실제 구현에서는 더 정확한 계산 필요)
        filter_text = self.view.filter_edit.text().strip()
        if filter_text:
            self.view.filter_count_label.setText(f"필터링됨: {log_count}")
        else:
            self.view.filter_count_label.setText("필터링됨: 0")


class LoggingTabOptimizer(TabActivationOptimizer):
    """로깅 탭 전용 최적화"""

    def __init__(self, tab_widget: QTabWidget, tab_index: int, batched_updater: BatchedLogUpdater):
        super().__init__(tab_widget, tab_index)
        self.batched_updater = batched_updater

    def _process_update(self, log_entry: str):
        """개별 업데이트 처리"""
        self.batched_updater.add_log_entry(log_entry)

    def _process_updates_batch(self, log_entries: List[str]):
        """배치 업데이트 처리"""
        for log_entry in log_entries:
            self.batched_updater.add_log_entry(log_entry)
```

## 📁 파일 구조

```
upbit_auto_trading/ui/desktop/screens/settings/logging_management/
├── __init__.py
├── logging_management_view.py          # MVP View
├── logging_management_presenter.py     # MVP Presenter
└── components/
    ├── __init__.py
    ├── optimized_log_viewer.py         # 최적화된 로그 뷰어
    ├── environment_control_panel.py    # 환경변수 제어 패널
    ├── batched_log_updater.py         # 배치 로그 업데이터
    └── tab_activation_optimizer.py    # 탭 활성화 최적화

upbit_auto_trading/application/use_cases/logging_management/
├── __init__.py
└── logging_management_use_case.py     # Use Case

upbit_auto_trading/infrastructure/logging/integration/
├── __init__.py
├── log_stream_capture.py              # 로그 스트림 캡처
├── environment_variable_manager.py    # 환경변수 관리
├── logging_system_integrator.py       # 시스템 통합
└── llm_briefing_remover.py           # LLM 브리핑 제거
```

## 🧪 테스트 전략

### 1. 단위 테스트

```python
# tests/ui/desktop/screens/settings/logging_management/test_logging_management_presenter.py
import pytest
from unittest.mock import Mock, patch
from upbit_auto_trading.ui.desktop.screens.settings.logging_management import LoggingManagementPresenter

class TestLoggingManagementPresenter:
    def test_environment_variable_update(self):
        """환경변수 업데이트 테스트"""
        pass

    def test_log_filtering(self):
        """로그 필터링 테스트"""
        pass

    def test_batch_update_performance(self):
        """배치 업데이트 성능 테스트"""
        pass
```

### 2. 통합 테스트

```python
# tests/integration/test_logging_system_integration.py
import pytest
from upbit_auto_trading.infrastructure.logging.integration import LoggingSystemIntegrator

class TestLoggingSystemIntegration:
    def test_stream_capture_integration(self):
        """스트림 캡처 통합 테스트"""
        pass

    def test_environment_variable_sync(self):
        """환경변수 동기화 테스트"""
        pass

    def test_llm_briefing_removal(self):
        """LLM 브리핑 제거 테스트"""
        pass
```

### 3. 성능 테스트

```python
# tests/performance/test_logging_tab_performance.py
import pytest
import time
from upbit_auto_trading.ui.desktop.screens.settings.logging_management import LoggingManagementPresenter

class TestLoggingTabPerformance:
    def test_log_append_performance(self):
        """로그 추가 성능 테스트 (< 10ms)"""
        pass

    def test_memory_usage_limit(self):
        """메모리 사용량 제한 테스트 (< 50MB)"""
        pass

    def test_ui_responsiveness(self):
        """UI 응답성 테스트 (60 FPS)"""
        pass
```

## 📈 성공 지표

### 1. 기능적 지표
- ✅ **실시간 로그 표시**: 모든 Infrastructure 로그가 실시간으로 표시됨
- ✅ **환경변수 제어**: 모든 로깅 환경변수가 UI에서 실시간 제어 가능
- ✅ **LLM 브리핑 제거**: LLM 관련 기능이 완전히 제거됨
- ✅ **탭 최적화**: 비활성 탭에서 성능 저하 없음

### 2. 성능 지표
- ✅ **로그 추가 지연 < 10ms**: QPlainTextEdit.appendPlainText 최적화
- ✅ **메모리 사용량 < 50MB**: setMaximumBlockCount(10000) 제한
- ✅ **UI 응답성 60 FPS**: QTimer 기반 배치 업데이트
- ✅ **스크롤 성능**: 끊김 없는 자동 스크롤

### 3. 사용성 지표
- ✅ **직관적 UI**: 좌우 1:2 분할로 명확한 기능 분리
- ✅ **실시간 피드백**: 환경변수 변경 시 즉시 로그에 반영
- ✅ **필터링 기능**: 정규식 지원하는 실시간 로그 필터
- ✅ **로그 관리**: 클리어, 저장, 통계 기능

## 🔄 향후 확장 계획

### 1. 고급 필터링
- 시간 범위 필터
- 로그 레벨별 색상 구분
- 즐겨찾기 필터 패턴

### 2. 로그 분석
- 로그 패턴 분석
- 에러 빈도 통계
- 성능 메트릭 표시

### 3. 내보내기 기능
- CSV/JSON 포맷 지원
- 압축 파일 생성
- 자동 백업 기능

---

## 📋 구현 체크리스트

- [ ] **Infrastructure 통합**: LoggingSystemIntegrator 구현
- [ ] **LLM 브리핑 제거**: LLMBriefingRemover 구현
- [ ] **스트림 캡처**: LogStreamCapture 구현
- [ ] **환경변수 관리**: EnvironmentVariableManager 구현
- [ ] **MVP View**: LoggingManagementView 구현
- [ ] **MVP Presenter**: LoggingManagementPresenter 구현
- [ ] **Use Case**: LoggingManagementUseCase 구현
- [ ] **성능 최적화**: BatchedLogUpdater, TabActivationOptimizer 구현
- [ ] **UI 통합**: 기존 설정 화면에 탭 추가
- [ ] **테스트 작성**: 단위/통합/성능 테스트
- [ ] **문서화**: 구현 완료 후 사용자 가이드 작성

이 설계 문서는 DDD 아키텍처와 MVP 패턴을 엄격히 준수하며, Infrastructure Layer 로깅 시스템 v4.0과 완전히 통합된 고성능 실시간 로깅 관리 탭을 구현하기 위한 기술적 청사진입니다.

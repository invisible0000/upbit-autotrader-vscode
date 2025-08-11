# 환경 프로파일 탭 재디자인 설계 문서

## 개요

본 문서는 환경 프로파일 탭의 좌우 분할 레이아웃 재디자인에 대한 상세 설계를 다룹니다. 기존 DDD 아키텍처와 Infrastructure 로깅 시스템 v4.0을 완전히 준수하면서 현대적이고 직관적인 UI/UX를 제공하는 시스템을 설계합니다.

## 아키텍처 설계

### 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                 Environment Profile Tab                    │
├─────────────────────┬───────────────────────────────────────┤
│   Profile Selector  │        YAML Editor & Viewer          │
│      (1:2 비율)      │            (2:2 비율)                │
│                     │                                       │
│  ┌───────────────┐  │  ┌─────────────────────────────────┐  │
│  │ Quick Buttons │  │  │     Status Label Area           │  │
│  │ 🔧 🧪 🚀     │  │  │ 🟢 현재환경: Development        │  │
│  └───────────────┘  │  └─────────────────────────────────┘  │
│                     │                                       │
│  ┌───────────────┐  │  ┌─────────────────────────────────┐  │
│  │ Profile Combo │  │  │                                 │  │
│  │ [Development] │  │  │       YAML Editor               │  │
│  └───────────────┘  │  │   (구문 강조, 모노스페이스)       │  │
│                     │  │                                 │  │
│  ┌───────────────┐  │  │    # Development Environment    │  │
│  │  Action Btns  │  │  │    logging:                     │  │
│  │ [전환적용]     │  │  │      level: "DEBUG"             │  │
│  │ [커스텀저장]   │  │  │      console_enabled: true      │  │
│  │ [삭제]        │  │  │      ...                        │  │
│  └───────────────┘  │  │                                 │  │
│                     │  └─────────────────────────────────┘  │
│                     │                                       │
│                     │  ┌─────────────────────────────────┐  │
│                     │  │     Control Buttons             │  │
│                     │  │  [편집] [취소] [저장]            │  │
│                     │  └─────────────────────────────────┘  │
└─────────────────────┴───────────────────────────────────────┘
```

### DDD 계층별 설계

#### Presentation Layer
```
upbit_auto_trading/ui/desktop/screens/settings/environment_logging/
├── widgets/
│   ├── environment_logging_redesigned_widget.py    # 메인 탭 위젯
│   ├── profile_selector_section.py                # 좌측 선택기 (1/3)
│   ├── yaml_editor_section.py                     # 우측 편집기 (2/3)
│   ├── quick_environment_buttons.py               # 퀵 환경 버튼
│   ├── profile_management_panel.py                # 프로파일 관리 패널
│   ├── yaml_syntax_highlighter.py                # YAML 구문 강조
│   ├── profile_metadata_dialog.py                # 메타데이터 편집 다이얼로그
│   └── __init__.py
└── presenters/
    ├── environment_profile_redesigned_presenter.py
    └── __init__.py
```

#### Application Layer
```
upbit_auto_trading/application/services/
├── config_profile_service.py                  # 기존 서비스 확장
└── use_cases/
    ├── profile_editor_use_case.py             # 프로파일 편집 로직
    ├── temp_file_management_use_case.py       # temp 파일 관리
    └── profile_metadata_use_case.py           # 메타데이터 관리
```

#### Domain Layer
```
upbit_auto_trading/domain/profile_management/
├── entities/
│   ├── profile_editor_session.py              # 편집 세션 엔티티
│   └── profile_metadata.py                    # 프로파일 메타데이터
├── value_objects/
│   ├── profile_display_name.py                # 표시명 VO
│   └── yaml_content.py                        # YAML 컨텐츠 VO
└── services/
    └── profile_validation_service.py          # 프로파일 검증
```

#### Infrastructure Layer
```
upbit_auto_trading/infrastructure/
├── profile_storage/
│   ├── temp_file_manager.py                   # temp 파일 관리
│   └── profile_metadata_repository.py        # 메타데이터 저장소
└── yaml_processing/
    ├── yaml_parser.py                         # YAML 파싱
    └── yaml_validator.py                      # YAML 검증
```

## UI 컴포넌트 상세 설계

### 1. 메인 위젯 (EnvironmentLoggingRedesignedWidget)

```python
class EnvironmentLoggingRedesignedWidget(QWidget):
    """환경 프로파일 재디자인 메인 위젯"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EnvironmentLoggingRedesigned")

        # MVP 패턴 초기화
        self.presenter = EnvironmentProfileRedesignedPresenter(self)

        # UI 구성
        self._setup_splitter_layout()
        self._setup_profile_selector()
        self._setup_yaml_editor()
        self._connect_signals()

    def _setup_splitter_layout(self):
        """좌우 분할 레이아웃 설정 (1:2 비율)"""
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("environment_profile_splitter")

        # 좌측: 프로파일 선택기
        self.profile_selector = ProfileSelectorSection()
        self.main_splitter.addWidget(self.profile_selector)

        # 우측: YAML 편집기
        self.yaml_editor = YamlEditorSection()
        self.main_splitter.addWidget(self.yaml_editor)

        # 비율 설정 (1:2)
        self.main_splitter.setSizes([300, 600])
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 2)

        # 최소 크기 설정
        self.profile_selector.setMinimumWidth(250)
        self.yaml_editor.setMinimumWidth(400)

        # 메인 레이아웃
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.main_splitter)
```

### 2. 프로파일 선택기 섹션 (ProfileSelectorSection)

```python
class ProfileSelectorSection(QWidget):
    """좌측 프로파일 선택 섹션"""

    # 시그널 정의
    profile_selected = pyqtSignal(str)          # 프로파일 선택
    environment_quick_switch = pyqtSignal(str)  # 퀵 환경 전환
    profile_apply_requested = pyqtSignal(str)   # 프로파일 적용 요청
    custom_save_requested = pyqtSignal()        # 커스텀 저장 요청
    profile_delete_requested = pyqtSignal(str)  # 프로파일 삭제 요청

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProfileSelectorSection")

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 퀵 환경 선택 버튼
        self._create_quick_environment_buttons(layout)

        # 구분선
        layout.addWidget(self._create_separator())

        # 프로파일 선택 섹션
        self._create_profile_selection_section(layout)

        # 구분선
        layout.addWidget(self._create_separator())

        # 액션 버튼 섹션
        self._create_action_buttons_section(layout)

        layout.addStretch()

    def _create_quick_environment_buttons(self, parent_layout):
        """퀵 환경 선택 버튼 생성"""
        # 섹션 제목
        title_label = QLabel("🚀 빠른 환경 전환")
        title_label.setObjectName("section_title")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        parent_layout.addWidget(title_label)

        # 버튼 그리드 (1x3)
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(8)

        # 환경별 버튼 설정
        self.environment_buttons = {}
        environments = {
            'development': {
                'icon': '🔧',
                'name': 'Development',
                'color': '#4CAF50',  # 녹색
                'description': '개발환경'
            },
            'testing': {
                'icon': '🧪',
                'name': 'Testing',
                'color': '#FF9800',  # 주황색
                'description': '테스트환경'
            },
            'production': {
                'icon': '🚀',
                'name': 'Production',
                'color': '#F44336',  # 빨간색
                'description': '운영환경'
            }
        }

        for i, (env_key, env_data) in enumerate(environments.items()):
            btn = QPushButton(f"{env_data['icon']} {env_data['name']}")
            btn.setObjectName(f"quick_env_btn_{env_key}")
            btn.setToolTip(f"{env_data['description']} 환경으로 빠른 전환")
            btn.setMinimumHeight(40)

            # 환경별 색상 스타일
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {env_data['color']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(env_data['color'])};
                }}
                QPushButton:pressed {{
                    background-color: {self._darken_color(env_data['color'], 0.3)};
                }}
                QPushButton:checked {{
                    border: 2px solid white;
                    background-color: {self._darken_color(env_data['color'], 0.1)};
                }}
            """)

            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, env=env_key: self.environment_quick_switch.emit(env))

            self.environment_buttons[env_key] = btn
            buttons_layout.addWidget(btn, 0, i)

        parent_layout.addLayout(buttons_layout)

    def _create_profile_selection_section(self, parent_layout):
        """프로파일 선택 섹션 생성"""
        # 섹션 제목
        title_label = QLabel("📋 프로파일 선택")
        title_label.setObjectName("section_title")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        parent_layout.addWidget(title_label)

        # 프로파일 콤보박스
        combo_layout = QFormLayout()

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("profile_selection_combo")
        self.profile_combo.setMinimumHeight(35)
        self.profile_combo.currentTextChanged.connect(self.profile_selected.emit)

        combo_layout.addRow("프로파일:", self.profile_combo)
        parent_layout.addLayout(combo_layout)

        # 프로파일 정보 표시
        self.profile_info_label = QLabel("프로파일을 선택하세요")
        self.profile_info_label.setObjectName("profile_info_label")
        self.profile_info_label.setWordWrap(True)
        self.profile_info_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-size: 10px;
            }
        """)
        parent_layout.addWidget(self.profile_info_label)

    def _create_action_buttons_section(self, parent_layout):
        """액션 버튼 섹션 생성"""
        # 섹션 제목
        title_label = QLabel("⚡ 액션")
        title_label.setObjectName("section_title")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        parent_layout.addWidget(title_label)

        # 버튼들
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(8)

        # 전환 적용 버튼
        self.apply_btn = QPushButton("🔄 선택한 프로파일로 전환")
        self.apply_btn.setObjectName("profile_apply_btn")
        self.apply_btn.setMinimumHeight(35)
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._on_apply_profile)

        # 커스텀 저장 버튼
        self.save_custom_btn = QPushButton("💾 현재 설정 커스텀 저장")
        self.save_custom_btn.setObjectName("save_custom_btn")
        self.save_custom_btn.setMinimumHeight(35)
        self.save_custom_btn.clicked.connect(self.custom_save_requested.emit)

        # 삭제 버튼
        self.delete_btn = QPushButton("🗑️ 선택한 프로파일 삭제")
        self.delete_btn.setObjectName("profile_delete_btn")
        self.delete_btn.setMinimumHeight(35)
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self._on_delete_profile)

        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.save_custom_btn)
        buttons_layout.addWidget(self.delete_btn)

        parent_layout.addLayout(buttons_layout)
```

### 3. YAML 편집기 섹션 (YamlEditorSection)

```python
class YamlEditorSection(QWidget):
    """우측 YAML 편집기 섹션"""

    # 시그널 정의
    edit_mode_requested = pyqtSignal()          # 편집 모드 요청
    save_requested = pyqtSignal(str, str)       # 저장 요청 (content, filename)
    cancel_requested = pyqtSignal()             # 취소 요청
    content_changed = pyqtSignal(str)           # 내용 변경

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("YamlEditorSection")

        self.current_mode = "view"  # view, edit
        self.temp_file_path = None
        self.original_content = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 상태 표시 영역
        self._create_status_area(layout)

        # YAML 편집기
        self._create_yaml_editor(layout)

        # 제어 버튼 영역
        self._create_control_buttons(layout)

    def _create_status_area(self, parent_layout):
        """상태 표시 영역 생성"""
        status_layout = QHBoxLayout()

        # 상태 레이블
        self.status_label = QLabel("🟢 현재 환경: 로딩중...")
        self.status_label.setObjectName("yaml_editor_status_label")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #e8f5e8;
                border: 1px solid #4CAF50;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        parent_layout.addLayout(status_layout)

    def _create_yaml_editor(self, parent_layout):
        """YAML 편집기 생성"""
        # 편집기 컨테이너
        editor_container = QFrame()
        editor_container.setObjectName("yaml_editor_container")
        editor_container.setFrameStyle(QFrame.Shape.Box)
        editor_container.setStyleSheet("""
            QFrame#yaml_editor_container {
                border: 1px solid #ccc;
                border-radius: 8px;
                background-color: white;
            }
        """)

        container_layout = QVBoxLayout(editor_container)
        container_layout.setContentsMargins(1, 1, 1, 1)

        # YAML 편집기 위젯
        self.yaml_editor = YamlEditor()
        self.yaml_editor.setObjectName("yaml_content_editor")
        container_layout.addWidget(self.yaml_editor)

        parent_layout.addWidget(editor_container)

    def _create_control_buttons(self, parent_layout):
        """제어 버튼 생성"""
        buttons_layout = QHBoxLayout()

        # 편집 버튼
        self.edit_btn = QPushButton("✏️ 편집")
        self.edit_btn.setObjectName("yaml_edit_btn")
        self.edit_btn.setMinimumHeight(35)
        self.edit_btn.clicked.connect(self._on_edit_mode)

        # 취소 버튼
        self.cancel_btn = QPushButton("❌ 취소")
        self.cancel_btn.setObjectName("yaml_cancel_btn")
        self.cancel_btn.setMinimumHeight(35)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._on_cancel)

        # 저장 버튼
        self.save_btn = QPushButton("💾 저장")
        self.save_btn.setObjectName("yaml_save_btn")
        self.save_btn.setMinimumHeight(35)
        self.save_btn.setVisible(False)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)

        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.save_btn)

        parent_layout.addLayout(buttons_layout)


class YamlEditor(QPlainTextEdit):
    """YAML 전용 편집기 위젯"""

    content_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("yaml_editor_text")

        # 구문 강조 설정
        self.syntax_highlighter = YamlSyntaxHighlighter(self.document())

        # 편집기 설정
        self._setup_editor()

        # 시그널 연결
        self.textChanged.connect(self._on_text_changed)

    def _setup_editor(self):
        """편집기 기본 설정"""
        # 모노스페이스 폰트
        font = QFont("Consolas", 11)
        if not font.exactMatch():
            font = QFont("Courier New", 11)
        font.setFixedPitch(True)
        self.setFont(font)

        # 탭 설정 (2스페이스)
        tab_stop = 2 * QFontMetrics(font).horizontalAdvance(' ')
        self.setTabStopDistance(tab_stop)

        # 기본 설정
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setTabChangesFocus(False)

    def _on_text_changed(self):
        """텍스트 변경 시"""
        self.content_changed.emit(self.toPlainText())


class YamlSyntaxHighlighter(QSyntaxHighlighter):
    """YAML 구문 강조 클래스"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_highlighting_rules()

    def _setup_highlighting_rules(self):
        """구문 강조 규칙 설정"""
        self.highlighting_rules = []

        # 키 (key:)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor("#0066CC"))
        key_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((
            QRegularExpression(r'^[ ]*[a-zA-Z_][a-zA-Z0-9_]*(?=:)'),
            key_format
        ))

        # 문자열 값
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        self.highlighting_rules.append((
            QRegularExpression(r'["\'].*?["\']'),
            string_format
        ))

        # 불린 값
        boolean_format = QTextCharFormat()
        boolean_format.setForeground(QColor("#800080"))
        boolean_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((
            QRegularExpression(r'\b(true|false|True|False|TRUE|FALSE)\b'),
            boolean_format
        ))

        # 숫자
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FF6600"))
        self.highlighting_rules.append((
            QRegularExpression(r'\b\d+\.?\d*\b'),
            number_format
        ))

        # 주석
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((
            QRegularExpression(r'#.*'),
            comment_format
        ))

        # YAML 구조 표시자
        structure_format = QTextCharFormat()
        structure_format.setForeground(QColor("#666666"))
        structure_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append((
            QRegularExpression(r'[-:]'),
            structure_format
        ))

    def highlightBlock(self, text):
        """블록 강조 적용"""
        for pattern, format_obj in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format_obj)
```

### 4. Presenter 설계

```python
class EnvironmentProfileRedesignedPresenter:
    """환경 프로파일 재디자인 MVP Presenter"""

    def __init__(self, view):
        self.view = view

        # Use Cases
        self.profile_editor_use_case = ProfileEditorUseCase()
        self.temp_file_use_case = TempFileManagementUseCase()
        self.metadata_use_case = ProfileMetadataUseCase()

        # Services
        self.config_service = ConfigProfileService()

        # Infrastructure 로깅
        self.logger = create_component_logger("EnvironmentProfileRedesignedPresenter")

        # 상태 관리
        self.current_profile = None
        self.selected_profile = None
        self.edit_session = None

        self._connect_view_signals()
        self._initialize_data()

    def _connect_view_signals(self):
        """View 시그널 연결"""
        # 프로파일 선택기 시그널
        self.view.profile_selector.profile_selected.connect(self._on_profile_selected)
        self.view.profile_selector.environment_quick_switch.connect(self._on_quick_environment_switch)
        self.view.profile_selector.profile_apply_requested.connect(self._on_profile_apply)
        self.view.profile_selector.custom_save_requested.connect(self._on_custom_save)
        self.view.profile_selector.profile_delete_requested.connect(self._on_profile_delete)

        # YAML 편집기 시그널
        self.view.yaml_editor.edit_mode_requested.connect(self._on_edit_mode_requested)
        self.view.yaml_editor.save_requested.connect(self._on_save_requested)
        self.view.yaml_editor.cancel_requested.connect(self._on_cancel_requested)
        self.view.yaml_editor.content_changed.connect(self._on_content_changed)

    def _initialize_data(self):
        """초기 데이터 로드"""
        try:
            self.logger.info("🏢 환경 프로파일 재디자인 초기화 시작")

            # 현재 프로파일 확인
            self.current_profile = self.config_service.get_current_profile()

            # 프로파일 목록 로드
            self._refresh_profile_list()

            # 현재 환경 표시
            self._update_current_environment_display()

            self.logger.info("✅ 환경 프로파일 재디자인 초기화 완료")

        except Exception as e:
            self.logger.error(f"❌ 초기화 실패: {e}")
            self.view.show_error_message("초기화 중 오류가 발생했습니다", str(e))

    def _on_profile_selected(self, profile_name: str):
        """프로파일 선택 처리"""
        try:
            self.selected_profile = profile_name
            self.logger.debug(f"📋 프로파일 선택: {profile_name}")

            # 프로파일 정보 표시
            profile_info = self.config_service.get_profile_info(profile_name)
            self._update_profile_info_display(profile_info)

            # YAML 내용 표시
            yaml_content = self._load_profile_yaml_content(profile_name)
            self.view.yaml_editor.set_content(yaml_content, readonly=True)

            # 상태 레이블 업데이트
            if profile_name == self.current_profile:
                self.view.yaml_editor.set_status_label("🟢 현재 환경", profile_info['name'])
            else:
                self.view.yaml_editor.set_status_label("🔵 선택 환경", profile_info['name'])

            # 버튼 상태 업데이트
            self._update_button_states()

        except Exception as e:
            self.logger.error(f"❌ 프로파일 선택 처리 실패: {e}")
            self.view.show_error_message("프로파일 로드 오류", str(e))

    def _on_edit_mode_requested(self):
        """편집 모드 요청 처리"""
        try:
            if not self.selected_profile:
                self.view.show_warning_message("편집할 프로파일을 선택해주세요")
                return

            # 기본 환경 편집 제한 확인
            if self._is_builtin_profile(self.selected_profile):
                result = self.view.show_question_message(
                    "기본 환경 편집 제한",
                    "기본 환경은 직접 편집할 수 없습니다.\n"
                    "현재 설정을 기반으로 커스텀 프로파일을 생성하시겠습니까?"
                )
                if result:
                    self._create_custom_from_current()
                return

            # 편집 세션 시작
            self.edit_session = self.profile_editor_use_case.start_edit_session(
                self.selected_profile,
                is_new_profile=False
            )

            # temp 파일 생성
            temp_content = self._load_profile_yaml_content(self.selected_profile)
            temp_file = self.temp_file_use_case.create_temp_file(
                self.selected_profile,
                temp_content
            )

            # 편집 모드로 전환
            self.view.yaml_editor.set_edit_mode(temp_content)
            self.view.yaml_editor.set_status_label("✏️ 편집중", self.selected_profile)

            self.logger.info(f"✏️ 편집 모드 시작: {self.selected_profile}")

        except Exception as e:
            self.logger.error(f"❌ 편집 모드 전환 실패: {e}")
            self.view.show_error_message("편집 모드 전환 오류", str(e))
```

## 데이터 흐름 설계

### 1. 프로파일 선택 흐름
```
사용자 선택 → ProfileSelectorSection.profile_selected
    ↓
Presenter._on_profile_selected()
    ↓
ConfigProfileService.get_profile_info() ← profile_name
    ↓
YamlEditorSection.set_content() ← yaml_content
    ↓
UI 업데이트 (상태 레이블, 버튼 상태)
```

### 2. 편집 모드 전환 흐름
```
편집 버튼 클릭 → YamlEditorSection.edit_mode_requested
    ↓
Presenter._on_edit_mode_requested()
    ↓
기본 환경 확인 → 제한 처리 또는 편집 허용
    ↓
TempFileManagementUseCase.create_temp_file()
    ↓
YamlEditor.set_edit_mode() ← temp_content
    ↓
UI 상태 변경 (편집 모드, 버튼 표시)
```

### 3. 저장 흐름
```
저장 버튼 클릭 → YamlEditorSection.save_requested
    ↓
Presenter._on_save_requested()
    ↓
YAML 검증 → ProfileValidationService.validate()
    ↓
기존 프로파일: temp → 원본 적용
새 프로파일: Custom_Profile_YYYYMMDD_HHMMSS.yaml 생성
    ↓
ConfigProfileService.save_profile()
    ↓
UI 업데이트 (콤보박스, 상태)
```

### 4. 환경 전환 흐름
```
퀵 버튼 클릭 → ProfileSelectorSection.environment_quick_switch
    ↓
Presenter._on_quick_environment_switch()
    ↓
ConfigProfileService.switch_profile()
    ↓
환경변수 적용 + DB 설정 동기화
    ↓
UI 전체 업데이트 (현재 환경, 버튼 상태)
    ↓
Infrastructure 로깅 기록
```

## 파일 구조 및 네이밍

### 1. 파일명 생성 규칙
```python
class ProfileFileNameGenerator:
    @staticmethod
    def generate_custom_profile_name() -> str:
        """커스텀 프로파일 파일명 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"Custom_Profile_{timestamp}"

        # 중복 방지
        counter = 1
        while ProfileFileNameGenerator._file_exists(f"{base_name}.yaml"):
            base_name = f"Custom_Profile_{timestamp}_{counter:02d}"
            counter += 1

        return f"{base_name}.yaml"

    @staticmethod
    def generate_temp_file_name(profile_name: str) -> str:
        """임시 파일명 생성"""
        timestamp = int(time.time())
        safe_name = re.sub(r'[^\w\-_.]', '_', profile_name)
        return f"temp_edit_{safe_name}_{timestamp}.yaml"
```

### 2. 프로파일 메타데이터 구조
```yaml
# Custom_Profile_20250811_143000.yaml
profile_info:
  name: "개발환경 커스텀 설정"
  description: "디버깅 최적화된 개발 환경"
  created_at: "2025-08-11T14:30:00"
  created_from: "development"
  tags: ["development", "debugging", "custom"]

logging:
  level: "DEBUG"
  console_enabled: true
  file_max_size_mb: 100
  # ... 기타 설정

database:
  backup_enabled: true
  connection_timeout: 30
  # ... 기타 설정
```

### 3. 표시명 생성 로직
```python
class ProfileDisplayNameService:
    def get_display_name(self, profile_name: str) -> str:
        """프로파일 표시명 생성"""
        profile_info = self.config_service.get_profile_info(profile_name)

        if profile_info['type'] == 'built-in':
            return f"{profile_info['name']} (기본환경)"
        elif profile_info['type'] == 'custom':
            display_name = profile_info.get('name', profile_name)
            return f"{display_name} (커스텀)"
        else:
            return profile_name
```

## 스타일링 및 테마 통합

### 1. QSS 스타일 정의
```css
/* environment_profile_redesigned.qss */

/* 메인 스플리터 */
QSplitter#environment_profile_splitter::handle {
    background-color: #e0e0e0;
    width: 6px;
}

QSplitter#environment_profile_splitter::handle:hover {
    background-color: #bdbdbd;
}

/* 섹션 제목 */
QLabel#section_title {
    color: #333333;
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 5px;
}

/* 퀵 환경 버튼들 - 기본 스타일은 코드에서 동적 설정 */

/* 프로파일 콤보박스 */
QComboBox#profile_selection_combo {
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px;
    background-color: white;
    font-size: 11px;
}

QComboBox#profile_selection_combo:focus {
    border-color: #4CAF50;
}

/* 프로파일 정보 라벨 */
QLabel#profile_info_label {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 8px;
    font-size: 10px;
    color: #6c757d;
}

/* 액션 버튼들 */
QPushButton#profile_apply_btn {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#profile_apply_btn:hover {
    background-color: #45a049;
}

QPushButton#profile_apply_btn:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#save_custom_btn {
    background-color: #2196F3;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#save_custom_btn:hover {
    background-color: #1976D2;
}

QPushButton#profile_delete_btn {
    background-color: #f44336;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#profile_delete_btn:hover {
    background-color: #d32f2f;
}

QPushButton#profile_delete_btn:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* YAML 편집기 상태 라벨 */
QLabel#yaml_editor_status_label {
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
    font-size: 12px;
}

/* YAML 편집기 컨테이너 */
QFrame#yaml_editor_container {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background-color: white;
}

/* YAML 편집기 */
QPlainTextEdit#yaml_content_editor {
    border: none;
    background-color: white;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    line-height: 1.4;
}

/* 편집 제어 버튼들 */
QPushButton#yaml_edit_btn {
    background-color: #FF9800;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#yaml_edit_btn:hover {
    background-color: #F57C00;
}

QPushButton#yaml_cancel_btn {
    background-color: #9E9E9E;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#yaml_cancel_btn:hover {
    background-color: #757575;
}

QPushButton#yaml_save_btn {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}

QPushButton#yaml_save_btn:hover {
    background-color: #45a049;
}

QPushButton#yaml_save_btn:disabled {
    background-color: #cccccc;
    color: #666666;
}
```

### 2. 다크 테마 대응
```python
class ThemeAwareYamlHighlighter(YamlSyntaxHighlighter):
    """테마 인식 YAML 구문 강조"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.theme_notifier = ThemeNotifier.instance()
        self.theme_notifier.theme_changed.connect(self._update_colors)

    def _update_colors(self, is_dark_theme: bool):
        """테마에 따른 색상 업데이트"""
        if is_dark_theme:
            self.colors = {
                'key': '#7DB3F3',        # 밝은 파란색
                'string': '#9ECE6A',     # 밝은 녹색
                'boolean': '#BB9AF7',    # 보라색
                'number': '#FF9E64',     # 주황색
                'comment': '#565F89',    # 회색
                'structure': '#A9A9A9'   # 밝은 회색
            }
        else:
            self.colors = {
                'key': '#0066CC',        # 파란색
                'string': '#008000',     # 녹색
                'boolean': '#800080',    # 보라색
                'number': '#FF6600',     # 주황색
                'comment': '#808080',    # 회색
                'structure': '#666666'   # 진한 회색
            }

        self._setup_highlighting_rules()
        self.rehighlight()
```

## 에러 처리 및 검증

### 1. YAML 검증 시스템
```python
class YamlValidationService:
    """YAML 검증 서비스"""

    def validate_yaml_content(self, content: str) -> ValidationResult:
        """YAML 내용 검증"""
        try:
            # 기본 YAML 구문 검사
            parsed_data = yaml.safe_load(content)

            # 스키마 검증
            validation_errors = self._validate_schema(parsed_data)

            # 환경변수 매핑 검증
            env_mapping_errors = self._validate_env_mapping(parsed_data)

            all_errors = validation_errors + env_mapping_errors

            return ValidationResult(
                is_valid=len(all_errors) == 0,
                errors=all_errors,
                parsed_data=parsed_data
            )

        except yaml.YAMLError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"YAML 구문 오류: {str(e)}"],
                parsed_data=None
            )

    def _validate_schema(self, data: dict) -> List[str]:
        """스키마 검증"""
        errors = []

        # 필수 섹션 확인
        required_sections = ['logging']
        for section in required_sections:
            if section not in data:
                errors.append(f"필수 섹션 누락: {section}")

        # 로깅 섹션 검증
        if 'logging' in data:
            logging_errors = self._validate_logging_section(data['logging'])
            errors.extend(logging_errors)

        return errors

    def _validate_logging_section(self, logging_config: dict) -> List[str]:
        """로깅 섹션 검증"""
        errors = []

        # 레벨 검증
        if 'level' in logging_config:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if logging_config['level'] not in valid_levels:
                errors.append(f"유효하지 않은 로그 레벨: {logging_config['level']}")

        # 불린 값 검증
        boolean_fields = ['console_enabled', 'llm_briefing_enabled', 'performance_monitoring']
        for field in boolean_fields:
            if field in logging_config:
                if not isinstance(logging_config[field], bool):
                    errors.append(f"{field}는 불린 값이어야 합니다")

        return errors
```

### 2. 실시간 검증 표시
```python
class YamlEditorWithValidation(YamlEditor):
    """검증 기능이 포함된 YAML 편집기"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.validation_service = YamlValidationService()
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_content)

        # 오류 표시용 위젯
        self.error_display = QLabel()
        self.error_display.setVisible(False)
        self.error_display.setStyleSheet("""
            QLabel {
                background-color: #ffebee;
                color: #c62828;
                border: 1px solid #ef5350;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
            }
        """)

    def _on_text_changed(self):
        """텍스트 변경 시 검증 예약"""
        super()._on_text_changed()
        self.validation_timer.start(1000)  # 1초 후 검증

    def _validate_content(self):
        """내용 검증 및 오류 표시"""
        content = self.toPlainText()
        result = self.validation_service.validate_yaml_content(content)

        if result.is_valid:
            self.error_display.setVisible(False)
            self._clear_error_highlighting()
        else:
            error_text = "\n".join(result.errors[:3])  # 최대 3개 오류만 표시
            if len(result.errors) > 3:
                error_text += f"\n... 외 {len(result.errors) - 3}개 오류"

            self.error_display.setText(f"⚠️ 오류:\n{error_text}")
            self.error_display.setVisible(True)
            self._highlight_errors(result.errors)
```

## 성능 최적화

### 1. 지연 로딩
```python
class LazyProfileLoader:
    """프로파일 지연 로딩"""

    def __init__(self):
        self._profile_cache = {}
        self._metadata_cache = {}

    def get_profile_content(self, profile_name: str) -> str:
        """프로파일 내용 캐시된 로드"""
        if profile_name not in self._profile_cache:
            content = self._load_profile_from_disk(profile_name)
            self._profile_cache[profile_name] = content

        return self._profile_cache[profile_name]

    def invalidate_cache(self, profile_name: str = None):
        """캐시 무효화"""
        if profile_name:
            self._profile_cache.pop(profile_name, None)
            self._metadata_cache.pop(profile_name, None)
        else:
            self._profile_cache.clear()
            self._metadata_cache.clear()
```

### 2. 비동기 처리
```python
class AsyncProfileOperations(QObject):
    """비동기 프로파일 작업"""

    profile_loaded = pyqtSignal(str, str)  # profile_name, content
    operation_completed = pyqtSignal(bool, str)  # success, message

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()

    def load_profile_async(self, profile_name: str):
        """비동기 프로파일 로드"""
        worker = ProfileLoadWorker(profile_name)
        worker.signals.result.connect(self.profile_loaded.emit)
        self.thread_pool.start(worker)

    def save_profile_async(self, profile_name: str, content: str):
        """비동기 프로파일 저장"""
        worker = ProfileSaveWorker(profile_name, content)
        worker.signals.finished.connect(self.operation_completed.emit)
        self.thread_pool.start(worker)


class ProfileLoadWorker(QRunnable):
    """프로파일 로드 워커"""

    def __init__(self, profile_name: str):
        super().__init__()
        self.profile_name = profile_name
        self.signals = WorkerSignals()

    def run(self):
        """워커 실행"""
        try:
            content = ConfigProfileService().load_profile_content(self.profile_name)
            self.signals.result.emit(self.profile_name, content)
        except Exception as e:
            self.signals.error.emit(str(e))
```

## 테스트 전략

### 1. 단위 테스트
```python
class TestEnvironmentProfileRedesigned(TestCase):
    """환경 프로파일 재디자인 테스트"""

    def setUp(self):
        """테스트 설정"""
        self.app = QApplication.instance() or QApplication([])
        self.widget = EnvironmentLoggingRedesignedWidget()
        self.presenter = self.widget.presenter

    def test_profile_selection(self):
        """프로파일 선택 테스트"""
        # Given
        test_profile = "development"

        # When
        self.widget.profile_selector.profile_combo.setCurrentText(test_profile)

        # Then
        self.assertEqual(self.presenter.selected_profile, test_profile)
        self.assertIn(test_profile, self.widget.yaml_editor.yaml_editor.toPlainText())

    def test_edit_mode_transition(self):
        """편집 모드 전환 테스트"""
        # Given
        self.presenter.selected_profile = "custom_test"

        # When
        self.widget.yaml_editor.edit_btn.click()

        # Then
        self.assertTrue(self.widget.yaml_editor.yaml_editor.isEnabled())
        self.assertTrue(self.widget.yaml_editor.save_btn.isVisible())
        self.assertTrue(self.widget.yaml_editor.cancel_btn.isVisible())

    def test_yaml_validation(self):
        """YAML 검증 테스트"""
        # Given
        invalid_yaml = "invalid: yaml: content:"
        validator = YamlValidationService()

        # When
        result = validator.validate_yaml_content(invalid_yaml)

        # Then
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
```

### 2. 통합 테스트
```python
class TestProfileWorkflow(TestCase):
    """프로파일 워크플로우 통합 테스트"""

    def test_complete_profile_creation_workflow(self):
        """완전한 프로파일 생성 워크플로우 테스트"""
        # 1. 현재 환경 설정 로드
        # 2. 커스텀 저장 요청
        # 3. 메타데이터 입력
        # 4. 파일 생성 확인
        # 5. 콤보박스 업데이트 확인
        pass

    def test_environment_switching_workflow(self):
        """환경 전환 워크플로우 테스트"""
        # 1. 퀵 버튼 클릭
        # 2. 환경 전환 확인
        # 3. UI 업데이트 확인
        # 4. 로깅 기록 확인
        pass
```

## 마이그레이션 계획

### 1. 기존 시스템과의 호환성
```python
class LegacyCompatibilityLayer:
    """기존 시스템 호환성 레이어"""

    def __init__(self):
        self.legacy_widget = None

    def migrate_from_legacy(self, legacy_widget):
        """기존 위젯에서 마이그레이션"""
        # 현재 상태 추출
        current_state = self._extract_legacy_state(legacy_widget)

        # 새 위젯에 상태 적용
        self._apply_state_to_new_widget(current_state)

    def _extract_legacy_state(self, widget) -> dict:
        """기존 위젯 상태 추출"""
        return {
            'current_profile': widget.get_current_profile(),
            'selected_profile': widget.get_selected_profile(),
            'user_preferences': widget.get_user_preferences()
        }
```

### 2. 점진적 배포 계획
```
Phase 1: 새 위젯 구현 (기존과 병행)
    - 새 탭으로 추가 ("환경 프로파일 (신규)")
    - 기존 탭 유지 ("환경 & 로깅")
    - 기능 검증 및 피드백 수집

Phase 2: 기능 동등성 확보
    - 모든 기존 기능 구현 완료
    - 성능 최적화
    - 사용자 테스트

Phase 3: 전환 및 정리
    - 기본 탭을 새 위젯으로 교체
    - 기존 위젯 제거
    - 문서 업데이트
```

이상으로 환경 프로파일 탭 재디자인의 상세 설계가 완료되었습니다. 이 설계는 requirements.md의 모든 요구사항을 충족하며, DDD 아키텍처와 Infrastructure 로깅 시스템 v4.0을 완전히 준수합니다.

"""
매매 전략 관리 화면 - 새로운 컴포넌트 기반 전략 관리
- 트리거 빌더 탭 (조건 생성 및 관리)
- 전략 메이커 탭 (실제 매매 전략 생성)
- 백테스팅 탭
- 전략 분석 탭
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QHBoxLayout,
    QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from upbit_auto_trading.logging import get_integrated_logger

# 리팩토링된 트리거 빌더 시스템 import
try:
    from .trigger_builder.trigger_builder_screen import TriggerBuilderScreen
    TRIGGER_BUILDER_AVAILABLE = True
    print("✅ 컴포넌트 기반 TriggerBuilderScreen 로드 성공")
except ImportError as e:
    print(f"❌ TriggerBuilderScreen 로드 실패: {e}")
    TRIGGER_BUILDER_AVAILABLE = False

# 레거시 integrated_condition_manager.py는 더 이상 사용하지 않음
# 모든 기능이 컴포넌트 기반 TriggerBuilderScreen으로 완전 이관됨


class StrategyManagementScreen(QWidget):
    """컴포넌트 기반 전략 관리 화면"""

    # 백테스팅 요청 시그널
    backtest_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 매매 전략 관리")
        self.logger = get_integrated_logger("StrategyManagement")

        # MVP Container 저장용
        self.mvp_container = None

        # LLM_REPORT 초기화 보고
        self._log_llm_report("StrategyScreen_초기화", "시작", "전략 관리 화면 생성")

        self.init_ui()

        # LLM_REPORT 완료 보고
        self._log_llm_report("StrategyScreen_초기화", "완료", "4개 탭 구성 완료")

    def set_mvp_container(self, mvp_container):
        """MVP Container 설정 (Main Window에서 주입)"""
        self.mvp_container = mvp_container
        self.logger.info("✅ MVP Container 주입 완료 - 전략 메이커 탭에 적용 예정")

    def _log_llm_report(self, operation: str, status: str, details: str = "") -> None:
        """LLM 에이전트 구조화된 보고"""
        if self.logger:
            self.logger.info(f"🤖 LLM_REPORT: Operation={operation}, Status={status}, Details={details}")
        else:
            print(f"🤖 LLM_REPORT: Operation={operation}, Status={status}, Details={details}")

    def init_ui(self):
        """UI 초기화"""
        self._log_llm_report("UI_초기화", "시작", "레이아웃 및 탭 구성")

        layout = QVBoxLayout(self)

        # 탭 위젯 생성
        self.tab_widget = QTabWidget()

        # 탭들 생성
        self.trigger_builder_tab = self.create_trigger_builder_tab()
        self.strategy_maker_tab = self.create_strategy_maker_tab()
        self.backtest_tab = self.create_backtest_tab()
        self.analysis_tab = self.create_analysis_tab()

        # 탭 추가
        self.tab_widget.addTab(self.trigger_builder_tab, "🎯 트리거 빌더")
        self.tab_widget.addTab(self.strategy_maker_tab, "⚙️ 전략 메이커")
        self.tab_widget.addTab(self.backtest_tab, "📊 백테스팅")
        self.tab_widget.addTab(self.analysis_tab, "📈 전략 분석")

        layout.addWidget(self.tab_widget)

        self.logger.debug("매매전략 관리 화면 초기화 완료 (4개 탭)")
        self._log_llm_report("UI_초기화", "완료", "4개 탭 생성 및 레이아웃 적용")

    def create_trigger_builder_tab(self):
        """트리거 빌더 탭 생성 - 리팩토링된 컴포넌트 기반"""
        self._log_llm_report("TriggerBuilder_탭_생성", "시작", "컴포넌트 기반 트리거 빌더 로딩")

        try:
            if TRIGGER_BUILDER_AVAILABLE:
                tab = TriggerBuilderScreen()
                self._log_llm_report("TriggerBuilder_탭_생성", "성공", "컴포넌트 로드 완료")
                return tab
            else:
                raise ImportError("트리거 빌더 컴포넌트들을 찾을 수 없습니다")
        except Exception as e:
            self.logger.error(f"트리거 빌더 탭 생성 실패: {e}")
            self._log_llm_report("TriggerBuilder_탭_생성", "실패", f"오류: {str(e)}")
            return self.create_fallback_screen("트리거 빌더 로딩 실패")

    def create_strategy_maker_tab(self):
        """전략 메이커 탭 생성 - MVP 패턴 적용 (TASK-13)"""
        self._log_llm_report("StrategyMaker_탭_생성", "시작", "MVP 패턴 기반 전략 메이커 로딩")

        try:
            # MVP Container가 있으면 MVP 패턴 사용
            if self.mvp_container:
                try:
                    presenter, view = self.mvp_container.create_strategy_maker_mvp()
                    self._log_llm_report("StrategyMaker_탭_생성", "MVP_성공", "MVP 패턴 적용 완료")
                    return view
                except Exception as mvp_error:
                    self.logger.warning(f"MVP 패턴 적용 실패, 기존 방식 사용: {mvp_error}")
                    self._log_llm_report("StrategyMaker_탭_생성", "MVP_실패", f"폴백: {str(mvp_error)}")

            # 폴백: 기존 전략 메이커 사용
            try:
                from .strategy_maker import StrategyMaker
                tab = StrategyMaker()
                self._log_llm_report("StrategyMaker_탭_생성", "기존_방식_성공", "전략 메이커 UI 초기화 완료")
                return tab
            except ImportError as import_error:
                self.logger.error(f"기존 전략 메이커 로드 실패: {import_error}")
                self._log_llm_report("StrategyMaker_탭_생성", "실패", f"Import 오류: {str(import_error)}")
                return self.create_fallback_screen("전략 메이커 로딩 실패")

        except Exception as e:
            self.logger.error(f"전략 메이커 탭 생성 실패: {e}")
            self._log_llm_report("StrategyMaker_탭_생성", "실패", f"오류: {str(e)}")
            return self.create_fallback_screen("전략 메이커 로딩 실패")

    def create_backtest_tab(self):
        """백테스팅 탭 생성"""
        self._log_llm_report("Backtest_탭_생성", "건너뛰기", "백테스팅 탭은 개발 예정")
        return self.create_fallback_screen("백테스팅 (개발 예정)")

    def create_analysis_tab(self):
        """전략 분석 탭 생성"""
        self._log_llm_report("Analysis_탭_생성", "건너뛰기", "분석 탭은 개발 예정")
        return self.create_fallback_screen("전략 분석 (개발 예정)")

    def create_fallback_screen(self, title):
        """폴백 화면 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        error_label = QLabel(f"🔧 {title}\n\n개발 진행 중입니다.")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 20px;
                background-color: #f8f9fa;
                border: 2px dashed #bdc3c7;
                border-radius: 8px;
            }
        """)
        layout.addWidget(error_label)

        return widget

    def refresh_all_data(self):
        """모든 데이터 새로고침"""
        try:
            self.logger.debug("전략 관리 데이터 새로고침")
            # TODO: 각 탭의 데이터 새로고침 구현
            QMessageBox.information(self, "새로고침", "데이터가 새로고침되었습니다.")
        except Exception as e:
            self.logger.error(f"데이터 새로고침 실패: {e}")
            QMessageBox.warning(self, "오류", f"데이터 새로고침 중 오류가 발생했습니다:\n{e}")

"""
코인 리스트 위젯 - 단순화된 버전

차트뷰어의 좌측 패널에 표시되는 코인 리스트입니다.
마켓 콤보박스, 검색 필터, 필터 초기화 버튼으로 구성됩니다.
"""

from typing import Optional, List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QLabel
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinListService, CoinInfo


class CoinListWidget(QWidget):
    """
    단순화된 코인 리스트 위젯

    구성:
    - 마켓 콤보박스 (KRW/BTC/USDT)
    - 검색 필터
    - 필터 초기화 버튼
    - 코인 리스트
    """

    # 시그널 정의
    coin_selected = pyqtSignal(str)  # 코인 선택 시그널
    market_changed = pyqtSignal(str)  # 마켓 변경 시그널

    def __init__(self, parent: Optional[QWidget] = None):
        """코인 리스트 위젯 초기화"""
        super().__init__(parent)

        self._logger = create_component_logger("CoinListWidget")

        # 상태 관리
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[CoinInfo] = []

        # 서비스
        self._coin_service = CoinListService()

        # UI 컴포넌트
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._coin_list: Optional[QListWidget] = None

        # UI 초기화
        self._setup_ui()

        # 초기 데이터 로드
        self._load_market_data()

        self._logger.info("✅ 단순화된 코인 리스트 위젯 초기화 완료")

    def _setup_ui(self) -> None:
        """UI 구성 - 단순화된 레이아웃"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 제목
        title = QLabel("📋 코인 리스트")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 컨트롤 영역 (한 줄에 배치)
        control_layout = QHBoxLayout()

        # 마켓 콤보박스
        self._market_combo = QComboBox()
        self._market_combo.addItems(["KRW", "BTC", "USDT"])
        self._market_combo.setCurrentText("KRW")
        self._market_combo.currentTextChanged.connect(self._on_market_changed)
        self._market_combo.setMinimumWidth(80)
        control_layout.addWidget(self._market_combo)

        # 검색 필터
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("검색...")
        self._search_input.textChanged.connect(self._on_search_changed)
        control_layout.addWidget(self._search_input)

        # 필터 초기화 버튼
        self._clear_button = QPushButton("초기화")
        self._clear_button.setMaximumWidth(60)
        self._clear_button.clicked.connect(self._clear_search)
        control_layout.addWidget(self._clear_button)

        layout.addLayout(control_layout)

        # 코인 리스트
        self._coin_list = QListWidget()
        self._coin_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._coin_list)

        self._logger.debug("✅ 단순화된 UI 구성 완료")

    def _load_market_data(self) -> None:
        """마켓 데이터 로드 - 동기적 처리"""
        try:
            # 동기적으로 데이터 로드
            import asyncio

            # 기존 이벤트 루프가 있으면 사용, 없으면 새로 생성
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 이미 실행 중인 루프가 있으면 태스크로 실행
                    import threading
                    result = None
                    exception = None

                    def load_data():
                        nonlocal result, exception
                        try:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            result = new_loop.run_until_complete(
                                self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                            )
                            new_loop.close()
                        except Exception as e:
                            exception = e

                    thread = threading.Thread(target=load_data)
                    thread.start()
                    thread.join()

                    if exception:
                        raise exception
                    coins = result
                else:
                    coins = loop.run_until_complete(
                        self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                    )
            except RuntimeError:
                # 새 이벤트 루프 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                coins = loop.run_until_complete(
                    self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                )
                loop.close()

            if coins:
                self._coin_data = coins
                self._update_coin_list()
                self._logger.info(f"✅ {self._current_market} 마켓 데이터 로드 완료: {len(coins)}개")
            else:
                self._coin_data = []
                self._update_coin_list()
                self._logger.warning(f"⚠️ {self._current_market} 마켓 데이터 없음")

        except Exception as e:
            self._logger.error(f"❌ 마켓 데이터 로드 실패: {e}")
            # 실패시 빈 리스트로 설정
            self._coin_data = []
            self._update_coin_list()

    def _update_coin_list(self) -> None:
        """코인 리스트 업데이트 - 일괄 처리"""
        if not self._coin_list:
            self._logger.error("❌ 코인 리스트 위젯이 없습니다")
            return

        # 기존 항목 클리어
        self._coin_list.clear()

        if not self._coin_data:
            self._logger.debug("코인 데이터가 없습니다")
            return

        # 필터링된 데이터
        filtered_data = []
        if self._search_filter:
            for coin in self._coin_data:
                if (self._search_filter.lower() in coin.symbol.lower() or
                    self._search_filter.lower() in coin.name.lower()):
                    filtered_data.append(coin)
        else:
            filtered_data = self._coin_data

        # 일괄로 항목 추가
        for coin in filtered_data:
            item_text = f"{coin.symbol}\n{coin.name} - {coin.price_formatted}"
            if coin.change_rate and coin.change_rate != "0.00%":
                item_text += f" ({coin.change_rate})"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, coin.symbol)
            self._coin_list.addItem(item)

        self._logger.debug(f"✅ 코인 리스트 업데이트 완료: {len(filtered_data)}개 표시")

    def _on_market_changed(self, market: str) -> None:
        """마켓 변경 처리"""
        if market != self._current_market:
            self._current_market = market
            self._logger.info(f"📊 마켓 변경: {market}")
            self._load_market_data()
            self.market_changed.emit(market)

    def _on_search_changed(self, text: str) -> None:
        """검색 필터 변경 처리"""
        self._search_filter = text
        self._update_coin_list()  # 즉시 필터링

    def _clear_search(self) -> None:
        """검색 필터 클리어"""
        if self._search_input:
            self._search_input.clear()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """코인 항목 클릭 처리"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.coin_selected.emit(symbol)
            self._logger.debug(f"� 코인 선택: {symbol}")

    def get_current_market(self) -> str:
        """현재 선택된 마켓 반환"""
        return self._current_market

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self._logger.info("🔄 데이터 새로고침")
        self._load_market_data()

    def _setup_ui(self) -> None:
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # 제목
        title = QLabel("📋 코인 리스트")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 마켓 선택 탭
        self._market_tabs = QTabWidget()
        self._market_tabs.addTab(QWidget(), "KRW")
        self._market_tabs.addTab(QWidget(), "BTC")
        self._market_tabs.addTab(QWidget(), "USDT")
        self._market_tabs.currentChanged.connect(self._on_market_changed)
        layout.addWidget(self._market_tabs)

        # 검색 필터
        search_layout = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("코인 검색...")
        self._search_input.textChanged.connect(self._on_search_changed)

        self._clear_button = QPushButton("×")
        self._clear_button.setMaximumWidth(30)
        self._clear_button.clicked.connect(self._clear_search)

        search_layout.addWidget(self._search_input)
        search_layout.addWidget(self._clear_button)
        layout.addLayout(search_layout)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # 로딩 라벨
        self._loading_label = QLabel("데이터 로딩 중...")
        self._loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_label.setVisible(False)
        layout.addWidget(self._loading_label)

        # 코인 리스트
        self._coin_list = QListWidget()
        self._coin_list.itemClicked.connect(self._on_item_clicked)
        self._coin_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._coin_list)

        self._logger.debug("UI 구성 완료")

    def _verify_ui_components(self) -> None:
        """UI 컴포넌트 상태 검증 및 복구"""
        # QListWidget이 None이면 다시 찾아서 설정
        if not self._coin_list:
            # 자식 위젯에서 QListWidget 찾기
            from PyQt6.QtWidgets import QListWidget
            widgets = self.findChildren(QListWidget)
            if widgets:
                self._coin_list = widgets[0]
                self._logger.info(f"✅ _coin_list 참조 복구 완료: {self._coin_list}")
            else:
                self._logger.warning("⚠️ QListWidget을 찾을 수 없습니다. UI 재구성이 필요할 수 있습니다.")

        # 기타 필수 컴포넌트 확인
        components_status = {
            "_market_tabs": self._market_tabs,
            "_search_input": self._search_input,
            "_clear_button": self._clear_button,
            "_loading_label": self._loading_label,
            "_coin_list": self._coin_list
        }

        missing_components = [name for name, comp in components_status.items() if comp is None]
        if missing_components:
            self._logger.warning(f"⚠️ 누락된 UI 컴포넌트: {missing_components}")
        else:
            self._logger.debug("✅ 모든 UI 컴포넌트 확인됨")

    def _load_initial_data(self) -> None:
        """초기 데이터 로드"""
        self._logger.debug("✅ UI 구성 확인 완료, 샘플 데이터로 즉시 표시")

        # 즉시 샘플 데이터 표시 (UI 검증용)
        self._load_sample_data()

        # 실제 API 데이터는 나중에 백그라운드에서 로드
        QTimer.singleShot(1000, self._load_market_data_async)  # 1초 후 실행

    def _load_sample_data(self) -> None:
        """샘플 데이터로 즉시 UI 표시"""
        from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinInfo

        # 간단한 샘플 데이터
        sample_data = [
            CoinInfo("KRW-BTC", "비트코인", "KRW", "45000000", "45,000,000", "+2.5%", "+1,000,000", "1.2B", 120000000.0, False),
            CoinInfo("KRW-ETH", "이더리움", "KRW", "3200000", "3,200,000", "+1.8%", "+56,000", "800M", 80000000.0, False),
            CoinInfo("KRW-ADA", "에이다", "KRW", "650", "650", "-0.5%", "-3", "500M", 50000000.0, False),
        ]

        # 직접 위젯에 항목 추가
        self._coin_data = sample_data
        self._force_update_ui()

    def _force_update_ui(self) -> None:
        """강제로 UI 업데이트 (위젯 참조 문제 우회)"""
        # 위젯 직접 찾기 및 사용
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        from PyQt6.QtCore import Qt

        widgets = self.findChildren(QListWidget)
        if not widgets:
            self._logger.warning("⚠️ QListWidget을 찾을 수 없습니다")
            return

        # 첫 번째 QListWidget 사용
        list_widget = widgets[0]

        try:
            # 기존 항목 클리어
            list_widget.clear()

            # 샘플 데이터 추가
            for coin in self._coin_data:
                item_text = f"{coin.symbol}\n{coin.name} - {coin.price_formatted} ({coin.change_rate})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, coin.symbol)
                list_widget.addItem(item)

            self._logger.info(f"✅ 강제 UI 업데이트 완료: {len(self._coin_data)}개 항목 추가")

        except Exception as e:
            self._logger.error(f"❌ 강제 UI 업데이트 실패: {e}")

    def _load_market_data_async(self) -> None:
        """비동기 마켓 데이터 로드 (백그라운드)"""
        import threading

        def load_data():
            try:
                # 동기적으로 실행하되 안전하게
                import asyncio
                loop = None
                try:
                    # 새로운 이벤트 루프 생성
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    coins = loop.run_until_complete(
                        self._coin_service.get_coins_by_market(self._current_market)
                    )

                    if coins:  # 데이터가 있으면 업데이트
                        self._coin_data = coins
                        self.update_coin_list_signal.emit()
                        self._logger.info(f"✅ 실제 API 데이터 로드 완료: {len(coins)}개")

                except Exception as e:
                    self._logger.error(f"❌ API 데이터 로드 실패: {e}")
                    # 샘플 데이터 유지
                finally:
                    if loop:
                        try:
                            loop.close()
                        except Exception:
                            pass
            except Exception as e:
                self._logger.error(f"❌ 데이터 로드 스레드 오류: {e}")

        # 백그라운드에서 데이터 로드
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()

    def _show_loading(self, show: bool) -> None:
        """로딩 상태 표시"""
        self._loading = show
        if self._loading_label and self._coin_list:
            self._loading_label.setVisible(show)
            self._coin_list.setVisible(not show)

    def _on_market_changed(self, index: int) -> None:
        """마켓 탭 변경 처리"""
        markets = ["KRW", "BTC", "USDT"]
        if 0 <= index < len(markets):
            self._current_market = markets[index]
            self._load_market_data()
            self.market_changed.emit(self._current_market)
            self._logger.debug(f"마켓 변경: {self._current_market}")

    def _load_market_data(self) -> None:
        """현재 마켓 데이터 로드"""
        import threading

        def load_data():
            try:
                import asyncio
                loop = None
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    coins = loop.run_until_complete(
                        self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                    )
                    self._coin_data = coins
                    # UI 업데이트는 메인 스레드에서
                    self.update_coin_list_signal.emit()
                except Exception as e:
                    self._logger.error(f"❌ 마켓 데이터 로드 실패: {e}")
                finally:
                    if loop:
                        try:
                            loop.close()
                        except Exception:
                            pass
            except Exception as e:
                self._logger.error(f"❌ 마켓 데이터 로드 스레드 오류: {e}")

        # 로딩 표시
        self._show_loading(True)

        # 백그라운드에서 데이터 로드
        thread = threading.Thread(target=load_data, daemon=True)
        thread.start()

    def _on_search_changed(self, text: str) -> None:
        """검색 필터 변경 처리"""
        self._search_filter = text.lower()
        self._load_market_data()  # 실시간 검색
        self._logger.debug(f"검색 필터: '{text}'")

    def _clear_search(self) -> None:
        """검색 필터 클리어"""
        if self._search_input:
            self._search_input.clear()
        self._search_filter = ""
        self._load_market_data()
        self._logger.debug("검색 필터 클리어")

    def _update_coin_list(self) -> None:
        """코인 리스트 업데이트"""
        self._logger.debug(f"_update_coin_list 호출됨: 데이터 개수={len(self._coin_data)}")

        # 작업할 위젯 확보 (직접 방식)
        working_widget = None

        # 1차: 기존 참조 확인
        if self._coin_list:
            try:
                self._coin_list.count()  # 테스트
                working_widget = self._coin_list
                self._logger.debug("✅ 기존 참조 사용")
            except (RuntimeError, AttributeError):
                self._logger.warning("⚠️ 기존 참조 무효")
                self._coin_list = None

        # 2차: findChildren으로 즉시 찾기
        if not working_widget:
            from PyQt6.QtWidgets import QListWidget
            widgets = self.findChildren(QListWidget)
            for widget in widgets:
                try:
                    widget.count()  # 테스트
                    working_widget = widget
                    self._coin_list = widget  # 참조 업데이트
                    self._logger.info(f"🔄 findChildren으로 위젯 확보: {len(widgets)}개 중 선택")
                    break
                except (RuntimeError, AttributeError):
                    self._logger.warning("⚠️ findChildren 위젯 무효")

        # 3차: 새로 생성
        if not working_widget:
            try:
                from PyQt6.QtWidgets import QListWidget
                working_widget = QListWidget()
                working_widget.itemClicked.connect(self._on_item_clicked)
                working_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

                # 레이아웃에 추가
                layout = self.layout()
                if layout:
                    layout.addWidget(working_widget)
                    self._coin_list = working_widget  # 참조 업데이트
                    self._logger.info("✅ 새 위젯 생성 및 추가 완료")
                else:
                    self._logger.error("❌ 레이아웃이 없어서 위젯을 추가할 수 없습니다")
                    working_widget = None
            except Exception as e:
                self._logger.error(f"❌ 새 위젯 생성 실패: {e}")
                working_widget = None

        # 위젯을 확보하지 못한 경우 포기
        if not working_widget:
            self._logger.error("❌ 작업할 위젯을 확보할 수 없습니다!")
            return

        # 위젯 작업 수행 (working_widget 직접 사용)
        try:
            # 기존 항목 클리어
            working_widget.clear()
            self._logger.debug("✅ 위젯 클리어 완료")

            # 로딩 상태 해제
            self._show_loading(False)

            if not self._coin_data:
                self._logger.warning("⚠️ 표시할 코인 데이터가 없습니다")
                return

            # 즐겨찾기 항목 먼저 추가
            favorites_added = []
            for coin in self._coin_data:
                if coin.symbol in self._favorites:
                    self._add_coin_item_direct(working_widget, coin, is_favorite=True)
                    favorites_added.append(coin.symbol)

            # 일반 항목 추가 (즐겨찾기 제외)
            for coin in self._coin_data:
                if coin.symbol not in favorites_added:
                    self._add_coin_item_direct(working_widget, coin, is_favorite=False)

            # 최종 확인
            final_count = working_widget.count()
            self._logger.info(f"✅ {self._current_market} 마켓 코인 리스트 업데이트 완료: "
                              f"{len(self._coin_data)}개 → UI 항목: {final_count}개")

        except Exception as e:
            self._logger.error(f"❌ 위젯 작업 실패: {e}")

    def _add_coin_item_direct(self, widget, coin: 'CoinInfo', is_favorite: bool = False) -> None:
        """코인 항목을 지정된 위젯에 직접 추가"""
        try:
            # 즐겨찾기 표시
            star = "⭐ " if is_favorite else ""

            # 경고 마켓 표시
            warning = "⚠️ " if coin.is_warning else ""

            # 항목 텍스트 구성
            item_text = f"{star}{warning}{coin.symbol}\n{coin.name} - {coin.price_formatted}"
            if coin.change_rate != "0.00%":
                item_text += f" ({coin.change_rate})"

            from PyQt6.QtWidgets import QListWidgetItem
            from PyQt6.QtCore import Qt

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, coin.symbol)  # 심벌 저장

            # 즐겨찾기 항목은 굵게 표시
            if is_favorite:
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            widget.addItem(item)
            self._logger.debug(f"✅ 직접 추가 완료: {coin.symbol}")

        except Exception as e:
            self._logger.error(f"❌ {coin.symbol} 항목 추가 실패: {e}")

    def _ensure_coin_list_widget(self) -> None:
        """코인 리스트 위젯 참조 확실히 보장"""
        if self._coin_list:
            # 위젯이 실제로 유효한지 확인
            try:
                self._coin_list.count()  # 실제 QListWidget 메서드 호출 테스트
                return  # 유효한 참조가 있음
            except (RuntimeError, AttributeError):
                self._logger.warning("⚠️ 기존 _coin_list 참조가 무효합니다. 재설정합니다.")
                self._coin_list = None

        self._logger.warning("🔄 _coin_list가 None입니다. 즉시 복구를 시도합니다.")

        # 1차: findChildren으로 찾기
        from PyQt6.QtWidgets import QListWidget
        widgets = self.findChildren(QListWidget)
        self._logger.debug(f"🔍 findChildren 결과: {len(widgets)}개의 QListWidget 발견")

        for i, widget in enumerate(widgets):
            try:
                # 위젯이 실제로 작동하는지 테스트
                count = widget.count()
                self._coin_list = widget
                self._logger.info(f"✅ 1차 복구 성공: findChildren[{i}]으로 발견 (항목 수: {count})")
                return
            except (RuntimeError, AttributeError) as e:
                self._logger.warning(f"⚠️ findChildren[{i}] 위젯 무효: {e}")

        # 2차: 레이아웃에서 찾기
        layout = self.layout()
        if layout:
            self._logger.debug(f"🔍 레이아웃에서 찾기: {layout.count()}개 아이템")
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and isinstance(widget, QListWidget):
                        try:
                            count = widget.count()
                            self._coin_list = widget
                            self._logger.info(f"✅ 2차 복구 성공: 레이아웃[{i}]에서 발견 (항목 수: {count})")
                            return
                        except (RuntimeError, AttributeError) as e:
                            self._logger.warning(f"⚠️ 레이아웃[{i}] 위젯 무효: {e}")

        # 3차: 새로 생성
        self._logger.warning("🚨 기존 위젯을 찾을 수 없습니다. 새로 생성합니다.")
        try:
            self._coin_list = QListWidget()
            self._coin_list.itemClicked.connect(self._on_item_clicked)
            self._coin_list.itemDoubleClicked.connect(self._on_item_double_clicked)

            # 레이아웃에 추가
            if layout:
                layout.addWidget(self._coin_list)
                self._logger.info("✅ 3차 복구 성공: 새 QListWidget 생성 및 추가")
            else:
                self._logger.error("❌ 레이아웃이 없어서 위젯을 추가할 수 없습니다")
        except Exception as e:
            self._logger.error(f"❌ 새 위젯 생성 실패: {e}")
            self._coin_list = None

    def _emergency_ui_recovery(self) -> None:
        """긴급 UI 복구 시도"""
        self._logger.warning("🚨 긴급 UI 복구 시도 중...")

        try:
            # 기존 레이아웃에서 QListWidget 재생성
            layout = self.layout()
            if layout and layout.count() > 0:
                # 마지막에 추가된 위젯이 코인 리스트여야 함
                from PyQt6.QtWidgets import QListWidget
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item:
                        widget = item.widget()
                        if widget and isinstance(widget, QListWidget):
                            self._coin_list = widget
                            self._logger.info("✅ 긴급 복구 성공: 기존 QListWidget 재연결")
                            return

                # QListWidget이 없으면 새로 생성
                if not self._coin_list:
                    self._coin_list = QListWidget()
                    self._coin_list.itemClicked.connect(self._on_item_clicked)
                    self._coin_list.itemDoubleClicked.connect(self._on_item_double_clicked)
                    layout.addWidget(self._coin_list)
                    self._logger.info("✅ 긴급 복구 성공: 새 QListWidget 생성")

        except Exception as e:
            self._logger.error(f"❌ 긴급 UI 복구 실패: {e}")

            # 최후의 수단: showEvent에서 다시 시도하도록 플래그 설정
            self._needs_ui_rebuild = True

    def _add_coin_item(self, coin: CoinInfo, is_favorite: bool = False) -> None:
        """코인 항목 추가"""
        self._logger.debug(f"코인 항목 추가: {coin.symbol} ({coin.name})")

        # 즐겨찾기 표시
        star = "⭐ " if is_favorite else ""

        # 경고 마켓 표시
        warning = "⚠️ " if coin.is_warning else ""

        # 항목 텍스트 구성
        item_text = f"{star}{warning}{coin.symbol}\n{coin.name} - {coin.price_formatted}"
        if coin.change_rate != "0.00%":
            item_text += f" ({coin.change_rate})"

        item = QListWidgetItem(item_text)
        item.setData(Qt.ItemDataRole.UserRole, coin.symbol)  # 심벌 저장

        # 즐겨찾기 항목은 굵게 표시
        if is_favorite:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        if self._coin_list:
            self._coin_list.addItem(item)
            self._logger.debug(f"✅ UI에 추가 완료: {coin.symbol}")
        else:
            self._logger.error(f"❌ _coin_list가 None이어서 {coin.symbol} 추가 실패")

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """코인 항목 클릭 처리"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.coin_selected.emit(symbol)
            self._logger.debug(f"코인 선택: {symbol}")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """코인 항목 더블클릭 처리 (즐겨찾기 토글)"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            # 즐겨찾기 토글
            if symbol in self._favorites:
                self._favorites.remove(symbol)
                is_favorite = False
                self._logger.debug(f"즐겨찾기 제거: {symbol}")
            else:
                self._favorites.append(symbol)
                is_favorite = True
                self._logger.debug(f"즐겨찾기 추가: {symbol}")

            # 시그널 발송
            self.favorite_toggled.emit(symbol, is_favorite)

            # 리스트 업데이트
            self._update_coin_list()

    def get_current_market(self) -> str:
        """현재 선택된 마켓 반환"""
        return self._current_market

    def get_favorites(self) -> List[str]:
        """즐겨찾기 목록 반환"""
        return self._favorites.copy()

    def set_favorites(self, favorites: List[str]) -> None:
        """즐겨찾기 설정"""
        self._favorites = favorites.copy()
        self._update_coin_list()
        self._logger.debug(f"즐겨찾기 설정: {len(favorites)}개")

    def refresh_data(self) -> None:
        """데이터 새로고침 (향후 API 연동용)"""
        self._logger.info("코인 데이터 새로고침 요청")
        self._load_market_data()

    def get_widget_info(self) -> Dict[str, Any]:
        """위젯 정보 반환"""
        return {
            "current_market": self._current_market,
            "search_filter": self._search_filter,
            "favorites_count": len(self._favorites),
            "total_coins": len(self._coin_data),
            "visible_coins": self._coin_list.count() if self._coin_list else 0,
            "loading": self._loading
        }

    def showEvent(self, a0) -> None:
        """위젯이 표시될 때 처리"""
        super().showEvent(a0)

        # UI 재구성이 필요한 경우 처리
        if self._needs_ui_rebuild:
            self._logger.info("🔧 showEvent에서 UI 재구성 시도")
            self._verify_ui_components()
            if self._coin_list:
                self._needs_ui_rebuild = False
                self._logger.info("✅ showEvent에서 UI 재구성 성공")
                # 데이터가 있으면 다시 표시
                if self._coin_data:
                    self._update_coin_list()

    def resizeEvent(self, a0) -> None:
        """위젯 크기 변경 시 처리"""
        super().resizeEvent(a0)

        # 크기 변경 시에도 UI 컴포넌트 확인
        if not self._coin_list and not self._needs_ui_rebuild:
            self._logger.debug("🔧 resizeEvent에서 UI 컴포넌트 재확인")
            self._verify_ui_components()

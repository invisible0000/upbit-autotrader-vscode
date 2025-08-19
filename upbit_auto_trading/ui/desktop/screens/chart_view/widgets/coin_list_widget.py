"""
코인 리스트 위젯 - 완전 재설계 버전

문제점:
1. _coin_list가 None이 되는 이슈
2. UI 중복 생성 문제
3. 재생성 로직의 복잡성

해결책:
1. 지연 초기화 (Lazy Initialization) 패턴
2. 프로퍼티 기반 안전한 접근
3. 단순하고 명확한 구조
"""

from typing import Optional, List, Set
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinListService, CoinInfo


class CoinListWidget(QWidget):
    """코인 리스트 위젯 - 완전 재설계 버전"""

    # 시그널
    coin_selected = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)
    market_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._logger = create_component_logger("CoinListWidget")

        # 상태 변수
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[CoinInfo] = []
        self._favorites: Set[str] = set()  # 즐겨찾기 심볼들
        self._sort_mode = "name"  # "name", "change", "volume"
        self._is_initialized = False

        # UI 컴포넌트 - None으로 시작
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._sort_name_radio: Optional[QRadioButton] = None
        self._sort_change_radio: Optional[QRadioButton] = None
        self._sort_volume_radio: Optional[QRadioButton] = None
        self._sort_button_group: Optional[QButtonGroup] = None
        self._list_widget: Optional[QListWidget] = None  # 이름 변경으로 충돌 방지

        # 서비스
        self._coin_service = CoinListService()

        # 즉시 초기화
        self._ensure_initialization()

        # 즐겨찾기 로드
        self._load_favorites()

        # 데이터 로드
        self._schedule_data_loading()

        self._logger.info("✅ 코인 리스트 위젯 초기화 완료")

    def _ensure_initialization(self) -> None:
        """확실한 초기화 보장"""
        if self._is_initialized:
            return

        try:
            self._create_ui_components()
            self._setup_layout()
            self._connect_signals()
            self._is_initialized = True
            self._logger.info("✅ UI 초기화 완료")
        except Exception as e:
            self._logger.error(f"❌ UI 초기화 실패: {e}")
            raise

    def _create_ui_components(self) -> None:
        """UI 컴포넌트 생성"""
        # 마켓 콤보박스
        self._market_combo = QComboBox()
        self._market_combo.addItems(["KRW", "BTC", "USDT"])
        self._market_combo.setCurrentText("KRW")

        # 검색 입력
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("코인 검색...")

        # 초기화 버튼
        self._clear_button = QPushButton("X")
        self._clear_button.setFixedWidth(30)

        # 정렬 라디오 버튼들
        self._sort_name_radio = QRadioButton("이름순")
        self._sort_change_radio = QRadioButton("변화율순")
        self._sort_volume_radio = QRadioButton("거래량순")

        # 기본 선택: 이름순
        self._sort_name_radio.setChecked(True)

        # 버튼 그룹으로 묶어서 하나만 선택 가능하게
        self._sort_button_group = QButtonGroup()
        self._sort_button_group.addButton(self._sort_name_radio, 0)
        self._sort_button_group.addButton(self._sort_change_radio, 1)
        self._sort_button_group.addButton(self._sort_volume_radio, 2)

        # 리스트 위젯 - 가장 중요!
        self._list_widget = QListWidget()
        # HTML 리치 텍스트 지원 활성화
        from PyQt6.QtCore import Qt
        self._list_widget.setTextElideMode(Qt.TextElideMode.ElideNone)

        # 컨텍스트 메뉴 설정 제거 (별표 클릭으로 대체)
        # self._list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # self._list_widget.customContextMenuRequested.connect(self._show_context_menu)        # 생성 즉시 검증 - None 체크로 수정
        if self._list_widget is None:
            raise RuntimeError("리스트 위젯 생성 실패")

        self._logger.debug(f"✅ 리스트 위젯 생성 완료: {id(self._list_widget)}")

    def _setup_layout(self) -> None:
        """레이아웃 설정"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # 마켓 선택 + 검색 영역 (같은 줄)
        top_layout = QHBoxLayout()
        market_label = QLabel("마켓:")
        market_label.setFixedWidth(40)
        top_layout.addWidget(market_label)
        top_layout.addWidget(self._market_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self._search_input)
        top_layout.addWidget(self._clear_button)

        # 정렬 영역 (라벨 제거)
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self._sort_name_radio)
        sort_layout.addWidget(self._sort_change_radio)
        sort_layout.addWidget(self._sort_volume_radio)
        sort_layout.addStretch()

        # 메인 레이아웃 조립
        main_layout.addLayout(top_layout)
        main_layout.addLayout(sort_layout)
        main_layout.addWidget(self._list_widget)

        self._logger.debug("✅ 레이아웃 설정 완료")

    def _connect_signals(self) -> None:
        """시그널 연결"""
        if self._market_combo is not None:
            self._market_combo.currentTextChanged.connect(self._on_market_changed)

        if self._search_input is not None:
            self._search_input.textChanged.connect(self._on_search_changed)

        if self._clear_button is not None:
            self._clear_button.clicked.connect(self._clear_search)

        # 정렬 라디오 버튼 시그널 연결
        if self._sort_button_group is not None:
            self._sort_button_group.buttonClicked.connect(self._on_sort_changed)

        if self._list_widget is not None:
            self._list_widget.itemClicked.connect(self._on_item_clicked)
            # 더블클릭으로 즐겨찾기 토글
            self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

        self._logger.debug("✅ 시그널 연결 완료")

    @property
    def coin_list(self) -> QListWidget:
        """안전한 리스트 위젯 접근"""
        if self._list_widget is None:
            self._logger.warning("⚠️ 리스트 위젯이 None임. 재초기화 시도...")
            self._ensure_initialization()

        if self._list_widget is None:
            raise RuntimeError("리스트 위젯 초기화 실패")

        return self._list_widget

    def _schedule_data_loading(self) -> None:
        """데이터 로드 스케줄링"""
        # 즉시 샘플 데이터 표시
        self._load_sample_data()

        # 1초 후 실제 데이터 로드
        QTimer.singleShot(1000, self._load_real_data)

    def _load_sample_data(self) -> None:
        """샘플 데이터 로드"""
        sample_data = [
            CoinInfo("KRW-BTC", "비트코인", "KRW", "45000000", "45,000,000", "+2.5%", "+1,000,000", "1.2B", 120000000.0, False),
            CoinInfo("KRW-ETH", "이더리움", "KRW", "3200000", "3,200,000", "+1.8%", "+56,000", "800M", 80000000.0, False),
            CoinInfo("KRW-ADA", "에이다", "KRW", "650", "650", "-0.5%", "-3", "500M", 50000000.0, False),
        ]

        self._coin_data = sample_data
        self._update_ui()
        self._logger.info("✅ 샘플 데이터 로드 완료")

    def _load_real_data(self) -> None:
        """실제 데이터 로드 - async 안전 처리"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        def load_data_sync():
            """동기 방식으로 데이터 로드"""
            try:
                # 새로운 이벤트 루프를 안전하게 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    coins = loop.run_until_complete(
                        self._coin_service.get_coins_by_market(self._current_market, self._search_filter)
                    )

                    if coins:
                        self._coin_data = coins
                        # 메인 스레드에서 UI 업데이트
                        QTimer.singleShot(0, self._update_ui)
                        self._logger.info(f"✅ {self._current_market} 실제 데이터 로드 완료: {len(coins)}개")
                    else:
                        self._logger.warning(f"⚠️ {self._current_market} 마켓에 데이터가 없습니다")
                        # 빈 데이터로라도 UI 업데이트
                        self._coin_data = []
                        QTimer.singleShot(0, self._update_ui)

                finally:
                    loop.close()

            except Exception as e:
                self._logger.error(f"❌ 실제 데이터 로드 실패: {e}")
                # 에러 발생 시 빈 리스트로 업데이트
                self._coin_data = []
                QTimer.singleShot(0, self._update_ui)

        # ThreadPoolExecutor를 사용하여 안전하게 실행
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(load_data_sync)

    def _update_ui(self) -> None:
        """UI 업데이트"""
        try:
            # 안전한 리스트 위젯 접근
            list_widget = self.coin_list
            list_widget.clear()

            # 필터링된 데이터 가져오기
            filtered_data = self._filter_coins()

            # 아이템 추가 - 개선된 형식: 거래량 + 볼드 + 변화율 색상
            for coin in filtered_data:
                # 즐겨찾기 상태에 따른 별표 표시
                star_icon = "⭐" if coin.symbol in self._favorites else "☆"

                # 기본 정보: 심볼과 이름
                base_text = f"{star_icon} {coin.symbol} - {coin.name}"

                # 가격 정보 추가
                if coin.price_formatted:
                    base_text += f" | {coin.price_formatted}"

                # 변화율 정보 추가
                if coin.change_rate and coin.change_rate != "0.00%":
                    base_text += f" | ({coin.change_rate})"

                # 거래량 정보 추가 (volume_raw를 사용)
                if hasattr(coin, 'volume_raw') and coin.volume_raw:
                    # 거래량을 억 단위로 표시 (24시간 거래량)
                    volume_billions = float(coin.volume_raw) / 100_000_000
                    if volume_billions >= 1:
                        base_text += f" | {volume_billions:.1f}억"
                    else:
                        volume_millions = float(coin.volume_raw) / 1_000_000
                        base_text += f" | {volume_millions:.0f}백만"

                item = QListWidgetItem(base_text)
                item.setData(Qt.ItemDataRole.UserRole, coin.symbol)

                # 폰트 설정 (볼드)
                font = QFont()
                font.setBold(True)
                item.setFont(font)

                # 변화율에 따른 색상 적용 (변화율 부분만 색상 변경하고 싶지만, QListWidget 한계로 전체 색상 조정)
                if coin.change_rate and coin.change_rate != "0.00%":
                    if coin.change_rate.startswith('+'):
                        # 상승: 빨간색 (약간 어둡게 하여 읽기 좋게)
                        item.setForeground(QColor(185, 28, 28))  # 진한 빨강
                    elif coin.change_rate.startswith('-'):
                        # 하락: 파란색 (약간 어둡게 하여 읽기 좋게)
                        item.setForeground(QColor(29, 78, 216))  # 진한 파랑

                # 즐겨찾기 상태를 아이템에 저장
                item.setData(Qt.ItemDataRole.UserRole + 1, coin.symbol in self._favorites)

                # 툴팁 추가
                item.setToolTip(f"더블클릭하여 {coin.symbol} 즐겨찾기 토글")

                list_widget.addItem(item)

            self._logger.info(f"✅ UI 업데이트 완료: {len(filtered_data)}개 아이템")

        except Exception as e:
            self._logger.error(f"❌ UI 업데이트 실패: {e}")

    def _filter_coins(self) -> List[CoinInfo]:
        """코인 필터링 - 즐겨찾기는 항상 상단, 검색 필터에서 제외"""
        # 디버그 로그
        self._logger.debug(f"🔍 필터링 시작 - 전체 코인: {len(self._coin_data)}개")
        self._logger.debug(f"🔍 즐겨찾기 목록: {self._favorites}")
        self._logger.debug(f"🔍 검색 필터: '{self._search_filter}'")

        # 즐겨찾기와 일반 코인 분리
        favorite_coins = []
        regular_coins = []

        for coin in self._coin_data:
            if coin.symbol in self._favorites:
                favorite_coins.append(coin)
            else:
                regular_coins.append(coin)

        # 검색 필터는 일반 코인에만 적용 (즐겨찾기는 항상 표시)
        if self._search_filter:
            search_lower = self._search_filter.lower()
            filtered_regular_coins = [
                coin for coin in regular_coins
                if (search_lower in coin.symbol.lower()
                    or search_lower in coin.name.lower())
            ]
            self._logger.debug(f"🔍 검색 필터 적용: {len(regular_coins)}개 → {len(filtered_regular_coins)}개 (일반 코인)")
        else:
            filtered_regular_coins = regular_coins

        # 최종 결과를 정렬 모드에 따라 정렬
        all_filtered_coins = favorite_coins + filtered_regular_coins
        sorted_coins = self._sort_coin_data(all_filtered_coins)

        self._logger.debug(
            f"🔍 최종 결과: 즐겨찾기 {len(favorite_coins)}개 + 일반 {len(filtered_regular_coins)}개 "
            f"= 총 {len(sorted_coins)}개 (정렬: {self._sort_mode})"
        )
        return sorted_coins

    def _on_market_changed(self, market: str) -> None:
        """마켓 변경 처리"""
        if market != self._current_market:
            self._current_market = market
            self.market_changed.emit(market)
            self._load_real_data()
            self._logger.info(f"📊 마켓 변경: {market}")

    def _on_search_changed(self, text: str) -> None:
        """검색 텍스트 변경 처리"""
        self._search_filter = text
        self._update_ui()

    def _clear_search(self) -> None:
        """검색 초기화"""
        if self._search_input is not None:
            self._search_input.clear()
        self._search_filter = ""
        self._update_ui()

    def _on_sort_changed(self, button: QRadioButton) -> None:
        """정렬 방식 변경 핸들러"""
        try:
            if button == self._sort_name_radio:
                self._sort_mode = "name"
                self._logger.debug("정렬 모드: 이름순")
            elif button == self._sort_change_radio:
                self._sort_mode = "change"
                self._logger.debug("정렬 모드: 변화율순")
            elif button == self._sort_volume_radio:
                self._sort_mode = "volume"
                self._logger.debug("정렬 모드: 거래량순")

            # 현재 표시된 데이터 다시 업데이트 (정렬 적용)
            self._apply_current_sort()

        except Exception as e:
            self._logger.error(f"정렬 변경 처리 중 오류: {e}")

    def _apply_current_sort(self) -> None:
        """현재 정렬 모드를 적용하여 리스트 업데이트"""
        try:
            # 현재 선택된 마켓과 검색어로 다시 업데이트
            self._update_ui()
        except Exception as e:
            self._logger.error(f"정렬 적용 중 오류: {e}")

    def _sort_coin_data(self, coin_data: List[CoinInfo]) -> List[CoinInfo]:
        """코인 데이터를 현재 정렬 모드에 따라 정렬"""
        try:
            # 즐겨찾기는 항상 최상단에 유지
            favorites = [coin for coin in coin_data if coin.symbol in self._favorites]
            non_favorites = [coin for coin in coin_data if coin.symbol not in self._favorites]

            # 정렬 모드에 따른 정렬
            if self._sort_mode == "name":
                favorites.sort(key=lambda x: x.name)
                non_favorites.sort(key=lambda x: x.name)
            elif self._sort_mode == "change":
                # 변화율 정렬 (높은 순)
                def change_sort_key(coin):
                    try:
                        if coin.change_rate and coin.change_rate != "0.00%":
                            rate_str = coin.change_rate.replace('%', '').replace('+', '')
                            return float(rate_str)
                        return 0.0
                    except ValueError:
                        return 0.0

                favorites.sort(key=change_sort_key, reverse=True)
                non_favorites.sort(key=change_sort_key, reverse=True)
            elif self._sort_mode == "volume":
                # 거래량 정렬 (높은 순)
                favorites.sort(key=lambda x: x.volume_raw, reverse=True)
                non_favorites.sort(key=lambda x: x.volume_raw, reverse=True)

            # 즐겨찾기 + 일반 순서로 결합
            return favorites + non_favorites

        except Exception as e:
            self._logger.error(f"코인 데이터 정렬 중 오류: {e}")
            return coin_data

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """아이템 클릭 처리 - 코인 선택"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.coin_selected.emit(symbol)
            self._logger.info(f"💰 코인 선택: {symbol}")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """아이템 더블클릭 처리 - 즐겨찾기 토글"""
        symbol = item.data(Qt.ItemDataRole.UserRole)
        if symbol:
            self.toggle_favorite(symbol)
            self._logger.info(f"🌟 더블클릭으로 즐겨찾기 토글: {symbol}")

    def toggle_favorite(self, symbol: str) -> None:
        """즐겨찾기 토글"""
        if symbol in self._favorites:
            self._favorites.remove(symbol)
            is_favorite = False
            self._logger.info(f"💔 즐겨찾기 해제: {symbol}")
        else:
            self._favorites.add(symbol)
            is_favorite = True
            self._logger.info(f"💖 즐겨찾기 추가: {symbol}")

        # 시그널 발송
        self.favorite_toggled.emit(symbol, is_favorite)

        # UI 업데이트
        self._update_ui()

        # 즐겨찾기 상태 저장 (향후 DB 연동)
        self._save_favorites()

    def _save_favorites(self) -> None:
        """즐겨찾기 상태 저장 (현재는 로깅만)"""
        self._logger.debug(f"💾 즐겨찾기 저장: {len(self._favorites)}개")
        # TODO: DB에 즐겨찾기 상태 저장 구현

    def _load_favorites(self) -> None:
        """즐겨찾기 상태 로드 (현재는 기본값)"""
        # TODO: DB에서 즐겨찾기 상태 로드 구현
        # 임시로 샘플 즐겨찾기 추가
        self._favorites = {"KRW-BTC", "KRW-ETH"}
        self._logger.debug(f"📖 즐겨찾기 로드: {len(self._favorites)}개")

    def get_current_market(self) -> str:
        """현재 마켓 반환"""
        return self._current_market

    def refresh_data(self) -> None:
        """데이터 새로고침"""
        self._load_real_data()

    def get_selected_symbol(self) -> Optional[str]:
        """선택된 심볼 반환"""
        try:
            current_item = self.coin_list.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        return None

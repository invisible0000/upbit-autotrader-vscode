"""
코인 리스트 위젯 - QAsync 통합 버전

QAsync 아키텍처 변경사항:
1. 격리 이벤트 루프 완전 제거 (new_event_loop, run_until_complete 금지)
2. @asyncSlot 패턴으로 UI-비동기 브리지 통일
3. AppKernel TaskManager 통합으로 태스크 생명주기 관리
4. LoopGuard 통합으로 루프 위반 실시간 감지

목적:
- 단일 QAsync 이벤트 루프에서 모든 비동기 작업 처리
- Thread-5 격리 루프 문제 완전 해결
- Infrastructure Layer와 완벽 호환성 확보
"""

from typing import Optional, List, Set
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

# QAsync 통합 imports
try:
    from qasync import asyncSlot
    QASYNC_AVAILABLE = True
except ImportError:
    QASYNC_AVAILABLE = False
    # 폴백 데코레이터 (QAsync 없는 환경용)

    def asyncSlot(*args):
        def decorator(func):
            return func
        return decorator

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinListService, CoinInfo

# AppKernel 통합
try:
    from upbit_auto_trading.infrastructure.runtime.app_kernel import get_kernel
    KERNEL_AVAILABLE = True
except ImportError:
    KERNEL_AVAILABLE = False

# LoopGuard 통합
try:
    from upbit_auto_trading.infrastructure.runtime.loop_guard import get_loop_guard
    LOOP_GUARD_AVAILABLE = True
except ImportError:
    LOOP_GUARD_AVAILABLE = False


class CoinListWidget(QWidget):
    """코인 리스트 위젯 - 완전 재설계 버전"""

    # 시그널
    coin_selected = pyqtSignal(str)
    favorite_toggled = pyqtSignal(str, bool)
    market_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._logger = create_component_logger("CoinListWidget")

        # QAsync 환경 검증
        if not QASYNC_AVAILABLE:
            self._logger.error("❌ QAsync가 설치되지 않았습니다. pip install qasync")
            raise RuntimeError("QAsync 필수 의존성 누락")

        # LoopGuard 등록
        if LOOP_GUARD_AVAILABLE:
            self._loop_guard = get_loop_guard()
            self._loop_guard.register_component("CoinListWidget", "코인 리스트 UI 위젯")
        else:
            self._loop_guard = None

        # 상태 변수
        self._current_market = "KRW"
        self._search_filter = ""
        self._coin_data: List[CoinInfo] = []
        self._favorites: Set[str] = set()  # 즐겨찾기 심볼들
        self._sort_mode = "name"  # "name", "change", "volume"
        self._is_initialized = False

        # 비동기 작업 상태 관리
        self._loading_task: Optional[asyncio.Task] = None
        self._refresh_task: Optional[asyncio.Task] = None

        # UI 컴포넌트 - None으로 시작
        self._market_combo: Optional[QComboBox] = None
        self._search_input: Optional[QLineEdit] = None
        self._clear_button: Optional[QPushButton] = None
        self._sort_name_radio: Optional[QRadioButton] = None
        self._sort_change_radio: Optional[QRadioButton] = None
        self._sort_volume_radio: Optional[QRadioButton] = None
        self._sort_button_group: Optional[QButtonGroup] = None
        self._list_widget: Optional[QListWidget] = None

        # 서비스
        self._coin_service = CoinListService()

        # 즉시 초기화
        self._ensure_initialization()

        # 즐겨찾기 로드
        self._load_favorites()

        # 데이터 로드 스케줄링
        self._schedule_data_loading()

        self._logger.info("✅ 코인 리스트 위젯 초기화 완료 (QAsync 모드)")

    def _ensure_initialization(self) -> None:
        """확실한 초기화 보장"""
        if self._is_initialized:
            return

        try:
            # LoopGuard 검증
            if self._loop_guard:
                self._loop_guard.ensure_main_loop(where="CoinListWidget._ensure_initialization")

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

        # 새로고침 버튼
        self._refresh_button = QPushButton("🔄")
        self._refresh_button.setFixedWidth(40)
        self._refresh_button.setToolTip("데이터 새로고침")

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

        # 마켓 선택 + 검색 영역 (마켓 라벨 제거)
        top_layout = QHBoxLayout()
        top_layout.addWidget(self._market_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self._search_input)
        top_layout.addWidget(self._clear_button)
        top_layout.addWidget(self._refresh_button)

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

        if self._refresh_button is not None:
            self._refresh_button.clicked.connect(self._on_refresh_clicked)

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

        # 1초 후 실제 데이터 로드 (QAsync 방식)
        QTimer.singleShot(1000, self._start_real_data_loading)

    def _load_sample_data(self) -> None:
        """샘플 데이터 로드"""
        from upbit_auto_trading.application.chart_viewer.coin_list_service import CoinInfo

        sample_data = [
            CoinInfo("KRW-BTC", "비트코인", "KRW", "45000000", "45,000,000", "+2.5%",
                     "+1,000,000", "1.2B", 120000000.0, 2.5, False),
            CoinInfo("KRW-ETH", "이더리움", "KRW", "3200000", "3,200,000", "+1.8%",
                     "+56,000", "800M", 80000000.0, 1.8, False),
            CoinInfo("KRW-ADA", "에이다", "KRW", "650", "650", "-0.5%",
                     "-3", "500M", 50000000.0, -0.5, False),
        ]

        self._coin_data = sample_data
        self._update_ui()
        self._logger.info("✅ 샘플 데이터 로드 완료")

    def _start_real_data_loading(self) -> None:
        """실제 데이터 로드 시작 (QTimer 콜백에서 호출)"""
        # 현재 로딩 태스크 취소
        if self._loading_task and not self._loading_task.done():
            self._loading_task.cancel()

        # QTimer를 사용하여 비동기 메서드 지연 호출
        QTimer.singleShot(0, self._trigger_load_async)

    @asyncSlot()
    async def _trigger_load_async(self) -> None:
        """데이터 로드 트리거 (QTimer에서 호출)"""
        # 현재 로딩 태스크 취소
        if self._loading_task and not self._loading_task.done():
            self._loading_task.cancel()

        # 새로운 로딩 태스크 시작 (TaskManager 사용)
        if KERNEL_AVAILABLE:
            try:
                kernel = get_kernel()
                self._loading_task = kernel.create_task(
                    self._load_real_data_async(),
                    name="coin_list_initial_load",
                    component="CoinListWidget"
                )
            except Exception as e:
                self._logger.warning(f"AppKernel 사용 불가: {e}. 직접 태스크 생성")
                self._loading_task = asyncio.create_task(self._load_real_data_async())
        else:
            self._loading_task = asyncio.create_task(self._load_real_data_async())

    async def _load_real_data_async(self) -> None:
        """
        실제 데이터 로드 - QAsync 통합 패턴

        ❌ 이전: threading + new_event_loop + run_until_complete
        ✅ 현재: @asyncSlot + await + TaskManager
        """
        try:
            # LoopGuard 검증
            if self._loop_guard:
                self._loop_guard.ensure_main_loop(where="CoinListWidget._load_real_data_async")

            self._logger.info(f"🔄 {self._current_market} 실제 데이터 로드 시작... (QAsync 모드)")

            # 🎯 핵심 변경: 격리 루프 대신 직접 await
            coins = await self._coin_service.get_coins_by_market(
                self._current_market,
                self._search_filter
            )

            self._logger.info(f"📊 데이터 로드 완료: {len(coins) if coins else 0}개")

            if coins:
                self._coin_data = coins
                # 🎯 UI 업데이트를 메인 스레드에서 안전하게 처리
                QTimer.singleShot(0, self._update_ui_after_load)
                self._logger.info(f"✅ {self._current_market} 실제 데이터 로드 완료: {len(coins)}개")
            else:
                self._logger.warning(f"⚠️ {self._current_market} 마켓에 데이터가 없습니다")
                self._coin_data = []
                QTimer.singleShot(0, self._update_ui_after_load)

        except asyncio.CancelledError:
            self._logger.info("데이터 로드 작업이 취소되었습니다")
            raise
        except Exception as e:
            self._logger.error(f"❌ 실제 데이터 로드 실패: {e}")
            import traceback
            self._logger.error(f"스택 트레이스: {traceback.format_exc()}")
            # 에러 발생 시 빈 데이터로 업데이트
            self._coin_data = []
            QTimer.singleShot(0, self._update_ui_after_load)

    def _update_ui_after_load(self) -> None:
        """데이터 로드 후 UI 업데이트"""
        try:
            self._logger.info(f"🎨 UI 업데이트 시작: {len(self._coin_data)}개 코인")
            self._update_ui()
            self._logger.info("✅ UI 업데이트 완료")
        except Exception as e:
            self._logger.error(f"❌ UI 업데이트 실패: {e}")
            import traceback
            self._logger.error(f"스택 트레이스: {traceback.format_exc()}")

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

                # 변화율 정보 추가 (음수 포함)
                if coin.change_rate:
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

                # 변화율에 따른 색상 적용 (음수 포함)
                if coin.change_rate:
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
            self._start_real_data_loading()  # QAsync 방식으로 로드
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

    def _on_refresh_clicked(self) -> None:
        """새로고침 버튼 클릭 처리 (동기 슬롯)"""
        # 현재 새로고침 태스크 취소
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

        # QTimer를 사용하여 비동기 메서드 지연 호출
        QTimer.singleShot(0, self._trigger_refresh_async)

    @asyncSlot()
    async def _trigger_refresh_async(self) -> None:
        """새로고침 트리거 (QTimer에서 호출)"""
        # 현재 새로고침 태스크 취소
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()

        # 새로운 새로고침 태스크 시작
        if KERNEL_AVAILABLE:
            try:
                kernel = get_kernel()
                self._refresh_task = kernel.create_task(
                    self._refresh_data_async(),
                    name="coin_list_refresh",
                    component="CoinListWidget"
                )
            except Exception as e:
                self._logger.warning(f"AppKernel 사용 불가: {e}. 직접 태스크 생성")
                self._refresh_task = asyncio.create_task(self._refresh_data_async())
        else:
            self._refresh_task = asyncio.create_task(self._refresh_data_async())

    async def _refresh_data_async(self) -> None:
        """
        새로고침 처리 - QAsync 통합 패턴

        ❌ 이전: threading + new_event_loop + run_until_complete
        ✅ 현재: @asyncSlot + await + TaskManager
        """
        try:
            # LoopGuard 검증
            if self._loop_guard:
                self._loop_guard.ensure_main_loop(where="CoinListWidget._refresh_data_async")

            self._logger.info(f"🔄 {self._current_market} 마켓 데이터 새로고침 시작")

            if self._coin_service:
                # 🎯 핵심 변경: 격리 루프 대신 직접 await
                await self._coin_service.refresh_data()
                # 현재 마켓 데이터 다시 로드
                await self._load_real_data_async()
            else:
                # 서비스가 없으면 단순 재로드
                await self._load_real_data_async()

        except asyncio.CancelledError:
            self._logger.info("새로고침 작업이 취소되었습니다")
            raise
        except Exception as e:
            self._logger.error(f"❌ 데이터 새로고침 실패: {e}")

    def _on_sort_changed(self, button: QRadioButton) -> None:
        """정렬 방식 변경 핸들러"""
        try:
            if button == self._sort_name_radio:
                self._sort_mode = "name"
            elif button == self._sort_change_radio:
                self._sort_mode = "change"
            elif button == self._sort_volume_radio:
                self._sort_mode = "volume"

            self._update_ui()
        except Exception as e:
            self._logger.error(f"정렬 변경 처리 중 오류: {e}")

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
                # 변화율 정렬 (높은 순) - change_rate_raw 필드 사용
                def change_sort_key(coin):
                    try:
                        if hasattr(coin, 'change_rate_raw'):
                            return coin.change_rate_raw
                        else:
                            # 기존 로직 (호환성)
                            if coin.change_rate:
                                rate_str = coin.change_rate.replace('%', '').replace('+', '')
                                return float(rate_str)
                            return 0.0
                    except (ValueError, AttributeError):
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

    # 외부 API 메서드들
    def get_current_market(self) -> str:
        """현재 마켓 반환"""
        return self._current_market

    def refresh_data(self) -> None:
        """외부 호출용 새로고침"""
        self._on_refresh_clicked()

    def get_selected_symbol(self) -> Optional[str]:
        """선택된 심볼 반환"""
        try:
            current_item = self.coin_list.currentItem()
            if current_item:
                return current_item.data(Qt.ItemDataRole.UserRole)
        except Exception:
            pass
        return None

    async def cleanup(self) -> None:
        """위젯 정리 (종료 시 호출)"""
        try:
            # 진행 중인 태스크 취소
            if self._loading_task and not self._loading_task.done():
                self._loading_task.cancel()

            if self._refresh_task and not self._refresh_task.done():
                self._refresh_task.cancel()

            # LoopGuard 해제
            if self._loop_guard:
                self._loop_guard.unregister_component("CoinListWidget")

            self._logger.info("🧹 CoinListWidget 정리 완료")

        except Exception as e:
            self._logger.error(f"❌ CoinListWidget 정리 실패: {e}")

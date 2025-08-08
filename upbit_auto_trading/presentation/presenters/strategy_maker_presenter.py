"""
Strategy Maker Presenter - MVP 패턴

전략 메이커 UI와 Application Service 사이의 중재자 역할을 수행합니다.
모든 비즈니스 로직은 Application Service에 위임하고,
UI는 순수한 표시/입력 기능만 담당하도록 분리합니다.
"""

from typing import Dict, Any, List, Optional
import logging

from upbit_auto_trading.presentation.interfaces.view_interfaces import IStrategyMakerView
from upbit_auto_trading.application.services.strategy_application_service import StrategyApplicationService
from upbit_auto_trading.application.commands.strategy_commands import CreateStrategyCommand, UpdateStrategyCommand
from upbit_auto_trading.application.dto.strategy_dto import StrategyDto


class StrategyMakerPresenter:
    """전략 메이커 Presenter

    MVP 패턴에서 Presenter 역할을 수행합니다:
    - View에서 사용자 입력을 받아 Application Service로 전달
    - Application Service 결과를 View에 적합한 형태로 변환
    - UI 로직과 비즈니스 로직의 완전한 분리
    """

    def __init__(self, view: Optional[IStrategyMakerView], strategy_service: StrategyApplicationService):
        """Presenter 초기화

        Args:
            view: 전략 메이커 View 인터페이스 (MVP 패턴에서 나중에 설정 가능)
            strategy_service: 전략 관리 Application Service
        """
        self._view = view
        self._strategy_service = strategy_service
        self._logger = logging.getLogger(__name__)
        self._current_strategy_id: str | None = None

    def load_strategies(self) -> None:
        """전략 목록 로드

        Application Service에서 전략 목록을 조회하고 View에 표시합니다.
        """
        if not self._view:
            self._logger.warning("View가 연결되지 않음, 전략 목록 로드 중단")
            return

        try:
            self._view.show_loading("전략 목록을 불러오는 중...")

            # Application Service를 통해 전략 목록 조회
            strategies = self._strategy_service.get_all_strategies()

            # DTO를 View에 적합한 Dictionary 형태로 변환
            strategy_dtos = [self._strategy_dto_to_dict(strategy) for strategy in strategies]

            # View에 표시
            self._view.display_strategy_list(strategy_dtos)
            self._view.hide_loading()

            self._logger.info(f"전략 목록 로드 완료: {len(strategies)}개")

        except Exception as e:
            if self._view:
                self._view.hide_loading()
                self._view.display_error_message(f"전략 목록 로드 실패: {str(e)}")
            self._logger.error(f"전략 목록 로드 실패: {e}", exc_info=True)

    def save_strategy(self) -> None:
        """전략 저장

        View에서 수집한 전략 데이터를 검증하고 Application Service를 통해 저장합니다.
        """
        try:
            # View에서 폼 데이터 수집
            strategy_data = self._view.get_strategy_form_data()

            # 클라이언트 사이드 기본 검증
            validation_errors = self._validate_strategy_form_data(strategy_data)
            if validation_errors:
                self._view.display_validation_errors(validation_errors)
                return

            self._view.show_loading("전략을 저장하는 중...")

            # 전략 생성 또는 업데이트 명령 생성
            if self._current_strategy_id:
                # 기존 전략 업데이트
                command = self._create_update_strategy_command(strategy_data)
                result = self._strategy_service.update_strategy(command)
                message = "전략이 성공적으로 업데이트되었습니다"
            else:
                # 새 전략 생성
                command = self._create_strategy_command(strategy_data)
                result = self._strategy_service.create_strategy(command)
                message = "전략이 성공적으로 생성되었습니다"
                self._current_strategy_id = result.strategy_id

            self._view.hide_loading()
            self._view.display_success_message(message)
            self._view.clear_form()

            # 전략 목록 새로고침
            self.load_strategies()

            self._logger.info(f"전략 저장 완료: {result.name}")

        except ValueError as e:
            # 비즈니스 규칙 위반 (검증 오류)
            self._view.hide_loading()
            self._view.display_validation_errors([str(e)])
            self._logger.warning(f"전략 검증 실패: {e}")

        except Exception as e:
            # 시스템 오류
            self._view.hide_loading()
            self._view.display_error_message(f"전략 저장 실패: {str(e)}")
            self._logger.error(f"전략 저장 실패: {e}", exc_info=True)

    def load_strategy(self, strategy_id: str) -> None:
        """기존 전략 로드

        Args:
            strategy_id: 로드할 전략 ID
        """
        try:
            self._view.show_loading("전략을 불러오는 중...")

            # TODO: Application Service에 get_strategy_by_id 구현 후 활성화
            # strategy = self._strategy_service.get_strategy_by_id(strategy_id)
            # if not strategy:
            #     self._view.display_error_message("전략을 찾을 수 없습니다")
            #     return

            # 임시: 기본 데이터로 폼 설정
            form_data = {
                'name': f'전략 {strategy_id}',
                'description': '불러온 전략입니다',
                'tags': [],
                'entry_triggers': [],
                'exit_triggers': [],
                'risk_management': {
                    'stop_loss': 5.0,
                    'take_profit': 10.0,
                    'position_size': 10.0,
                    'max_positions': 3
                }
            }

            # View에 데이터 설정
            self._view.set_strategy_form_data(form_data)
            self._current_strategy_id = strategy_id

            self._view.hide_loading()
            self._view.display_success_message("전략을 불러왔습니다")

            self._logger.info(f"전략 로드 완료: {strategy_id}")

        except Exception as e:
            self._view.hide_loading()
            self._view.display_error_message(f"전략 로드 실패: {str(e)}")
            self._logger.error(f"전략 로드 실패: {e}", exc_info=True)

    def validate_strategy(self) -> None:
        """전략 유효성 검증

        현재 폼의 전략 데이터를 검증하고 결과를 표시합니다.
        """
        try:
            strategy_data = self._view.get_strategy_form_data()
            validation_errors = self._validate_strategy_form_data(strategy_data)

            if validation_errors:
                self._view.display_validation_errors(validation_errors)
            else:
                self._view.display_success_message("전략 구성이 유효합니다")

        except Exception as e:
            self._view.display_error_message(f"검증 실패: {str(e)}")
            self._logger.error(f"전략 검증 실패: {e}", exc_info=True)

    def clear_strategy(self) -> None:
        """전략 폼 초기화"""
        try:
            self._view.clear_form()
            self._current_strategy_id = None
            self._view.display_success_message("전략이 초기화되었습니다")

        except Exception as e:
            self._view.display_error_message(f"초기화 실패: {str(e)}")
            self._logger.error(f"전략 초기화 실패: {e}", exc_info=True)

    # Private Helper Methods

    def _validate_strategy_form_data(self, data: Dict[str, Any]) -> List[str]:
        """클라이언트 사이드 폼 데이터 검증

        Args:
            data: 검증할 폼 데이터

        Returns:
            List[str]: 검증 오류 메시지 목록
        """
        errors = []

        # 필수 필드 검증
        if not data.get('name', '').strip():
            errors.append("전략 이름을 입력해주세요")

        if not data.get('description', '').strip():
            errors.append("전략 설명을 입력해주세요")

        # 현재 CreateStrategyCommand에서는 entry_triggers 등을 지원하지 않으므로
        # 해당 검증은 주석 처리하거나 제거

        # # 진입 조건 검증
        # if not data.get('entry_triggers') or len(data.get('entry_triggers', [])) == 0:
        #     errors.append("진입 조건을 최소 하나 설정해주세요")

        # # 리스크 관리 설정 검증
        # risk_management = data.get('risk_management', {})
        # if not risk_management:
        #     errors.append("리스크 관리 설정이 필요합니다")

        return errors

    def _create_strategy_command(self, data: Dict[str, Any]) -> CreateStrategyCommand:
        """전략 생성 명령 생성

        Args:
            data: 폼 데이터

        Returns:
            CreateStrategyCommand: 전략 생성 명령
        """
        return CreateStrategyCommand(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            tags=data.get('tags', []),
            created_by="MVP_UI"  # UI 식별자
        )

    def _create_update_strategy_command(self, data: Dict[str, Any]) -> UpdateStrategyCommand:
        """전략 업데이트 명령 생성

        Args:
            data: 폼 데이터

        Returns:
            UpdateStrategyCommand: 전략 업데이트 명령
        """
        if not self._current_strategy_id:
            raise ValueError("업데이트할 전략 ID가 없습니다")

        return UpdateStrategyCommand(
            strategy_id=self._current_strategy_id,
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            tags=data.get('tags', []),
            updated_by="MVP_UI"
        )

    def _strategy_dto_to_dict(self, strategy: StrategyDto) -> Dict[str, Any]:
        """StrategyDTO를 View용 Dictionary로 변환

        Args:
            strategy: 전략 DTO

        Returns:
            Dict[str, Any]: View용 전략 데이터
        """
        return {
            'id': strategy.strategy_id,
            'name': strategy.name,
            'description': strategy.description,
            'status': strategy.status,
            'created_at': strategy.created_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.created_at else "",
            'updated_at': strategy.updated_at.strftime("%Y-%m-%d %H:%M:%S") if strategy.updated_at else ""
        }

    def _strategy_dto_to_form_data(self, strategy: StrategyDto) -> Dict[str, Any]:
        """StrategyDTO를 View 폼 데이터로 변환

        Args:
            strategy: 전략 DTO

        Returns:
            Dict[str, Any]: View 폼 데이터
        """
        return {
            'name': strategy.name,
            'description': strategy.description or '',
            'tags': strategy.tags or [],
            # 트리거와 리스크 관리는 별도 로직으로 처리 (현재 DTO에 없음)
            'entry_triggers': [],
            'exit_triggers': [],
            'risk_management': {
                'stop_loss': 5.0,
                'take_profit': 10.0,
                'position_size': 10.0,
                'max_positions': 3
            }
        }

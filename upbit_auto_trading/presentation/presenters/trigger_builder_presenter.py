"""
Trigger Builder Presenter - MVP 패턴

트리거 빌더 UI와 Application Service 사이의 중재자 역할을 수행합니다.
트리거 및 조건 생성 로직을 Application Layer로 분리합니다.
"""

from typing import Dict, Any, List
import logging

from upbit_auto_trading.presentation.interfaces.view_interfaces import ITriggerBuilderView
from upbit_auto_trading.application.services.trigger_application_service import TriggerApplicationService


class TriggerBuilderPresenter:
    """트리거 빌더 Presenter

    트리거 및 조건 생성 UI의 MVP 패턴 Presenter입니다.
    """

    def __init__(self, view: ITriggerBuilderView, trigger_service: TriggerApplicationService):
        """Presenter 초기화

        Args:
            view: 트리거 빌더 View 인터페이스
            trigger_service: 트리거 관리 Application Service
        """
        self._view = view
        self._trigger_service = trigger_service
        self._logger = logging.getLogger(__name__)

    def load_available_variables(self) -> None:
        """사용 가능한 변수 목록 로드"""
        try:
            # Application Service를 통해 변수 목록 조회
            variables = self._trigger_service.get_available_variables()

            # View에 표시
            self._view.display_variables(variables)

            self._logger.info(f"변수 목록 로드 완료: {len(variables)}개")

        except Exception as e:
            self._view.display_compatibility_warning(f"변수 로드 실패: {str(e)}")
            self._logger.error(f"변수 로드 실패: {e}", exc_info=True)

    def validate_trigger_condition(self) -> None:
        """트리거 조건 검증 및 미리보기 업데이트"""
        try:
            # View에서 트리거 데이터 수집
            trigger_data = self._view.get_trigger_form_data()

            # Application Service를 통해 조건 검증
            validation_result = self._trigger_service.validate_trigger_condition(trigger_data)

            if validation_result.is_valid:
                # 성공 시 미리보기 업데이트
                preview = self._trigger_service.generate_condition_preview(trigger_data)
                self._view.update_condition_preview(preview)
            else:
                # 검증 실패 시 경고 표시
                error_message = "\n".join(validation_result.errors)
                self._view.display_compatibility_warning(f"조건 검증 실패:\n{error_message}")

        except Exception as e:
            self._view.display_compatibility_warning(f"조건 검증 중 오류: {str(e)}")
            self._logger.error(f"트리거 조건 검증 실패: {e}", exc_info=True)

    def save_trigger(self) -> None:
        """트리거 저장"""
        try:
            trigger_data = self._view.get_trigger_form_data()

            # Application Service를 통해 저장
            result = self._trigger_service.save_trigger(trigger_data)

            if result.success:
                self._view.clear_trigger_form()
                # 성공 메시지는 View에서 처리하지 않고 상위 컴포넌트에서 처리
                self._logger.info(f"트리거 저장 완료: {result.trigger_id}")
            else:
                error_message = "\n".join(result.errors)
                self._view.display_compatibility_warning(f"저장 실패:\n{error_message}")

        except Exception as e:
            self._view.display_compatibility_warning(f"트리거 저장 실패: {str(e)}")
            self._logger.error(f"트리거 저장 실패: {e}", exc_info=True)


class BacktestPresenter:
    """백테스팅 Presenter

    백테스팅 실행 및 결과 관리 UI의 MVP 패턴 Presenter입니다.
    """

    def __init__(self, view, backtest_service):
        """Presenter 초기화

        Args:
            view: 백테스팅 View 인터페이스
            backtest_service: 백테스팅 Application Service
        """
        self._view = view
        self._backtest_service = backtest_service
        self._logger = logging.getLogger(__name__)
        self._current_backtest_id: str | None = None

    def start_backtest(self) -> None:
        """백테스팅 시작"""
        try:
            # View에서 백테스팅 파라미터 수집
            parameters = self._view.get_backtest_parameters()

            # 컨트롤 비활성화
            self._view.enable_backtest_controls(False)
            self._view.update_backtest_progress(0, "백테스팅을 시작합니다...")

            # Application Service를 통해 백테스팅 시작
            self._current_backtest_id = self._backtest_service.start_backtest(
                parameters,
                progress_callback=self._on_backtest_progress,
                completion_callback=self._on_backtest_completed
            )

            self._logger.info(f"백테스팅 시작: {self._current_backtest_id}")

        except Exception as e:
            self._view.enable_backtest_controls(True)
            self._view.update_backtest_progress(0, f"백테스팅 시작 실패: {str(e)}")
            self._logger.error(f"백테스팅 시작 실패: {e}", exc_info=True)

    def stop_backtest(self) -> None:
        """백테스팅 중지"""
        try:
            if self._current_backtest_id:
                self._backtest_service.stop_backtest(self._current_backtest_id)
                self._view.update_backtest_progress(0, "백테스팅이 중지되었습니다")
                self._view.enable_backtest_controls(True)

                self._logger.info(f"백테스팅 중지: {self._current_backtest_id}")
                self._current_backtest_id = None

        except Exception as e:
            self._view.update_backtest_progress(0, f"백테스팅 중지 실패: {str(e)}")
            self._logger.error(f"백테스팅 중지 실패: {e}", exc_info=True)

    def _on_backtest_progress(self, progress: int, message: str) -> None:
        """백테스팅 진행률 콜백"""
        self._view.update_backtest_progress(progress, message)

    def _on_backtest_completed(self, results: Dict[str, Any]) -> None:
        """백테스팅 완료 콜백"""
        try:
            self._view.display_backtest_results(results)
            self._view.update_backtest_progress(100, "백테스팅이 완료되었습니다")
            self._view.enable_backtest_controls(True)

            self._logger.info(f"백테스팅 완료: {self._current_backtest_id}")
            self._current_backtest_id = None

        except Exception as e:
            self._view.update_backtest_progress(100, f"결과 표시 실패: {str(e)}")
            self._logger.error(f"백테스팅 결과 표시 실패: {e}", exc_info=True)

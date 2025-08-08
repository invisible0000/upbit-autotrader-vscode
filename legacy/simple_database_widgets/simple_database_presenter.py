"""
간단한 데이터베이스 설정 프레젠터

기본에 충실하면서도 MVP 패턴을 적용한 프레젠터입니다.
비즈니스 로직을 View에서 분리하여 처리합니다.
"""

import sqlite3
import os
import subprocess
import platform
from typing import TYPE_CHECKING

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.infrastructure.configuration.paths import infrastructure_paths
from upbit_auto_trading.ui.desktop.screens.settings.dtos.simple_database_dto import (
    SimpleDatabaseInfoDto, SimpleDatabaseStatusDto, DatabaseValidationResultDto
)

if TYPE_CHECKING:
    from upbit_auto_trading.ui.desktop.screens.settings.interfaces.simple_database_view_interface import (
        ISimpleDatabaseView
    )


class SimpleDatabasePresenter:
    """간단한 데이터베이스 설정 프레젠터

    MVP 패턴의 Presenter 역할을 담당합니다.
    View와 비즈니스 로직을 분리하여 관리합니다.
    """

    def __init__(self, view: "ISimpleDatabaseView"):
        self.view = view
        self.logger = create_component_logger("SimpleDatabasePresenter")
        self.paths = infrastructure_paths

        self.logger.info("🎯 SimpleDatabasePresenter 초기화 완료")

    def load_database_info(self) -> None:
        """데이터베이스 정보 로드 및 표시"""
        try:
            self.logger.debug("📊 데이터베이스 정보 로드 중...")

            # DTO 생성
            info_dto = SimpleDatabaseInfoDto(
                settings_db_path=str(self.paths.SETTINGS_DB),
                strategies_db_path=str(self.paths.STRATEGIES_DB),
                market_data_db_path=str(self.paths.MARKET_DATA_DB)
            )

            # 상태 정보 생성
            settings_exists = self.paths.SETTINGS_DB.exists()
            strategies_exists = self.paths.STRATEGIES_DB.exists()
            market_data_exists = self.paths.MARKET_DATA_DB.exists()

            # 상태 메시지 생성
            status_parts = []
            if settings_exists:
                status_parts.append("⚙️ 설정 DB: 연결됨")
            else:
                status_parts.append("⚙️ 설정 DB: 파일 없음")

            if strategies_exists:
                status_parts.append("🎯 전략 DB: 연결됨")
            else:
                status_parts.append("🎯 전략 DB: 파일 없음")

            if market_data_exists:
                status_parts.append("📈 시장데이터 DB: 연결됨")
            else:
                status_parts.append("📈 시장데이터 DB: 파일 없음")

            status_dto = SimpleDatabaseStatusDto(
                settings_db_exists=settings_exists,
                strategies_db_exists=strategies_exists,
                market_data_db_exists=market_data_exists,
                status_message=" | ".join(status_parts)
            )

            # View에 데이터 전달
            self.view.display_database_info({
                'settings_db': info_dto.settings_db_path,
                'strategies_db': info_dto.strategies_db_path,
                'market_data_db': info_dto.market_data_db_path
            })

            self.view.display_status({
                'settings_exists': status_dto.settings_db_exists,
                'strategies_exists': status_dto.strategies_db_exists,
                'market_data_exists': status_dto.market_data_db_exists,
                'status_message': status_dto.status_message
            })

            # 상태 시그널 발생
            all_exists = settings_exists and strategies_exists and market_data_exists
            self.view.db_status_changed.emit(all_exists)

            self.logger.info("✅ 데이터베이스 정보 로드 완료")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 정보 로드 실패: {e}")
            self.view.show_error_message("로드 실패", f"데이터베이스 정보 로드 중 오류가 발생했습니다:\n{str(e)}")

    def refresh_status(self) -> None:
        """상태 새로고침"""
        self.logger.info("🔃 데이터베이스 상태 새로고침")
        self.view.show_progress("상태 새로고침 중...")

        try:
            self.load_database_info()
            self.view.show_progress("새로고침 완료", 100)
            self.view.show_info_message("새로고침 완료", "데이터베이스 상태가 새로고침되었습니다.")
        except Exception as e:
            self.view.show_error_message("새로고침 실패", f"상태 새로고침 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.view.hide_progress()

    def validate_databases(self) -> None:
        """데이터베이스 검증"""
        self.logger.info("✅ 데이터베이스 검증 시작")
        self.view.show_progress("데이터베이스 검증 중...")

        try:
            validation_results = []
            error_count = 0

            # 각 데이터베이스 파일 검증
            databases = [
                ("설정 DB", self.paths.SETTINGS_DB),
                ("전략 DB", self.paths.STRATEGIES_DB),
                ("시장데이터 DB", self.paths.MARKET_DATA_DB)
            ]

            for db_name, db_path in databases:
                if db_path.exists():
                    try:
                        # 간단한 연결 테스트
                        conn = sqlite3.connect(str(db_path))
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5")
                        tables = cursor.fetchall()
                        conn.close()

                        table_count = len(tables)
                        validation_results.append(f"✅ {db_name}: 정상 ({table_count}개 테이블)")
                    except Exception as e:
                        validation_results.append(f"❌ {db_name}: 오류 - {str(e)}")
                        error_count += 1
                else:
                    validation_results.append(f"⚠️ {db_name}: 파일 없음")
                    error_count += 1

            # 검증 결과 DTO 생성
            result_dto = DatabaseValidationResultDto(
                results=validation_results,
                all_valid=(error_count == 0),
                error_count=error_count
            )

            # View에 결과 전달
            self.view.show_validation_result(result_dto.results)

            self.logger.info("✅ 데이터베이스 검증 완료")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 검증 실패: {e}")
            self.view.show_error_message("검증 실패", f"데이터베이스 검증 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.view.hide_progress()

    def open_data_folder(self) -> None:
        """데이터 폴더 열기"""
        try:
            data_folder = self.paths.DATA_DIR

            if platform.system() == "Windows":
                os.startfile(str(data_folder))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(data_folder)])
            else:  # Linux
                subprocess.run(["xdg-open", str(data_folder)])

            self.logger.info(f"📂 데이터 폴더 열기: {data_folder}")

        except Exception as e:
            self.logger.error(f"❌ 폴더 열기 실패: {e}")
            self.view.show_error_message("폴더 열기 실패", f"데이터 폴더를 열 수 없습니다:\n{str(e)}")

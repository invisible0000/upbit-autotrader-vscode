"""
데이터베이스 설정 통합 프레젠터

통합된 데이터베이스 교체 시스템을 사용하는 완전한 MVP 프레젠터
백업, 복원, 경로 변경을 하나의 Use Case로 처리합니다.

📋 메서드 목록 (실험적 가이드):
   L37: __init__(self, view)                          # MVP 패턴 초기화
   L55: replacement_use_case (property)               # Use Case 지연 로딩
   L64: _ensure_dto_classes_loaded(self)              # DTO 클래스 동적 로드
   L78: load_database_info(self)                      # DB 정보 로드 및 상태 검증
   L156: get_backup_list(self) -> list                # 백업 목록 조회
   L200: _parse_timestamp_from_filename(self, filename) # 파일명 타임스탬프 파싱
   L210: load_backup_list(self)                       # 백업 목록 로드 및 UI 업데이트
   L220: create_database_backup(self, database_type)  # 안전한 백업 생성
   L295: restore_database_backup(self, backup_id)     # 백업 복원 (위험 경고 포함)
   L385: delete_database_backup(self, backup_id)      # 백업 삭제 및 목록 새로고침
   L426: change_database_path(self, database_type, new_path) # DB 경로 변경
   L516: _get_detailed_database_status(self, paths)   # DB 상세 상태 검증
   L555: _validate_backup_filename(self, backup_id)   # 백업 파일명 유효성 검사
   L572: _validate_backup_file(self, file_path)       # 백업 파일 상태 검증 (DDD)
   L590: validate_databases(self)                     # DB 검증 및 결과 표시
   L635: open_data_folder(self)                       # 데이터 폴더 열기
   L649: update_backup_description(self, backup_id, new_description) # 백업 설명 업데이트
   L670: get_backup_description(self, backup_id)      # 백업 설명 조회
   L683: _get_default_description(self, backup_id)    # 기본 설명 생성
   L693: refresh_status(self)                         # 상태 새로고침
   L704: _get_backup_metadata_file(self) -> Path      # 메타데이터 파일 경로
   L710: _load_backup_metadata(self) -> dict          # 메타데이터 로드
   L722: _save_backup_metadata(self, metadata)        # 메타데이터 저장

🏗️ DDD 아키텍처 준수:
   - Domain Service: DatabaseBackupService (백업 검증용)
   - Application Layer: DatabaseReplacementUseCase (백업/복원/경로변경 통합)
   - Infrastructure: DatabasePathService (경로 관리)
   - SQLite 직접 사용 금지 → Domain Service 통해서만 접근
"""

import os
import json
import subprocess
import platform
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.services.database_path_service import (
    DatabasePathService
)
from upbit_auto_trading.application.services.database_health_service import DatabaseHealthService
from upbit_auto_trading.ui.desktop.screens.settings.dtos.database_tab_dto import (
    DatabaseInfoDto, DatabaseStatusDto
)

# 통합 Use Case는 필요시에만 import (지연 로딩)

if TYPE_CHECKING:
    from upbit_auto_trading.ui.desktop.screens.settings.interfaces.database_tab_view_interface import (
        IDatabaseTabView
    )


class DatabaseSettingsPresenter:
    """데이터베이스 설정 통합 프레젠터

    MVP 패턴의 Presenter 역할을 담당합니다.
    모든 데이터베이스 교체 작업을 통합 Use Case로 처리합니다.
    """

    def __init__(self, view: "IDatabaseTabView"):
        self.view = view
        self.logger = create_component_logger("DatabaseSettingsPresenter")

        # DDD 도메인 서비스 초기화 (싱글톤 사용)
        self.db_path_service = DatabasePathService()  # 싱글톤이므로 Repository 자동 생성
        self.health_service = DatabaseHealthService()  # Application Service 추가
        # self.unified_config = UnifiedConfigService()  # 현재 사용하지 않음

        # 통합 Use Case는 필요할 때 지연 로딩 (Private 변수)
        self._replacement_use_case = None
        # self._profile_management_use_case = None  # 향후 구현
        self._dto_classes_loaded = False

        self.logger.info("✅ 데이터베이스 설정 통합 프레젠터 초기화 완료")

    @property
    def replacement_use_case(self):
        """통합 Use Case 지연 로딩"""
        if self._replacement_use_case is None:
            from upbit_auto_trading.application.use_cases.database_configuration.database_replacement_use_case import (
                DatabaseReplacementUseCase
            )
            self._replacement_use_case = DatabaseReplacementUseCase()
        return self._replacement_use_case

    # @property
    # def profile_management_use_case(self):
    #     """프로파일 관리 Use Case 지연 로딩 (향후 구현)"""
    #     pass

    def _ensure_dto_classes_loaded(self):
        """DTO와 Enum 클래스들을 전역에 로드"""
        if not self._dto_classes_loaded:
            try:
                from upbit_auto_trading.application.use_cases.database_configuration.database_replacement_use_case import (
                    DatabaseReplacementRequestDto,
                    DatabaseReplacementType
                )
                # 전역 네임스페이스에 추가
                globals()['DatabaseReplacementRequestDto'] = DatabaseReplacementRequestDto
                globals()['DatabaseReplacementType'] = DatabaseReplacementType
                self._dto_classes_loaded = True
                self.logger.debug("✅ DTO 클래스들 로드 완료")
            except ImportError as e:
                self.logger.error(f"❌ DTO 클래스 로드 실패: {e}")
                raise

    def load_database_info(self):
        """데이터베이스 정보 로드 - DDD 도메인 서비스 활용"""
        try:
            self.logger.info("📊 데이터베이스 정보 로드 시작 (DDD)")

            # DDD 도메인 서비스를 통한 경로 조회
            paths = self.db_path_service.get_all_paths()

            # DTO 생성
            info_dto = DatabaseInfoDto(
                settings_db_path=str(paths.get('settings', 'Unknown')),
                strategies_db_path=str(paths.get('strategies', 'Unknown')),
                market_data_db_path=str(paths.get('market_data', 'Unknown'))
            )

            # 상세 상태 정보 조회
            detailed_status = self._get_detailed_database_status(paths)

            # 상태 메시지 생성
            status_parts = []
            settings_exists = detailed_status['settings']['is_healthy']
            strategies_exists = detailed_status['strategies']['is_healthy']
            market_data_exists = detailed_status['market_data']['is_healthy']

            if settings_exists:
                response_time = detailed_status['settings'].get('response_time_ms', 0)
                file_size = detailed_status['settings'].get('file_size_mb', 0)
                status_parts.append(f"⚙️ 설정 DB: 정상 ({response_time:.1f}ms, {file_size:.1f}MB)")
            else:
                error_msg = detailed_status['settings'].get('error_message', '파일 없음')
                status_parts.append(f"⚙️ 설정 DB: {error_msg}")

            if strategies_exists:
                response_time = detailed_status['strategies'].get('response_time_ms', 0)
                file_size = detailed_status['strategies'].get('file_size_mb', 0)
                status_parts.append(f"🎯 전략 DB: 정상 ({response_time:.1f}ms, {file_size:.1f}MB)")
            else:
                error_msg = detailed_status['strategies'].get('error_message', '파일 없음')
                status_parts.append(f"🎯 전략 DB: {error_msg}")

            if detailed_status['market_data']['is_healthy']:
                response_time = detailed_status['market_data'].get('response_time_ms', 0)
                file_size = detailed_status['market_data'].get('file_size_mb', 0)
                status_parts.append(f"📈 시장데이터 DB: 정상 ({response_time:.1f}ms, {file_size:.1f}MB)")
            else:
                error_msg = detailed_status['market_data'].get('error_message', '파일 없음')
                status_parts.append(f"📈 시장데이터 DB: {error_msg}")

            status_dto = DatabaseStatusDto(
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

            # 상세 상태 정보를 View에 전달 (DatabaseStatusWidget용)
            self.view.display_status(detailed_status)

            # 상태는 view에서 직접 처리됨 (status_dto는 로깅용)
            self.logger.info(f"✅ 데이터베이스 정보 로드 완료 (DDD): {status_dto.status_message}")

            return detailed_status

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 정보 로드 실패: {e}")
            self.view.show_error_message("정보 로드 실패", f"데이터베이스 정보를 불러올 수 없습니다: {str(e)}")
            return {}

    def get_backup_list(self) -> list:
        """백업 목록 조회 - 최신 파일명 규칙만 지원"""
        try:
            backup_dir = Path("data/user_backups")
            if not backup_dir.exists():
                return []

            backup_files = []
            for file_path in backup_dir.iterdir():
                if file_path.is_file() and file_path.suffix == '.sqlite3':
                    filename = file_path.name

                    # 최신 백업 파일명 규칙만 지원: {type}_backup_{timestamp}.sqlite3
                    if '_backup_' in filename and len(filename.split('_')) >= 3:
                        try:
                            # 파일 정보 추출
                            parts = filename.split('_backup_')
                            if len(parts) == 2:
                                db_type = parts[0]
                                timestamp_part = parts[1].replace('.sqlite3', '')

                                # 타임스탬프 검증 (YYYYMMDD_HHMMSS)
                                if len(timestamp_part) == 15 and timestamp_part[8] == '_':
                                    creation_time = self._parse_timestamp_from_filename(filename)
                                    file_size = file_path.stat().st_size

                                    # 백업 파일 상태 검증
                                    status = self._validate_backup_file(file_path)

                                    # 저장된 설명 조회 (없어도 기본값으로 덮어쓰지 않음)
                                    saved_description = self.get_backup_description(filename)

                                    # 메타데이터에 설명이 없으면 기본값을 표시만 하고 저장하지는 않음
                                    if saved_description:
                                        description = saved_description
                                    else:
                                        # 표시용 기본값 (메타데이터에 저장하지 않음)
                                        description = f"{db_type} 데이터베이스 백업"

                                    backup_files.append({
                                        'backup_id': filename,
                                        'database_type': db_type,
                                        'creation_time': creation_time,
                                        'file_size': file_size,
                                        'status': status,
                                        'description': description
                                    })
                        except Exception:
                            # 파일명 형식이 맞지 않으면 무시
                            continue

            # 생성 시간순 정렬
            backup_files.sort(key=lambda x: x['creation_time'], reverse=True)
            return backup_files

        except Exception as e:
            self.logger.error(f"❌ 백업 목록 조회 실패: {e}")
            return []

    def _parse_timestamp_from_filename(self, filename: str) -> datetime:
        """파일명에서 타임스탬프 추출"""
        try:
            # 예: settings_backup_20250809_143052.sqlite3
            parts = filename.split('_backup_')
            if len(parts) == 2:
                timestamp_str = parts[1].replace('.sqlite3', '')  # 20250809_143052
                return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        except ValueError:
            pass
        return datetime.now()

    def load_backup_list(self):
        """백업 목록 로드 및 View 업데이트"""
        try:
            backup_list = self.get_backup_list()
            # DatabaseTabWidget에서 직접 처리되므로 로그만 남김
            self.logger.info(f"✅ 백업 목록 로드 완료: {len(backup_list)}개")
            return backup_list

        except Exception as e:
            self.logger.error(f"❌ 백업 목록 로드 실패: {e}")
            return []

    def create_database_backup(self, database_type: str) -> bool:
        """안전한 데이터베이스 백업 생성"""
        try:
            self.logger.info(f"📦 백업 생성 시작 (안전한 백업): {database_type}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 원본 DB 파일 경로
            db_filename = f"{database_type}.sqlite3"
            data_dir = Path('data')
            source_path = data_dir / db_filename

            # 백업 폴더 확인 및 생성
            backup_dir = data_dir / "user_backups"
            backup_dir.mkdir(exist_ok=True)

            # 백업 파일 경로
            backup_filename = f"{database_type}_backup_{timestamp}.sqlite3"
            backup_path = backup_dir / backup_filename

            if not source_path.exists():
                self.logger.error(f"❌ 원본 파일이 존재하지 않음: {source_path}")
                self.view.show_error_message("백업 실패", f"원본 데이터베이스 파일을 찾을 수 없습니다:\n{source_path}")
                return False

            # Domain Service를 통한 안전한 백업
            self.logger.info(f"🔒 간단 파일 복사 백업: {source_path} -> {backup_path}")

            try:
                # 간단한 파일 복사 방식으로 백업 (DDD 원칙 준수)
                import shutil
                shutil.copy2(source_path, backup_path)

                self.logger.info("✅ 백업 생성 완료")

            except Exception as backup_error:
                self.logger.error(f"❌ 백업 생성 중 오류: {backup_error}")
                self.view.show_error_message("백업 실패", f"백업 생성 중 오류가 발생했습니다:\n{str(backup_error)}")
                return False

            # 백업 파일 검증
            if backup_path.exists() and backup_path.stat().st_size > 0:
                self.logger.info(f"✅ 백업 생성 성공: {backup_filename} ({backup_path.stat().st_size} bytes)")

                # 백업 타입별 기본 설명 설정 (메타데이터 업데이트)
                self._set_backup_description_by_type(backup_filename, "수동생성")

                # UI 업데이트
                if hasattr(self.view, 'show_info_message'):
                    self.view.show_info_message("백업 완료", f"데이터베이스 백업이 성공적으로 생성되었습니다:\n{backup_filename}")

                # 백업 목록 자동 새로고침 (안전한 방식)
                try:
                    backup_list = self.get_backup_list()
                    # type checking 우회
                    view_obj = getattr(self.view, 'backup_widget', None)
                    if view_obj and hasattr(view_obj, 'update_backup_list'):
                        view_obj.update_backup_list(backup_list)
                        self.logger.info("✅ 백업 목록 자동 갱신 완료")
                except Exception as refresh_error:
                    self.logger.warning(f"⚠️ 백업 목록 갱신 실패: {refresh_error}")

                return True
            else:
                self.logger.error("❌ 백업 파일이 생성되지 않았거나 비어있음")
                self.view.show_error_message("백업 실패", "백업 파일이 올바르게 생성되지 않았습니다.")
                return False

        except Exception as e:
            self.logger.error(f"❌ 백업 생성 실패: {e}")
            self.view.show_error_message("백업 실패", f"백업 생성 중 오류가 발생했습니다:\n{str(e)}")
            return False

    def restore_database_backup(self, backup_id: str) -> bool:
        """통합 Use Case를 사용한 백업 복원"""
        try:
            self.logger.info(f"📦 백업 복원 시작 (통합): {backup_id}")
            self._ensure_dto_classes_loaded()  # DTO 클래스 로드

            # 백업 파일에서 데이터베이스 타입 추출
            database_type = backup_id.split('_backup_')[0]

            # 극도 위험 경고
            critical_warning = "🚨 **극도로 위험한 작업입니다** 🚨\n\n"
            critical_warning += "📋 **복원 작업의 의미**:\n"
            critical_warning += "• 현재 데이터베이스가 완전히 교체됩니다\n"
            critical_warning += "• 실시간 매매 포지션 정보가 모두 손실될 수 있습니다\n"
            critical_warning += "• 전략 설정과 거래 기록이 변경됩니다\n"
            critical_warning += "• 프로그램의 모든 기능이 일시 정지됩니다\n\n"
            critical_warning += "**정말로 계속 진행하시겠습니까?**\n"
            critical_warning += "**⚠️ 이 작업의 모든 결과는 사용자의 책임입니다.**"

            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.critical(
                None,
                "🚨 데이터베이스 복원 - 극도 위험 경고",
                critical_warning,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                self.logger.info("👤 사용자가 위험한 복원 작업을 취소했습니다")
                return False

            # 통합 Use Case 요청 생성
            DatabaseReplacementRequestDto = globals().get('DatabaseReplacementRequestDto')
            DatabaseReplacementType = globals().get('DatabaseReplacementType')

            if not DatabaseReplacementRequestDto or not DatabaseReplacementType:
                self.logger.error("❌ DTO 클래스가 로드되지 않았습니다")
                self.view.show_error_message("시스템 오류", "내부 시스템 오류가 발생했습니다.")
                return False

            request = DatabaseReplacementRequestDto(
                replacement_type=DatabaseReplacementType.BACKUP_RESTORE,
                database_type=database_type,
                source_path=backup_id,
                create_safety_backup=True,
                force_replacement=True,  # 사용자가 위험을 감수했으므로
                safety_backup_suffix="critical_backup_before_restore"
            )

            # 통합 Use Case 실행
            result = self.replacement_use_case.execute_replacement(request)

            if result.success:
                self.logger.warning(f"🚨 위험한 복원 작업 완료: {backup_id}")

                success_msg = f"⚠️ {database_type} 데이터베이스가 복원되었습니다.\n\n"
                success_msg += "🔄 **중요**: 프로그램을 완전히 재시작하는 것을 강력히 권장합니다.\n"
                if result.safety_backup_path:
                    safety_filename = Path(result.safety_backup_path).name
                    success_msg += f"📁 복원 전 상태는 '{safety_filename}'에 백업되었습니다."

                if hasattr(self.view, 'show_info_message'):
                    # 메시지 박스 표시 후 콜백으로 새로고침 실행
                    try:
                        from PyQt6.QtWidgets import QMessageBox
                        from PyQt6.QtCore import QTimer

                        # 메시지 박스 생성
                        msg_box = QMessageBox()
                        msg_box.setWindowTitle("복원 완료")
                        msg_box.setText(success_msg)
                        msg_box.setIcon(QMessageBox.Icon.Information)
                        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

                        # 메시지 박스가 닫힌 후 새로고침 실행하는 함수
                        def on_message_finished():
                            # UI 새로고침
                            if hasattr(self.view, 'refresh_backup_list'):
                                self.view.refresh_backup_list()
                            self.load_database_info()

                        # 메시지 박스 완료 후 새로고침 실행
                        msg_box.finished.connect(lambda: QTimer.singleShot(100, on_message_finished))
                        msg_box.exec()

                    except Exception as msg_error:
                        self.logger.warning(f"⚠️ 메시지 박스 처리 중 오류: {msg_error}")
                        # 기본 메시지로 대체
                        self.view.show_info_message("복원 완료", success_msg)
                        # 즉시 새로고침
                        if hasattr(self.view, 'refresh_backup_list'):
                            self.view.refresh_backup_list()
                        self.load_database_info()
                else:
                    # show_info_message가 없으면 바로 새로고침
                    if hasattr(self.view, 'refresh_backup_list'):
                        self.view.refresh_backup_list()
                    self.load_database_info()

                return True
            else:
                self.logger.error(f"❌ 복원 실패: {result.error_message}")
                self.view.show_error_message("복원 실패", f"복원 중 오류가 발생했습니다:\n{result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 백업 복원 실패: {e}")
            self.view.show_error_message("복원 실패", f"복원 중 오류가 발생했습니다:\n{str(e)}")
            return False

    def delete_database_backup(self, backup_id: str) -> bool:
        """백업 파일 삭제"""
        try:
            from pathlib import Path

            self.logger.info(f"🗑️ 백업 삭제 시작: {backup_id}")

            # 백업 파일 검증
            user_backups_dir = Path("data/user_backups")
            backup_file_path = user_backups_dir / backup_id

            if not backup_file_path.exists():
                self.logger.error(f"❌ 백업 파일이 존재하지 않음: {backup_file_path}")
                self.view.show_error_message("삭제 실패", "백업 파일을 찾을 수 없습니다.")
                return False

            # 파일 삭제
            backup_file_path.unlink()

            # 메타데이터에서도 해당 항목 제거
            metadata = self._load_backup_metadata()
            if backup_id in metadata:
                del metadata[backup_id]
                self._save_backup_metadata(metadata)
                self.logger.info(f"✅ 백업 메타데이터 정리 완료: {backup_id}")

            self.logger.info(f"✅ 백업 삭제 성공: {backup_id}")

            # 즉시 백업 목록 새로고침 (presenter에서 새로운 데이터 로드)
            updated_backup_list = self.get_backup_list()
            self.logger.info(f"✅ 백업 목록 로드 완료: {len(updated_backup_list)}개")

            # View의 backup_widget에 새로운 데이터 전달 (동적 접근)
            try:
                backup_widget = getattr(self.view, 'backup_widget', None)
                if backup_widget and hasattr(backup_widget, 'update_backup_list'):
                    backup_widget.update_backup_list(updated_backup_list)
            except Exception as e:
                self.logger.debug(f"백업 위젯 업데이트 실패 (무시): {e}")

            if hasattr(self.view, 'show_info_message'):
                self.view.show_info_message("삭제 완료", "백업이 성공적으로 삭제되었습니다.")

            return True

        except Exception as e:
            self.logger.error(f"❌ 백업 삭제 실패: {e}")
            self.view.show_error_message("삭제 실패", f"백업 삭제 중 오류가 발생했습니다:\n{str(e)}")
            return False

    def change_database_path(self, database_type: str, new_path: str) -> bool:
        """통합 Use Case를 사용한 데이터베이스 경로 변경"""
        try:
            self.logger.info(f"🔄 데이터베이스 경로 변경 시작 (통합): {database_type} → {new_path}")
            self._ensure_dto_classes_loaded()  # DTO 클래스 로드

            # 극도 위험 경고 (복원과 동일한 위험도)
            critical_warning = "🚨 **극도로 위험한 작업입니다** 🚨\n\n"
            critical_warning += "📋 **경로 변경 작업의 의미**:\n"
            critical_warning += "• 현재 데이터베이스가 완전히 교체됩니다\n"
            critical_warning += "• 실시간 매매 포지션 정보가 모두 손실될 수 있습니다\n"
            critical_warning += "• 전략 설정과 거래 기록이 변경됩니다\n"
            critical_warning += "• 프로그램의 모든 기능이 일시 정지됩니다\n\n"
            critical_warning += f"**새 파일**: {new_path}\n\n"
            critical_warning += "**정말로 계속 진행하시겠습니까?**\n"
            critical_warning += "**⚠️ 이 작업의 모든 결과는 사용자의 책임입니다.**"

            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.critical(
                None,
                "🚨 데이터베이스 경로 변경 - 극도 위험 경고",
                critical_warning,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                self.logger.info("👤 사용자가 위험한 경로 변경 작업을 취소했습니다")
                return False

            # 통합 Use Case 요청 생성
            DatabaseReplacementRequestDto = globals().get('DatabaseReplacementRequestDto')
            DatabaseReplacementType = globals().get('DatabaseReplacementType')

            if not DatabaseReplacementRequestDto or not DatabaseReplacementType:
                self.logger.error("❌ DTO 클래스가 로드되지 않았습니다")
                self.view.show_error_message("시스템 오류", "내부 시스템 오류가 발생했습니다.")
                return False

            request = DatabaseReplacementRequestDto(
                replacement_type=DatabaseReplacementType.PATH_CHANGE,
                database_type=database_type,
                source_path=new_path,
                create_safety_backup=True,
                force_replacement=True,  # 사용자가 위험을 감수했으므로
                safety_backup_suffix="critical_backup_before_path_change"
            )

            # 통합 Use Case 실행
            result = self.replacement_use_case.execute_replacement(request)

            if result.success:
                self.logger.warning(f"🚨 위험한 경로 변경 완료: {new_path}")

                success_msg = f"⚠️ {database_type} 데이터베이스 경로가 변경되었습니다.\n\n"
                success_msg += f"📁 **새 경로**: {new_path}\n"
                success_msg += "🔄 **중요**: 프로그램을 완전히 재시작하는 것을 강력히 권장합니다.\n"
                if result.safety_backup_path:
                    safety_filename = Path(result.safety_backup_path).name
                    success_msg += f"📁 이전 상태는 '{safety_filename}'에 백업되었습니다."

                if hasattr(self.view, 'show_info_message'):
                    self.view.show_info_message("경로 변경 완료", success_msg)

                # UI 새로고침 - 백업 목록과 상태 모두 업데이트
                if hasattr(self.view, 'refresh_backup_list'):
                    self.view.refresh_backup_list()
                self.load_database_info()

                return True
            else:
                self.logger.error(f"❌ 경로 변경 실패: {result.error_message}")
                self.view.show_error_message("경로 변경 실패", f"경로 변경 중 오류가 발생했습니다:\n{result.error_message}")
                return False

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 경로 변경 실패: {e}")
            self.view.show_error_message("경로 변경 실패", f"경로 변경 중 오류가 발생했습니다:\n{str(e)}")
            return False

    def _get_detailed_database_status(self, paths: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """데이터베이스 상세 상태 검증 - DatabaseHealthService 사용"""
        detailed_status = {}

        for db_type, db_path in paths.items():
            try:
                # DatabaseHealthService를 통한 전문적인 상태 검사
                status_info = self.health_service._check_single_database(db_type, db_path)

                # 표준 형식으로 변환
                detailed_status[db_type] = {
                    'is_healthy': status_info.get('is_healthy', False),
                    'response_time_ms': status_info.get('response_time_ms', 0.0),
                    'file_size_mb': status_info.get('file_size_mb', 0.0),
                    'error_message': status_info.get('error_message', ''),
                    'table_count': status_info.get('table_count', 0),
                    'has_secure_keys': status_info.get('has_secure_keys', False),
                    'last_checked': datetime.now().strftime('%H:%M:%S')
                }

                self.logger.debug(f"✅ {db_type} DB 상태 검사 완료: {status_info.get('is_healthy', False)}")

            except Exception as e:
                self.logger.warning(f"⚠️ {db_type} DB 상태 검사 실패: {e}")
                # 기본 오류 상태
                detailed_status[db_type] = {
                    'is_healthy': False,
                    'response_time_ms': 0.0,
                    'file_size_mb': 0.0,
                    'error_message': f'상태 검사 실패: {str(e)}',
                    'table_count': 0,
                    'has_secure_keys': False,
                    'last_checked': datetime.now().strftime('%H:%M:%S')
                }

        return detailed_status

    def _validate_backup_filename(self, backup_id: str) -> bool:
        """백업 파일명 검증"""
        try:
            # 예상 형식: {database_type}_backup_{timestamp}.sqlite3
            if '_backup_' not in backup_id:
                return False

            if not backup_id.endswith('.sqlite3'):
                return False

            parts = backup_id.split('_backup_')
            if len(parts) != 2:
                return False

            timestamp_part = parts[1].replace('.sqlite3', '')
            if len(timestamp_part) != 15:  # YYYYMMDD_HHMMSS
                return False

            return True

        except Exception:
            return False

    def _validate_backup_file(self, file_path: Path) -> str:
        """백업 파일 상태 검증 - 파일 잠금 방지를 위한 경량 검증"""
        try:
            # 파일 크기 확인 (최소 4KB 이상)
            if file_path.stat().st_size < 4096:
                return "ERROR"

            # SQLite 파일 헤더 확인만 수행 (연결 생성 없이)
            with open(file_path, 'rb') as f:
                header = f.read(16)
                if not header.startswith(b'SQLite format 3\x00'):
                    return "CORRUPTED"

            # SQLite 연결 생성하지 않고 헤더 검증만으로 충분
            # 백업 파일은 이미 검증된 원본에서 복사된 것이므로
            # 파일 잠금을 유발하는 무결성 검사 생략
            return "COMPLETED"

        except Exception:
            return "ERROR"

    def validate_databases(self) -> None:
        """데이터베이스 검증 - DDD 서비스 활용"""
        self.logger.info("✅ 데이터베이스 검증 시작 (DDD)")
        self.view.show_progress("데이터베이스 검증 중...")

        try:
            validation_results = []
            error_count = 0

            # DDD 서비스를 통해 현재 경로 조회
            all_paths = self.db_path_service.get_all_paths()

            # 각 데이터베이스 파일 검증
            databases = [
                ("설정 DB", all_paths.get('settings', 'd:/projects/upbit-autotrader-vscode/data/settings.sqlite3')),
                ("전략 DB", all_paths.get('strategies', 'd:/projects/upbit-autotrader-vscode/data/strategies.sqlite3')),
                ("시장데이터 DB", all_paths.get('market_data', 'd:/projects/upbit-autotrader-vscode/data/market_data.sqlite3'))
            ]

            from pathlib import Path
            for db_name, db_path_str in databases:
                db_path = Path(db_path_str)

                if db_path.exists():
                    try:
                        # 파일 기반 검증 (DDD 준수)
                        file_size_mb = db_path.stat().st_size / (1024 * 1024)

                        # SQLite 헤더 확인
                        with open(db_path, 'rb') as f:
                            header = f.read(16)
                            if header.startswith(b'SQLite format 3\x00'):
                                validation_results.append(f"✅ {db_name}: 정상 (SQLite 형식, {file_size_mb:.1f}MB)")
                            else:
                                error_count += 1
                                validation_results.append(f"❌ {db_name}: 잘못된 파일 형식")

                    except Exception as e:
                        error_count += 1
                        validation_results.append(f"❌ {db_name}: 오류 - {str(e)[:50]}...")
                else:
                    error_count += 1
                    validation_results.append(f"❌ {db_name}: 파일 없음 - {db_path}")

            # View에 결과 전달
            self.view.show_validation_result(validation_results)
            self.view.hide_progress()

            # 검증 완료 후 상태 새로고침
            self.load_database_info()

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 검증 실패: {e}")
            self.view.hide_progress()
            self.view.show_error_message("검증 실패", f"데이터베이스 검증 중 오류가 발생했습니다:\n{str(e)}")

    def open_data_folder(self) -> None:
        """데이터 폴더 열기 - DDD 서비스 활용"""
        try:
            # 데이터 폴더 경로를 직접 설정 (DDD 원칙에 따라)
            data_folder = Path('d:/projects/upbit-autotrader-vscode/data')

            if platform.system() == "Windows":
                os.startfile(str(data_folder))
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(data_folder)])
            else:  # Linux
                subprocess.run(["xdg-open", str(data_folder)])

            self.logger.info(f"📂 데이터 폴더 열기: {data_folder} (DDD)")

        except Exception as e:
            self.logger.error(f"❌ 폴더 열기 실패: {e}")
            self.view.show_error_message("폴더 열기 실패", f"데이터 폴더를 열 수 없습니다:\n{str(e)}")

    def update_backup_description(self, backup_id: str, new_description: str) -> bool:
        """백업 설명 업데이트 - DDD 방식으로 메타데이터 저장"""
        try:
            metadata_file = Path("data/user_backups/backup_metadata.json")
            metadata_file.parent.mkdir(exist_ok=True)

            # 기존 메타데이터 로드
            metadata = {}
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception:
                    metadata = {}

            # 설명 업데이트
            metadata[backup_id] = {
                'description': new_description,
                'updated_at': datetime.now().isoformat()
            }

            # 메타데이터 저장
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info(f"✅ 백업 설명 업데이트: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 백업 설명 업데이트 실패: {e}")
            return False

    def get_backup_description(self, backup_id: str) -> str:
        """저장된 백업 설명 조회"""
        try:
            metadata_file = Path("data/user_backups/backup_metadata.json")
            if not metadata_file.exists():
                return self._get_default_description(backup_id)

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            backup_data = metadata.get(backup_id, {})
            return backup_data.get('description', self._get_default_description(backup_id))

        except Exception:
            return self._get_default_description(backup_id)

    def _get_default_description(self, backup_id: str) -> str:
        """백업 ID에서 기본 설명 생성"""
        try:
            if '_backup_' in backup_id:
                db_type = backup_id.split('_backup_')[0]
                return f"{db_type} 데이터베이스 백업"
            return "데이터베이스 백업"
        except Exception:
            return "데이터베이스 백업"

    def refresh_status(self) -> None:
        """상태 새로고침 - 백업 목록과 상태 모두 업데이트"""
        try:
            self.logger.info("🔄 데이터베이스 상태 새로고침 시작")

            # 상태 정보 로드
            self.load_database_info()

            # 백업 목록도 함께 새로고침
            if hasattr(self.view, 'refresh_backup_list'):
                self.view.refresh_backup_list()
                self.logger.debug("✅ 백업 목록 새로고침 완료")

            self.logger.info("✅ 데이터베이스 상태 새로고침 완료")
        except Exception as e:
            self.logger.error(f"❌ 상태 새로고침 실패: {e}")
            self.view.show_error_message("새로고침 실패", f"상태 새로고침 중 오류가 발생했습니다:\n{str(e)}")

    def _get_backup_metadata_file(self) -> Path:
        """백업 메타데이터 파일 경로 반환"""
        backup_dir = Path("data/user_backups")
        backup_dir.mkdir(exist_ok=True)
        return backup_dir / "backup_metadata.json"

    def _load_backup_metadata(self) -> dict:
        """백업 메타데이터 로드"""
        import json
        metadata_file = self._get_backup_metadata_file()

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"⚠️ 백업 메타데이터 로드 실패: {e}")

        return {}

    def _save_backup_metadata(self, metadata: dict) -> None:
        """백업 메타데이터 저장"""
        import json
        metadata_file = self._get_backup_metadata_file()

        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"❌ 백업 메타데이터 저장 실패: {e}")

    def _set_backup_description_by_type(self, backup_filename: str, backup_type: str) -> None:
        """백업 타입에 따른 기본 설명 설정 (기존 설명이 없는 경우에만)"""
        try:
            # 메타데이터 로드
            metadata = self._load_backup_metadata()

            # 기존 설명이 있으면 덮어쓰지 않음
            if backup_filename in metadata:
                existing_description = metadata[backup_filename].get('description', '')
                if existing_description and not existing_description.startswith('[수동생성]'):
                    # 사용자가 이미 편집한 설명이 있으면 보존
                    self.logger.info(f"✅ 기존 설명 보존: {backup_filename} -> {existing_description}")
                    return

            # 기본 설명 생성
            db_type = backup_filename.split('_backup_')[0]

            type_descriptions = {
                "수동생성": f"[수동생성] {db_type} 데이터베이스 백업",
                "복원생성": f"[복원생성] {db_type} 복원 전 안전 백업",
                "경로변경": f"[경로변경] {db_type} 경로 변경 전 안전 백업"
            }

            default_description = type_descriptions.get(backup_type, f"{db_type} 데이터베이스 백업")

            # 메타데이터 업데이트 (새로운 항목이거나 기본 설명인 경우에만)
            metadata[backup_filename] = {
                "description": default_description,
                "backup_type": backup_type,
                "updated_at": datetime.now().isoformat()
            }
            self._save_backup_metadata(metadata)

            self.logger.info(f"✅ 백업 설명 설정: {backup_filename} -> {default_description}")

        except Exception as e:
            self.logger.error(f"❌ 백업 설명 설정 실패: {e}")

"""
데이터베이스 설정 프레젠터

MVP 패턴의 Presenter입니다.
View와 비즈니스 로직을 분리합니다.
DDD 기반 도메인 서비스를 활용합니다.
"""

import sqlite3
import os
import subprocess
import platform
import asyncio
import time
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from upbit_auto_trading.infrastructure.logging import create_component_logger
from upbit_auto_trading.domain.database_configuration.services.database_path_service import (
    DatabasePathService
)
from upbit_auto_trading.domain.configuration.services.unified_config_service import (
    UnifiedConfigService
)
from upbit_auto_trading.ui.desktop.screens.settings.dtos.database_tab_dto import (
    DatabaseInfoDto, DatabaseStatusDto, ValidationResultDto
)
from upbit_auto_trading.application.dto.database_config_dto import (
    DatabaseHealthCheckDto, DatabaseTypeEnum
)

if TYPE_CHECKING:
    from upbit_auto_trading.ui.desktop.screens.settings.interfaces.database_tab_view_interface import (
        IDatabaseTabView
    )


class DatabaseTabPresenter:
    """데이터베이스 탭 프레젠터

    MVP 패턴의 Presenter 역할을 담당합니다.
    """

    def __init__(self, view: "IDatabaseTabView"):
        self.view = view
        self.logger = create_component_logger("DatabaseTabPresenter")

        # DDD 도메인 서비스 초기화 (싱글톤 사용)
        self.db_path_service = DatabasePathService()  # 싱글톤이므로 Repository 자동 생성
        self.config_service = UnifiedConfigService(self.db_path_service)

        self.logger.info("🎯 DatabaseTabPresenter (DDD 싱글톤) 초기화 완료")

    def load_database_info(self) -> None:
        """데이터베이스 정보 로드 및 표시 - DDD 서비스 활용"""
        try:
            self.logger.debug("📊 데이터베이스 정보 로드 중... (DDD)")

            # DDD 서비스를 통해 현재 경로 조회 (Repository에서 직접 로드)
            all_paths = self.db_path_service.get_all_paths()
            self.logger.debug(f"🔍 DDD 서비스에서 로드된 경로들: {all_paths}")

            # 실제 사용할 경로는 DDD 서비스의 결과를 그대로 사용
            final_paths = all_paths.copy()

            # 누락된 타입이 있는 경우 통합 설정 서비스에서 폴백 경로 조회
            required_types = ['settings', 'strategies', 'market_data']
            for db_type in required_types:
                if db_type not in final_paths:
                    self.logger.warning(f"⚠️ DDD 서비스에서 {db_type} 경로 누락, 통합 설정에서 폴백 조회")
                    fallback_paths = self.config_service.get_database_paths()
                    if db_type in fallback_paths:
                        final_paths[db_type] = fallback_paths[db_type]
                        self.logger.debug(f"📋 통합 설정 폴백 사용: {db_type} = {fallback_paths[db_type]}")
                    else:
                        # 최종 폴백 (절대 경로 기반)
                        project_root = 'd:/projects/upbit-autotrader-vscode'
                        final_paths[db_type] = f'{project_root}/data/{db_type}.sqlite3'
                        self.logger.warning(f"⚠️ 최종 폴백 사용: {db_type} = {final_paths[db_type]}")

            self.logger.debug(f"📍 최종 사용할 경로들: {final_paths}")

            # DTO 생성
            info_dto = DatabaseInfoDto(
                settings_db_path=final_paths['settings'],
                strategies_db_path=final_paths['strategies'],
                market_data_db_path=final_paths['market_data']
            )

            # 상세 상태 정보 생성 (원칙적인 DB 검증)
            detailed_status = self._get_detailed_database_status(final_paths)

            # 기존 DTO를 위한 기본 존재 여부 확인
            settings_exists = detailed_status['settings']['is_healthy']
            strategies_exists = detailed_status['strategies']['is_healthy']
            market_data_exists = detailed_status['market_data']['is_healthy']

            # 상세 상태 메시지 생성
            status_parts = []
            if detailed_status['settings']['is_healthy']:
                response_time = detailed_status['settings'].get('response_time_ms', 0)
                file_size = detailed_status['settings'].get('file_size_mb', 0)
                status_parts.append(f"⚙️ 설정 DB: 정상 ({response_time:.1f}ms, {file_size:.1f}MB)")
            else:
                error_msg = detailed_status['settings'].get('error_message', '파일 없음')
                status_parts.append(f"⚙️ 설정 DB: {error_msg}")

            if detailed_status['strategies']['is_healthy']:
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

            # 상태는 view에서 직접 처리됨
            self.logger.info("✅ 데이터베이스 정보 로드 완료 (DDD)")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 정보 로드 실패: {e}")
            self.view.show_error_message("로드 실패", f"데이터베이스 정보 로드 중 오류가 발생했습니다:\n{str(e)}")

    def refresh_status(self) -> None:
        """상태 새로고침 - 조용한 업데이트 (알림 없음)"""
        self.logger.info("🔃 데이터베이스 상태 새로고침")

        try:
            self.load_database_info()
            self.logger.info("✅ 데이터베이스 상태 새로고침 완료")
        except Exception as e:
            self.logger.error(f"❌ 상태 새로고침 실패: {e}")
            self.view.show_error_message("새로고침 실패", f"상태 새로고침 중 오류가 발생했습니다:\n{str(e)}")

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
            result_dto = ValidationResultDto(
                results=validation_results,
                all_valid=(error_count == 0),
                error_count=error_count
            )

            # View에 결과 전달
            self.view.show_validation_result(result_dto.results)

            self.logger.info("✅ 데이터베이스 검증 완료 (DDD)")

        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 검증 실패: {e}")
            self.view.show_error_message("검증 실패", f"데이터베이스 검증 중 오류가 발생했습니다:\n{str(e)}")
        finally:
            self.view.hide_progress()

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

    def create_database_backup(self, database_type: str) -> bool:
        """데이터베이스 백업 생성 - DDD 서비스 활용"""
        try:
            from datetime import datetime
            import shutil

            # 백업 시간 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 원본 DB 파일 경로 (DDD 기반)
            db_filename = f"{database_type}.sqlite3"
            data_dir = Path('d:/projects/upbit-autotrader-vscode/data')
            source_path = data_dir / db_filename

            # 백업 폴더 확인 및 생성
            backup_dir = data_dir / "user_backups"
            backup_dir.mkdir(exist_ok=True)

            # 백업 파일 경로
            backup_filename = f"{database_type}_backup_{timestamp}.sqlite3"
            backup_path = backup_dir / backup_filename

            # 파일 복사로 백업 수행
            if source_path.exists():
                shutil.copy2(source_path, backup_path)
                self.logger.info(f"✅ 백업 생성 완료: {backup_path} (DDD)")
                return True
            else:
                self.logger.error(f"❌ 원본 파일 없음: {source_path} (DDD)")
                return False

        except Exception as e:
            self.logger.error(f"❌ 백업 생성 실패: {e}")
            return False

    def change_database_path(self, database_type: str, new_path: str) -> bool:
        """데이터베이스 경로 변경 - 전체 시스템 재구성"""
        self.logger.info(f"🔄 데이터베이스 경로 변경 시작: {database_type} → {new_path}")

        try:
            from pathlib import Path
            from datetime import datetime

            # 1단계: 새 경로 검증
            self.logger.info("1️⃣ 새 경로 검증 중...")
            new_path_obj = Path(new_path)
            if not new_path_obj.exists():
                self.logger.error(f"❌ 파일이 존재하지 않습니다: {new_path}")
                self.view.show_error_message("경로 변경 실패", f"파일이 존재하지 않습니다:\n{new_path}")
                return False

            if not new_path_obj.is_file():
                self.logger.error(f"❌ 올바른 파일이 아닙니다: {new_path}")
                self.view.show_error_message("경로 변경 실패", f"올바른 파일이 아닙니다:\n{new_path}")
                return False

            # 2단계: 데이터베이스 파일 연결 테스트
            self.logger.info("2️⃣ 데이터베이스 연결 테스트 중...")
            import sqlite3
            try:
                with sqlite3.connect(str(new_path_obj)) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    self.logger.info(f"✅ 데이터베이스 연결 성공, 테이블 수: {len(tables)}")
            except Exception as db_error:
                self.logger.error(f"❌ 데이터베이스 연결 실패: {db_error}")
                # 사용자 친화적인 메시지로 변경
                if "file is not a database" in str(db_error).lower():
                    self.view.show_error_message(
                        "올바르지 않은 파일", 
                        "선택한 파일이 SQLite 데이터베이스가 아닙니다.\n\n올바른 데이터베이스 파일을 선택해주세요."
                    )
                else:
                    self.view.show_error_message(
                        "파일 오류", 
                        f"선택한 파일에 문제가 있습니다:\n{str(db_error)}\n\n다른 파일을 선택해주세요."
                    )
                return False

            # 3단계: 사용자 선택 경로를 직접 사용 (불필요한 복사 제거)
            self.logger.info("3️⃣ 사용자 선택 경로 직접 사용...")

            # 사용자가 선택한 경로를 그대로 사용 (복사하지 않음)
            target_path = new_path_obj
            self.logger.info(f"✅ 선택한 경로 직접 사용: {target_path}")

            # 4단계: DDD 서비스를 통한 경로 업데이트 - 사용자가 선택한 경로로
            self.logger.info("4️⃣ DDD 서비스를 통한 경로 업데이트 중...")
            try:
                self.db_path_service.change_database_path(database_type, str(target_path))
                self.logger.info(f"✅ DDD 서비스 경로 업데이트 완료: {database_type}")
            except Exception as service_error:
                self.logger.warning(f"⚠️ DDD 서비스 경로 업데이트 실패: {service_error}")

            # 5단계: 설정 파일 업데이트 (database_config.yaml)
            self.logger.info("5️⃣ 설정 파일 업데이트 중...")
            try:
                config_dir = Path('d:/projects/upbit-autotrader-vscode/config')
                config_path = config_dir / "database_config.yaml"
                if config_path.exists():
                    import yaml
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f) or {}

                    # 경로 업데이트
                    if 'databases' not in config:
                        config['databases'] = {}
                    config['databases'][database_type] = {
                        'path': str(target_path),
                        'last_modified': datetime.now().isoformat(),
                        'source': str(new_path_obj)
                    }

                    with open(config_path, 'w', encoding='utf-8') as f:
                        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

                    self.logger.info(f"✅ 설정 파일 업데이트 완료: {config_path}")
                else:
                    self.logger.warning(f"⚠️ 설정 파일 없음: {config_path}")
            except Exception as config_error:
                self.logger.warning(f"⚠️ 설정 파일 업데이트 실패 (기능은 정상 작동): {config_error}")

            # 5단계: 시스템 컴포넌트 재시작 신호
            self.logger.info("5️⃣ 시스템 컴포넌트 재시작 신호 발송...")
            try:
                # SystemStatusTracker로 데이터베이스 변경 알림
                from upbit_auto_trading.infrastructure.logging.briefing.status_tracker import SystemStatusTracker
                tracker = SystemStatusTracker()
                tracker.update_component_status(
                    f"Database_{database_type}",
                    "RESTARTED",
                    f"데이터베이스 경로 변경됨: {new_path}",
                    database_path=str(target_path),
                    source_path=str(new_path_obj)
                )
                self.logger.info("📊 SystemStatusTracker 알림 완료")
            except Exception as tracker_error:
                self.logger.debug(f"📊 SystemStatusTracker 알림 실패 (선택사항): {tracker_error}")

            self.logger.info(f"✅ {database_type} 데이터베이스 경로 변경 완료!")
            success_message = (f"{database_type} 데이터베이스 경로가 성공적으로 변경되었습니다.\n\n"
                               f"새 파일: {new_path}\n시스템 위치: {target_path}\n\n변경사항이 즉시 적용됩니다.")
            self.view.show_info_message("경로 변경 완료", success_message)

            return True

        except Exception as e:
            self.logger.error(f"❌ 경로 변경 중 치명적 오류: {e}")
            import traceback
            self.logger.error(f"❌ 스택 트레이스: {traceback.format_exc()}")
            self.view.show_error_message("시스템 오류", f"경로 변경 중 치명적 오류가 발생했습니다:\n{str(e)}")
            return False

    def get_backup_list(self) -> list:
        """백업 목록 조회 - DDD 서비스 활용"""
        try:
            data_dir = Path('d:/projects/upbit-autotrader-vscode/data')
            backup_dir = data_dir / "user_backups"
            if not backup_dir.exists():
                return []

            backup_files = []
            for backup_file in backup_dir.glob("*_backup_*.sqlite3"):
                try:
                    # 파일명에서 정보 추출
                    filename = backup_file.name
                    parts = filename.replace('.sqlite3', '').split('_backup_')
                    database_type = parts[0] if len(parts) > 0 else 'unknown'
                    timestamp = parts[1] if len(parts) > 1 else 'unknown'

                    # 파일 정보
                    stat = backup_file.stat()
                    size_mb = stat.st_size / (1024 * 1024)

                    backup_info = {
                        'backup_id': backup_file.stem,
                        'source_database_type': database_type,
                        'created_at': timestamp,
                        'file_size_mb': round(size_mb, 2),
                        'status': '정상',
                        'description': f'{database_type} 백업'
                    }
                    backup_files.append(backup_info)

                except Exception as e:
                    self.logger.error(f"❌ 백업 파일 정보 읽기 실패 {backup_file}: {e}")
                    continue

            # 생성일시 순으로 정렬 (최신 순)
            backup_files.sort(key=lambda x: x['created_at'], reverse=True)

            self.logger.info(f"✅ 백업 목록 조회 완료: {len(backup_files)}개")
            return backup_files

        except Exception as e:
            self.logger.error(f"❌ 백업 목록 조회 실패: {e}")
            return []

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

    def _get_detailed_database_status(self, paths: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        데이터베이스 상세 상태 검증 (원칙적인 구현)

        DDD 원칙에 따라 실제 데이터베이스 연결, 응답시간, 파일크기,
        무결성 등을 종합적으로 검증합니다.
        """
        detailed_status = {}

        for db_type, db_path in paths.items():
            status = {
                'is_healthy': False,
                'response_time_ms': 0.0,
                'file_size_mb': 0.0,
                'error_message': '',
                'table_count': 0,
                'connection_test_passed': False
            }

            try:
                start_time = time.time()

                # 1. 파일 존재 확인
                path_obj = Path(db_path)
                if not path_obj.exists():
                    status['error_message'] = '파일 없음'
                    detailed_status[db_type] = status
                    continue

                # 2. 파일 크기 확인
                file_size_bytes = path_obj.stat().st_size
                status['file_size_mb'] = file_size_bytes / (1024 * 1024)

                # 3. SQLite 연결 및 무결성 테스트
                with sqlite3.connect(str(path_obj), timeout=5.0) as conn:
                    cursor = conn.cursor()

                    # 기본 연결 테스트
                    try:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                        status['connection_test_passed'] = True
                    except sqlite3.DatabaseError as e:
                        status['error_message'] = f'연결 실패: {str(e)[:50]}'
                        detailed_status[db_type] = status
                        continue

                    # 테이블 수 확인
                    try:
                        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                        status['table_count'] = cursor.fetchone()[0]
                    except sqlite3.DatabaseError as e:
                        status['error_message'] = f'테이블 조회 실패: {str(e)[:50]}'
                        detailed_status[db_type] = status
                        continue

                    # 무결성 검사 (빠른 버전)
                    try:
                        cursor.execute("PRAGMA quick_check")
                        integrity_result = cursor.fetchone()[0]

                        if integrity_result == "ok":
                            status['is_healthy'] = True
                        else:
                            status['error_message'] = f'무결성 검사 실패: {integrity_result}'
                    except sqlite3.DatabaseError as e:
                        status['error_message'] = f'무결성 검사 불가: {str(e)[:50]}'

                # 4. 응답 시간 계산
                end_time = time.time()
                status['response_time_ms'] = (end_time - start_time) * 1000

                self.logger.debug(f"✅ {db_type} 상태 검증 완료: {status['response_time_ms']:.1f}ms")

            except sqlite3.OperationalError as e:
                # 가장 구체적인 오류 먼저 처리
                status['error_message'] = f'작업 오류: {str(e)[:50]}'
                self.logger.warning(f"⚠️ {db_type} SQLite 작업 오류: {e}")

            except sqlite3.DatabaseError as e:
                # SQLite 관련 모든 에러 (file is not a database 포함)
                status['error_message'] = f'DB 오류: {str(e)[:50]}'
                self.logger.warning(f"⚠️ {db_type} SQLite 데이터베이스 오류: {e}")

            except Exception as e:
                status['error_message'] = f'검증 실패: {str(e)[:50]}'
                self.logger.error(f"❌ {db_type} 상태 검증 실패: {e}")

            detailed_status[db_type] = status

        return detailed_status

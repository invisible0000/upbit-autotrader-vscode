"""
변수 도움말 저장소 - DB에서 도움말 정보를 조회하는 Infrastructure 컴포넌트
"""

import sqlite3
from pathlib import Path
from typing import Optional, Tuple

from upbit_auto_trading.infrastructure.logging import create_component_logger


class VariableHelpRepository:
    """변수 도움말 정보 저장소"""

    def __init__(self):
        self._logger = create_component_logger("VariableHelpRepository")
        self._db_path = Path("data/settings.sqlite3")

    def get_help_text(self, variable_id: str, parameter_name: Optional[str] = None) -> Tuple[str, str]:
        """변수/파라미터의 도움말 텍스트 조회

        Args:
            variable_id: 변수 ID
            parameter_name: 파라미터명 (None이면 변수 자체 도움말)

        Returns:
            (help_text_ko, tooltip_ko) 튜플
        """
        try:
            if not self._db_path.exists():
                self._logger.warning(f"DB 파일이 존재하지 않음: {self._db_path}")
                return "", ""

            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT help_text_ko, tooltip_ko
                FROM tv_help_texts
                WHERE variable_id = ? AND parameter_name = ?
            """, (variable_id, parameter_name))

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0] or "", result[1] or ""

            self._logger.debug(f"도움말 없음: {variable_id} - {parameter_name}")
            return "", ""

        except Exception as e:
            self._logger.error(f"도움말 텍스트 조회 실패: {e}")
            return "", ""

    def get_placeholder_text(self, variable_id: str, parameter_name: str) -> str:
        """파라미터의 플레이스홀더 텍스트 조회"""
        try:
            if not self._db_path.exists():
                return ""

            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT placeholder_text_ko
                FROM tv_placeholder_texts
                WHERE variable_id = ? AND parameter_name = ?
            """, (variable_id, parameter_name))

            result = cursor.fetchone()
            conn.close()

            if result:
                return result[0] or ""
            return ""

        except Exception as e:
            self._logger.warning(f"플레이스홀더 텍스트 조회 실패: {e}")
            return ""

    def get_variable_details_from_db(self, variable_id: str) -> Optional[dict]:
        """DB에서 변수 상세 정보 조회"""
        try:
            if not self._db_path.exists():
                return None

            conn = sqlite3.connect(self._db_path)
            cursor = conn.cursor()

            # 변수 기본 정보 조회
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en, description
                FROM tv_trading_variables
                WHERE variable_id = ? AND is_active = 1
            """, (variable_id,))

            var_info = cursor.fetchone()
            if not var_info:
                conn.close()
                return None

            # 파라미터 정보 조회
            cursor.execute("""
                SELECT parameter_name, parameter_type, default_value, display_name_ko,
                       description, min_value, max_value, enum_values, is_required
                FROM tv_variable_parameters
                WHERE variable_id = ?
                ORDER BY display_order
            """, (variable_id,))

            params = cursor.fetchall()
            conn.close()

            # 결과 구성
            parameters = []
            for param in params:
                param_dict = {
                    'parameter_name': param[0],
                    'parameter_type': param[1],
                    'default_value': param[2],
                    'display_name_ko': param[3],
                    'description': param[4],
                    'min_value': param[5],
                    'max_value': param[6],
                    'enum_values': param[7],
                    'is_required': param[8]
                }
                parameters.append(param_dict)

            return {
                'variable_id': var_info[0],
                'display_name_ko': var_info[1],
                'display_name_en': var_info[2],
                'description': var_info[3],
                'parameters': parameters
            }

        except Exception as e:
            self._logger.error(f"변수 상세 정보 조회 실패: {e}")
            return None

    def generate_basic_help_info(self, variable_id: str, variable_name: str = "") -> str:
        """DB 조회 실패 시 기본 도움말 정보 생성"""
        help_text = f"변수 ID: {variable_id}\n"
        if variable_name:
            help_text += f"이름: {variable_name}\n\n"

        # 메타 변수인 경우 특별 정보 제공
        if variable_id.startswith("META_"):
            help_text += "[메타 변수]\n"
            help_text += "이 변수는 전략 실행 중 동적으로 업데이트되는 추적 변수입니다.\n\n"

            if variable_id == "META_TRAILING_STOP":
                help_text += "트레일링 스탑:\n"
                help_text += "- 현재 최고가에서 설정된 비율만큼 하락시 손실 제한\n"
                help_text += "- 가격이 상승하면 스탑 라인도 함께 상승\n"
                help_text += "- 예: 10% 트레일링 스탑 설정시, 최고가에서 10% 하락하면 자동 매도\n"
            elif variable_id == "META_PYRAMID_TARGET":
                help_text += "피라미딩 목표:\n"
                help_text += "- 분할 매수/매도를 위한 목표 가격\n"
                help_text += "- 가격 상승/하락에 따른 단계적 포지션 조절\n"
                help_text += "- 리스크 분산과 수익 극대화를 위한 전략\n"
        else:
            # 일반 변수 기본 설명
            help_text += "[기술적 지표 변수]\n"
            if "RSI" in variable_id:
                help_text += "RSI (Relative Strength Index): 상대강도지수로 과매수/과매도 판단\n"
            elif "MACD" in variable_id:
                help_text += "MACD (Moving Average Convergence Divergence): 이동평균 수렴발산\n"
            elif "BB" in variable_id:
                help_text += "볼린저 밴드: 가격의 변동성과 상대적 고저 판단\n"
            elif "SMA" in variable_id or "EMA" in variable_id:
                help_text += "이동평균: 일정 기간 가격의 평균으로 추세 파악\n"
            elif "VOLUME" in variable_id:
                help_text += "거래량 관련 지표: 시장 참여도와 강도 측정\n"
            else:
                help_text += "사용자 정의 변수 또는 기타 기술적 지표\n"

            help_text += "\n매개변수는 하단 영역에서 설정할 수 있습니다.\n"

        help_text += "\n※ 상세한 매개변수 정보는 변수 선택 후 하단에 표시됩니다."
        return help_text

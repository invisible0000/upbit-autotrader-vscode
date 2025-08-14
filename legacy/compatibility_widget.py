#!/usr/bin/env python3
"""
호환성 검증 위젯 - 조건 빌더 컴포넌트

변수 간 호환성 검증 및 상태 표시를 담당하는 독립적인 위젯입니다.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox
)
from PyQt6.QtCore import pyqtSignal
from typing import Dict, Any, Optional

from upbit_auto_trading.infrastructure.logging import create_component_logger

# 호환성 검증 시스템 import
try:
    from ...trigger_builder.components.shared.compatibility_validator import (
        check_compatibility_with_status
    )
    COMPATIBILITY_SERVICE_AVAILABLE = True
except ImportError:
    COMPATIBILITY_SERVICE_AVAILABLE = False


class CompatibilityWidget(QWidget):
    """호환성 검증 위젯

    변수 간 호환성 검증 및 실시간 상태 표시를 담당합니다.
    단일 책임 원칙을 따라 호환성 관련 기능만 처리합니다.

    Signals:
        compatibility_checked: 호환성 검증 완료 시 발생 (is_compatible, status_info)
    """

    # 시그널 정의
    compatibility_checked = pyqtSignal(bool, dict)  # is_compatible, status_info

    def __init__(self, parent=None):
        """호환성 검증 위젯 초기화"""
        super().__init__(parent)
        self.logger = create_component_logger("CompatibilityWidget")

        # 현재 검증 상태
        self.current_variable1 = None
        self.current_variable2 = None
        self.current_status = None

        # UI 초기화
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 호환성 상태 그룹
        status_group = QGroupBox("🔍 호환성 검증")
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(6)

        # 상태 표시 라벨
        self.status_label = QLabel("변수를 선택하면 호환성을 확인합니다.")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 11px;
                color: #495057;
            }
        """)
        status_layout.addWidget(self.status_label)

        # 제안 사항 라벨 (호환 가능한 변수 제안)
        self.suggestion_label = QLabel()
        self.suggestion_label.setWordWrap(True)
        self.suggestion_label.setStyleSheet("""
            QLabel {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                padding: 6px;
                border-radius: 3px;
                margin: 2px 0;
                font-size: 10px;
                color: #0066cc;
            }
        """)
        self.suggestion_label.hide()  # 초기에는 숨김
        status_layout.addWidget(self.suggestion_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        self.setLayout(layout)

    def check_variable_compatibility(self, var1_id: str, var2_id: str):
        """두 변수 간 호환성 검증 (변수 ID 기반)"""
        if not COMPATIBILITY_SERVICE_AVAILABLE:
            self._show_fallback_status()
            return

        try:
            # 호환성 검증 실행
            compatibility_result, reason, suggestion = check_compatibility_with_status(
                var1_id, var2_id
            )

            is_compatible = compatibility_result == 1  # 1이 호환 가능
            status_info = {'reason': reason, 'suggestion': suggestion}

            self.current_status = {
                'compatible': is_compatible,
                'details': status_info
            }

            # UI 업데이트
            self._update_status_display(is_compatible, status_info)

            # 시그널 발생
            self.compatibility_checked.emit(is_compatible, status_info)

            self.logger.debug(f"호환성 검증 완료: {is_compatible} - {reason}")

        except Exception as e:
            self.logger.error(f"호환성 검증 실패: {e}")
            self._show_error_status(str(e))

    def check_single_variable_compatibility(self, var_info: Dict[str, Any]):
        """단일 변수의 호환 가능한 변수들 제안"""
        if not COMPATIBILITY_SERVICE_AVAILABLE:
            return

        try:
            # 호환 가능한 변수 타입 확인
            comparison_group = var_info.get('comparison_group', 'unknown')

            suggestion_text = self._generate_suggestion_text(comparison_group)

            if suggestion_text:
                self.suggestion_label.setText(suggestion_text)
                self.suggestion_label.show()
            else:
                self.suggestion_label.hide()

        except Exception as e:
            self.logger.error(f"호환성 제안 실패: {e}")
            self.suggestion_label.hide()

    def _update_status_display(self, is_compatible: bool, status_info: Dict[str, Any]):
        """호환성 상태 UI 업데이트"""
        if is_compatible:
            # 호환 가능 - 초록색
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 2px 0;
                    font-size: 11px;
                    color: #155724;
                }
            """)
            status_text = "✅ 호환 가능"

            # 상세 정보 추가
            if 'reason' in status_info:
                status_text += f"\n📝 {status_info['reason']}"

        else:
            # 호환 불가 - 빨간색
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    padding: 8px;
                    border-radius: 4px;
                    margin: 2px 0;
                    font-size: 11px;
                    color: #721c24;
                }
            """)
            status_text = "❌ 호환 불가"

            # 상세 정보 추가
            if 'reason' in status_info:
                status_text += f"\n📝 {status_info['reason']}"

        self.status_label.setText(status_text)

    def _show_fallback_status(self):
        """호환성 검증 서비스가 없을 때 표시"""
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 11px;
                color: #856404;
            }
        """)
        self.status_label.setText("⚠️ 호환성 검증 서비스를 사용할 수 없습니다.")

    def _show_error_status(self, error_message: str):
        """오류 상태 표시"""
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 11px;
                color: #721c24;
            }
        """)
        self.status_label.setText(f"❌ 호환성 검증 오류: {error_message}")

    def _generate_suggestion_text(self, comparison_group: str) -> str:
        """호환 가능한 변수 그룹 제안 텍스트 생성"""
        suggestions = {
            'price_comparable': "💰 현재가, 고가, 저가, 시가 등과 호환",
            'percentage_comparable': "📊 RSI, 스토캐스틱, %R 등과 호환",
            'zero_centered': "⚖️ MACD, CCI, Williams %R 등과 호환",
            'volume_comparable': "📦 거래량, 거래대금 등과 호환"
        }

        return suggestions.get(comparison_group, "")

    # === 공개 API ===

    def get_current_status(self) -> Optional[Dict[str, Any]]:
        """현재 호환성 상태 반환"""
        return self.current_status

    def clear_status(self):
        """상태 초기화"""
        self.status_label.setText("변수를 선택하면 호환성을 확인합니다.")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
                font-size: 11px;
                color: #495057;
            }
        """)
        self.suggestion_label.hide()
        self.current_status = None

    def is_compatible(self) -> bool:
        """현재 호환성 상태 반환"""
        if self.current_status:
            return self.current_status.get('compatible', False)
        return False

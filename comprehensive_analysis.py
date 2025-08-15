#!/usr/bin/env python3
"""
로깅 시스템 및 초기화 문제 종합 분석 스크립트

분석 항목:
1. urllib3, asyncio 외부 라이브러리 디버그 메시지 제거
2. matplotlib 디버그 메시지 원론적 해결
3. 트리거 빌더 중복 초기화 문제 분석
4. 탭별 선별적 초기화 방안
5. external_variable 기능 추적 분석
"""

import os
import sys
from pathlib import Path

def analyze_logging_issues():
    """로깅 시스템 문제 분석"""

    print("=== 1. 로깅 시스템 문제 분석 ===\n")

    # 1. urllib3 디버그 메시지 분석
    print("📋 1-1. urllib3/requests 디버그 메시지")
    print("  문제: DEBUG:urllib3.connectionpool 메시지가 Infrastructure 로깅과 혼재")
    print("  원인: requests 라이브러리가 자체 로깅 사용")
    print("  해결: urllib3 로거 레벨을 WARNING으로 설정")

    # 2. asyncio 디버그 메시지 분석
    print("\n📋 1-2. asyncio 디버그 메시지")
    print("  문제: DEBUG:asyncio:Using proactor 메시지")
    print("  원인: PyQt6와 asyncio 이벤트 루프 초기화 시 자동 출력")
    print("  해결: asyncio 로거 레벨 조정")

    # 3. matplotlib 디버그 메시지 분석
    print("\n📋 1-3. matplotlib 디버그 메시지")
    print("  문제: DEBUG:matplotlib 폰트/설정 메시지 과다")
    print("  원인: matplotlib 초기화 시 자체 로깅 시스템 사용")
    print("  해결: matplotlib 로거 레벨을 WARNING으로 설정")

def analyze_initialization_problems():
    """초기화 문제 분석"""

    print("\n=== 2. 초기화 문제 분석 ===\n")

    print("📋 2-1. 트리거 빌더 중복 초기화 문제")
    print("  관찰된 현상:")
    print("    - TriggerBuilderPresenter 초기화가 여러 번 발생")
    print("    - 변수 목록 로드가 반복됨")
    print("    - DB 연결/종료가 과도하게 발생")

    print("\n  추정 원인:")
    print("    1. 탭 전환 시마다 위젯 재생성")
    print("    2. MVP 패턴에서 Presenter 중복 생성")
    print("    3. 시그널 연결 과정에서 중복 초기화")

    print("\n📋 2-2. 리소스 낭비 문제")
    print("  현재 상황: 모든 탭이 동시 초기화")
    print("  문제점: 사용하지 않는 탭도 리소스 소모")
    print("  해결방안: Lazy Loading + 선별적 갱신")

def analyze_external_variable_feature():
    """external_variable 기능 심층 분석"""

    print("\n=== 3. external_variable 기능 분석 ===\n")

    print("📋 3-1. external_variable의 정의")
    print("  목적: 다른 변수의 값을 참조하는 파라미터")
    print("  예시: tracking_variable = 'RSI' (RSI 변수의 현재값 추적)")

    print("\n📋 3-2. 사용 사례 분석")
    print("  1. PYRAMID_TARGET.tracking_variable")
    print("     - 값: 'RSI', 'MACD', '종가' 등")
    print("     - 역할: 어떤 변수를 추적할지 지정")
    print("     - 계산: RSI > 30일 때 불타기 실행")

    print("\n  2. META_TRAILING_STOP.tracking_variable")
    print("     - 값: 'HIGH_PRICE', 'RSI', 'BOLLINGER_BAND' 등")
    print("     - 역할: 트레일링 스탑의 기준 변수")
    print("     - 계산: 지정된 변수의 극값 추적하여 스탑 조정")

    print("\n  3. META_PRICE_BREAKOUT.source_variable")
    print("     - 값: '종가', '고가', 'SMA_20' 등")
    print("     - 역할: 돌파 감지의 기준 가격")
    print("     - 계산: source_variable > reference_value 돌파 감지")

def analyze_trigger_builder_workflow():
    """트리거 빌더에서 external_variable 처리 흐름"""

    print("\n📋 3-3. 트리거 빌더 처리 흐름")

    workflow_steps = [
        "1. 사용자가 조건 생성 시 변수 선택",
        "2. 변수에 external_variable 파라미터 있으면",
        "3. UI에서 다른 변수 목록 드롭다운 표시",
        "4. 사용자가 참조할 변수 선택 (예: RSI)",
        "5. 트리거 실행 시 실시간으로 RSI 값 조회",
        "6. 조건 계산에 RSI 현재값 사용",
        "7. 조건 만족 시 매매 신호 생성"
    ]

    for step in workflow_steps:
        print(f"     {step}")

    print("\n📋 3-4. 계산 예시")
    print("  조건: PYRAMID_TARGET.tracking_variable = 'RSI'")
    print("       PYRAMID_TARGET.difference_value = 5.0")
    print("  계산: if RSI >= (진입시_RSI + 5.0): 불타기_실행()")
    print("  실시간: RSI 값이 30 → 35로 상승 시 불타기 트리거")

def generate_logging_fix_script():
    """로깅 문제 해결 스크립트 생성"""

    print("\n=== 4. 해결 방안 ===\n")

    print("📝 4-1. 로깅 레벨 조정 코드")

    fix_code = '''
# Infrastructure 로깅 초기화 시 추가할 코드
import logging

def configure_external_loggers():
    """외부 라이브러리 로거 레벨 조정"""

    # urllib3 디버그 메시지 억제
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    # requests 디버그 메시지 억제
    logging.getLogger("requests").setLevel(logging.WARNING)

    # asyncio 디버그 메시지 억제
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # matplotlib 디버그 메시지 억제
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

    print("✅ 외부 라이브러리 로거 레벨 조정 완료")
'''

    print(fix_code)

    print("📝 4-2. 탭별 Lazy Loading 설계")

    lazy_loading_design = '''
class StrategyManagementScreen:
    def __init__(self):
        self._active_tabs = {}  # 초기화된 탭들
        self._tab_widget = QTabWidget()

        # 탭 생성만 하고 내용은 지연 로딩
        self._setup_tab_headers()
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, index):
        """탭 변경 시에만 해당 탭 초기화"""
        tab_name = self._get_tab_name(index)

        if tab_name not in self._active_tabs:
            self._initialize_tab(tab_name)
            self._active_tabs[tab_name] = True
'''

    print(lazy_loading_design)

def check_current_external_variable_usage():
    """현재 external_variable 사용 현황 확인"""

    print("\n📋 3-5. 현재 DB에서 external_variable 사용 현황")

    check_script = '''
import sqlite3

conn = sqlite3.connect('data/settings.sqlite3')
cursor = conn.cursor()

# external_variable 타입 파라미터들 조회
cursor.execute("""
    SELECT variable_id, parameter_name, default_value, description
    FROM tv_variable_parameters
    WHERE parameter_type = 'external_variable'
    ORDER BY variable_id, parameter_name
""")

print("현재 external_variable 파라미터들:")
for var_id, param_name, default_value, description in cursor.fetchall():
    print(f"  {var_id}.{param_name}")
    print(f"    - 기본값: {default_value}")
    print(f"    - 설명: {description}")
    print()

conn.close()
'''

    print(check_script)

if __name__ == "__main__":
    print("🔍 종합 분석 리포트")
    print("=" * 50)

    analyze_logging_issues()
    analyze_initialization_problems()
    analyze_external_variable_feature()
    analyze_trigger_builder_workflow()
    generate_logging_fix_script()
    check_current_external_variable_usage()

    print("\n" + "=" * 50)
    print("🎯 우선순위 해결 과제:")
    print("1. 외부 라이브러리 로거 레벨 조정")
    print("2. 트리거 빌더 중복 초기화 방지")
    print("3. 탭별 Lazy Loading 구현")
    print("4. external_variable UI 지원 구현")
    print("=" * 50)

#!/usr/bin/env python3
"""
조건 다이얼로그 자동 호출 문제 추적 스크립트
"""

import sys
import os

# 프로젝트 루트를 경로에 추가
sys.path.append('.')

def trace_save_condition_calls():
    """save_condition 호출을 추적하는 스크립트"""
    
    print("🔍 save_condition 자동 호출 원인 조사")
    print("=" * 60)
    
    # ConditionDialog에 디버그 래퍼 추가
    original_save_condition = None
    
    try:
        from components.condition_dialog import ConditionDialog
        
        # 원본 메서드 백업
        original_save_condition = ConditionDialog.save_condition
        
        def debug_save_condition(self):
            """디버그용 save_condition 래퍼"""
            import traceback
            print("\n🚨 save_condition 호출됨!")
            print("호출 스택:")
            traceback.print_stack()
            
            # 원본 메서드 호출
            return original_save_condition(self)
        
        # 메서드 교체
        ConditionDialog.save_condition = debug_save_condition
        
        print("✅ ConditionDialog.save_condition에 디버그 래퍼 적용")
        
        # IntegratedConditionManager 초기화 시뮬레이션
        print("\n📱 IntegratedConditionManager 초기화 시뮬레이션...")
        
        # QApplication 없이는 실제 위젯을 생성할 수 없으므로 
        # 초기화 로직만 분석
        
        print("✅ 디버그 설정 완료")
        print("\n💡 실제 UI를 실행하여 호출 스택을 확인하세요.")
        
    except Exception as e:
        print(f"❌ 디버그 설정 실패: {str(e)}")
    
    finally:
        # 원본 메서드 복원
        if original_save_condition:
            try:
                ConditionDialog.save_condition = original_save_condition
                print("✅ 원본 메서드 복원 완료")
            except:
                pass

def check_event_connections():
    """이벤트 연결 상태 확인"""
    
    print("\n🔗 이벤트 연결 분석")
    print("=" * 60)
    
    # 가능한 자동 호출 원인들
    possible_causes = [
        "save_btn.clicked.connect(self.save_current_condition) - 저장 버튼 더블 클릭",
        "키보드 단축키 (Ctrl+S 등)",
        "초기화 중 자동 저장 로직",
        "시그널 연결 중 즉시 호출",
        "condition_dialog.condition_saved.connect() 시그널",
        "텍스트 변경 이벤트에서 자동 검증",
        "위젯 포커스 변경 시 검증"
    ]
    
    print("🔍 가능한 자동 호출 원인들:")
    for i, cause in enumerate(possible_causes, 1):
        print(f"  {i}. {cause}")
    
    print("\n💡 해결 방안:")
    print("  1. save_condition 호출 전에 UI 상태 검증")
    print("  2. 초기화 완료 후에만 저장 기능 활성화")
    print("  3. collect_condition_data에서 조기 검증 추가")

def suggest_fixes():
    """수정 방안 제안"""
    
    print("\n🛠️ 수정 방안")
    print("=" * 60)
    
    fixes = [
        {
            "method": "조기 검증 추가",
            "file": "components/condition_dialog.py",
            "description": "save_condition 시작 부분에 UI 준비 상태 확인",
            "code": """
def save_condition(self):
    # UI 초기화 완료 여부 확인
    if not hasattr(self, '_ui_initialized') or not self._ui_initialized:
        return
    
    # 변수 선택 상태 확인
    if not self.variable_combo.currentData():
        return  # 경고창 없이 조용히 리턴
    
    # 기존 로직 계속...
"""
        },
        {
            "method": "초기화 플래그 추가",
            "file": "components/condition_dialog.py", 
            "description": "init_ui 완료 후 플래그 설정",
            "code": """
def init_ui(self):
    # 기존 UI 초기화 코드...
    
    # 마지막에 초기화 완료 플래그 설정
    self._ui_initialized = True
"""
        },
        {
            "method": "수동 저장 모드",
            "file": "integrated_condition_manager.py",
            "description": "자동 저장 비활성화, 수동 저장만 허용",
            "code": """
def save_current_condition(self):
    # 사용자 명시적 요청인지 확인
    if not hasattr(self, '_manual_save_requested'):
        return
    
    # 기존 저장 로직...
    self._manual_save_requested = False
"""
        }
    ]
    
    for i, fix in enumerate(fixes, 1):
        print(f"\n{i}. {fix['method']}")
        print(f"   파일: {fix['file']}")
        print(f"   설명: {fix['description']}")
        print(f"   코드:")
        print(fix['code'])

if __name__ == "__main__":
    trace_save_condition_calls()
    check_event_connections()
    suggest_fixes()

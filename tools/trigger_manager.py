#!/usr/bin/env python3
"""
트리거 관리 스크립트 - 효율적인 트리거 생성 및 관리 도구
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage import ConditionStorage

class TriggerManager:
    """트리거 관리 클래스"""
    
    def __init__(self):
        self.storage = ConditionStorage()
    
    def clean_all_triggers(self, confirm: bool = False):
        """모든 트리거 삭제 (데이터베이스 초기화)"""
        try:
            existing_triggers = self.storage.get_all_conditions(active_only=False)
            if not existing_triggers:
                print("✅ 삭제할 트리거가 없습니다.")
                return True
            
            if not confirm:
                print(f"⚠️ 주의: {len(existing_triggers)}개의 모든 트리거가 삭제됩니다!")
                response = input("정말 모든 트리거를 삭제하시겠습니까? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("❌ 삭제가 취소되었습니다.")
                    return False
            
            delete_count = 0
            for trigger in existing_triggers:
                try:
                    trigger_id = trigger.get('id')
                    if trigger_id:
                        success = self.storage.delete_condition(trigger_id)
                        if success:
                            delete_count += 1
                            print(f"  ✅ 삭제: '{trigger.get('name', 'Unknown')}'")
                        else:
                            print(f"  ❌ 실패: '{trigger.get('name', 'Unknown')}'")
                except Exception as e:
                    print(f"  ❌ 오류: '{trigger.get('name', 'Unknown')}' - {e}")
            
            print(f"\n🧹 전체 삭제 완료: {delete_count}/{len(existing_triggers)} 성공")
            return delete_count == len(existing_triggers)
            
        except Exception as e:
            print(f"❌ 전체 삭제 실패: {e}")
            return False
    
    def backup_triggers(self, backup_file: str = None):
        """트리거 백업 (삭제 전 안전장치)"""
        try:
            if not backup_file:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"trigger_backup_{timestamp}.json"
            
            return self.export_triggers(output_file=backup_file)
            
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            return False

    def batch_create_triggers(self, triggers_file: str):
        """JSON 파일에서 트리거들을 일괄 생성"""
        try:
            with open(triggers_file, 'r', encoding='utf-8') as f:
                triggers = json.load(f)
            
            success_count = 0
            for trigger in triggers:
                success, message, trigger_id = self.storage.save_condition(trigger, overwrite=True)
                if success:
                    success_count += 1
                    print(f"✅ '{trigger['name']}' 생성 완료 (ID: {trigger_id})")
                else:
                    print(f"❌ '{trigger['name']}' 생성 실패: {message}")
            
            print(f"\n📊 일괄 생성 완료: {success_count}/{len(triggers)} 성공")
            return success_count == len(triggers)
            
        except Exception as e:
            print(f"❌ 일괄 생성 실패: {e}")
            return False
    
    def export_triggers(self, category: str = None, output_file: str = "exported_triggers.json"):
        """트리거들을 JSON 파일로 내보내기"""
        try:
            if category:
                triggers = self.storage.get_conditions_by_category(category)
            else:
                triggers = self.storage.get_all_conditions(active_only=False)
            
            # ID 제거 (새로 생성할 때 충돌 방지)
            clean_triggers = []
            for trigger in triggers:
                clean_trigger = {k: v for k, v in trigger.items() if k != 'id'}
                clean_triggers.append(clean_trigger)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(clean_triggers, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {len(clean_triggers)}개 트리거를 '{output_file}'로 내보내기 완료")
            return True
            
        except Exception as e:
            print(f"❌ 트리거 내보내기 실패: {e}")
            return False
    
    def list_triggers(self, category: str = None):
        """트리거 목록 조회"""
        try:
            if category:
                triggers = self.storage.get_conditions_by_category(category)
                print(f"\n📋 '{category}' 카테고리 트리거 목록:")
            else:
                triggers = self.storage.get_all_conditions(active_only=False)
                print(f"\n📋 전체 트리거 목록:")
            
            if not triggers:
                print("  (등록된 트리거가 없습니다)")
                return
            
            for i, trigger in enumerate(triggers, 1):
                status = "🟢" if trigger.get('is_active', True) else "🔴"
                print(f"  {i:2d}. {status} [{trigger.get('category', 'unknown')}] {trigger['name']}")
                print(f"      📝 {trigger.get('description', 'N/A')}")
                
                # 태그 표시
                if 'tags' in trigger and trigger['tags']:
                    tags = trigger['tags'] if isinstance(trigger['tags'], list) else []
                    if tags:
                        print(f"      🏷️  {', '.join(tags)}")
                print()
            
            return True
            
        except Exception as e:
            print(f"❌ 트리거 목록 조회 실패: {e}")
            return False
    
    def get_statistics(self):
        """트리거 통계 조회"""
        try:
            stats = self.storage.get_condition_statistics()
            print(f"\n📊 트리거 통계:")
            print(f"  • 전체 트리거 수: {stats.get('total_conditions', 0)}")
            print(f"  • 활성 트리거 수: {stats.get('active_conditions', 0)}")
            print(f"  • 카테고리별 분포:")
            
            category_stats = stats.get('by_category', {})
            for category, count in category_stats.items():
                print(f"    - {category}: {count}개")
            
            return True
            
        except Exception as e:
            print(f"❌ 통계 조회 실패: {e}")
            return False

def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="트리거 관리 도구")
    parser.add_argument('action', choices=['create', 'export', 'list', 'stats', 'clean', 'backup'], 
                       help='수행할 작업')
    parser.add_argument('--file', '-f', help='JSON 파일 경로')
    parser.add_argument('--category', '-c', help='카테고리 필터')
    parser.add_argument('--output', '-o', default='exported_triggers.json', 
                       help='출력 파일명')
    parser.add_argument('--force', action='store_true',
                       help='확인 없이 강제 실행 (clean 명령용)')
    
    args = parser.parse_args()
    
    manager = TriggerManager()
    
    if args.action == 'create':
        if not args.file:
            print("❌ 생성할 트리거 JSON 파일을 지정하세요 (--file)")
            return
        manager.batch_create_triggers(args.file)
        
    elif args.action == 'export':
        manager.export_triggers(args.category, args.output)
        
    elif args.action == 'list':
        manager.list_triggers(args.category)
        
    elif args.action == 'stats':
        manager.get_statistics()
        
    elif args.action == 'clean':
        manager.clean_all_triggers(confirm=args.force)
        
    elif args.action == 'backup':
        manager.backup_triggers(args.output)

if __name__ == "__main__":
    main()

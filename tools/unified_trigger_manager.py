#!/usr/bin/env python3
"""
통합 트리거 관리 도구
트리거 정규화, 파라미터 복원, 진단 기능을 하나로 통합
"""

import sqlite3
import json
import shutil
import os
from pathlib import Path
from datetime import datetime

class TriggerManager:
    """트리거 관리 통합 클래스"""
    
    def __init__(self, db_path="data/app_settings.sqlite3"):
        self.db_path = db_path
        
    def backup_database(self):
        """데이터베이스 백업"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"trigger_backup_{timestamp}.json"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM trading_conditions")
        triggers = cursor.fetchall()
        
        # 컬럼명 가져오기
        cursor.execute("PRAGMA table_info(trading_conditions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 백업 데이터 구성
        backup_data = {
            "backup_time": datetime.now().isoformat(),
            "table_schema": columns,
            "triggers": [dict(zip(columns, trigger)) for trigger in triggers]
        }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        conn.close()
        print(f"✅ 백업 완료: {backup_path}")
        return backup_path
    
    def diagnose_triggers(self):
        """트리거 진단"""
        print("🔍 트리거 진단")
        print("=" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 전체 트리거 개수
        cursor.execute("SELECT COUNT(*) FROM trading_conditions")
        total_count = cursor.fetchone()[0]
        print(f"📊 총 트리거 수: {total_count}개")
        
        # 외부변수 트리거 확인
        cursor.execute("SELECT COUNT(*) FROM trading_conditions WHERE comparison_type = 'external'")
        external_count = cursor.fetchone()[0]
        print(f"🔗 외부변수 트리거: {external_count}개")
        
        # 문제 트리거 찾기
        cursor.execute("""
            SELECT id, name, comparison_type, target_value, external_variable
            FROM trading_conditions 
            WHERE (comparison_type = 'external' AND external_variable IS NULL)
               OR (target_value LIKE '%ma_%' OR target_value LIKE '%macd%')
               OR (comparison_type IN ('cross_up', 'cross_down'))
        """)
        
        problem_triggers = cursor.fetchall()
        
        if problem_triggers:
            print(f"\n⚠️  문제 트리거: {len(problem_triggers)}개")
            for trigger_id, name, comp_type, target_value, external_var in problem_triggers:
                print(f"  - ID {trigger_id}: {name}")
                print(f"    타입: {comp_type}, 대상값: {target_value}")
        else:
            print("\n✅ 모든 트리거가 정상입니다")
        
        conn.close()
        
    def fix_variable_limits(self):
        """변수 정의에서 50봉 제한 해제"""
        print("\n🔧 변수 정의 50봉 제한 해제")
        
        variable_def_file = "upbit_auto_trading/ui/desktop/screens/strategy_management/components/variable_definitions.py"
        
        if not os.path.exists(variable_def_file):
            print(f"❌ 파일을 찾을 수 없음: {variable_def_file}")
            return
        
        with open(variable_def_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 백업
        backup_file = f"{variable_def_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(variable_def_file, backup_file)
        
        # 50 제한을 240으로 변경
        replacements = [
            ('"max": 50,', '"max": 240,'),
            ("'max': 50,", "'max': 240,"),
        ]
        
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
                print(f"  ✅ {old} → {new}")
        
        if modified:
            with open(variable_def_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📄 백업: {backup_file}")
        else:
            print("  📝 변경할 내용이 없음")
            os.remove(backup_file)
    
    def fix_deadcross_triggers(self):
        """잘못된 데드크로스 트리거 수정"""
        print("\n🔧 데드크로스 트리거 수정")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 잘못된 데드크로스 트리거 찾기
            cursor.execute("""
                SELECT id, name, external_variable 
                FROM trading_conditions 
                WHERE name LIKE '%데드크로스%' 
                AND (external_variable LIKE '%RSI%' OR external_variable IS NULL)
            """)
            
            wrong_triggers = cursor.fetchall()
            
            for trigger_id, name, external_var in wrong_triggers:
                print(f"  🔧 수정: {name} (ID: {trigger_id})")
                
                # 이름에서 기간 추출
                if "120, 50" in name:
                    period = 50
                elif "60" in name:
                    period = 60
                else:
                    period = 20  # 기본값
                
                # 올바른 외부변수 데이터 생성
                external_variable_data = {
                    "variable_id": "SMA",
                    "variable_name": "📈 단순이동평균",
                    "category": "indicator", 
                    "parameters": {
                        "period": period,
                        "timeframe": "포지션 설정 따름"
                    }
                }
                
                cursor.execute("""
                    UPDATE trading_conditions 
                    SET external_variable = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (json.dumps(external_variable_data, ensure_ascii=False), trigger_id))
                
                print(f"    ✅ 외부변수를 SMA({period})로 수정")
            
            conn.commit()
            print(f"  📊 {len(wrong_triggers)}개 트리거 수정 완료")
            
        except Exception as e:
            conn.rollback()
            print(f"  ❌ 오류: {e}")
        finally:
            conn.close()
    
    def verify_parameters(self):
        """파라미터 복원 검증"""
        print("\n📊 파라미터 복원 검증")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, variable_params, external_variable
            FROM trading_conditions 
            WHERE comparison_type = 'external'
            ORDER BY id
        """)
        
        for trigger_id, name, variable_params, external_variable_str in cursor.fetchall():
            print(f"\n🔧 {name} (ID: {trigger_id})")
            
            # 주 변수 파라미터
            if variable_params:
                try:
                    params = json.loads(variable_params)
                    period = params.get('period', 'N/A')
                    print(f"  주변수 기간: {period}")
                except json.JSONDecodeError:
                    print("  주변수: 파라미터 파싱 실패")
            
            # 외부 변수 파라미터
            if external_variable_str:
                try:
                    external_var = json.loads(external_variable_str)
                    ext_params = external_var.get('parameters', {})
                    ext_period = ext_params.get('period', 'N/A')
                    print(f"  외부변수 기간: {ext_period}")
                    
                    if ext_period != 'N/A' and int(ext_period) > 50:
                        print(f"    ✅ 50봉 초과 지원: {ext_period}일")
                except (json.JSONDecodeError, ValueError):
                    print("  외부변수: 파라미터 파싱 실패")
        
        conn.close()
    
    def run_full_maintenance(self):
        """전체 유지보수 실행"""
        print("🛠️  트리거 시스템 전체 유지보수")
        print("=" * 50)
        
        # 1. 백업
        backup_file = self.backup_database()
        
        # 2. 진단
        self.diagnose_triggers()
        
        # 3. 변수 제한 해제
        self.fix_variable_limits()
        
        # 4. 데드크로스 트리거 수정
        self.fix_deadcross_triggers()
        
        # 5. 검증
        self.verify_parameters()
        
        print(f"\n✅ 전체 유지보수 완료!")
        print(f"📄 백업 파일: {backup_file}")

def main():
    """메인 함수"""
    manager = TriggerManager()
    
    print("🛠️  통합 트리거 관리 도구")
    print("1: 진단만 실행")
    print("2: 전체 유지보수 실행")
    print("3: 파라미터 검증만 실행")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    if choice == "1":
        manager.diagnose_triggers()
    elif choice == "2":
        manager.run_full_maintenance()
    elif choice == "3":
        manager.verify_parameters()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()

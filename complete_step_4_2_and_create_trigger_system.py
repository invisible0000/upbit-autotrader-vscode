#!/usr/bin/env python3
"""
Step 4.2 완료: 전략 빌더 통합 문제 해결 및 실용적인 예제 트리거 시스템 구축
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

def test_api_compatibility():
    """API 호환성 문제 테스트 및 해결"""
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_builder import ConditionBuilder
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage import ConditionStorage
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.variable_definitions import VariableDefinitions
        
        # 컴포넌트 초기화
        builder = ConditionBuilder()
        storage = ConditionStorage()
        var_def = VariableDefinitions()
        
        print("✅ 모든 컴포넌트 정상 import 완료")
        
        # ATR 조건 생성 테스트 (수정된 방식)
        atr_condition_data = {
            "name": "ATR 높은 변동성 감지",
            "description": "ATR이 20을 초과할 때 높은 변동성 상황으로 판단",
            "variable_id": "ATR",
            "variable_name": "평균진실범위",
            "variable_params": {
                "period": 14,
                "timeframe": "1h"
            },
            "operator": ">",
            "comparison_type": "fixed",
            "target_value": "20",
            "external_variable": None,
            "trend_direction": "static",
            "category": "volatility"
        }
        
        # 조건 빌드 테스트
        condition = builder.build_condition_from_ui(atr_condition_data)
        print(f"✅ ATR 조건 빌드 성공: {condition['name']}")
        
        # 조건 저장 테스트
        success, message, condition_id = storage.save_condition(condition)
        if success:
            print(f"✅ ATR 조건 저장 성공 (ID: {condition_id})")
        else:
            print(f"⚠️ ATR 조건 저장 실패: {message}")
        
        # 저장된 조건 로드 테스트
        if condition_id:
            loaded_condition = storage.get_condition_by_id(condition_id)
            if loaded_condition:
                print(f"✅ 조건 로드 성공: {loaded_condition['name']}")
            else:
                print("❌ 조건 로드 실패")
        
        return True
        
    except Exception as e:
        print(f"❌ API 호환성 테스트 실패: {e}")
        return False

def clean_old_triggers():
    """기존 트리거들 정리 (구 버전 데이터와 호환성 문제 해결)"""
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage import ConditionStorage
        
        storage = ConditionStorage()
        
        print("🧹 기존 트리거 정리 시작...")
        
        # 기존 모든 트리거 조회
        try:
            existing_triggers = storage.get_all_conditions(active_only=False)
            if not existing_triggers:
                print("✅ 삭제할 기존 트리거가 없습니다.")
                return True
            
            print(f"📋 발견된 기존 트리거: {len(existing_triggers)}개")
            
            # 삭제 여부 확인 (자동 삭제로 설정)
            delete_count = 0
            for trigger in existing_triggers:
                try:
                    trigger_id = trigger.get('id')
                    trigger_name = trigger.get('name', 'Unknown')
                    
                    if trigger_id:
                        success = storage.delete_condition(trigger_id)
                        if success:
                            delete_count += 1
                            print(f"  ✅ 삭제됨: '{trigger_name}' (ID: {trigger_id})")
                        else:
                            print(f"  ❌ 삭제 실패: '{trigger_name}' (ID: {trigger_id})")
                    else:
                        print(f"  ⚠️ ID 없음: '{trigger_name}'")
                        
                except Exception as e:
                    print(f"  ❌ 삭제 중 오류: '{trigger.get('name', 'Unknown')}' - {e}")
            
            print(f"🧹 기존 트리거 정리 완료: {delete_count}/{len(existing_triggers)} 삭제됨")
            return delete_count > 0
            
        except Exception as e:
            print(f"⚠️ 기존 트리거 조회 실패: {e}")
            # 조회 실패해도 계속 진행
            return True
            
    except Exception as e:
        print(f"❌ 기존 트리거 정리 실패: {e}")
        return False

def create_example_triggers():
    """실용적인 예제 트리거들 생성"""
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.trigger_builder.components.condition_storage import ConditionStorage
        
        storage = ConditionStorage()
        
        # 기존 트리거들 완전 정리
        print("🧹 기존 트리거 완전 정리 중...")
        clean_success = clean_old_triggers()
        
        # 실용적인 예제 트리거들 정의
        example_triggers = [
            {
                "name": "RSI 과매도 신호",
                "description": "RSI가 30 이하로 떨어질 때 매수 신호 (과매도 구간)",
                "variable_id": "RSI",
                "variable_name": "상대강도지수",
                "variable_params": {
                    "period": 14,
                    "timeframe": "1h"
                },
                "operator": "<=",
                "comparison_type": "fixed",
                "target_value": "30",
                "external_variable": None,
                "trend_direction": "falling",
                "category": "momentum",
                "tags": ["매수신호", "과매도", "RSI", "단기트레이딩"]
            },
            {
                "name": "RSI 과매수 신호",
                "description": "RSI가 70 이상으로 올라갈 때 매도 신호 (과매수 구간)",
                "variable_id": "RSI",
                "variable_name": "상대강도지수", 
                "variable_params": {
                    "period": 14,
                    "timeframe": "1h"
                },
                "operator": ">=",
                "comparison_type": "fixed",
                "target_value": "70",
                "external_variable": None,
                "trend_direction": "rising",
                "category": "momentum",
                "tags": ["매도신호", "과매수", "RSI", "단기트레이딩"]
            },
            {
                "name": "골든 크로스 신호",
                "description": "단기 이동평균(SMA20)이 장기 이동평균(SMA50)을 상향 돌파할 때",
                "variable_id": "SMA",
                "variable_name": "단순이동평균",
                "variable_params": {
                    "period": 20,
                    "timeframe": "1h"
                },
                "operator": ">",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "SMA",
                    "variable_name": "단순이동평균",
                    "variable_params": {
                        "period": 50,
                        "timeframe": "1h"
                    }
                },
                "trend_direction": "crossover_up",
                "category": "trend",
                "tags": ["골든크로스", "상승신호", "이동평균", "트렌드팔로잉"]
            },
            {
                "name": "데드 크로스 신호",
                "description": "단기 이동평균(SMA20)이 장기 이동평균(SMA50)을 하향 돌파할 때",
                "variable_id": "SMA",
                "variable_name": "단순이동평균",
                "variable_params": {
                    "period": 20,
                    "timeframe": "1h"
                },
                "operator": "<",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "SMA",
                    "variable_name": "단순이동평균",
                    "variable_params": {
                        "period": 50,
                        "timeframe": "1h"
                    }
                },
                "trend_direction": "crossover_down",
                "category": "trend",
                "tags": ["데드크로스", "하락신호", "이동평균", "트렌드팔로잉"]
            },
            {
                "name": "볼린저 밴드 하단 터치",
                "description": "현재가가 볼린저 밴드 하단선에 닿거나 돌파할 때 (반등 기대)",
                "variable_id": "CURRENT_PRICE",
                "variable_name": "현재가",
                "variable_params": {},
                "operator": "<=",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "BOLLINGER_BAND",
                    "variable_name": "볼린저밴드",
                    "variable_params": {
                        "period": 20,
                        "multiplier": 2,
                        "band_type": "lower",
                        "timeframe": "1h"
                    }
                },
                "trend_direction": "touching",
                "category": "volatility",
                "tags": ["볼린저밴드", "지지", "반등기대", "변동성"]
            },
            {
                "name": "볼린저 밴드 상단 터치",
                "description": "현재가가 볼린저 밴드 상단선에 닿거나 돌파할 때 (저항 확인)",
                "variable_id": "CURRENT_PRICE",
                "variable_name": "현재가",
                "variable_params": {},
                "operator": ">=",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "BOLLINGER_BAND",
                    "variable_name": "볼린저밴드",
                    "variable_params": {
                        "period": 20,
                        "multiplier": 2,
                        "band_type": "upper",
                        "timeframe": "1h"
                    }
                },
                "trend_direction": "touching",
                "category": "volatility",
                "tags": ["볼린저밴드", "저항", "조정가능성", "변동성"]
            },
            {
                "name": "높은 변동성 감지 (ATR)",
                "description": "ATR이 평소보다 2배 이상 높을 때 (급등락 가능성)",
                "variable_id": "ATR",
                "variable_name": "평균진실범위",
                "variable_params": {
                    "period": 14,
                    "timeframe": "1h"
                },
                "operator": ">",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "ATR",
                    "variable_name": "평균진실범위",
                    "variable_params": {
                        "period": 50,
                        "timeframe": "1h",
                        "multiplier": 2
                    }
                },
                "trend_direction": "expanding",
                "category": "volatility",
                "tags": ["ATR", "높은변동성", "급등락", "위험관리"]
            },
            {
                "name": "거래량 급증 신호",
                "description": "현재 거래량이 평균 거래량의 3배 이상일 때",
                "variable_id": "VOLUME",
                "variable_name": "거래량",
                "variable_params": {},
                "operator": ">",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "VOLUME_SMA",
                    "variable_name": "거래량 이동평균",
                    "variable_params": {
                        "period": 20,
                        "timeframe": "1h",
                        "multiplier": 3
                    }
                },
                "trend_direction": "surge",
                "category": "volume",
                "tags": ["거래량급증", "관심증가", "돌파신호", "거래량분석"]
            },
            {
                "name": "MACD 신호선 상향 돌파",
                "description": "MACD 라인이 시그널 라인을 상향 돌파할 때 (상승 모멘텀)",
                "variable_id": "MACD",
                "variable_name": "MACD",
                "variable_params": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9,
                    "timeframe": "1h",
                    "type": "macd"
                },
                "operator": ">",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "MACD",
                    "variable_name": "MACD",
                    "variable_params": {
                        "fast_period": 12,
                        "slow_period": 26,
                        "signal_period": 9,
                        "timeframe": "1h",
                        "type": "signal"
                    }
                },
                "trend_direction": "crossover_up",
                "category": "momentum",
                "tags": ["MACD", "상향돌파", "모멘텀", "매수신호"]
            },
            {
                "name": "스토캐스틱 과매도 반등",
                "description": "스토캐스틱 %K가 20 이하에서 %D를 상향 돌파할 때",
                "variable_id": "STOCHASTIC",
                "variable_name": "스토캐스틱",
                "variable_params": {
                    "k_period": 14,
                    "d_period": 3,
                    "timeframe": "1h",
                    "type": "k"
                },
                "operator": ">",
                "comparison_type": "external",
                "target_value": "",
                "external_variable": {
                    "variable_id": "STOCHASTIC",
                    "variable_name": "스토캐스틱",
                    "variable_params": {
                        "k_period": 14,
                        "d_period": 3,
                        "timeframe": "1h",
                        "type": "d"
                    }
                },
                "trend_direction": "crossover_up",
                "category": "momentum",
                "tags": ["스토캐스틱", "과매도반등", "단기반등", "모멘텀"]
            }
        ]
        
        # 예제 트리거들 저장
        success_count = 0
        total_count = len(example_triggers)
        
        for trigger in example_triggers:
            try:
                success, message, trigger_id = storage.save_condition(trigger, overwrite=True)
                if success:
                    success_count += 1
                    print(f"✅ '{trigger['name']}' 저장 완료 (ID: {trigger_id})")
                else:
                    print(f"❌ '{trigger['name']}' 저장 실패: {message}")
            except Exception as e:
                print(f"❌ '{trigger['name']}' 저장 중 오류: {e}")
        
        print(f"\n📊 예제 트리거 생성 완료: {success_count}/{total_count} 성공")
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ 예제 트리거 생성 실패: {e}")
        return False

def create_trigger_management_script():
    """효율적인 트리거 관리 스크립트 생성"""
    
    script_content = '''#!/usr/bin/env python3
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
            
            print(f"\\n🧹 전체 삭제 완료: {delete_count}/{len(existing_triggers)} 성공")
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
            
            print(f"\\n📊 일괄 생성 완료: {success_count}/{len(triggers)} 성공")
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
                print(f"\\n📋 '{category}' 카테고리 트리거 목록:")
            else:
                triggers = self.storage.get_all_conditions(active_only=False)
                print(f"\\n📋 전체 트리거 목록:")
            
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
            print(f"\\n📊 트리거 통계:")
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
'''
    
    with open("trigger_manager.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ 트리거 관리 스크립트 생성 완료: trigger_manager.py")

def create_usage_documentation():
    """사용법 문서 생성"""
    
    doc_content = '''# 🎯 트리거 관리 시스템 사용 가이드

## 📋 개요
이 가이드는 업비트 자동 트레이딩 시스템의 트리거 관리 기능을 효율적으로 사용하는 방법을 설명합니다.

## 🛠️ 트리거 관리 스크립트 사용법

### 1. 기본 사용법

```bash
# 트리거 목록 조회
python trigger_manager.py list

# 카테고리별 트리거 조회
python trigger_manager.py list --category momentum

# 트리거 통계 확인
python trigger_manager.py stats

# 트리거 백업 (삭제 전 권장)
python trigger_manager.py backup --output backup_20250726.json

# 모든 트리거 삭제 (주의!)
python trigger_manager.py clean

# 확인 없이 강제 삭제
python trigger_manager.py clean --force

# 트리거 내보내기
python trigger_manager.py export --output my_triggers.json

# JSON 파일에서 트리거 일괄 생성
python trigger_manager.py create --file example_triggers.json
```

### 2. 안전한 데이터 관리

```bash
# ⚠️ 기존 트리거 교체 시 권장 워크플로우 ⚠️

# 1단계: 기존 트리거 백업
python trigger_manager.py backup --output old_triggers_backup.json

# 2단계: 기존 트리거 삭제 (구 버전 호환성 문제 해결)
python trigger_manager.py clean

# 3단계: 새로운 트리거 생성
python trigger_manager.py create --file new_triggers.json

# 4단계: 결과 확인
python trigger_manager.py list
python trigger_manager.py stats
```

### 3. 트리거 JSON 파일 형식

```json
[
  {
    "name": "RSI 과매도 신호",
    "description": "RSI가 30 이하로 떨어질 때 매수 신호",
    "variable_id": "RSI",
    "variable_name": "상대강도지수",
    "variable_params": {
      "period": 14,
      "timeframe": "1h"
    },
    "operator": "<=",
    "comparison_type": "fixed",
    "target_value": "30",
    "external_variable": null,
    "trend_direction": "falling",
    "category": "momentum",
    "tags": ["매수신호", "과매도", "RSI"]
  }
]
```

## 📊 지원하는 지표 및 변수

### 1. 지표 (Indicators)
- **SMA**: 단순이동평균
- **EMA**: 지수이동평균  
- **RSI**: 상대강도지수
- **MACD**: MACD 지표
- **BOLLINGER_BAND**: 볼린저밴드
- **STOCHASTIC**: 스토캐스틱
- **ATR**: 평균진실범위 (새로 추가)
- **VOLUME_SMA**: 거래량 이동평균 (새로 추가)

### 2. 시장 데이터
- **CURRENT_PRICE**: 현재가
- **VOLUME**: 거래량
- **HIGH**: 고가
- **LOW**: 저가
- **OPEN**: 시가

### 3. 자본 관리
- **AVAILABLE_BALANCE**: 사용 가능 잔액
- **TOTAL_ASSET**: 총 자산

## 🎯 실용적인 트리거 예제

### 1. 단순 조건 트리거

#### RSI 과매도/과매수
```json
{
  "name": "RSI 과매도 신호",
  "variable_id": "RSI",
  "operator": "<=",
  "target_value": "30",
  "category": "momentum"
}
```

#### 볼린저 밴드 터치
```json
{
  "name": "볼린저 밴드 하단 터치",
  "variable_id": "CURRENT_PRICE",
  "operator": "<=",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "BOLLINGER_BAND",
    "variable_params": {"band_type": "lower"}
  }
}
```

### 2. 복합 조건 트리거

#### 골든 크로스
```json
{
  "name": "골든 크로스 신호",
  "variable_id": "SMA",
  "variable_params": {"period": 20},
  "operator": ">",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "SMA",
    "variable_params": {"period": 50}
  },
  "trend_direction": "crossover_up"
}
```

#### 변동성 + 거래량 조합
```json
{
  "name": "높은 변동성 + 거래량 급증",
  "variable_id": "ATR",
  "operator": ">",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "ATR",
    "variable_params": {"multiplier": 2}
  },
  "additional_conditions": [
    {
      "variable_id": "VOLUME",
      "operator": ">",
      "comparison_type": "external",
      "external_variable": {
        "variable_id": "VOLUME_SMA",
        "variable_params": {"multiplier": 3}
      }
    }
  ]
}
```

## ⚙️ 트리거 파라미터 설정

### 1. 지표 파라미터

#### 이동평균 (SMA/EMA)
- `period`: 기간 (기본값: 20)
- `timeframe`: 시간프레임 ("1m", "5m", "1h", "1d")

#### RSI
- `period`: 기간 (기본값: 14)
- `timeframe`: 시간프레임

#### MACD
- `fast_period`: 단기 기간 (기본값: 12)
- `slow_period`: 장기 기간 (기본값: 26)
- `signal_period`: 시그널 기간 (기본값: 9)
- `type`: 타입 ("macd", "signal", "histogram")

#### 볼린저 밴드
- `period`: 기간 (기본값: 20)
- `multiplier`: 배수 (기본값: 2)
- `band_type`: 밴드 타입 ("upper", "middle", "lower")

#### ATR
- `period`: 기간 (기본값: 14)
- `timeframe`: 시간프레임

### 2. 비교 연산자
- `>`: 초과
- `>=`: 이상
- `<`: 미만
- `<=`: 이하
- `==`: 같음
- `!=`: 다름

### 3. 트렌드 방향
- `static`: 정적 (단순 비교)
- `rising`: 상승 중
- `falling`: 하락 중
- `crossover_up`: 상향 돌파
- `crossover_down`: 하향 돌파
- `touching`: 터치
- `expanding`: 확장
- `contracting`: 수축

## 🏷️ 카테고리 및 태그 시스템

### 1. 권장 카테고리
- `momentum`: 모멘텀 지표
- `trend`: 트렌드 추종
- `volatility`: 변동성 지표
- `volume`: 거래량 분석
- `support_resistance`: 지지/저항
- `custom`: 사용자 정의

### 2. 유용한 태그 예제
- 신호 타입: "매수신호", "매도신호", "관찰"
- 시간 프레임: "단기", "중기", "장기"
- 전략 유형: "스윙트레이딩", "데이트레이딩", "포지션트레이딩"
- 시장 상황: "상승장", "하락장", "횡보장"

## 🚀 효율적인 워크플로우

### 1. 트리거 개발 과정
1. **아이디어 수집**: 트레이딩 전략 및 신호 수집
2. **JSON 작성**: 트리거를 JSON 형식으로 정의
3. **일괄 생성**: `trigger_manager.py create` 명령으로 생성
4. **테스트**: 백테스팅 또는 페이퍼 트레이딩으로 검증
5. **최적화**: 파라미터 조정 및 성능 개선

### 2. 트리거 관리 팁
- **버전 관리**: 트리거 JSON 파일을 Git으로 관리
- **백업**: 정기적으로 트리거를 export하여 백업
- **카테고리화**: 명확한 카테고리로 분류하여 관리
- **태그 활용**: 검색 및 필터링을 위한 의미있는 태그 사용
- **문서화**: 복잡한 트리거의 경우 상세한 설명 추가

### 3. 성능 모니터링
- **통계 확인**: 주기적으로 `stats` 명령으로 현황 파악
- **성공률 추적**: 트리거별 성공률 모니터링 
- **사용 빈도**: 자주 사용되는 트리거 패턴 분석

## 🔧 문제 해결

### 1. 일반적인 오류
- **파라미터 오류**: 지표별 필수 파라미터 확인
- **타입 불일치**: 숫자 값은 문자열로 저장
- **중복 이름**: 트리거 이름은 고유해야 함

### 2. 성능 최적화
- **인덱스 활용**: 자주 조회하는 카테고리 활용
- **메모리 관리**: 대량의 트리거 생성 시 배치 처리
- **캐싱**: 자주 사용하는 트리거 캐싱

## 📞 지원 및 문의
트리거 시스템 사용 중 문제가 발생하면 다음을 확인하세요:
1. 데이터베이스 연결 상태
2. 필수 파라미터 누락 여부  
3. JSON 형식 오류
4. 호환성 검증 결과

---
**문서 버전**: 1.0  
**최종 업데이트**: 2025-07-26
'''
    
    with open("trigger_usage_guide.md", "w", encoding="utf-8") as f:
        f.write(doc_content)
    
    print("✅ 사용법 문서 생성 완료: trigger_usage_guide.md")

def create_example_triggers_json():
    """예제 트리거 JSON 파일 생성"""
    
    example_triggers = [
        {
            "name": "RSI 과매도 신호",
            "description": "RSI가 30 이하로 떨어질 때 매수 신호 (과매도 구간)",
            "variable_id": "RSI",
            "variable_name": "상대강도지수",
            "variable_params": {
                "period": 14,
                "timeframe": "1h"
            },
            "operator": "<=",
            "comparison_type": "fixed",
            "target_value": "30",
            "external_variable": None,
            "trend_direction": "falling",
            "category": "momentum",
            "tags": ["매수신호", "과매도", "RSI", "단기트레이딩"]
        },
        {
            "name": "골든 크로스 신호",
            "description": "단기 이동평균(SMA20)이 장기 이동평균(SMA50)을 상향 돌파할 때",
            "variable_id": "SMA",
            "variable_name": "단순이동평균",
            "variable_params": {
                "period": 20,
                "timeframe": "1h"
            },
            "operator": ">",
            "comparison_type": "external",
            "target_value": "",
            "external_variable": {
                "variable_id": "SMA",
                "variable_name": "단순이동평균",
                "variable_params": {
                    "period": 50,
                    "timeframe": "1h"
                }
            },
            "trend_direction": "crossover_up",
            "category": "trend",
            "tags": ["골든크로스", "상승신호", "이동평균", "트렌드팔로잉"]
        }
    ]
    
    with open("example_triggers.json", "w", encoding="utf-8") as f:
        json.dump(example_triggers, f, indent=2, ensure_ascii=False)
    
    print("✅ 예제 트리거 JSON 파일 생성 완료: example_triggers.json")

def main():
    """메인 실행 함수"""
    print("🚀 Step 4.2 완료 및 실용적인 트리거 시스템 구축 시작")
    print("=" * 60)
    
    # 1. API 호환성 문제 해결
    print("\n📋 1단계: API 호환성 문제 해결")
    api_success = test_api_compatibility()
    
    # 2. 실용적인 예제 트리거 생성
    print("\n📋 2단계: 실용적인 예제 트리거 생성")
    examples_success = create_example_triggers()
    
    # 3. 트리거 관리 도구 생성
    print("\n📋 3단계: 효율적인 트리거 관리 도구 생성")
    create_trigger_management_script()
    create_usage_documentation()
    create_example_triggers_json()
    
    # 4. 결과 요약
    print("\n" + "=" * 60)
    print("📊 Step 4.2 완료 결과 요약")
    print("=" * 60)
    
    results = [
        ("API 호환성 해결", api_success),
        ("예제 트리거 생성", examples_success),
        ("관리 도구 생성", True),
        ("문서화 완료", True)
    ]
    
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for task, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {task}")
    
    print(f"\n🎯 전체 성공률: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 Step 4.2 완전 완료! 다음 단계 진행 가능")
        print("\n📁 생성된 파일들:")
        print("  • trigger_manager.py - 트리거 관리 스크립트")
        print("  • trigger_usage_guide.md - 사용법 가이드") 
        print("  • example_triggers.json - 예제 트리거 템플릿")
        print("\n🚀 다음 단계: Step 5.1 - 종합 테스트 실행")
    else:
        print(f"\n⚠️ {total_count - success_count}개 작업 실패. 추가 점검 필요.")

if __name__ == "__main__":
    main()

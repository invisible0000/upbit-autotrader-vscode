import sqlite3
import json

# 데이터베이스 연결
conn = sqlite3.connect('strategies.db')
cursor = conn.cursor()

# strategies 테이블의 전체 데이터 확인
cursor.execute("SELECT strategy_id, name, strategy_data FROM strategies")
strategies = cursor.fetchall()

print(f"전체 전략 개수: {len(strategies)}")
print("\n전략 목록:")

for strategy in strategies:
    strategy_id, name, strategy_data = strategy
    print(f"\nStrategy ID: {strategy_id}")
    print(f"Name: {name}")
    
    if strategy_data:
        try:
            data = json.loads(strategy_data)
            print("Strategy Data 구조:")
            
            # JSON 데이터의 구조 분석
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {type(value).__name__}")
                    
                    # 조건/트리거 관련 데이터 찾기
                    if 'condition' in key.lower() or 'trigger' in key.lower() or 'rule' in key.lower():
                        print(f"    >>> {key} 내용: {value}")
                        
                        # 리스트인 경우 각 요소 확인
                        if isinstance(value, list):
                            for i, item in enumerate(value):
                                if isinstance(item, dict) and 'name' in item:
                                    if '자동 생성' in str(item.get('name', '')):
                                        print(f"    !!! [자동 생성] 발견: {item}")
                                        
            # 전체 JSON에서 "자동 생성" 텍스트 검색
            data_str = json.dumps(data, ensure_ascii=False)
            if '자동 생성' in data_str:
                print(f"  !!! 이 전략에 '자동 생성' 텍스트 포함됨")
                
        except json.JSONDecodeError:
            print("  JSON 파싱 오류")
    else:
        print("  Strategy Data 없음")

conn.close()

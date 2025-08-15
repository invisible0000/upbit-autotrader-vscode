#!/usr/bin/env python3
"""
Timeframe Enum Migration Script
API 친화적인 timeframe 값으로 데이터베이스 일괄 변경
"""

import sqlite3
import json
import sys
from pathlib import Path

def migrate_timeframe_enums():
    """timeframe enum 값들을 API 친화적으로 변경"""

    # 데이터베이스 경로
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print(f"❌ 데이터베이스 파일을 찾을 수 없습니다: {db_path}")
        return False

    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 새로운 timeframe enum 값 정의 (API 친화적)
        new_timeframe_enum = [
            'position_follow', '1m', '3m', '5m', '10m', '15m', '30m', '1h', '4h', '1d', '1w', '1M'
        ]

        print('🔄 timeframe enum 값들을 API 친화적으로 변경 중...')

        # 1. 먼저 현재 상태 확인
        cursor.execute('''
            SELECT parameter_id, variable_id, default_value, enum_values
            FROM tv_variable_parameters
            WHERE parameter_name = 'timeframe'
        ''')

        before_results = cursor.fetchall()
        print(f'📊 업데이트 대상: {len(before_results)}개 timeframe 파라미터')

        # 2. 현재 상태 출력
        print('\n📋 변경 전 상태:')
        for param_id, var_id, default_val, enum_values_str in before_results:
            try:
                enum_values = json.loads(enum_values_str) if enum_values_str else []
                print(f'  • {var_id}.timeframe: default="{default_val}", enum={enum_values[:3]}...')
            except:
                print(f'  • {var_id}.timeframe: default="{default_val}", enum_raw="{enum_values_str}"')

        # 3. enum_values와 default_value 업데이트
        cursor.execute('''
            UPDATE tv_variable_parameters
            SET enum_values = ?,
                default_value = 'position_follow'
            WHERE parameter_name = 'timeframe'
        ''', (json.dumps(new_timeframe_enum),))

        # 4. 업데이트 후 확인
        cursor.execute('''
            SELECT parameter_id, variable_id, default_value, enum_values
            FROM tv_variable_parameters
            WHERE parameter_name = 'timeframe'
        ''')

        after_results = cursor.fetchall()
        print(f'\n✅ 업데이트 완료: {len(after_results)}개 파라미터')

        # 5. 변경 후 상태 출력
        print('\n📋 변경 후 상태:')
        for param_id, var_id, default_val, enum_values_str in after_results:
            enum_values = json.loads(enum_values_str)
            print(f'  • {var_id}.timeframe: default="{default_val}", enum_count={len(enum_values)}')
            print(f'    └─ enum: {enum_values}')

        # 변경사항 커밋
        conn.commit()
        conn.close()

        print('\n🎉 데이터베이스 마이그레이션 완료!')
        print('📝 변경사항:')
        print('  ✅ 한글 → 영어 timeframe 값으로 변경')
        print('  ✅ 누락된 10m, 1w, 1M 추가')
        print('  ✅ API 친화적 형식으로 통일')

        return True

    except Exception as e:
        print(f"❌ 마이그레이션 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = migrate_timeframe_enums()
    sys.exit(0 if success else 1)

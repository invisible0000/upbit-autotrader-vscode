"""
SQL 바인딩 오류 디버깅 스크립트
"""

import sqlite3
import tempfile
import os

def debug_sql_binding():
    """SQL 바인딩 문제를 정확히 파악"""
    
    # 임시 DB 파일 생성
    temp_db = tempfile.mktemp(suffix='.db')
    print(f'임시 DB 파일: {temp_db}')
    
    try:
        with sqlite3.connect(temp_db) as conn:
            # 1. 테이블 생성
            conn.execute("""
            CREATE TABLE IF NOT EXISTS custom_indicators (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                name_ko TEXT NOT NULL,
                description TEXT,
                formula TEXT NOT NULL,
                parameters TEXT,
                category TEXT DEFAULT 'custom',
                created_by TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
            """)
            
            # 2. 테이블 스키마 확인
            cursor = conn.execute('PRAGMA table_info(custom_indicators)')
            columns = cursor.fetchall()
            print('\n📋 테이블 컬럼 정보:')
            for i, col in enumerate(columns):
                print(f'  {i+1}: {col[1]} ({col[2]})')
            print(f'📊 총 컬럼 수: {len(columns)}')
            
            # 3. INSERT SQL 분석
            insert_sql = """
            INSERT OR IGNORE INTO custom_indicators 
            (id, name, name_ko, description, formula, parameters, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            # SQL에서 지정된 컬럼 수 계산
            specified_columns = ['id', 'name', 'name_ko', 'description', 'formula', 'parameters', 'category']
            placeholders = insert_sql.count('?')
            
            print(f'\n🔍 INSERT SQL 분석:')
            print(f'  지정된 컬럼: {specified_columns}')
            print(f'  컬럼 수: {len(specified_columns)}')
            print(f'  플레이스홀더(?): {placeholders}개')
            
            # 4. 샘플 데이터 분석
            sample_indicators = [
                ('PRICE_MOMENTUM', '가격 모멘텀', '현재가와 N일 전 가격의 비율',
                 '현재가와 N일 전 가격의 비율을 계산', 'close / SMA(close, {period})', '{"period": 20}', 'custom'),
                ('VOLUME_PRICE_TREND', '거래량-가격 추세', '거래량과 가격 변화의 상관관계',
                 '거래량과 가격 변화의 상관관계를 나타내는 지표', '(close - SMA(close, {period})) * volume', '{"period": 14}', 'custom'),
                ('CUSTOM_RSI_SMA', 'RSI 기반 이동평균', 'RSI에 이동평균을 적용',
                 'RSI 값에 이동평균을 적용한 부드러운 지표', 'SMA(RSI(close, {rsi_period}), {sma_period})', '{"rsi_period": 14, "sma_period": 5}', 'custom')
            ]
            
            print(f'\n📦 샘플 데이터 분석:')
            for i, indicator in enumerate(sample_indicators, 1):
                print(f'  {i}번째 지표:')
                print(f'    값 개수: {len(indicator)}')
                print(f'    값들: {indicator}')
                
                # 개별 삽입 테스트
                try:
                    conn.execute(insert_sql, indicator)
                    print(f'    ✅ 삽입 성공')
                except Exception as e:
                    print(f'    ❌ 삽입 실패: {e}')
                    print(f'    오류 타입: {type(e).__name__}')
                    
                    # 상세 분석
                    if "binding" in str(e).lower():
                        # SQLite가 기대하는 바인딩 수 vs 실제 제공된 수 분석
                        print(f'    🔍 바인딩 분석:')
                        print(f'      SQL 플레이스홀더: {placeholders}개')
                        print(f'      제공된 값: {len(indicator)}개')
                        
                        if len(indicator) != placeholders:
                            print(f'      ⚠️  바인딩 수 불일치!')
                            if len(indicator) < placeholders:
                                print(f'         부족한 값: {placeholders - len(indicator)}개')
                            else:
                                print(f'         초과된 값: {len(indicator) - placeholders}개')
                print()
            
            # 5. 수동으로 각 필드 매핑 테스트
            print('🧪 수동 필드 매핑 테스트:')
            test_indicator = sample_indicators[0]
            
            field_mapping = {
                'id': test_indicator[0],
                'name': test_indicator[1], 
                'name_ko': test_indicator[2],
                'description': test_indicator[3],
                'formula': test_indicator[4],
                'parameters': test_indicator[5],
                'category': test_indicator[6]
            }
            
            print('  필드 매핑:')
            for field, value in field_mapping.items():
                print(f'    {field}: {value}')
            
            # 명시적 삽입 테스트
            try:
                conn.execute("""
                INSERT OR IGNORE INTO custom_indicators 
                (id, name, name_ko, description, formula, parameters, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    field_mapping['id'],
                    field_mapping['name'],
                    field_mapping['name_ko'], 
                    field_mapping['description'],
                    field_mapping['formula'],
                    field_mapping['parameters'],
                    field_mapping['category']
                ))
                print('  ✅ 명시적 매핑 삽입 성공')
                
                # 데이터 확인
                cursor = conn.execute('SELECT * FROM custom_indicators WHERE id = ?', (field_mapping['id'],))
                result = cursor.fetchone()
                if result:
                    print(f'  📊 삽입된 데이터: {result}')
                
            except Exception as e:
                print(f'  ❌ 명시적 매핑 삽입 실패: {e}')
                
    except Exception as e:
        print(f'❌ 전체 테스트 실패: {e}')
        print(f'오류 타입: {type(e).__name__}')
        
    finally:
        # 임시 파일 정리
        if os.path.exists(temp_db):
            os.remove(temp_db)
            print('\n🗑️  임시 DB 파일 삭제됨')

if __name__ == "__main__":
    debug_sql_binding()

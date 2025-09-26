import sqlite3
import json

# 1. config/secure/api_credentials.json 확인
try:
    with open('config/secure/api_credentials.json', 'r', encoding='utf-8') as f:
        creds = json.load(f)
    print('✅ API Credentials 파일 존재 (암호화된 내용):')
    for key, value in creds.items():
        if key in ['access_key', 'secret_key']:
            print(f'   {key}: {value[:20]}...')
        else:
            print(f'   {key}: {value}')
except Exception as e:
    print(f'❌ API Credentials 파일 없음: {e}')

print()

# 2. settings.sqlite3에서 암호화 키 확인
try:
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    # 테이블 존재 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%key%';")
    tables = cursor.fetchall()
    print('🔍 Settings DB의 키 관련 테이블:', tables)

    # secure_keys 테이블이 있다면 확인
    try:
        cursor.execute('SELECT * FROM secure_keys;')
        keys = cursor.fetchall()
        print(f'🔐 설정된 암호화 키 개수: {len(keys)}')
        if keys:
            for i, key_row in enumerate(keys):
                print(f'   키 {i+1}: ID={key_row[0]}, 값 길이={len(str(key_row[1]))}자, 생성시간={key_row[2] if len(key_row) > 2 else "불명"}')
    except Exception as e:
        print(f'⚠️ secure_keys 테이블 조회 실패: {e}')

    conn.close()
except Exception as e:
    print(f'❌ Settings DB 조회 실패: {e}')

print()

# 3. ApiKeyService 테스트
try:
    from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
    from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
    from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

    # DatabaseManager와 Repository 인스턴스 생성
    db_paths = {
        'settings': 'data/settings.sqlite3',
        'strategies': 'data/strategies.sqlite3',
        'market_data': 'data/market_data.sqlite3'
    }
    db_manager = DatabaseManager(db_paths)
    repository = SqliteSecureKeysRepository(db_manager)
    api_key_service = ApiKeyService(repository)

    print("🔧 ApiKeyService 인스턴스 생성 완료")

    # API 키 로드 테스트
    access_key, secret_key, trade_permission = api_key_service.load_api_keys()
    print(f"📋 API 키 로드 결과:")
    print(f"   access_key: {'존재' if access_key else '없음'}")
    print(f"   secret_key: {'존재' if secret_key else '없음'}")
    print(f"   trade_permission: {trade_permission}")

    if access_key and secret_key:
        print(f"   access_key 길이: {len(access_key)}자")
        print(f"   secret_key 길이: {len(secret_key)}자")

except Exception as e:
    print(f"❌ ApiKeyService 테스트 실패: {e}")
    import traceback
    traceback.print_exc()

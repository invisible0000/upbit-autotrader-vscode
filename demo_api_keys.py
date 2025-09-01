#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 키 상태 확인 스크립트
"""

from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
from upbit_auto_trading.infrastructure.repositories.sqlite_secure_keys_repository import SqliteSecureKeysRepository
from upbit_auto_trading.infrastructure.database.database_manager import DatabaseManager

def check_api_keys():
    # DatabaseManager와 Repository 인스턴스 생성
    db_paths = {
        'settings': 'data/settings.sqlite3',
        'strategies': 'data/strategies.sqlite3',
        'market_data': 'data/market_data.sqlite3'
    }
    db_manager = DatabaseManager(db_paths)
    repository = SqliteSecureKeysRepository(db_manager)
    api_key_service = ApiKeyService(repository)

    # 현재 저장된 키 확인
    access_key, secret_key, trade_permission = api_key_service.load_api_keys()

    print('=== 저장된 API 키 상태 ===')
    print(f'Access Key: {access_key[:10] + "..." if access_key else "None"}')
    print(f'Secret Key: {secret_key[:10] + "..." if secret_key else "None"}')
    print(f'Trade Permission: {trade_permission}')
    print(f'Has Valid Keys: {api_key_service.has_valid_keys()}')

    return access_key, secret_key, trade_permission

if __name__ == "__main__":
    check_api_keys()

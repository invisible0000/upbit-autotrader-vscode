"""
❌ DEPRECATED: DatabasePathService 완전 제거

DatabasePathService는 더 이상 사용하지 않습니다.
Factory + Caching 패턴 (PathServiceFactory)으로 완전 교체됨

Migration Guide:
- DatabasePathService() -> get_path_service()
- db_path_service.get_all_paths() -> path_service.get_all_database_paths()
- db_path_service.get_current_path() -> path_service.get_database_path()
- db_path_service.change_database_path() -> path_service.change_database_location()

새로운 사용법:
```python
from upbit_auto_trading.infrastructure.configuration import get_path_service

path_service = get_path_service()  # Factory에서 캐시된 인스턴스 반환
settings_db = path_service.get_database_path('settings')
```
"""

# 이 파일은 참조용이므로 실제 코드는 없습니다.
# DatabasePathService를 import하지 마세요!

print("⚠️ DatabasePathService는 deprecated됨. get_path_service() 사용하세요!")

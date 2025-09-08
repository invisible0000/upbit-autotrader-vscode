### **Core System Architecture (DDD 준수 + 성능 최적화)**
```
upbit_auto_trading/
├── domain/
│   └── repositories/
│       └── candle_repository_interface.py      # 🎯 Repository 인터페이스 (DDD)
├── infrastructure/
│   ├── database/
│   │   └── database_manager.py                 # ⚡ Connection Pooling + WAL 모드
│   ├── repositories/
│   │   └── sqlite_candle_repository.py         # 🔧 DDD 준수 구현체
│   └── market_data/candle/
│       ├── candle_data_provider.py             # 🏆 메인 Facade (Application Service)
│       ├── candle_client.py                    # 📡 업비트 API 클라이언트
│       ├── candle_cache.py                     # ⚡ 고속 메모리 캐시 (60초 TTL)
│       ├── overlap_optimizer.py               # 🎯 4단계 최적화 (시간 통일)
│       ├── time_utils.py                      # ⏰ 시간 처리 유틸 (확장된 V4)
│       └── models.py                          # 📝 데이터 모델 통합
```

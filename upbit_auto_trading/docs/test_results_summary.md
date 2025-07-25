# 테스트 결과 요약

실행 일시: 2025-07-24 21:53:10

## 테스트 파일별 요약

| 파일명 | 실행 | 오류 | 실패 | 건너뜀 | 상태 |
|--------|------|------|------|--------|------|
| test_02_1_upbit_api.py | 10 | 0 | 0 | 0 | ✅ 성공 |
| test_02_2_backup_manager.py | 6 | 0 | 0 | 0 | ✅ 성공 |
| test_02_2_migration_manager.py | 5 | 0 | 0 | 0 | ✅ 성공 |
| test_03_2_data_collector.py | 13 | 0 | 0 | 0 | ✅ 성공 |
| test_03_3_data_processor.py | 10 | 0 | 0 | 0 | ✅ 성공 |
| test_04_1_base_screener.py | 5 | 0 | 0 | 0 | ✅ 성공 |
| test_04_2_screener_result.py | 7 | 0 | 0 | 0 | ✅ 성공 |
| test_05_1_strategy_factory.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_05_1_strategy_interface.py | 7 | 0 | 0 | 0 | ✅ 성공 |
| test_05_1_strategy_parameter.py | 14 | 0 | 0 | 0 | ✅ 성공 |
| test_05_2_basic_trading_strategies.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_05_3_strategy_management.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_06_1_portfolio_model.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_06_2_portfolio_performance.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_07_1_backtest_runner.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_07_2_backtest_analyzer.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_07_3_portfolio_backtest.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_07_4_backtest_results_management.py | 7 | 0 | 1 | 0 | ❌ 실패 |
| test_08_1_main_application.py | 6 | 0 | 0 | 0 | ✅ 성공 |
| test_10_1_upbit_websocket.py | 0 | 1 | 0 | 0 | ❌ 실패 |
| test_10_2_trading_settings.py | 3 | 0 | 0 | 0 | ✅ 성공 |
| test_10_3_market_monitoring.py | 3 | 0 | 0 | 0 | ✅ 성공 |
| test_10_4_order_execution.py | 4 | 0 | 0 | 0 | ✅ 성공 |
| test_10_5_trading_state.py | 3 | 0 | 0 | 0 | ✅ 성공 |

**총계:** 103개 테스트 실행, 9개 오류, 1개 실패, 0개 건너뜀

## 테스트 ID별 상세 결과

| 테스트 ID | 테스트 이름 | 파일 | 개발 단계 | 테스트 내용 | 상태 |
|-----------|------------|------|----------|------------|------|
| 2_1_1 | test_get_markets | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 마켓 코드 조회 테스트 | ✅ 성공 |
| 2_1_2 | test_get_candles_1m | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 1분봉 조회 테스트 | ✅ 성공 |
| 2_1_3 | test_get_orderbook | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 호가 데이터 조회 테스트 | ✅ 성공 |
| 2_1_4 | test_get_tickers | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 티커 데이터 조회 테스트 | ✅ 성공 |
| 2_1_5 | test_check_rate_limit | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | API 요청 제한 확인 테스트 | ✅ 성공 |
| 2_1_6 | test_create_session | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | HTTP 세션 생성 테스트 | ✅ 성공 |
| 2_1_7 | test_request_with_retry | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | API 요청 재시도 테스트 | ✅ 성공 |
| 2_1_8 | test_get_order | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 개별 주문 조회 테스트 | ✅ 성공 |
| 2_1_9 | test_get_market_day_candles | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 일 캔들 조회 테스트 | ✅ 성공 |
| 2_1_10 | test_get_trades_ticks | test_02_1_upbit_api.py | 2.1 업비트 REST API 기본 클라이언트 구현 | 최근 체결 내역 조회 테스트 | ✅ 성공 |
| 2_2_1 | test_backup_sqlite | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | SQLite 백업 테스트 | ✅ 성공 |
| 2_2_2 | test_backup_sqlite_with_name | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | 이름이 지정된 SQLite 백업 테스트 | ✅ 성공 |
| 2_2_3 | test_restore_sqlite | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | SQLite 복원 테스트 | ✅ 성공 |
| 2_2_4 | test_backup_mysql | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | MySQL 백업 테스트 | ✅ 성공 |
| 2_2_5 | test_backup_postgresql | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | PostgreSQL 백업 테스트 | ✅ 성공 |
| 2_2_6 | test_list_backups | test_02_2_backup_manager.py | 2.2 데이터베이스 스키마 설계 | 백업 목록 조회 테스트 | ✅ 성공 |
| 2_2_7 | test_ensure_migration_table | test_02_2_migration_manager.py | 2.2 데이터베이스 스키마 설계 | 마이그레이션 테이블 생성 테스트 | ✅ 성공 |
| 2_2_8 | test_get_available_migrations | test_02_2_migration_manager.py | 2.2 데이터베이스 스키마 설계 | 사용 가능한 마이그레이션 목록 조회 테스트 | ✅ 성공 |
| 2_2_9 | test_get_applied_migrations | test_02_2_migration_manager.py | 2.2 데이터베이스 스키마 설계 | 적용된 마이그레이션 목록 조회 테스트 | ✅ 성공 |
| 2_2_10 | test_get_pending_migrations | test_02_2_migration_manager.py | 2.2 데이터베이스 스키마 설계 | 보류 중인 마이그레이션 목록 조회 테스트 | ✅ 성공 |
| 2_2_11 | test_create_migration | test_02_2_migration_manager.py | 2.2 데이터베이스 스키마 설계 | 마이그레이션 생성 테스트 | ✅ 성공 |
| 3_2_1 | test_ensure_tables | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 테이블 생성 테스트 | ✅ 성공 |
| 3_2_2 | test_collect_ohlcv | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | OHLCV 데이터 수집 테스트 | ✅ 성공 |
| 3_2_3 | test_collect_orderbook | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 호가 데이터 수집 테스트 | ✅ 성공 |
| 3_2_4 | test_get_ohlcv_data | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | OHLCV 데이터 조회 테스트 | ✅ 성공 |
| 3_2_5 | test_get_orderbook_data | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 호가 데이터 조회 테스트 | ✅ 성공 |
| 3_2_6 | test_collect_historical_ohlcv_new_data | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 과거 OHLCV 데이터 수집 테스트 (새 데이터) | ✅ 성공 |
| 3_2_7 | test_collect_historical_ohlcv_existing_data | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 과거 OHLCV 데이터 수집 테스트 (기존 데이터 있음) | ✅ 성공 |
| 3_2_8 | test_cleanup_old_data | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 오래된 데이터 정리 테스트 | ✅ 성공 |
| 3_2_9 | test_start_ohlcv_collection | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | OHLCV 데이터 수집 작업 시작 테스트 | ✅ 성공 |
| 3_2_10 | test_start_orderbook_collection | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 호가 데이터 수집 작업 시작 테스트 | ✅ 성공 |
| 3_2_11 | test_stop_collection | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 데이터 수집 작업 중지 테스트 | ✅ 성공 |
| 3_2_12 | test_stop_all_collections | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 모든 데이터 수집 작업 중지 테스트 | ✅ 성공 |
| 3_2_13 | test_get_collection_status | test_03_2_data_collector.py | 3.2 데이터 수집기 구현 | 데이터 수집 작업 상태 조회 테스트 | ✅ 성공 |
| 4_1_1 | test_screen_by_volume | test_04_1_base_screener.py | 4.1 기본 스크리닝 기능 구현 | 거래량 기준 스크리닝 테스트 | ✅ 성공 |
| 4_1_2 | test_screen_by_volatility | test_04_1_base_screener.py | 4.1 기본 스크리닝 기능 구현 | 변동성 기준 스크리닝 테스트 | ✅ 성공 |
| 4_1_3 | test_screen_by_trend | test_04_1_base_screener.py | 4.1 기본 스크리닝 기능 구현 | 추세 기준 스크리닝 테스트 | ✅ 성공 |
| 4_1_4 | test_combine_screening_results | test_04_1_base_screener.py | 4.1 기본 스크리닝 기능 구현 | 스크리닝 결과 조합 테스트 | ✅ 성공 |
| 4_2_1 | test_save_screening_result | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 스크리닝 결과 저장 테스트 | ✅ 성공 |
| 4_2_2 | test_get_screening_result | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 특정 스크리닝 결과 조회 테스트 | ✅ 성공 |
| 4_2_3 | test_get_screening_results | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 스크리닝 결과 목록 조회 테스트 | ✅ 성공 |
| 4_2_4 | test_delete_screening_result | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 스크리닝 결과 삭제 테스트 | ✅ 성공 |
| 4_2_5 | test_filter_screening_results | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 스크리닝 결과 필터링 테스트 | ✅ 성공 |
| 4_2_6 | test_export_to_csv | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | CSV 내보내기 테스트 | ✅ 성공 |
| 4_2_7 | test_sort_screening_details | test_04_2_screener_result.py | 4.2 스크리닝 결과 처리 및 저장 기능 구현 | 스크리닝 결과 상세 정보 정렬 테스트 | ✅ 성공 |
| 5_1_5 | test_strategy_initialization | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 전략 초기화 테스트 | ✅ 성공 |
| 5_1_6 | test_get_parameters | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 매개변수 조회 테스트 | ✅ 성공 |
| 5_1_7 | test_set_parameters | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 매개변수 설정 테스트 | ✅ 성공 |
| 5_1_8 | test_validate_parameters | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 매개변수 유효성 검사 테스트 | ✅ 성공 |
| 5_1_9 | test_get_strategy_info | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 전략 정보 조회 테스트 | ✅ 성공 |
| 5_1_10 | test_get_required_indicators | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 필요한 지표 조회 테스트 | ✅ 성공 |
| 5_1_11 | test_generate_signals | test_05_1_strategy_interface.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 매매 신호 생성 테스트 | ✅ 성공 |
| 5_1_12 | test_validate_int_parameter | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 정수형 매개변수 유효성 검사 테스트 | ✅ 성공 |
| 5_1_13 | test_validate_float_parameter | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 실수형 매개변수 유효성 검사 테스트 | ✅ 성공 |
| 5_1_14 | test_validate_str_parameter | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 문자열 매개변수 유효성 검사 테스트 | ✅ 성공 |
| 5_1_15 | test_validate_bool_parameter | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 불리언 매개변수 유효성 검사 테스트 | ✅ 성공 |
| 5_1_16 | test_to_dict | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 딕셔너리 변환 테스트 | ✅ 성공 |
| 5_1_17 | test_from_dict | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 딕셔너리에서 생성 테스트 | ✅ 성공 |
| 5_1_18 | test_initialization | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 초기화 테스트 | ✅ 성공 |
| 5_1_19 | test_set_parameter | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 단일 매개변수 설정 테스트 | ✅ 성공 |
| 5_1_20 | test_set_parameters | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 여러 매개변수 설정 테스트 | ✅ 성공 |
| 5_1_21 | test_get_all_parameters | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 모든 매개변수 조회 테스트 | ✅ 성공 |
| 5_1_22 | test_reset_to_defaults | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 기본값으로 재설정 테스트 | ✅ 성공 |
| 5_1_23 | test_get_parameter_definitions | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | 매개변수 정의 조회 테스트 | ✅ 성공 |
| 5_1_24 | test_json_serialization | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | JSON 직렬화 테스트 | ✅ 성공 |
| 5_1_25 | test_json_deserialization | test_05_1_strategy_parameter.py | 5.1 전략 인터페이스 및 기본 클래스 구현 | JSON 역직렬화 테스트 | ✅ 성공 |

## 개발 단계별 테스트 현황

| 개발 단계 | 총 테스트 수 | 성공 | 실패 | 성공률 |
|-----------|-------------|------|------|--------|
| 2 | 21 | 21 | 0 | 100.00% |
| 3 | 13 | 13 | 0 | 100.00% |
| 4 | 11 | 11 | 0 | 100.00% |
| 5 | 21 | 21 | 0 | 100.00% |

# 📋 TASK_20250820_03: Market Data Storage 개발

## 🎯 태스크 목표
- **주요 목표**: 마켓 데이터의 영속성, 캐싱, 비즈니스 서비스 통합 인터페이스 제공
- **완료 기준**: 스크리너, 백테스터 등이 통합된 인터페이스로 효율적으로 데이터에 접근할 수 있는 시스템

## 📊 현재 상황 분석 (업데이트: 2025-08-20)
### ✅ **의존성 태스크 현재 상황**
- **TASK_20250820_01**: Phase 1 완료 ✅ (WebSocket 장애복구, 스냅샷/실시간 구분)
- **TASK_20250820_02**: Phase 1 준비 완료 ✅ (병행 개발 가능)
- **3번 태스크 시작 조건**: 2번 태스크와 독립적 병행 개발 가능

### Storage Layer의 역할 정의 (Layer 3)
- **Layer 3 포지션**: 가장 상위 레이어, 비즈니스 서비스와 직접 연결
- **선택적 영속성**: 캔들 데이터만 DB 저장, 실시간 데이터는 메모리 캐시만
- **캐싱 전략**: 메모리/디스크 캐시, 만료 정책 (데이터 타입별 차별화)
- **다중 API 인터페이스**: 캔들(DB+캐시), 티커/호가창/체결(메모리만)
- **단순한 데이터 제공**: 복잡한 최적화 없이 순수한 데이터 저장/조회만 담당
- **Smart Router 연동**: WebSocket 장애복구 시스템과 협력하여 안정적 데이터 저장

### 핵심 기능 요구사항
1. **캔들 데이터 영속성**: OHLCV 데이터의 효율적 DB 저장 (백테스트, 차트용)
2. **실시간 데이터 캐싱**: 티커/호가창/체결의 메모리 캐시 (DB 저장 없음)
3. **빠른 조회**: 캔들 DB 인덱스 최적화, 실시간 데이터 메모리 액세스
4. **증분 업데이트**: 기존 캔들 데이터에 새 데이터 효율적 추가
5. **데이터 정합성**: 캔들 데이터 트랜잭션, 백업, 복구 (실시간 데이터는 제외)

## 💾 Storage Layer 데이터 정책

### ✅ **DB 영속성 대상 (market_data.sqlite3)**
- **캔들 데이터 (OHLCV)**
  - **테이블**: candles (symbol, timeframe, timestamp, open, high, low, close, volume)
  - **인덱스**: (symbol, timeframe, timestamp) 복합 인덱스
  - **파편화 관리**: 자동 VACUUM, 인덱스 재구성, 통계 업데이트
  - **사용처**: 백테스트, 차트 표시, 기술적 분석

### 🔄 **메모리 캐시 대상**
- **티커 데이터**: 현재가, 변동률 (TTL: 5분)
- **호가창 데이터**: 매수/매도 호가 (TTL: 30초)
- **체결 데이터**: 최근 거래 내역 (TTL: 10분)

### 🚫 **Storage에서 제외**
- **전략 실행 데이터**: strategies.sqlite3으로 분리
- **사용자 설정**: settings.sqlite3으로 분리
- **임시 파일**: 시스템 temp 디렉토리 활용

## 🛠️ 스마트 DB 최적화 전략

### 📊 **파편화 감지 및 관리**
SQLite에서 심볼/타임프레임별 대량 INSERT/UPDATE로 인한 파편화는 필연적입니다. 이를 스마트하게 관리하는 전략:

#### **1. 실시간 파편화 모니터링**
```python
class FragmentationMonitor:
    def check_fragmentation_ratio(self) -> float:
        """
        SELECT (page_count - freelist_count) * 100.0 / page_count
        FROM pragma_page_count(), pragma_freelist_count()
        """
        # 파편화율 = (전체페이지 - 빈페이지) / 전체페이지
        # 85% 이상 시 VACUUM 필요

    async def monitor_insert_patterns(self):
        """
        - 심볼별 INSERT 빈도 추적
        - 타임프레임별 데이터 증가율 분석
        - Hot/Cold 데이터 패턴 식별
        """
```

#### **2. 조건부 자동 VACUUM**
```python
class SmartVacuumScheduler:
    async def evaluate_vacuum_need(self) -> bool:
        """
        VACUUM 실행 조건:
        1. 파편화율 > 15%
        2. 빈 페이지 > 1000개
        3. 마지막 VACUUM 후 1주일 경과
        4. 현재 시간이 거래 비활성 시간대 (새벽 2-4시)
        """

    async def incremental_vacuum(self, pages: int = 100):
        """
        PRAGMA incremental_vacuum(100)
        - 전체 VACUUM 대신 점진적 정리
        - 서비스 중단 없이 실행 가능
        """
```

#### **3. 인덱스 최적화**
```python
class IndexOptimizer:
    async def analyze_index_usage(self):
        """
        EXPLAIN QUERY PLAN으로 인덱스 사용률 분석:
        - 사용되지 않는 인덱스 제거
        - 커버링 인덱스 생성 검토
        - 인덱스 키 순서 최적화
        """

    async def reindex_if_needed(self, table: str):
        """
        조건부 REINDEX:
        1. 인덱스 통계가 오래된 경우
        2. 대량 INSERT 후
        3. 쿼리 성능 저하 감지 시
        """
```

## 🔄 체계적 작업 절차 (업데이트)

### 📊 **Phase 1 시작 조건 확인**
- ✅ Smart Router Phase 1 완료 (WebSocket 장애복구 포함)
- ✅ Coordinator Phase 1 준비 완료 (병행 개발 가능)
- 💡 **독립적 병행 개발**: Storage는 Coordinator와 독립적으로 개발 가능

### Phase 1: 데이터 모델 및 스키마 설계 📝 **준비 완료**
- [ ] 1.1 캔들 데이터 테이블 스키마 설계 (OHLCV + 메타데이터)
- [ ] 1.2 메모리 캐시 모델 설계 (티커, 호가창, 체결용)
- [ ] 1.3 캔들 데이터 인덱스 전략 설계 (복합 인덱스, 범위 쿼리 최적화)
- [ ] 1.4 데이터 압축 및 정규화 전략 (캔들 데이터만)

### Phase 2: 핵심 저장소 구현
- [ ] 2.1 IMarketDataStorage 인터페이스 정의 (캔들 DB + 실시간 캐시)
- [ ] 2.2 SQLite 기반 CandleRepository 구현 (DB 저장)
- [ ] 2.3 메모리 기반 RealtimeDataCache 구현 (티커/호가창/체결)
- [ ] 2.4 Smart Router 메모리 캐시 연동 인터페이스 구현 ✅ **추가**
- [ ] 2.5 트랜잭션 관리 및 롤백 처리 (캔들 데이터만)

### Phase 3: 캐싱 시스템 구현
- [ ] 3.1 IDataCache 인터페이스 정의
- [ ] 3.2 메모리 캐시 구현 (LRU, TTL 정책)
- [ ] 3.3 디스크 캐시 구현 (임시 파일 기반)
- [ ] 3.4 캐시 무효화 및 동기화 로직

### Phase 4: 기본 비즈니스 인터페이스
- [ ] 4.1 IMarketDataService 통합 인터페이스 정의 (다중 타입)
- [ ] 4.2 캔들 데이터 서비스 (get_candle_data)
- [ ] 4.3 티커 데이터 서비스 (get_ticker_data)
- [ ] 4.4 호가창 데이터 서비스 (get_orderbook_data)
- [ ] 4.5 체결 데이터 서비스 (get_trade_data)

### Phase 5: DB 최적화 및 파편화 관리
- [ ] 5.1 스마트 VACUUM 스케줄러 구현 (파편화 임계값 기반)
- [ ] 5.2 인덱스 성능 모니터링 및 자동 재구성
- [ ] 5.3 테이블 통계 자동 업데이트 (ANALYZE)
- [ ] 5.4 쿼리 성능 분석 및 최적화 제안

## 🛠️ 폴더 구조 및 파일 설계

### 폴더 구조
```
market_data_storage/
├── __init__.py
├── interfaces/                    # 추상 인터페이스
│   ├── __init__.py
│   ├── storage.py                # IMarketDataStorage
│   ├── cache.py                  # IDataCache
│   ├── repository.py             # IRepository
│   └── service.py                # IMarketDataService
├── implementations/               # 핵심 구현체
│   ├── __init__.py
│   ├── sqlite_storage.py         # SQLite 기반 저장소
│   ├── market_data_service.py    # 통합 비즈니스 서비스 (다중 타입)
│   ├── candle_repository.py      # 캔들 데이터 저장소
│   ├── ticker_repository.py      # 티커 데이터 저장소
│   ├── orderbook_repository.py   # 호가창 데이터 저장소
│   ├── trade_repository.py       # 체결 데이터 저장소
│   └── metadata_repository.py    # 메타데이터 저장소
├── cache/                         # 캐싱 시스템
│   ├── __init__.py
│   ├── memory_cache.py           # 메모리 캐시 (LRU)
│   ├── disk_cache.py             # 디스크 캐시
│   ├── cache_manager.py          # 캐시 통합 관리
│   └── cache_policies.py         # 캐시 정책 (TTL, LRU 등)
├── persistence/                   # 영속성 관리
│   ├── __init__.py
│   ├── schema_manager.py         # 스키마 버전 관리
│   ├── migration_runner.py       # 데이터 마이그레이션
│   └── integrity_checker.py      # 데이터 정합성 검증
├── optimization/                  # DB 최적화 (새로 추가)
│   ├── __init__.py
│   ├── fragmentation_monitor.py  # 파편화 모니터링
│   ├── vacuum_scheduler.py       # 스마트 VACUUM 스케줄러
│   ├── index_optimizer.py        # 인덱스 최적화
│   └── query_analyzer.py         # 쿼리 성능 분석
├── models/                        # 데이터 모델
│   ├── __init__.py
│   ├── stored_candle.py          # 저장용 캔들 모델
│   ├── query_criteria.py         # 쿼리 조건 모델
│   ├── cache_entry.py            # 캐시 엔트리 모델
│   └── storage_metadata.py       # 저장소 메타데이터
└── utils/                         # 유틸리티
    ├── __init__.py
    ├── compression.py             # 데이터 압축 유틸
    ├── indexing.py                # 인덱스 관리 유틸
    ├── query_optimizer.py         # 쿼리 최적화
    └── performance_monitor.py     # 성능 모니터링
```

## 🎯 핵심 구현 목표

### 1. 효율적 데이터 저장
- **캔들 데이터**: 중복 데이터 자동 처리 (UPSERT), 배치 insert 최적화
- **실시간 데이터**: 메모리 캐시 TTL 관리, 자동 정리
- **트랜잭션 보장**: 캔들 데이터 저장 시 ACID 속성 보장
- **압축 저장**: 필요시 오래된 데이터 압축 관리

### 2. 지능적 캐싱 시스템
- **4단계 계층적 캐시**: Storage 메모리 → Smart Router 메모리 → 디스크 캐시 → SQLite DB ✅ **확정**
- **자동 최적화**: 파편화율 15% 초과 시 incremental_vacuum 실행
- **인덱스 관리**: 통계 업데이트, 사용하지 않는 인덱스 정리
- **쿼리 최적화**: 느린 쿼리 감지 시 인덱스 추천
- **Smart Router 연동**: Smart Router의 실시간 메모리 캐시 우선 활용 ✅ **확정**

### 3. 단순한 데이터 인터페이스
- **기본 CRUD**: 캔들/티커/호가창/체결 데이터의 저장/조회만 제공
- **메타데이터 관리**: 요청 통계, 성능 지표 등 기본 정보 제공
- **데이터 정합성**: 타임스탬프 기반 중복 검사, 연속성 검증
- **클라이언트 독립**: 각 클라이언트가 필요한 데이터를 직접 요청

## 🔗 다른 레이어와의 협력

### Market Data Coordinator (Layer 2) 협력 (업데이트)
- **데이터 수신**: Coordinator가 통합한 대용량 데이터를 저장
- **증분 요청**: 캐시에 없는 데이터만 Coordinator에 요청
- **성능 피드백**: 저장소 성능 지표를 Coordinator에 전달
- **장애복구 지원**: Smart Router의 WebSocket 장애복구 데이터 안정적 저장
- **병행 개발**: Coordinator 완성 이전에도 독립적 개발 및 테스트 가능

### 비즈니스 서비스와의 협력
- **데이터 요청 응답**: 클라이언트가 요청한 데이터를 있는 그대로 제공
- **캐시 활용**: 최근 데이터는 캐시에서 즉시 응답
- **DB 조회**: 캐시에 없는 데이터는 DB에서 조회 후 제공
- **메타데이터 제공**: 데이터 품질, 수집 시간 등 기본 정보만 제공

## 💡 성능 최적화 전략

### 1. 데이터베이스 최적화
- **파편화 관리**: 스마트 VACUUM 스케줄러, 임계값 기반 자동 실행
- **인덱스 최적화**: 사용 패턴 분석, 커버링 인덱스, 자동 REINDEX
- **통계 관리**: ANALYZE 자동 실행, 쿼리 플래너 최적화
- **압축**: 오래된 데이터 압축 저장 (선택적)

### 2. 캐싱 최적화
- **계층 구조**: 메모리 → 디스크 → DB 순차 조회
- **사전 로딩**: 자주 사용되는 데이터 미리 캐시
- **지능적 만료**: 거래 시간 고려한 TTL 정책
- **압축 캐시**: 메모리 사용량 최적화

### 3. 쿼리 최적화
- **배치 조회**: 여러 심볼을 한 번에 조회
- **범위 쿼리**: 시간 범위 기반 효율적 조회
- **결과 캐시**: 복잡한 쿼리 결과 임시 저장
- **비동기 처리**: I/O 블로킹 최소화

## 🔧 운영 및 모니터링

### 1. 데이터 정합성
- **중복 검사**: 타임스탬프 기반 중복 데이터 감지
- **연속성 검증**: 시간 순서 및 누락 구간 검사
- **무결성 확인**: 외래키 제약, 데이터 타입 검증

### 2. 성능 모니터링
- **쿼리 성능**: 느린 쿼리 감지 및 최적화 (EXPLAIN QUERY PLAN)
- **파편화 추적**: 실시간 파편화율 모니터링, 임계값 알림
- **캐시 효율**: 히트율, 메모리 사용량 추적
- **저장소 용량**: 디스크 사용량, 증가율 모니터링

### 3. 자동화 운영
- **스마트 VACUUM**: 파편화 임계값 기반 자동 실행
- **인덱스 관리**: 통계 업데이트, 사용하지 않는 인덱스 정리
- **캐시 정리**: 만료된 캐시 자동 정리
- **성능 튜닝**: 쿼리 패턴 분석 후 자동 최적화 제안

## 🎯 성공 기준
- ✅ **캔들 데이터 조회**: 최근 1000개 캔들 조회 < 100ms (DB 최적화)
- ✅ **실시간 데이터 응답**: 티커/호가창 조회 < 10ms (메모리 캐시)
- ✅ **캔들 데이터 저장**: 10만개 캔들 배치 저장 < 5초 (DB 최적화)
- ✅ **메모리 효율성**: 실시간 데이터 메모리 사용량 최적화 (DB 저장 없음)
- ✅ **데이터 정합성**: 중복 없고 연속성 있는 데이터 보장

## 🚀 개발 우선순위
1. **Phase 1**: 데이터 모델 및 스키마 설계
2. **Phase 2**: 기본 저장소 구현 (SQLite)
3. **Phase 3**: 메모리 캐싱 시스템
4. **Phase 4**: 기본 비즈니스 인터페이스
5. **Phase 5**: 성능 최적화 및 운영 기능

---
**의존성**: ✅ TASK_20250820_01 Smart Routing Phase 1 완료 (WebSocket 장애복구 포함)
**시작 조건**: TASK_20250820_02 Coordinator와 독립적 병행 개발 가능
**연관 태스크**: TASK_20250820_04 Backbone API와 통합
**예상 소요시간**: 3-4일 (독립적 병행 개발로 효율성 확보)
**핵심 가치**: 마켓 데이터의 안정적 저장 및 빠른 조회

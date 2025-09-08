# 📚 SQLite VACUUM 완전 가이드

> SQLite 데이터베이스 최적화를 위한 단계별 완전 가이드

---

## 🗄️ VACUUM이란?

**VACUUM**은 데이터베이스의 **물리적 저장 공간을 최적화**하는 명령어입니다. 데이터를 삭제해도 실제 파일 크기는 줄어들지 않는 문제를 해결합니다.

---

## 📚 1단계: 기본 개념 이해

### 왜 VACUUM이 필요한가?

```sql
-- 예시: 테이블에 데이터 삽입
CREATE TABLE test_table (id INTEGER, data TEXT);
INSERT INTO test_table VALUES (1, 'data1'), (2, 'data2'), (3, 'data3');

-- 데이터 삭제
DELETE FROM test_table WHERE id = 2;
```

**문제점**: `DELETE`로 데이터를 삭제해도 **파일 크기는 그대로**입니다!
- 삭제된 공간은 "빈 공간"으로 남아있음
- 새 데이터가 들어올 때까지 재사용되지 않음
- 파일 크기가 계속 증가만 함

---

## 🔧 2단계: VACUUM 작동 원리

### VACUUM 실행 과정

1. **전체 데이터베이스 스캔**: 모든 활성 데이터 식별
2. **새 임시 파일 생성**: 깨끗한 파일에 데이터 복사
3. **데이터 재배치**: 활성 데이터만 연속적으로 배치
4. **원본 파일 교체**: 임시 파일로 원본 파일 대체
5. **메타데이터 갱신**: 인덱스와 통계 정보 재구성

```python
# 실제 테스트에서 본 VACUUM 효과
print("VACUUM 전: 43.37MB")
# VACUUM 실행 시간: 6.5초
print("VACUUM 후: 파일 크기 최적화 완료")
```

---

## 📊 3단계: VACUUM 종류와 차이점

### SQLite VACUUM 종류

| 종류 | 설명 | 사용 시기 |
|------|------|-----------|
| `VACUUM` | 전체 데이터베이스 재구성 | 대량 삭제 후 |
| `VACUUM table_name` | 특정 테이블만 최적화 | 특정 테이블 정리 시 |
| `PRAGMA auto_vacuum` | 자동 정리 모드 설정 | 지속적 관리 |

### Auto Vacuum 모드

```sql
-- 설정 확인
PRAGMA auto_vacuum;

-- 모드 설정
PRAGMA auto_vacuum = FULL;    -- 즉시 공간 반환
PRAGMA auto_vacuum = INCREMENTAL; -- 점진적 정리
PRAGMA auto_vacuum = NONE;    -- 수동 관리 (기본값)
```

---

## ⚡ 4단계: 성능 특성과 주의사항

### VACUUM 성능 특성

```python
# 우리 테스트 결과 분석
database_size = "43.37MB"
tables_count = 5580
vacuum_time = "6.5초"

# 성능 계산
vacuum_rate = 43.37 / 6.5  # ≈ 6.7MB/초
```

**성능 영향 요소**:
- **데이터베이스 크기**: 클수록 오래 걸림
- **삭제된 데이터 비율**: 많을수록 효과 큼
- **디스크 I/O 성능**: SSD vs HDD 차이
- **메모리 크기**: 캐시 효율성

### 주의사항 ⚠️

1. **배타적 잠금**: VACUUM 중에는 다른 작업 불가
2. **임시 공간 필요**: 원본 크기만큼 추가 디스크 공간 필요
3. **시간 소요**: 대용량 DB에서는 수분~수시간 소요
4. **트랜잭션 롤백**: VACUUM 중 중단되면 원상복구

---

## 🎯 5단계: 실무 활용 가이드

### 언제 VACUUM을 실행해야 하나?

```python
# VACUUM 필요성 체크 쿼리
def check_vacuum_needed():
    """
    1. 대량 DELETE/UPDATE 후
    2. 파일 크기 vs 실제 데이터 크기 비교
    3. 성능 저하 감지 시
    """

    # 페이지 통계 확인
    cursor.execute("PRAGMA page_count")  # 전체 페이지
    total_pages = cursor.fetchone()[0]

    cursor.execute("PRAGMA freelist_count")  # 빈 페이지
    free_pages = cursor.fetchone()[0]

    fragmentation_ratio = free_pages / total_pages

    if fragmentation_ratio > 0.1:  # 10% 이상 단편화
        print("VACUUM 권장!")
```

### 최적 실행 전략

```python
# 1. 유지보수 시간에 실행
def scheduled_vacuum():
    """새벽 시간대 배치 작업으로 실행"""
    import schedule
    schedule.every().day.at("02:00").do(run_vacuum)

# 2. 임계값 기반 자동 실행
def auto_vacuum_trigger():
    """파일 크기나 성능 기준으로 자동 실행"""
    if file_size > threshold or query_time > baseline * 1.5:
        run_vacuum()

# 3. 점진적 VACUUM (대용량 DB용)
def incremental_vacuum():
    """작은 단위로 나누어 실행"""
    cursor.execute("PRAGMA incremental_vacuum(100)")  # 100페이지씩
```

---

## 🔍 6단계: 고급 최적화 기법

### VACUUM과 함께 사용하는 최적화

```sql
-- 1. 통계 정보 갱신
ANALYZE;

-- 2. 인덱스 재구성
REINDEX;

-- 3. 페이지 크기 최적화
PRAGMA page_size = 4096;  -- 데이터 특성에 맞게 조정

-- 4. 캐시 크기 조정
PRAGMA cache_size = -2000;  -- 2MB 캐시
```

### 모니터링 쿼리

```python
def vacuum_monitoring():
    """VACUUM 효과 측정"""

    # Before
    before_size = os.path.getsize('database.sqlite3')
    before_time = time.time()

    # VACUUM 실행
    cursor.execute("VACUUM")

    # After
    after_size = os.path.getsize('database.sqlite3')
    after_time = time.time()

    print(f"크기 감소: {before_size - after_size:,} bytes")
    print(f"소요 시간: {after_time - before_time:.2f}초")
    print(f"압축률: {(1 - after_size/before_size)*100:.1f}%")
```

---

## 💡 7단계: 실제 프로젝트 적용 예시

우리 업비트 프로젝트에서의 VACUUM 활용:

```python
# upbit_auto_trading/infrastructure/database/sqlite_utils.py
class DatabaseMaintenance:
    """데이터베이스 유지보수 유틸리티"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = create_component_logger("DatabaseMaintenance")

    def smart_vacuum(self) -> bool:
        """스마트 VACUUM 실행"""
        try:
            # 1. 단편화 수준 체크
            if not self._needs_vacuum():
                self.logger.info("VACUUM 불필요 - 단편화 수준 낮음")
                return False

            # 2. 디스크 공간 체크
            if not self._has_enough_space():
                self.logger.warning("VACUUM 중단 - 디스크 공간 부족")
                return False

            # 3. VACUUM 실행
            start_time = time.time()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")

            duration = time.time() - start_time
            self.logger.info(f"VACUUM 완료 - 소요시간: {duration:.2f}초")
            return True

        except Exception as e:
            self.logger.error(f"VACUUM 실패: {e}")
            return False

    def _needs_vacuum(self) -> bool:
        """VACUUM 필요성 판단"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA page_count")
            total_pages = cursor.fetchone()[0]
            cursor.execute("PRAGMA freelist_count")
            free_pages = cursor.fetchone()[0]

            if total_pages == 0:
                return False

            fragmentation = free_pages / total_pages
            return fragmentation > 0.1  # 10% 이상 단편화시 VACUUM

    def _has_enough_space(self) -> bool:
        """충분한 디스크 공간 확인"""
        import shutil
        db_size = os.path.getsize(self.db_path)
        free_space = shutil.disk_usage(os.path.dirname(self.db_path)).free

        # DB 크기의 2배 공간이 필요
        return free_space > db_size * 2
```

---

## 📈 성능 테스트 결과 (실제 데이터)

### 업비트 프로젝트 테스트 환경
- **테이블 수**: 5,580개 (558 마켓 × 10 타임프레임)
- **데이터베이스 크기**: 43.37MB
- **VACUUM 소요 시간**: 6.5초
- **처리 속도**: 약 6.7MB/초

### 파일 vs 메모리 DB 성능 비교

| 항목 | 메모리 DB | 파일 DB | 차이 |
|------|-----------|---------|------|
| 메타데이터 쿼리 | 3.42ms | 8.11ms | 2.4배 느림 |
| 테이블 존재 확인 | 0.794ms | 5.185ms | 6.5배 느림 |
| 기본 쿼리 | 0.363ms | 0.156ms | 57% 빠름 |

**결론**: 파일 DB는 메모리 DB보다 2-6배 느리지만, 절대적으로는 여전히 매우 빠른 성능을 보임

---

## 📋 요약: VACUUM 체크리스트

### ✅ VACUUM 실행 전 체크사항
- [ ] 데이터베이스 백업 완료
- [ ] 충분한 디스크 공간 확보 (DB 크기의 2배)
- [ ] 다른 프로세스의 DB 접근 중단
- [ ] 유지보수 시간대 확인

### ✅ VACUUM 실행 후 확인사항
- [ ] 파일 크기 감소 확인
- [ ] 쿼리 성능 개선 확인
- [ ] 애플리케이션 정상 동작 확인
- [ ] 로그에서 에러 메시지 확인

### 🔧 PRAGMA 명령어 활용

```sql
-- 데이터베이스 상태 확인
PRAGMA database_list;          -- 연결된 DB 목록
PRAGMA table_info(table_name); -- 테이블 스키마 정보
PRAGMA index_list(table_name); -- 인덱스 목록

-- 성능 관련 설정
PRAGMA page_size;              -- 페이지 크기 확인/설정
PRAGMA cache_size;             -- 캐시 크기 확인/설정
PRAGMA synchronous;            -- 동기화 모드 확인/설정
PRAGMA journal_mode;           -- 저널링 모드 확인/설정

-- 공간 사용량 분석
PRAGMA page_count;             -- 전체 페이지 수
PRAGMA freelist_count;         -- 빈 페이지 수
PRAGMA integrity_check;        -- 무결성 검사
```

### 🚀 고급 팁

1. **대용량 DB VACUUM 최적화**
   ```sql
   -- 임시 디렉토리 설정 (빠른 디스크로)
   PRAGMA temp_store_directory = '/fast/ssd/temp';

   -- 메모리 사용량 증가
   PRAGMA cache_size = -64000;  -- 64MB 캐시
   ```

2. **부분적 VACUUM (SQLite 3.15+)**
   ```sql
   -- 특정 양만큼만 정리
   PRAGMA incremental_vacuum(1000);
   ```

3. **VACUUM 모니터링**
   ```python
   # VACUUM 진행률 모니터링 (콜백 등록)
   def vacuum_progress_callback(progress):
       print(f"VACUUM 진행률: {progress}%")

   conn.set_progress_handler(vacuum_progress_callback, 1000)
   ```

---

## 🎓 학습 참고 자료

- [SQLite 공식 VACUUM 문서](https://www.sqlite.org/lang_vacuum.html)
- [SQLite PRAGMA 명령어 가이드](https://www.sqlite.org/pragma.html)
- [SQLite 성능 최적화 가이드](https://www.sqlite.org/optoverview.html)

---

**작성일**: 2025년 9월 8일
**프로젝트**: 업비트 자동매매 시스템
**테스트 환경**: 5,580개 테이블, 43.37MB DB 기준

이 가이드를 통해 SQLite VACUUM을 완전히 마스터하여 데이터베이스 성능을 극대화하세요! 🚀

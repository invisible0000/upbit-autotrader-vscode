# WebSocket 티커 테스트 스위트

업비트 WebSocket Provider의 포괄적인 테스트 인프라입니다.

## 📋 테스트 개요

총 **11개의 테스트 시나리오**로 구성되어 있으며, 기본 통신부터 대용량 처리까지 단계적으로 검증합니다.

### 🔧 기본 통신 테스트 (Test 1-7, 10)
- **Test 1**: 단일 티커 요청 - 기본 WebSocket 통신 검증
- **Test 2**: 5회 연속 요청 - 연속 요청 성능 및 지연시간 분석
- **Test 3**: 멀티 심볼 구독 - 3개 심볼 동시/순차 처리
- **Test 4**: 5개 티커 멀티 구독 - 동시 구독 확장성 검증
- **Test 5**: 다회 멀티 구독 - 안정성 및 버스트 처리
- **Test 6**: 순서대로 요청 - 처리 순서 및 우선순위 검증
- **Test 7**: 다중 동시 요청 - 단계별 부하 증가 및 동시성 분석
- **Test 10**: 연속 5회 일관성 - 성능 일관성 및 시간별 안정성

### 🔥 대용량 및 특수 테스트 (Test 8-9)
- **Test 8**: 50개 티커 대용량 처리 - 배치 처리, 메모리 효율성, 지속적 부하
- **Test 9**: KRW 마켓 전체 포괄 - 전체 KRW 마켓 스캔 및 카테고리별 분석

### ⚡ 부하 및 확장성 테스트 (Test 11)
- **Test 11**: 부하 및 확장성 - 단계별 부하 증가 및 성능 한계 분석

## 🚀 실행 방법

### 전체 테스트 스위트 실행
```powershell
cd tests/websocket
python run_all_tests.py
```

### 개별 테스트 실행
```powershell
# 단일 티커 테스트
python ticker/test_01_single_request.py

# 5회 연속 요청 테스트
python ticker/test_02_multiple_requests.py

# 멀티 심볼 구독 테스트
python ticker/test_03_multi_symbol.py

# 5개 티커 멀티 구독 테스트
python ticker/test_04_multi_5_ticker.py

# 다회 멀티 구독 테스트
python ticker/test_05_multiple_multi.py

# 순서대로 요청 테스트
python ticker/test_06_sequential_ordered.py

# 다중 동시 요청 테스트
python ticker/test_07_multiple_simultaneous.py

# 50개 티커 대용량 처리 테스트
python ticker/test_08_large_scale_50_ticker.py

# KRW 마켓 전체 포괄 테스트
python ticker/test_09_krw_market_comprehensive.py

# 연속 5회 일관성 테스트
python ticker/test_10_consecutive_5_rounds.py

# 부하 및 확장성 테스트
python ticker/test_11_load_scalability.py
```

## 📊 성능 분석 기능

### 🎯 실시간 성능 측정
- **응답시간**: 평균, 최소, 최대, 중간값, 백분위수 (P50, P95)
- **처리량**: RPS (Requests Per Second) 계산
- **성공률**: 요청 성공/실패 비율
- **동시성 효율성**: 이론적 순차 처리 대비 실제 성능

### 📈 확장성 분석
- **부하 증가 패턴**: 요청 수 증가에 따른 성능 변화
- **성능 저하 지점**: 기울기 계산을 통한 병목 지점 탐지
- **메모리 사용량**: 대용량 처리 시 메모리 효율성 모니터링

### 🔍 일관성 검증
- **통계적 분석**: 평균, 중간값, 표준편차, 변동계수
- **이상치 탐지**: Z-score 기반 이상치 식별
- **시간별 안정성**: 시간-성능 상관관계 분석

## 📁 결과 저장

### 📂 디렉토리 구조
```
tests/websocket/test_results/
├── test_01_single_request_results.json
├── test_02_multiple_requests_results.json
├── ...
├── test_11_load_scalability_results.json
└── test_suite_summary_YYYYMMDD_HHMMSS.json
```

### 📄 통합 리포트
전체 테스트 완료 후 `test_suite_summary_*.json` 파일에 다음 정보가 저장됩니다:
- 전체 실행 시간 및 테스트 통계
- 개별 테스트 결과 및 성능 지표
- 종합 분석 및 권장사항

## 🛠️ 기술 구조

### 🧩 핵심 컴포넌트
- **WebSocketTestBase**: 공통 테스트 기반 클래스
- **PerformanceMetrics**: 성능 지표 수집 및 계산
- **LoadTestAnalyzer**: 부하 테스트 및 확장성 분석
- **Infrastructure Logger**: 컴포넌트별 로깅 시스템

### 🔄 테스트 플로우
1. **환경 초기화**: Provider 생성 및 로깅 설정
2. **요청 실행**: 타이밍 측정 및 결과 수집
3. **성능 분석**: 통계 계산 및 패턴 분석
4. **결과 저장**: JSON 형태로 결과 영구 저장
5. **정리**: Provider 정리 및 리소스 해제

## 📏 성능 기준

### ✅ 우수한 성능
- **응답시간**: < 300ms
- **성공률**: > 95%
- **변동계수**: < 10% (일관성)
- **동시성 효율성**: > 80%

### ⚠️ 개선 필요
- **응답시간**: > 1000ms
- **성공률**: < 85%
- **변동계수**: > 30% (불일치)
- **메모리 증가**: > 100MB

## 🔧 설정 및 커스터마이징

### 환경 변수
```powershell
# 로깅 설정
$env:UPBIT_CONSOLE_OUTPUT = "true"
$env:UPBIT_LOG_SCOPE = "verbose"
$env:UPBIT_COMPONENT_FOCUS = "WebSocketTest"

# API 키 (실제 사용 시)
$env:UPBIT_ACCESS_KEY = "your_access_key"
$env:UPBIT_SECRET_KEY = "your_secret_key"
```

### 테스트 파라미터 수정
각 테스트 파일의 `__init__` 메서드에서 다음 값들을 조정할 수 있습니다:
- 테스트 심볼 목록
- 배치 크기
- 반복 횟수
- 시간 간격

## 🚨 주의사항

### 🛡️ API 사용량 제한
- 업비트 API Rate Limit을 고려하여 테스트 간 적절한 쿨다운 적용
- 대용량 테스트는 실제 환경에서 신중하게 실행
- Dry-run 모드로 먼저 검증 후 실제 API 테스트 수행

### 🔒 보안
- API 키는 환경변수로만 설정
- 테스트 결과에 민감한 정보 포함 금지
- 로그 파일의 접근 권한 관리

### ⚡ 성능 고려사항
- 전체 테스트 스위트는 약 20-30분 소요 예상
- 대용량 테스트는 시스템 리소스를 많이 사용
- 동시에 여러 테스트 실행 시 결과 왜곡 가능성

## 📞 지원 및 문의

테스트 관련 문제나 개선사항은 프로젝트 이슈 트래커를 통해 제보해 주세요.

---

> 💡 **팁**: 첫 실행 시에는 개별 테스트부터 시작하여 환경을 검증한 후, 전체 스위트를 실행하는 것을 권장합니다.

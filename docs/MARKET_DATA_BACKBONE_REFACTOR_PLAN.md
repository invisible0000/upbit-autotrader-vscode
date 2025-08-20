# MarketDataBackbone 통합 및 정리 계획

## 📊 현황 분석

### 현재 구조
```
market_data_backbone/
├── v2/                        # 새로운 V2 시스템 (81 테스트 통과)
│   ├── unified_market_data_api.py   # 메인 API (간소화된 라우터 적용)
│   ├── smart_channel_router.py      # 통합된 스마트 라우터
│   ├── data_unifier.py              # 데이터 통합기
│   ├── data_models.py               # 데이터 모델
│   ├── api_exceptions.py            # 예외 처리
│   └── [정리 대상 파일들]
├── unified_market_data_api.py # 기존 V1 시스템
├── data_collector.py          # 기존 컬렉터
└── [기타 레거시 파일들]
```

### 사용처 분석
- ✅ **주요 사용처**: 테스트 코드 (81개 통과)
- ✅ **UI 연동**: 아직 직접 연동 없음 (차트뷰 준비 단계)
- ✅ **전환 용이성**: UI에서 사용 전이므로 안전한 전환 가능

## 🎯 정리 목표

### 1. 파일 구조 최적화
- V2를 메인으로 승격
- 불필요한 파일 정리
- 명명 컨벤션 통일

### 2. 기능별 모듈 분리
```
market_data_backbone/
├── core/              # 핵심 기능
│   ├── router.py          # 스마트 라우터 (통합)
│   ├── api.py             # 통합 API
│   ├── data_unifier.py    # 데이터 통합
│   └── exceptions.py      # 예외 처리
├── models/            # 데이터 모델
│   ├── ticker.py          # 티커 모델
│   ├── candle.py          # 캔들 모델
│   └── unified.py         # 통합 모델
├── adapters/          # 외부 연동
│   ├── rest_adapter.py    # REST API 어댑터
│   └── websocket_adapter.py # WebSocket 어댑터
└── __init__.py        # 공개 인터페이스
```

### 3. 레거시 정리
- V1 파일들 legacy/ 폴더로 이동
- 백업 파일들 정리
- 중복 파일 제거

## 🚀 실행 계획

### Phase 1: 구조 정리 (30분)
1. 새로운 폴더 구조 생성
2. V2 핵심 파일들 이동 및 이름 정리
3. 레거시 파일 정리

### Phase 2: 인터페이스 통일 (30분)
1. 공개 API 인터페이스 정의
2. Import 경로 업데이트
3. 테스트 코드 수정

### Phase 3: 검증 및 최적화 (30분)
1. 모든 테스트 통과 확인
2. 성능 검증
3. 문서 업데이트

## 📋 세부 작업

### 1단계: 핵심 파일 이동
```bash
# 현재 V2 핵심 파일들을 새 구조로
v2/smart_channel_router.py      → core/router.py
v2/unified_market_data_api.py   → core/api.py
v2/data_unifier.py              → core/data_unifier.py
v2/api_exceptions.py            → core/exceptions.py
v2/data_models.py               → models/unified.py
```

### 2단계: 정리 대상 파일들
```bash
# 삭제할 파일들
v2/simplified_smart_router.py   # 통합됨
v2/request_analyzer.py          # 통합됨
v2/*_backup_*.py                # 백업 파일들
v2/*_new.py                     # 임시 파일들

# 레거시로 이동
unified_market_data_api.py      → legacy/
data_collector.py               → legacy/
```

### 3단계: 공개 인터페이스
```python
# market_data_backbone/__init__.py
from .core.api import UnifiedMarketDataAPI
from .models.unified import UnifiedTickerData
from .core.exceptions import UnifiedDataException

__all__ = [
    "UnifiedMarketDataAPI",
    "UnifiedTickerData",
    "UnifiedDataException"
]
```

## ✅ 성공 기준

### 기능적 요구사항
- [ ] 모든 기존 테스트 통과 (81개)
- [ ] 새로운 import 경로로 정상 동작
- [ ] 스마트 라우터 정상 작동
- [ ] 차트뷰 연동 준비 완료

### 구조적 요구사항
- [ ] 명확한 폴더 구조
- [ ] 컨벤션 준수 파일명
- [ ] 중복 코드 제거
- [ ] 레거시 분리

---

**다음 단계**: 1단계부터 차근차근 실행

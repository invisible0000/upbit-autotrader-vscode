# 스마트 라우팅 시스템 기획 문서

## 📋 현황 분석

### 문제점
- ❌ 파일 분산으로 복잡성 증가 (smart_channel_router.py, simplified_smart_router.py, request_analyzer.py)
- ❌ 컨벤션 위반 파일명 (simplified_smart_router.py)
- ❌ 과도한 세분화로 오히려 성능 저하
- ❌ 사용자가 RequestType, Priority를 일일이 지정해야 하는 비스마트함

### 핵심 요구사항
1. **단순한 요청**: 시스템은 URL만 요청
2. **자동 분류**: REST 전용 vs WebSocket 가능 자동 판별
3. **패턴 학습**: 요청 간격 히스토리로 고빈도/저빈도 예측
4. **Rate Limit 준수**: 업비트 API 제한 엄격 준수
5. **트레이드오프 허용**: 예측 실패는 감수, 반응속도 우선

## 🎯 단일 파일 통합 설계

### 파일 구조 (단순화)
```
smart_channel_router.py  # ← 기존 파일 1개로 통합
├── ChannelDecision (기존 유지)
├── SmartChannelRouter (완전 재설계)
└── 보조 클래스들
```

## 🧠 핵심 로직

### 1단계: 요청 분류 (즉시 판별)
```
URL 패턴 매칭 → REST 전용 / WebSocket 가능 구분
- /v1/orders/* → REST 전용 (Rate Limit: 8 req/s)
- /v1/accounts → REST 전용 (Rate Limit: 30 req/s)
- /v1/ticker → 혼용 가능 (실시간성에 따라 결정)
- /v1/candles → REST 선호 (과거 데이터)
```

### 2단계: 패턴 분석 (히스토리 기반)
```
요청 간격 히스토리 → 그래프 패턴 → 다음 요청 예측
- 간격 리스트: [5.2, 4.8, 5.1, 0.9, 0.8, ...] (최근 20개)
- 추세 분석: 하향(고빈도화) / 상향(저빈도화) / 안정
- 예측: 다음 5개 요청의 예상 빈도
```

### 3단계: 라우팅 결정 (5단계)
```
1) REST 전용 → 무조건 REST (Rate Limit 확인)
2) WebSocket 불가 → REST 폴백
3) 고빈도 예측 + 실시간 → WebSocket
4) 저빈도 + 과거 데이터 → REST
5) 기본값 → 현재 상태 유지
```

### 4단계: Rate Limit 관리
```
업비트 실제 제한:
- REST Order: 8 req/s
- REST Exchange: 30 req/s
- REST Quotation: 10 req/s
- WebSocket: 5 req/s, 100 req/min

Buffer: 80% 사용 (안전 마진)
```

## 📊 패턴 분석 알고리즘

### 간격 그래프 분석
```python
def analyze_interval_trend(intervals: List[float]) -> str:
    if len(intervals) < 3:
        return "insufficient_data"

    # 최근 3개와 이전 3개 비교
    recent_avg = sum(intervals[-3:]) / 3
    previous_avg = sum(intervals[-6:-3]) / 3

    if recent_avg < previous_avg * 0.7:
        return "accelerating"  # 고빈도화
    elif recent_avg > previous_avg * 1.3:
        return "decelerating"  # 저빈도화
    else:
        return "stable"
```

### 예측 로직
```python
def predict_next_frequency(trend: str, current_freq: float) -> str:
    if trend == "accelerating" or current_freq > 0.5:  # 2초 이하 간격
        return "high_frequency"
    elif trend == "decelerating" or current_freq < 0.1:  # 10초 이상 간격
        return "low_frequency"
    else:
        return "medium_frequency"
```

## ⚡ 성능 최적화

### 반응속도 우선
- URL 패턴 매칭: 정규식 사전 컴파일
- 히스토리: 최대 20개 제한
- 계산: 단순 평균/비교만 사용
- 캐시: 동일 URL 1초간 결과 재사용

### 메모리 효율
- 심볼별 분리 저장
- 비활성 심볼 자동 정리 (1시간 이상 미사용)
- 고정 크기 버퍼 사용

## 🔄 트레이드오프 정책

### 허용되는 실패
- 예측 정확도: 70% 목표 (30% 실패 허용)
- 채널 전환 지연: 최대 3회 요청
- Rate Limit 초과: 일시 대기 허용

### 우선순위
1. 안정성 > 성능
2. 반응속도 > 정확도
3. 단순함 > 완벽함

## 📝 구현 계획

### Phase 1: 통합 및 단순화 (현재)
- 기존 3개 파일을 1개로 통합
- 핵심 로직만 유지
- 테스트 호환성 확보

### Phase 2: 패턴 분석 구현
- 간격 히스토리 추가
- 추세 분석 알고리즘
- 예측 로직 구현

### Phase 3: 최적화
- 성능 튜닝
- 메모리 효율화
- 모니터링 추가

## 🎯 성공 기준

### 기능 요구사항
- [x] URL만으로 자동 라우팅
- [ ] 패턴 학습 기반 예측
- [ ] Rate Limit 100% 준수
- [ ] WebSocket/REST 자동 전환

### 성능 요구사항
- 라우팅 결정: < 1ms
- 메모리 사용: < 50MB
- 예측 정확도: > 70%
- 시스템 안정성: 99.9%

## 🚀 다음 단계

1. **즉시**: 파일 통합 (smart_channel_router.py 1개로)
2. **1시간**: 핵심 로직 구현
3. **2시간**: 패턴 분석 추가
4. **3시간**: 테스트 및 검증

---

**핵심 철학**: "단순하고 빠르게, 70% 정확도로 충분하다"

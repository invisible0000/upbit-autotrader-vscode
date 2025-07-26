# 🎯 트리거 관리 시스템 사용 가이드

## 📋 개요
이 가이드는 업비트 자동 트레이딩 시스템의 트리거 관리 기능을 효율적으로 사용하는 방법을 설명합니다.

## 🛠️ 트리거 관리 스크립트 사용법

### 1. 기본 사용법

```bash
# 트리거 목록 조회
python trigger_manager.py list

# 카테고리별 트리거 조회
python trigger_manager.py list --category momentum

# 트리거 통계 확인
python trigger_manager.py stats

# 트리거 백업 (삭제 전 권장)
python trigger_manager.py backup --output backup_20250726.json

# 모든 트리거 삭제 (주의!)
python trigger_manager.py clean

# 확인 없이 강제 삭제
python trigger_manager.py clean --force

# 트리거 내보내기
python trigger_manager.py export --output my_triggers.json

# JSON 파일에서 트리거 일괄 생성
python trigger_manager.py create --file example_triggers.json
```

### 2. 안전한 데이터 관리

```bash
# ⚠️ 기존 트리거 교체 시 권장 워크플로우 ⚠️

# 1단계: 기존 트리거 백업
python trigger_manager.py backup --output old_triggers_backup.json

# 2단계: 기존 트리거 삭제 (구 버전 호환성 문제 해결)
python trigger_manager.py clean

# 3단계: 새로운 트리거 생성
python trigger_manager.py create --file new_triggers.json

# 4단계: 결과 확인
python trigger_manager.py list
python trigger_manager.py stats
```

### 3. 트리거 JSON 파일 형식

```json
[
  {
    "name": "RSI 과매도 신호",
    "description": "RSI가 30 이하로 떨어질 때 매수 신호",
    "variable_id": "RSI",
    "variable_name": "상대강도지수",
    "variable_params": {
      "period": 14,
      "timeframe": "1h"
    },
    "operator": "<=",
    "comparison_type": "fixed",
    "target_value": "30",
    "external_variable": null,
    "trend_direction": "falling",
    "category": "momentum",
    "tags": ["매수신호", "과매도", "RSI"]
  }
]
```

## 📊 지원하는 지표 및 변수

### 1. 지표 (Indicators)
- **SMA**: 단순이동평균
- **EMA**: 지수이동평균  
- **RSI**: 상대강도지수
- **MACD**: MACD 지표
- **BOLLINGER_BAND**: 볼린저밴드
- **STOCHASTIC**: 스토캐스틱
- **ATR**: 평균진실범위 (새로 추가)
- **VOLUME_SMA**: 거래량 이동평균 (새로 추가)

### 2. 시장 데이터
- **CURRENT_PRICE**: 현재가
- **VOLUME**: 거래량
- **HIGH**: 고가
- **LOW**: 저가
- **OPEN**: 시가

### 3. 자본 관리
- **AVAILABLE_BALANCE**: 사용 가능 잔액
- **TOTAL_ASSET**: 총 자산

## 🎯 실용적인 트리거 예제

### 1. 단순 조건 트리거

#### RSI 과매도/과매수
```json
{
  "name": "RSI 과매도 신호",
  "variable_id": "RSI",
  "operator": "<=",
  "target_value": "30",
  "category": "momentum"
}
```

#### 볼린저 밴드 터치
```json
{
  "name": "볼린저 밴드 하단 터치",
  "variable_id": "CURRENT_PRICE",
  "operator": "<=",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "BOLLINGER_BAND",
    "variable_params": {"band_type": "lower"}
  }
}
```

### 2. 복합 조건 트리거

#### 골든 크로스
```json
{
  "name": "골든 크로스 신호",
  "variable_id": "SMA",
  "variable_params": {"period": 20},
  "operator": ">",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "SMA",
    "variable_params": {"period": 50}
  },
  "trend_direction": "crossover_up"
}
```

#### 변동성 + 거래량 조합
```json
{
  "name": "높은 변동성 + 거래량 급증",
  "variable_id": "ATR",
  "operator": ">",
  "comparison_type": "external",
  "external_variable": {
    "variable_id": "ATR",
    "variable_params": {"multiplier": 2}
  },
  "additional_conditions": [
    {
      "variable_id": "VOLUME",
      "operator": ">",
      "comparison_type": "external",
      "external_variable": {
        "variable_id": "VOLUME_SMA",
        "variable_params": {"multiplier": 3}
      }
    }
  ]
}
```

## ⚙️ 트리거 파라미터 설정

### 1. 지표 파라미터

#### 이동평균 (SMA/EMA)
- `period`: 기간 (기본값: 20)
- `timeframe`: 시간프레임 ("1m", "5m", "1h", "1d")

#### RSI
- `period`: 기간 (기본값: 14)
- `timeframe`: 시간프레임

#### MACD
- `fast_period`: 단기 기간 (기본값: 12)
- `slow_period`: 장기 기간 (기본값: 26)
- `signal_period`: 시그널 기간 (기본값: 9)
- `type`: 타입 ("macd", "signal", "histogram")

#### 볼린저 밴드
- `period`: 기간 (기본값: 20)
- `multiplier`: 배수 (기본값: 2)
- `band_type`: 밴드 타입 ("upper", "middle", "lower")

#### ATR
- `period`: 기간 (기본값: 14)
- `timeframe`: 시간프레임

### 2. 비교 연산자
- `>`: 초과
- `>=`: 이상
- `<`: 미만
- `<=`: 이하
- `==`: 같음
- `!=`: 다름

### 3. 트렌드 방향
- `static`: 정적 (단순 비교)
- `rising`: 상승 중
- `falling`: 하락 중
- `crossover_up`: 상향 돌파
- `crossover_down`: 하향 돌파
- `touching`: 터치
- `expanding`: 확장
- `contracting`: 수축

## 🏷️ 카테고리 및 태그 시스템

### 1. 권장 카테고리
- `momentum`: 모멘텀 지표
- `trend`: 트렌드 추종
- `volatility`: 변동성 지표
- `volume`: 거래량 분석
- `support_resistance`: 지지/저항
- `custom`: 사용자 정의

### 2. 유용한 태그 예제
- 신호 타입: "매수신호", "매도신호", "관찰"
- 시간 프레임: "단기", "중기", "장기"
- 전략 유형: "스윙트레이딩", "데이트레이딩", "포지션트레이딩"
- 시장 상황: "상승장", "하락장", "횡보장"

## 🚀 효율적인 워크플로우

### 1. 트리거 개발 과정
1. **아이디어 수집**: 트레이딩 전략 및 신호 수집
2. **JSON 작성**: 트리거를 JSON 형식으로 정의
3. **일괄 생성**: `trigger_manager.py create` 명령으로 생성
4. **테스트**: 백테스팅 또는 페이퍼 트레이딩으로 검증
5. **최적화**: 파라미터 조정 및 성능 개선

### 2. 트리거 관리 팁
- **버전 관리**: 트리거 JSON 파일을 Git으로 관리
- **백업**: 정기적으로 트리거를 export하여 백업
- **카테고리화**: 명확한 카테고리로 분류하여 관리
- **태그 활용**: 검색 및 필터링을 위한 의미있는 태그 사용
- **문서화**: 복잡한 트리거의 경우 상세한 설명 추가

### 3. 성능 모니터링
- **통계 확인**: 주기적으로 `stats` 명령으로 현황 파악
- **성공률 추적**: 트리거별 성공률 모니터링 
- **사용 빈도**: 자주 사용되는 트리거 패턴 분석

## 🔧 문제 해결

### 1. 일반적인 오류
- **파라미터 오류**: 지표별 필수 파라미터 확인
- **타입 불일치**: 숫자 값은 문자열로 저장
- **중복 이름**: 트리거 이름은 고유해야 함

### 2. 성능 최적화
- **인덱스 활용**: 자주 조회하는 카테고리 활용
- **메모리 관리**: 대량의 트리거 생성 시 배치 처리
- **캐싱**: 자주 사용하는 트리거 캐싱

## 📞 지원 및 문의
트리거 시스템 사용 중 문제가 발생하면 다음을 확인하세요:
1. 데이터베이스 연결 상태
2. 필수 파라미터 누락 여부  
3. JSON 형식 오류
4. 호환성 검증 결과

---
**문서 버전**: 1.0  
**최종 업데이트**: 2025-07-26

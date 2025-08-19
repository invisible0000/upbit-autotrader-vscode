# 변화율 음수 코인 표시 안됨 문제 해결

## 🚨 문제 상황
- **증상**: 변화율이 음수인 코인들이 UI에 0.00%로 표시되거나 검은색 글자로 나타남
- **발생 시점**: 2025-08-19
- **영향 범위**: 차트뷰 코인 리스트의 변화율 표시 및 색상

## 🔍 근본 원인 분석
디버깅 결과 업비트 API의 특별한 데이터 구조 발견:
1. **`change_rate` 필드는 항상 절댓값(양수)으로 반환**
2. **실제 상승/하락은 `change` 필드로 구분** (`RISE`, `FALL`, `EVEN`)
3. **기존 로직은 `change_rate` 값만으로 음수 판단**

**예시**:
```
KRW-CARV: change: FALL, change_rate: 0.015251 (양수)
-> 실제로는 -1.53% 하락이지만 +1.53%로 표시됨
```

## 🛠️ 해결 방법

### 1. 수정 파일
- `upbit_auto_trading/application/chart_viewer/coin_list_service.py`
- `upbit_auto_trading/ui/desktop/screens/chart_view/widgets/coin_list_widget.py`

### 2. 핵심 수정 내용

#### 변화율 포맷팅 로직 개선:
```python
def _format_change_rate(self, change_rate: float, change_status: str) -> str:
    """변화율 포맷팅 (change 상태 고려)"""
    try:
        rate_percent = change_rate * 100

        if change_status == 'RISE':
            return f"+{rate_percent:.2f}%"
        elif change_status == 'FALL':
            return f"-{rate_percent:.2f}%"
        else:  # EVEN
            return "0.00%"
    except Exception:
        return "0.00%"
```

#### CoinInfo DTO 확장:
```python
@dataclass(frozen=True)
class CoinInfo:
    # 기존 필드들...
    change_rate_raw: float  # 정렬용 원본 변화율 (음수 포함)
```

#### 정렬 로직 개선:
```python
# change_rate_raw 필드 사용으로 정확한 음수/양수 정렬
def change_sort_key(coin):
    if hasattr(coin, 'change_rate_raw'):
        return coin.change_rate_raw  # -1.5, +2.3 등
    # 호환성 로직...
```

## ✅ 기대 결과
- 하락 코인: `-1.53%` (파란색 표시)
- 상승 코인: `+2.45%` (빨간색 표시)
- 보합 코인: `0.00%` (검은색 표시)
- 변화율 정렬에서 음수 코인이 하단에 정확히 위치

## 🧪 검증 방법
```python
# debug_change_rates.py 실행으로 API 데이터 구조 확인
python debug_change_rates.py
```

## 🔗 관련 파일
- `CoinInfo` DTO: 변화율 데이터 구조 확장
- `coin_list_service.py`: 업비트 API 변화율 처리 로직
- `coin_list_widget.py`: UI 표시 및 정렬 로직

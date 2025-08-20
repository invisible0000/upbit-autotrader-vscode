# 📋 TASK_20250818_02: 매매 변수 통계 계산 기능 추가

## 🎯 태스크 목표
- **주요 목표**: 7개 핵심 매매 변수에 통계 계산 기능 추가 (min/max/average/previous)
- **완료 기준**:
  - 각 변수별 최근 N일 통계 분석 가능 (N: 1-50)
  - "20일 최고 ATR", "5일전 RSI" 등 직관적 표현 구현
  - 개별 계산기 600라인 이하로 LLM 친화적 설계

## 📊 현재 상황 분석
### 문제점
1. 단순 현재값 비교로 시장 맥락 파악 한계
2. 과거 데이터 활용 불가능 (추세, 패턴 분석 부족)
3. 적응형 임계값 설정 불가능
4. TriggerCalculator 2000+ 라인으로 LLM 처리 한계 초과

### 사용 가능한 리소스
- 기존 technical_indicators 테이블 (히스토리 데이터)
- TASK_20250818_01 완료 후 multiplier_percent 파라미터
- 개별 계산기 아키텍처 설계 (ATR_enhancement_design.md)

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **⚡ 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## 🛠️ 작업 계획

### Phase 1: 아키텍처 설계 및 기반 구축 (3일)
- [ ] BaseCalculator 인터페이스 정의 (50라인)
- [ ] CalculatorFactory 패턴 구현 (150라인)
- [ ] 히스토리 데이터 캐싱 시스템 설계
- [ ] 개별 계산기 폴더 구조 생성

### Phase 2: 통계 파라미터 추가 (2일)
- [ ] calculation_method 파라미터 추가 (basic/previous/min/max/average)
- [ ] calculation_period 파라미터 추가 (1-50, basic이 아닐 때만 활성화)
- [ ] 조건부 UI 활성화 로직 구현
- [ ] 파라미터 검증 및 기본값 설정

### Phase 3: 개별 계산기 개발 (8일, 병렬 가능)
#### 변동성 그룹 (3일)
- [ ] ATRCalculator 구현 (500라인)
- [ ] BollingerBandCalculator 구현 (400라인)

#### 가격 그룹 (3일)
- [ ] HighPriceCalculator 구현 (350라인)
- [ ] LowPriceCalculator 구현 (350라인)
- [ ] OpenPriceCalculator 구현 (300라인)

#### 모멘텀/볼륨 그룹 (2일)
- [ ] RSICalculator 구현 (600라인)
- [ ] VolumeCalculator 구현 (400라인)

### Phase 4: 통합 및 최적화 (3일)
- [ ] 계산기 팩토리 통합 테스트
- [ ] 성능 최적화 (캐싱, 배치 처리)
- [ ] 메모리 사용량 모니터링 및 최적화
- [ ] 기존 TriggerEvaluationService와 연동

### Phase 5: UI 및 사용자 경험 (2일)
- [ ] 조건부 파라미터 활성화 UI 구현
- [ ] 계산 방식별 툴팁 및 도움말 추가
- [ ] 실시간 미리보기 기능 구현
- [ ] 오류 처리 및 데이터 부족 안내

### Phase 6: 검증 및 테스트 (2일)
- [ ] 각 계산기별 단위 테스트 (Given-When-Then)
- [ ] 통계 계산 정확도 검증
- [ ] 7규칙 전략에서 통합 테스트
- [ ] 성능 벤치마크 (기존 대비 20% 이하 증가)

## 🛠️ 개발할 도구
- `statistical_parameter_migrator.py`: 통계 파라미터 일괄 추가
- `calculator_generator.py`: 개별 계산기 템플릿 생성기
- `history_data_manager.py`: 히스토리 데이터 캐싱 및 관리
- `statistical_accuracy_validator.py`: 통계 계산 정확도 검증

## 🎯 성공 기준
- ✅ 7개 개별 계산기 모두 600라인 이하
- ✅ "ATR(20일최고, 150%)" 등 직관적 표현 지원
- ✅ 히스토리 데이터 최근 50개 메모리 캐싱
- ✅ 계산 시간 기존 대비 20% 이하 증가
- ✅ 데이터 부족시 안전한 폴백 처리
- ✅ UI 조건부 활성화 300ms 이내 반응

## 💡 작업 시 주의사항
### 안전성 원칙
- 각 계산기 독립 개발로 상호 영향 최소화
- 데이터 부족시 기존 basic 모드로 안전 복귀
- 단계별 백업 및 롤백 지점 설정

### LLM 친화적 설계
- 개별 파일 600라인 이하 엄격 준수
- 명확한 메서드명과 타입 힌트 필수
- 단순한 메서드 체인 구성

### 성능 최적화
- 메모리 캐싱: 심볼당 50개 * 8바이트 = 400바이트
- 계산 복잡도: O(1) ~ O(50) 수준 유지
- 배치 처리로 DB 접근 최소화

## 🚀 즉시 시작할 작업
```python
# Step 1: BaseCalculator 인터페이스 정의
from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class BaseCalculator(ABC):
    @abstractmethod
    def calculate(self, market_data: pd.DataFrame, params: Dict) -> float:
        """변수 계산 메인 메서드"""
        pass
```

## 📈 혁신적 활용 사례
```yaml
# 적응형 저항선 돌파
HIGH_PRICE(20일최고, 102%): 최강 저항선 2% 돌파 확인

# 변동성 수축 감지
ATR(20일최저, 120%): 극도 수축 상태에서 폭발 대기

# 거래량 급증 확인
VOLUME(10일평균, 200%): 평균 거래량 2배 돌파시 신호

# 모멘텀 확인
RSI(5일전) vs RSI(현재): 모멘텀 변화 추세 분석

# 복합 조건
ATR(수축) + HIGH_PRICE(돌파) + VOLUME(급증) = 완벽한 브레이크아웃
```

## 📁 권장 파일 구조
```
upbit_auto_trading/domain/trading_variables/calculators/
├── base_calculator.py              # 100라인 - 인터페이스
├── calculator_factory.py           # 150라인 - 팩토리
├── volatility/
│   ├── atr_calculator.py          # 500라인 - ATR 전용
│   └── bollinger_calculator.py    # 400라인 - 볼린저밴드
├── price/
│   ├── high_price_calculator.py   # 350라인 - 고가 전용
│   ├── low_price_calculator.py    # 350라인 - 저가 전용
│   └── open_price_calculator.py   # 300라인 - 시가 전용
├── momentum/
│   └── rsi_calculator.py          # 600라인 - RSI 전용
├── volume/
│   └── volume_calculator.py       # 400라인 - 거래량 전용
└── utils/
    ├── data_validator.py          # 200라인 - 데이터 검증
    └── cache_manager.py           # 250라인 - 캐싱 관리
```

---
**다음 에이전트 시작점**: BaseCalculator 인터페이스 정의 후 ATRCalculator부터 순차 개발
**의존성**: TASK_20250818_01(배율 기능) 완료 후 시작 권장
**핵심 원칙**: 한 번에 하나의 계산기만 개발하여 LLM 처리 한계 준수

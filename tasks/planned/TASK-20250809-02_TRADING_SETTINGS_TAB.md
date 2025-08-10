# 💰 TASK-20250809-02: 매매설정 탭 구현

## 📋 **작업 개요**
**목표**: 매매 전략 및 리스크 관리 설정을 위한 새로운 "매매설정" 탭 구현
**중요도**: ⭐⭐⭐⭐ (높음)
**예상 기간**: 3-4일
**담당자**: 개발팀

## 🎯 **작업 목표**
- config.yaml의 trading 섹션 전체를 UI로 구현
- 7규칙 전략 연동 및 리스크 관리 설정
- 실시간 매매 상태 모니터링 기능
- 매매 로그 및 백테스팅 결과 연동

## 🏗️ **아키텍처 설계**

### **Presentation Layer (MVP)**
```
📁 upbit_auto_trading/ui/desktop/screens/settings/trading/
├── presenters/
│   ├── trading_settings_presenter.py       # 매매설정 메인 프레젠터
│   ├── risk_management_presenter.py        # 리스크 관리 프레젠터
│   ├── strategy_config_presenter.py        # 전략 설정 프레젠터
│   └── position_management_presenter.py    # 포지션 관리 프레젠터
├── views/
│   ├── trading_settings_view.py            # 매매설정 뷰 인터페이스
│   ├── risk_management_view.py             # 리스크 관리 뷰 인터페이스
│   ├── strategy_config_view.py             # 전략 설정 뷰 인터페이스
│   └── position_management_view.py         # 포지션 관리 뷰 인터페이스
└── widgets/
    ├── trading_settings_widget.py          # 메인 매매설정 위젯
    ├── risk_management_section.py          # 리스크 관리 섹션
    ├── strategy_configuration_section.py   # 전략 설정 섹션
    ├── position_management_section.py      # 포지션 관리 섹션
    └── trading_status_monitor.py           # 매매 상태 모니터
```

### **Application Layer**
```
📁 upbit_auto_trading/application/trading_settings/
├── use_cases/
│   ├── update_risk_parameters_use_case.py  # 리스크 파라미터 업데이트
│   ├── validate_strategy_config_use_case.py # 전략 설정 검증
│   ├── get_trading_status_use_case.py      # 매매 상태 조회
│   └── apply_trading_settings_use_case.py  # 매매 설정 적용
└── dtos/
    ├── risk_management_dto.py              # 리스크 관리 DTO
    ├── strategy_configuration_dto.py       # 전략 설정 DTO
    ├── position_management_dto.py          # 포지션 관리 DTO
    └── trading_status_dto.py               # 매매 상태 DTO
```

## 📝 **작업 단계**

### **Sub-Task 2.1: 리스크 관리 섹션 구현** (1.5일)
**목표**: config.yaml trading 섹션의 리스크 관리 설정 UI 구현

#### **Step 2.1.1**: 기본 리스크 설정 UI
- [ ] 최대 투자 금액 설정 (max_investment_amount)
- [ ] 최대 포지션 수 설정 (max_positions)
- [ ] 손실 한도 설정 (stop_loss_percentage)
- [ ] 일일 손실 한도 설정 (daily_loss_limit)
- [ ] 계좌 잔고 비율 제한 (account_balance_ratio)

#### **Step 2.1.2**: 고급 리스크 설정 UI
- [ ] 변동성 기반 포지션 크기 조정
- [ ] 리스크 평가 지표 설정
- [ ] 상관관계 기반 포지션 제한
- [ ] 긴급 정지 조건 설정
- [ ] 리스크 알림 임계값 설정

#### **Step 2.1.3**: 리스크 시뮬레이션 도구
- [ ] 리스크 시나리오 테스트
- [ ] 최대 낙폭 계산기
- [ ] 포트폴리오 리스크 분석
- [ ] 백테스팅 연동 리스크 평가

**예상 산출물**:
- `risk_management_section.py` (완성)
- `risk_simulation_widget.py` (시뮬레이션 도구)
- `risk_parameters_form.py` (설정 폼)

---

### **Sub-Task 2.2: 전략 설정 섹션 구현** (1.5일)
**목표**: 매매 전략 관련 설정 UI 구현

#### **Step 2.2.1**: 기본 전략 설정 UI
- [ ] 기본 7규칙 전략 토글
- [ ] RSI 임계값 설정 (oversold/overbought)
- [ ] 이동평균 기간 설정
- [ ] 볼린저 밴드 설정
- [ ] 매매 시간대 제한 설정

#### **Step 2.2.2**: 고급 전략 설정 UI
- [ ] 사용자 정의 지표 조합
- [ ] 백테스팅 기간 설정
- [ ] 전략 우선순위 설정
- [ ] 시장 조건별 전략 전환
- [ ] 전략 성과 추적 설정

#### **Step 2.2.3**: 전략 검증 도구
- [ ] 전략 설정 유효성 검증
- [ ] 실시간 전략 테스트
- [ ] 과거 데이터 백테스팅
- [ ] 전략 성과 지표 표시

**예상 산출물**:
- `strategy_configuration_section.py` (완성)
- `strategy_validator.py` (검증 도구)
- `strategy_backtesting_widget.py` (백테스팅 위젯)

---

### **Sub-Task 2.3: 포지션 관리 섹션 구현** (1일)
**목표**: 포지션 관리 및 주문 설정 UI 구현

#### **Step 2.3.1**: 포지션 관리 UI
- [ ] 현재 포지션 목록 표시
- [ ] 포지션별 손익 현황
- [ ] 포지션 크기 조정 기능
- [ ] 강제 청산 기능
- [ ] 포지션 알림 설정

#### **Step 2.3.2**: 주문 관리 UI
- [ ] 주문 방식 설정 (시장가/지정가)
- [ ] 주문 분할 설정 (부분 매수/매도)
- [ ] 주문 타이밍 설정
- [ ] 슬리피지 허용치 설정
- [ ] 주문 실패 재시도 설정

#### **Step 2.3.3**: 자동 매매 설정
- [ ] 자동 매매 활성화/비활성화
- [ ] 운영 시간 설정
- [ ] 긴급 정지 조건
- [ ] 시스템 재시작 설정
- [ ] 네트워크 오류 대응 설정

**예상 산출물**:
- `position_management_section.py` (완성)
- `order_management_widget.py` (주문 관리)
- `auto_trading_controls.py` (자동매매 제어)

---

### **Sub-Task 2.4: 매매 상태 모니터링 구현** (1일)
**목표**: 실시간 매매 상태 모니터링 및 통계 표시

#### **Step 2.4.1**: 실시간 상태 표시
- [ ] 매매 시스템 상태 (활성/비활성/오류)
- [ ] 현재 신호 상태 (매수/매도/대기)
- [ ] 마지막 거래 정보
- [ ] 네트워크 연결 상태
- [ ] API 요청 한도 현황

#### **Step 2.4.2**: 매매 통계 표시
- [ ] 일일/주간/월간 매매 실적
- [ ] 총 손익 및 수익률
- [ ] 매매 횟수 및 성공률
- [ ] 평균 보유 기간
- [ ] 최대 낙폭/상승률

#### **Step 2.4.3**: 알림 및 로그 연동
- [ ] 중요 이벤트 알림 표시
- [ ] 매매 로그 간략 표시
- [ ] 에러 로그 모니터링
- [ ] 시스템 성능 지표
- [ ] 메모리/CPU 사용률

**예상 산출물**:
- `trading_status_monitor.py` (완성)
- `trading_statistics_widget.py` (통계 위젯)
- `trading_alerts_panel.py` (알림 패널)

---

## 🧪 **테스트 계획**

### **Unit Tests**
- [ ] 리스크 파라미터 검증 테스트
- [ ] 전략 설정 유효성 테스트
- [ ] 포지션 관리 로직 테스트
- [ ] MVP 시그널 연결 테스트

### **Integration Tests**
- [ ] Config YAML 연동 테스트
- [ ] StrategyRepository 통합 테스트
- [ ] 백테스팅 시스템 통합 테스트
- [ ] 알림 시스템 통합 테스트

### **Performance Tests**
- [ ] 실시간 데이터 업데이트 성능 테스트
- [ ] 대량 포지션 처리 테스트
- [ ] 메모리 사용량 테스트

---

## 📊 **성공 기준**

### **기능적 요구사항**
- ✅ config.yaml trading 섹션 완전 UI 구현
- ✅ 7규칙 전략과의 완전 연동
- ✅ 실시간 매매 상태 모니터링
- ✅ 리스크 관리 도구 완전 구현

### **기술적 요구사항**
- ✅ MVP 패턴 완전 적용
- ✅ DDD 아키텍처 준수
- ✅ 기존 전략 시스템과 호환성 유지
- ✅ 실시간 업데이트 성능 < 500ms

### **사용성 요구사항**
- ✅ 직관적인 매매 설정 인터페이스
- ✅ 전문가/초보자 모드 지원
- ✅ 설정 유효성 실시간 검증
- ✅ 풍부한 도움말 및 가이드

---

## 🔗 **의존성**

### **Prerequisites**
- Config YAML 시스템 (기존 완성)
- StrategyRepository (기존 완성)
- 7규칙 전략 시스템 (기존 완성)
- Infrastructure Layer v4.0 (기존 완성)

### **Parallel Tasks**
- TASK-20250809-01: 환경&로깅 탭 (독립적)
- TASK-20250809-03: UI설정 탭 정리 (독립적)

### **Dependent Tasks**
- 없음 (독립적으로 수행 가능)

---

## 🚀 **완료 후 기대효과**

1. **매매 설정 통합 관리**: 모든 매매 관련 설정을 한 곳에서 관리
2. **리스크 관리 강화**: 체계적인 리스크 관리 도구 제공
3. **전략 운영 효율성**: 전략 설정 및 모니터링 효율성 대폭 향상
4. **사용자 경험 개선**: 직관적이고 전문적인 매매 설정 인터페이스

## 📝 **추가 고려사항**

- **보안**: 매매 설정 암호화 저장 고려
- **감사**: 매매 설정 변경 이력 추적 고려
- **백업**: 매매 설정 백업/복원 기능 고려
- **API**: 외부 시스템 연동 API 고려

# 🚀 업비트 자동매매 시스템 - 프로젝트 명세서

> **중요**: 이 문서는 모든 개발 작업의 기준이 되는 핵심 명세서입니다.  
> Copilot은 항상 이 문서를 참조하여 일관된 개발을 수행해야 합니다.

## 📋 프로젝트 개요

**프로젝트명**: 업비트 자동매매 시스템 (Upbit Auto Trading System)  
**기술스택**: Python 3.8+, PyQt6, SQLite, pandas, ta-lib  
**아키텍처**: 컴포넌트 기반 데스크톱 애플리케이션  
**개발방법론**: 스펙 기반 개발 (Specification-Driven Development)

## 🎯 핵심 비즈니스 로직

### 1. 종목 스크리닝 시스템
- **목적**: 거래량 추세와 변동성 기반 코인 필터링
- **기준**: 24시간 거래대금, 7일 변동성, 가격 추세
- **결과**: 수익성 있는 거래 기회 식별

### 2. 매매 전략 관리 (V1.0.1)
#### 🔄 전략 역할 분리 구조
- **진입 전략**: 포지션 없을 때 최초 진입 신호 (`BUY`, `SELL`, `HOLD`)
- **관리 전략**: 활성 포지션의 리스크 관리 (`ADD_BUY`, `CLOSE_POSITION`, `UPDATE_STOP`)
- **조합 시스템**: 1개 진입 전략(필수) + 0~N개 관리 전략(선택)

#### 📈 지원 진입 전략 (6종)
1. **이동평균 교차**: 단기/장기 이평선 크로스오버
2. **RSI**: 과매도/과매수 구간 진입
3. **볼린저 밴드**: 밴드 터치 반전/돌파
4. **변동성 돌파**: 전일 변동폭 기반 돌파
5. **MACD**: 시그널 교차 및 다이버전스
6. **스토캐스틱**: %K, %D 교차 신호

#### 🛡️ 지원 관리 전략 (6종)
1. **물타기**: 하락 시 추가 매수 (최대 5회)
2. **불타기**: 상승 시 피라미드 추가 매수 (최대 3회)
3. **트레일링 스탑**: 수익률 추적 손절
4. **고정 익절/손절**: 목표 수익률 도달 시 청산
5. **부분 청산**: 단계별 수익 실현
6. **시간 기반 청산**: 최대 보유 시간 제한

### 3. 백테스팅 엔진
- **상태 기반 실행**: 진입 대기 ↔ 포지션 관리 상태 전환
- **성능 지표**: 수익률, 최대손실폭, 승률, 샤프비율
- **검증 기준**: 1년치 분봉 데이터 5분 내 처리

### 4. 실시간 거래 시스템
- **모니터링**: 1초 이내 시장 데이터 갱신
- **주문 실행**: 업비트 API 연동, 원자적 거래 처리
- **리스크 관리**: 최대 포지션 크기, 드로우다운 제한

## 🏗️ 아키텍처 원칙

### 계층 구조
```
📱 UI Layer (PyQt6)
├── 대시보드 (포트폴리오 요약, 활성 거래)
├── 차트 뷰 (캔들스틱, 기술적 지표)
├── 전략 관리 (3탭: 진입/관리/조합)
└── 설정 화면 (API 키, 알림, 백업)

🧠 Business Logic Layer
├── 스크리너 (거래량/변동성/추세 필터링)
├── 전략 엔진 (진입/관리 전략 실행)
├── 백테스터 (상태 기반 성능 검증)
├── 거래 엔진 (실시간 주문 실행)
└── 포트폴리오 관리 (다중 전략 조합)

💾 Data Layer
├── 데이터 수집기 (업비트 API 연동)
├── 데이터 처리기 (지표 계산, 정규화)
└── 데이터 저장소 (SQLite, 자동 정리)
```

### 컴포넌트 설계 원칙
1. **단일 책임**: 각 컴포넌트는 하나의 명확한 역할
2. **의존성 역전**: 인터페이스 기반 느슨한 결합
3. **상태 관리**: 진입/관리 전략의 명확한 상태 분리
4. **확장성**: 플러그인 방식 전략 추가 지원

## 🔧 기술적 제약사항

### 성능 요구사항
- **백테스팅**: 1년치 분봉(525,600개) 5분 내 완료
- **실시간 처리**: 시장 데이터 1초 내 갱신
- **UI 반응성**: 사용자 입력 0.5초 내 응답
- **동시성**: 최소 10개 백테스팅 작업 지원

### 보안 요구사항
- **API 키 보호**: AES-256 암호화 저장
- **통신 보안**: HTTPS/SSL 강제 사용
- **로깅 보안**: 민감 정보 평문 저장 금지
- **권한 분리**: 조회/거래 API 키 분리 지원

### 사용성 요구사항
- **직관성**: 초보자 80% 기능 무도움 사용
- **오류 처리**: 명확한 한국어 오류 메시지
- **접근성**: 최소 1280x720 해상도 지원
- **테마**: 다크/라이트 모드 지원 (선택)

## 📊 데이터 모델 핵심

### 전략 역할 분리 스키마
```sql
-- 전략 기본 테이블 (역할 분리)
trading_strategies (
    strategy_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    strategy_role TEXT CHECK (strategy_role IN ('entry', 'management')),
    parameters TEXT, -- JSON 파라미터
    created_at TIMESTAMP
)

-- 전략 조합 테이블
strategy_combinations (
    combination_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    entry_strategy_id TEXT NOT NULL, -- 필수 1개
    execution_order TEXT DEFAULT 'parallel',
    conflict_resolution TEXT DEFAULT 'priority',
    risk_limit TEXT -- JSON 리스크 설정
)

-- 조합의 관리 전략들
combination_management_strategies (
    combination_id TEXT,
    management_strategy_id TEXT,
    priority INTEGER,
    parameters TEXT -- 개별 파라미터 오버라이드
)
```

### 백테스팅 상태 관리
```python
class BacktestState(Enum):
    WAITING_ENTRY = "waiting_entry"    # 진입 대기 (진입 전략만 활성)
    POSITION_MANAGEMENT = "position_management"  # 포지션 관리 (관리 전략들 활성)

class PositionState:
    entry_price: float
    current_price: float
    quantity: float
    side: str  # 'long' or 'short'
    entry_time: datetime
    management_history: List[Dict]  # 관리 전략 실행 이력
```

## 🎨 UI/UX 설계 원칙

### 3탭 구조 (전략 관리)
1. **📈 진입 전략 탭**: 6개 진입 전략 관리
2. **🛡️ 관리 전략 탭**: 6개 관리 전략 관리  
3. **🔗 전략 조합 탭**: 진입+관리 조합 생성

### 스타일 시스템
- **컬러 팔레트**: 
  - 주요: #1E88E5 (파란색)
  - 성공: #4CAF50 (녹색)
  - 경고: #FF9800 (주황색)
  - 위험: #F44336 (빨간색)
  - 배경: #FAFAFA (연회색)

### 컴포넌트 라이브러리
```python
# 항상 공통 컴포넌트 사용
from upbit_auto_trading.ui.desktop.common.components import (
    PrimaryButton,      # 주요 동작
    SecondaryButton,    # 보조 동작
    DangerButton,       # 위험 동작
    StyledLineEdit,     # 입력 필드
    StyledComboBox,     # 드롭다운
    StyledDialog        # 다이얼로그
)
```

## 🧪 테스트 전략

### 단위 테스트 우선순위
1. **전략 엔진**: 각 진입/관리 전략 신호 생성 로직
2. **백테스터**: 상태 전환 및 성과 계산 정확성
3. **데이터 처리**: 기술적 지표 계산 검증
4. **거래 엔진**: 주문 실행 및 오류 처리

### 통합 테스트 시나리오
1. **전체 워크플로**: 스크리닝 → 전략 설정 → 백테스팅 → 거래
2. **전략 조합**: 진입→관리→청산 전체 상태 전환
3. **충돌 해결**: 다중 관리 전략 동시 신호 처리
4. **오류 복구**: 네트워크 장애, API 오류 상황

## 🔄 개발 워크플로

### 스펙 기반 개발 원칙
1. **요구사항 우선**: 모든 기능은 명세서 기반 개발
2. **일관성 유지**: 기존 컴포넌트 재사용 우선
3. **단계적 구현**: 진입 전략 → 관리 전략 → 조합 순서
4. **지속적 검증**: 각 단계마다 백테스팅 검증

### 코드 품질 기준
- **타입 힌트**: 모든 함수 파라미터/반환값
- **한국어 주석**: 비즈니스 로직 설명
- **예외 처리**: 모든 외부 API 호출
- **로깅**: 디버깅을 위한 상세 로그

## 📚 참조 문서 계층

```
.vscode/
├── copilot-instructions.md     # 🎯 메인 지침 (이 문서 참조)
├── project-specs.md           # 📋 프로젝트 명세 (현재 문서)
├── architecture/
│   ├── component-design.md    # 🏗️ 컴포넌트 설계
│   └── data-models.md        # 💾 데이터 모델 상세
├── strategy/
│   ├── entry-strategies.md    # 📈 진입 전략 명세
│   ├── management-strategies.md # 🛡️ 관리 전략 명세
│   └── combination-rules.md   # 🔗 조합 규칙
├── ui/
│   ├── design-system.md      # 🎨 디자인 시스템
│   └── component-library.md  # 📦 컴포넌트 라이브러리
└── testing/
    ├── test-strategy.md      # 🧪 테스트 전략
    └── validation-rules.md   # ✅ 검증 규칙
```

---

## ⚡ 빠른 참조

### 현재 개발 우선순위
1. **전략 역할 분리**: 진입/관리 전략 클래스 재설계
2. **3탭 UI 구현**: 전략 관리 인터페이스 분리
3. **상태 기반 백테스터**: 포지션 상태 추적 엔진
4. **충돌 해결 시스템**: 다중 관리 전략 조율

### 개발 시 필수 확인사항
- [ ] 기존 공통 컴포넌트 재사용 여부
- [ ] 전략 역할(진입/관리) 명확히 구분
- [ ] 상태 전환 로직 정확성
- [ ] 한국어 주석 및 사용자 친화적 메시지
- [ ] 예외 처리 및 로깅 포함

이 명세서는 **프로젝트의 북극성**입니다. 모든 개발 결정은 이 문서를 기준으로 판단해야 합니다.

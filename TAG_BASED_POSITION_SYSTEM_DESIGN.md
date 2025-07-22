"""
태그 기반 포지션 관리 시스템 핵심 설계
Tag-Based Position Management System Core Design

=== 문제 해결 방식 ===

사용자가 지적한 핵심 문제들:
1. 전략 기반 vs 포지션 기반 관리 딜레마
2. 수동 개입 시 평단가 재계산 복잡성
3. 하나의 코인에 여러 개별 포지션 (다른 자본 규모)

해결책: 포지션 태그 시스템
- 각 포지션을 태그로 구분하여 완전 독립적으로 관리
- 자동매매와 수동매매의 엄격한 분리
- 복잡한 평단가 재계산 로직 불필요

=== 태그 시스템 구조 ===

1. PositionTag (Enum)
   - AUTO: 완전 자동매매 포지션
   - MANUAL: 수동 매매 포지션
   - HYBRID: 제한적 자동화 허용
   - LOCKED: 모든 거래 금지

2. TaggedPosition (Class)
   - 태그별로 독립된 포지션 관리
   - 각각 고유한 진입가, 평단가, 수량 보유
   - 태그에 따른 매매 권한 제어

3. PositionManager (Class)
   - 심볼별 + 태그별 다중 포지션 관리
   - 전략ID와 포지션 연결 관리
   - 안전한 매매 권한 검증

=== 실제 사용 시나리오 ===

시나리오 1: 비트코인 분산 투자
- KRW-BTC + AUTO: 물타기 전략으로 100만원 자동 투자
- KRW-BTC + MANUAL: 직감으로 50만원 수동 투자
- 두 포지션은 완전 독립적으로 관리됨

시나리오 2: 수동 개입 방지
- AUTO 포지션: 사용자가 절대 건드릴 수 없음
- MANUAL 포지션: 전략이 절대 건드릴 수 없음
- 실수로 간섭할 가능성 완전 차단

시나리오 3: 다중 전략 운용
- 같은 코인에 여러 전략 동시 운용 가능
- 각 전략마다 독립적인 AUTO 포지션
- 전략간 간섭 없이 안전한 운용

=== UI/UX 설계 ===

1. 포지션 목록 화면
```
[KRW-BTC]
├── 🤖 AUTO (물타기전략): 0.01 BTC @ 48,000,000원 (수동매매 🚫)
├── 👤 MANUAL (직감매수): 0.005 BTC @ 50,000,000원 (자동매매 🚫)
└── 🔒 LOCKED (홀딩): 0.002 BTC @ 45,000,000원 (거래금지)

[KRW-ETH]  
└── 🤖 AUTO (RSI전략): 2.5 ETH @ 3,200,000원
```

2. 전략 설정 화면
- 전략 생성 시 태그 선택 필수
- AUTO 태그 선택 시 "수동 개입 불가" 경고
- 포지션별 독립적인 리스크 설정

3. 거래 화면
- 각 포지션별 독립적인 매수/매도 버튼
- 권한 없는 버튼은 비활성화
- 명확한 태그 표시로 혼동 방지

=== 기술적 구현 ===

1. 데이터베이스 스키마
```sql
CREATE TABLE tagged_positions (
    id PRIMARY KEY,
    symbol VARCHAR(20),
    tag ENUM('AUTO', 'MANUAL', 'HYBRID', 'LOCKED'),
    strategy_id VARCHAR(50),
    created_at TIMESTAMP,
    UNIQUE(symbol, tag, strategy_id)
);

CREATE TABLE position_entries (
    id PRIMARY KEY,
    position_id FOREIGN KEY,
    timestamp TIMESTAMP,
    quantity DECIMAL(20, 8),
    price DECIMAL(20, 2),
    notes TEXT
);
```

2. 컴포넌트 시스템 연결
- ExecutionContext가 특정 태그의 포지션만 참조
- TriggerComponent가 태그별 데이터 필터링
- ActionComponent가 매매 권한 검증

3. 전략 엔진 통합
- 각 전략이 고유한 strategy_id 보유
- AUTO 태그 포지션만 제어 가능
- 크로스 전략 간섭 완전 차단

=== 장점 및 효과 ===

1. 안전성
   - 자동매매와 수동매매 완전 분리
   - 실수로 인한 포지션 손상 방지
   - 명확한 책임 분리

2. 유연성
   - 동일 코인에 다중 전략 적용 가능
   - 각 포지션별 독립적인 관리
   - 사용자의 다양한 투자 스타일 지원

3. 단순성
   - 복잡한 평단가 재계산 로직 불필요
   - 직관적이고 명확한 UX
   - 개발 복잡도 대폭 감소

4. 확장성
   - 새로운 태그 타입 쉽게 추가 가능
   - 포지션별 독립적인 기능 확장
   - 미래 요구사항 유연하게 대응

=== 다음 단계 ===

1. 즉시 구현 필요
   - 기존 ExecutionContext를 태그 시스템으로 완전 전환
   - UI에서 태그별 포지션 분리 표시
   - 매매 권한 검증 로직 구현

2. 단계적 적용
   - 기존 포지션을 MANUAL 태그로 마이그레이션
   - 새로운 전략을 AUTO 태그로 생성
   - 사용자에게 태그 개념 교육

3. 고도화
   - HYBRID 태그의 세밀한 권한 제어
   - 포지션간 이동/병합 기능
   - 태그별 성과 분석 및 리포팅

이 설계로 사용자가 제기한 모든 문제가 근본적으로 해결됩니다!
"""

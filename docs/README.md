# UI 프로토타입 모음

이 디렉토리는 전략 UI 개발을 위한 다양한 프로토타입들을 모아둔 곳입니다.

## 📋 프로토타입 목록

### 1. comprehensive_strategy_engine.py
**기능**: GUI 없는 실전 백테스팅 엔진
- 7가지 핵심 전략 조합 
- 실제 백테스팅 실행
- 결과 리포트 생성
- **용도**: 백테스팅 로직 검증

### 2. drag_drop_vs_button_comparison.py
**기능**: 드래그앤드롭 vs 버튼 방식 UX 비교
- 두 가지 UI 방식 직접 비교
- 사용성 통계 측정
- **용도**: 최적 UI 방식 결정

### 3. enhanced_strategy_builder.py  
**기능**: 강화된 전략 빌더
- 트리거 레지스트리 시스템
- 상세한 파라미터 설정
- 도움말 시스템
- **용도**: 복잡한 전략 구성 UI

### 4. hybrid_strategy_builder.py
**기능**: 하이브리드 전략 빌더 (빈 파일)
- **용도**: 추후 개발 예정

### 5. improved_strategy_manager.py
**기능**: 개선된 전략 관리 시스템
- SQLite 데이터베이스 저장
- 전략 목록 관리
- 액션 타입 설명 시스템
- **용도**: 전략 저장/로드 기능

### 6. rule_based_strategy_maker.py
**기능**: 규칙 기반 전략 메이커
- 7개 핵심 규칙 템플릿
- 직관적인 규칙 선택
- JSON 미리보기
- **용도**: 템플릿 기반 전략 구성

### 7. strategy_maker_ui.py
**기능**: 하이브리드 전략 메이커 UI
- 컴포넌트 팔레트
- 드래그앤드롭 캔버스
- **용도**: 컴포넌트 기반 전략 구성

### 8. table_strategy_builder.py
**기능**: 테이블 기반 전략 빌더
- 행 단위로 규칙 추가
- 트리거-액션 매핑
- **용도**: 스프레드시트 스타일 전략 구성

### 9. unified_strategy_maker.py
**기능**: 통합 전략 메이커
- 템플릿 + 컴포넌트 하이브리드
- 탭 기반 모드 선택
- **용도**: 두 방식의 장점 결합

### 10. unified_strategy_system_v2.py
**기능**: 통합 전략 관리 시스템 V2
- 다중 트리거 지원
- 검증 시스템
- DB 저장 기능
- **용도**: 완전한 통합 시스템

## 🎯 프로토타입 테스트 방법

```bash
# 프로토타입 실행 (각각 독립 실행 가능)
cd ui_prototypes
python drag_drop_vs_button_comparison.py
python enhanced_strategy_builder.py  
python rule_based_strategy_maker.py
# ... 등등
```

## 🤔 선택 기준

각 프로토타입의 특징:

1. **간단함**: `rule_based_strategy_maker.py` - 7개 템플릿 선택
2. **유연성**: `enhanced_strategy_builder.py` - 세밀한 설정
3. **직관성**: `table_strategy_builder.py` - 스프레드시트 스타일
4. **통합성**: `unified_strategy_system_v2.py` - 모든 기능 통합

## 🚀 다음 단계

1. 각 프로토타입 실행해보기
2. UX 비교 분석
3. 최적 방식 선택
4. 실제 시스템에 적용

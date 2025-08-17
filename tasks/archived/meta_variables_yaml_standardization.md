# 🎯 메타변수 YAML 표준화 작업

## 📋 작업 개요
**목적**: 메타변수 YAML 파일들을 SMA 표준 형식에 맞춰 수정하여 UI에서 정상 표시되도록 함
**영향도**: 높음 (트리거 빌더 핵심 기능)
**접근법**: 보수적 단계별 수정

## 🔍 문제 분석

### 현재 문제점
- [ ] 메타변수가 UI에서 표시되지 않음
- [ ] parameters.yaml이 SMA 표준 형식과 다름 (리스트 → 객체 구조)
- [ ] tracked_variable enum이 기본 변수 추적 원칙과 상충
- [ ] help_texts.yaml과 placeholders.yaml이 구 형식 사용

### 📖 사용자 요구사항 (재확인)
1. **메타변수 특징**: 기본 변수를 기본적으로 추적 (별도 BaseVariable enum 불필요)
2. **4가지 계산 방식**:
   - `평단값 퍼센트포인트 (%p)` - 평단가 기준
   - `진입값 퍼센트포인트 (%p)` - 진입가 기준
   - `정적차이` - 원화/수치 절대값
   - `극값 비율퍼센트 (%)` - 최고/최저점 대비
3. **추적 방향**: UP (상향), DOWN (하향)
4. **피라미딩 전용**: 횟수 파라미터 추가
5. **타임프레임**: 기본 변수를 따름 (별도 설정 불필요)

## 🎯 작업 범위

### A. trailing_stop 메타변수 (5개 파일)
- [ ] definition.yaml - 기본 정의 (동적 관리 카테고리 유지)
- [ ] parameters.yaml - SMA 형식으로 완전 재작성
- [ ] help_guide.yaml - 트레일링 스탑 전용 상세 가이드 작성
- [ ] help_texts.yaml - 새 파라미터에 맞는 툴팁 작성
- [ ] placeholders.yaml - 새 파라미터에 맞는 예시 작성

### B. pyramid_target 메타변수 (5개 파일)
- [ ] definition.yaml - 기본 정의 (동적 관리 카테고리 유지)
- [ ] parameters.yaml - SMA 형식으로 완전 재작성 (횟수 파라미터 포함)
- [ ] help_guide.yaml - 피라미딩 전용 상세 가이드 작성
- [ ] help_texts.yaml - 새 파라미터에 맞는 툴팁 작성
- [ ] placeholders.yaml - 새 파라미터에 맞는 예시 작성

## 📊 새로운 파라미터 설계

### trailing_stop 파라미터
```yaml
parameters:
  calculation_method:    # enum: 4가지 계산 방식
  value:                # decimal: 계산값 (%, 원화 등)
  trail_direction:      # enum: up/down
  # timeframe 제거 (기본 변수 따름)
  # tracked_variable 제거 (기본 변수 추적)
```

### pyramid_target 파라미터
```yaml
parameters:
  calculation_method:    # enum: 4가지 계산 방식
  value:                # decimal: 계산값 (%, 원화 등)
  trail_direction:      # enum: up/down
  max_count:           # integer: 최대 횟수 (피라미딩 전용)
  # timeframe 제거 (기본 변수 따름)
  # tracked_variable 제거 (기본 변수 추적)
```

## 🔄 작업 순서

### Phase 1: trailing_stop 수정
1. [x] parameters.yaml 완전 재작성
2. [x] help_texts.yaml 새 파라미터에 맞게 수정
3. [x] placeholders.yaml 새 파라미터에 맞게 수정
4. [x] help_guide.yaml 트레일링 스탑 전용 내용 작성
5. [x] definition.yaml 검토 및 필요시 수정

### Phase 2: pyramid_target 수정
1. [x] parameters.yaml 완전 재작성 (횟수 파라미터 포함)
2. [x] help_texts.yaml 새 파라미터에 맞게 수정
3. [x] placeholders.yaml 새 파라미터에 맞게 수정
4. [x] help_guide.yaml 피라미딩 전용 내용 작성
5. [x] definition.yaml 검토 및 필요시 수정

### Phase 3: DB 업데이트
1. [x] 기존 메타변수 파라미터 완전 삭제
2. [x] merge_trading_variables_to_db.py로 새 파라미터 삽입
3. [x] DB 상태 검증

### Phase 4: 최종 검증
1. [ ] UI에서 메타변수 범주 표시 확인
2. [ ] 파라미터 정상 작동 확인
3. [ ] 헬프 가이드 정상 표시 확인

## ⚠️ 주의사항

### 절대 피해야 할 것
- parameters.yaml에서 tracked_variable enum 설정 (기본 변수 추적 원칙 위배)
- timeframe 파라미터 추가 (기본 변수 따름 원칙 위배)
- SMA 형식 벗어나는 구조 사용

### 반드시 지켜야 할 것
- dynamic_management 카테고리 유지
- SMA와 동일한 parameters 객체 구조 사용
- 4가지 계산 방식만 enum으로 제공
- 트레일링/피라미딩 고유 특성 반영

## 📝 검토 포인트

### 기술적 검토
- [ ] YAML 문법 오류 없음
- [ ] SMA 구조와 일치
- [ ] enum 값들이 적절함
- [ ] 기본값이 합리적임

### 기능적 검토
- [ ] 메타변수 특성이 올바르게 반영됨
- [ ] 사용자 요구사항과 일치
- [ ] 실제 트레이딩 시나리오에 적합
- [ ] 도메인 가이드와 일치

### UI/UX 검토
- [ ] 파라미터명이 직관적임
- [ ] 도움말이 이해하기 쉬움
- [ ] 예시가 실용적임
- [ ] 경고 메시지가 적절함

## 🎯 성공 기준
- [ ] UI에서 메타변수가 정상 표시됨
- [ ] 모든 파라미터가 올바르게 작동함
- [ ] 헬프 가이드가 정상 표시됨
- [ ] DB 테이블에 파라미터가 정상 삽입됨

---

**다음 단계**: 사용자 검토 및 승인 후 Phase 1부터 차근차근 진행

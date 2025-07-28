# 📊 TASK-20250728-03_Database_Location_Optimization

## 🎯 태스크 개요
**태스크명**: 데이터베이스 위치 최적화 및 설치형 환경 준비  
**생성일**: 2025.07.28  
**우선순위**: 🟡 중간 (설치형 배포 준비)  
**예상 소요시간**: 1-2시간  
**의존성**: TASK-20250728-01 (데이터베이스 구조 통합) 완료 후

## 📋 발견된 문제

### 🚨 데이터베이스 위치 불일치
database structure unification 과정에서 발견된 구조적 문제:

1. **API 키 위치**: `upbit_auto_trading\data\settings\` (올바름)
2. **DB 파일 위치**: 루트 `data\` (설치형 환경에서 부적절)
3. **중복/잔여 파일**: `upbit_auto_trading\ui\desktop\data\trading_conditions.db` (빈 파일)

### 🎯 설치형 프로그램 관점의 문제점
- 사용자 데이터가 두 곳에 분산: 루트 `data\`와 `upbit_auto_trading\data\`
- 설치형 환경에서는 모든 사용자 데이터가 한 곳에 있어야 함
- API 키와 DB 파일이 분리되어 관리 복잡성 증가

## 🎯 목표 구조

### 📂 올바른 사용자 데이터 구조
```
upbit_auto_trading/
├── data/                    ← 모든 사용자 데이터 통합 위치
│   ├── settings/           ← API 키, 암호화 키 (기존 유지)
│   │   ├── api_keys.json
│   │   └── encryption_key.key
│   ├── settings.sqlite3    ← 이동 필요 (from 루트 data/)
│   ├── strategies.sqlite3  ← 이동 필요 (from 루트 data/)
│   └── market_data.sqlite3 ← 이동 필요 (from 루트 data/)
```

### 🚀 예상 효과
- **통합성**: 모든 사용자 데이터가 한 위치에 집중
- **설치 용이성**: 패키징 시 단일 데이터 폴더만 관리
- **백업 편의성**: 하나의 폴더만 백업하면 모든 데이터 보존
- **이식성**: 전체 data 폴더 복사로 환경 이전 가능

## 🚀 작업 단계별 계획

### 📋 Phase 1: 사전 준비 및 백업
- [ ] 1.1. 현재 database_paths.py 설정 백업
- [ ] 1.2. 현재 DB 파일들 백업 생성
- [ ] 1.3. 이동 전 데이터 무결성 검증

### 📋 Phase 2: 파일 이동
- [ ] 2.1. settings.sqlite3 이동: `data/` → `upbit_auto_trading/data/`
- [ ] 2.2. strategies.sqlite3 이동: `data/` → `upbit_auto_trading/data/`
- [ ] 2.3. market_data.sqlite3 이동: `data/` → `upbit_auto_trading/data/`
- [ ] 2.4. 이동 후 파일 무결성 검증

### 📋 Phase 3: 경로 시스템 업데이트
- [ ] 3.1. database_paths.py 경로 상수 업데이트
- [ ] 3.2. 모든 하드코딩된 경로 검토 및 업데이트
- [ ] 3.3. 상대경로 기반 시스템으로 전환 검토

### 📋 Phase 4: 잔여 파일 정리
- [ ] 4.1. upbit_auto_trading/ui/desktop/data/trading_conditions.db 제거
- [ ] 4.2. 빈 data/ 폴더 처리 결정
- [ ] 4.3. 기타 중복/잔여 파일 정리

### 📋 Phase 5: 검증 및 테스트
- [ ] 5.1. 모든 데이터베이스 연결 테스트
- [ ] 5.2. API 키 접근 테스트
- [ ] 5.3. 주요 기능 동작 확인
- [ ] 5.4. 경로 변경 영향도 검증

### 📋 Phase 6: 문서화
- [ ] 6.1. 새로운 데이터 구조 문서화
- [ ] 6.2. 설치형 배포 가이드 업데이트
- [ ] 6.3. 백업/복원 절차 문서화

## ⚠️ 주의사항 및 리스크

### 🚨 높은 리스크
- **API 키 접근 실패**: 경로 변경 시 암호화 키 경로 오류 가능성
- **데이터 손실**: 파일 이동 중 데이터 손실 위험
- **서비스 중단**: 이동 과정에서 일시적 기능 중단

### 🛡️ 완화 방안
- **단계별 백업**: 각 단계마다 데이터 백업 생성
- **점진적 이동**: 한 번에 모든 파일을 이동하지 않고 단계별 진행
- **롤백 계획**: 문제 발생 시 즉시 복구 가능한 절차 수립
- **테스트 우선**: 각 단계마다 기능 테스트 수행

## 📝 후속 작업

### 🔗 관련 태스크들
1. **TASK-20250728-02**: Trading Variables Schema Compatibility (이 작업 후 진행)
2. **패키징 최적화**: 설치형 프로그램 배포 준비
3. **경로 관리 시스템**: 상대경로 기반 시스템 구축

## 🎯 성공 기준

### ✅ 필수 목표
- 모든 사용자 데이터가 `upbit_auto_trading/data/`에 통합
- 기존 기능 모두 정상 동작
- API 키 접근 및 암호화/복호화 정상 동작

### 🚀 추가 목표
- 설치형 배포 시 단일 폴더 관리 가능
- 데이터 백업/복원 프로세스 단순화
- 개발/프로덕션 환경 간 일관성 확보

---

**생성일**: 2025.07.28  
**관련 태스크**: TASK-20250728-01_Database_Structure_Unification  
**담당자**: GitHub Copilot  
**상태**: 계획됨 (TASK-20250728-01 완료 후 진행)

# 🚨 CRITICAL TASK: 시뮬레이션 아키텍처 마이그레이션 완료

## ⚠️ 위험도: HIGH - 매우 신중하게 작업 필요

### 📍 현재 상황 (2025-07-29)
- **폴더 구조 설계는 완료**되었으나 **실제 파일 이동/통합 작업은 미완료**
- **Junction 링크 제거** 작업 중 구조가 복잡해짐
- **GitHub 푸시 완료**된 상태이므로 롤백 시 주의 필요
- **다음 에이전트는 매우 보수적으로 접근** 필요

### 🎯 목표
Junction 링크 없이 GitHub Clone만으로 즉시 실행 가능한 구조 완성

### 📊 현재 아키텍처 상태

#### ✅ 완료된 작업
1. **shared_simulation/ 폴더 구조 생성 완료**
   - `upbit_auto_trading/ui/desktop/screens/strategy_management/shared_simulation/`
   - 하위 디렉토리: `engines/`, `data_sources/`, `charts/`

2. **핵심 파일들 생성 완료**
   - `simulation_engines.py` - 통합 시뮬레이션 엔진 (실제 샘플 DB 연동 완료)
   - `market_data_manager.py` - 데이터 로더
   - `simulation_panel.py` - UI 컴포넌트

3. **샘플 DB 연동 완료**
   - 실제 2,862개 비트코인 데이터 사용 확인
   - 가격대: 161백만원 (실제 데이터)

#### ❌ 미완료 작업 (위험 요소)
1. **기존 Junction 링크 파일들이 여전히 존재**
2. **중복된 코드 정리 필요**
3. **import 경로 통합 미완료**
4. **전체 시스템 검증 필요**

### 🔍 상황 파악 참고 문서

#### 필수 읽기 문서
1. `docs/CLEAR_PROJECT_STRUCTURE_GUIDE.md` - 새로운 구조 설명
2. `docs/DB_MIGRATION_USAGE_GUIDE.md` - DB 관련 정보
3. `docs/STRATEGY_ARCHITECTURE_OVERVIEW.md` - 전체 아키텍처
4. `logs/agent_log_2025-07.md` - 현재까지 작업 로그

#### 핵심 참고 파일
1. `test_new_structure.py` - 시스템 검증 스크립트
2. `verify_real_data.py` - 실제 데이터 사용 확인
3. `debug_sample_db.py` - DB 연결 확인

### 📋 다음 에이전트 작업 지침

#### 🛡️ 안전 수칙 (필수)
1. **백업 먼저**: 작업 전 반드시 `git commit` 으로 현재 상태 백업
2. **점진적 접근**: 한 번에 하나씩만 변경
3. **검증 우선**: 매 단계마다 `python test_new_structure.py` 실행
4. **롤백 준비**: 문제 발생 시 즉시 이전 커밋으로 복구

#### 📝 권장 작업 순서

##### Phase 1: 현재 상태 파악 (1시간)
```bash
# 1. 현재 상태 확인
python test_new_structure.py
python verify_real_data.py

# 2. Junction 링크 현황 파악
find . -type l  # Linux/WSL에서
dir /al        # Windows PowerShell에서

# 3. 중복 파일 확인
find . -name "simulation_engines.py" -type f
find . -name "market_data_manager.py" -type f
```

##### Phase 2: 안전한 정리 작업 (2-3시간)
1. **중복 파일 제거**
   - 기존 Junction 링크 파일들을 하나씩 확인 후 제거
   - 각 제거 후 테스트 실행

2. **import 경로 수정**
   - shared_simulation을 사용하도록 import 문 업데이트
   - 한 파일씩 수정 후 테스트

3. **데이터 검증**
   - 실제 샘플 DB 연동 유지 확인
   - 161백만원대 가격 데이터 로드 확인

##### Phase 3: 최종 검증 (1시간)
```bash
# 전체 시스템 테스트
python test_new_structure.py
python verify_real_data.py

# 새로운 환경에서 테스트
cd /tmp
git clone https://github.com/invisible0000/upbit-autotrader-vscode.git
cd upbit-autotrader-vscode
pip install -r requirements.txt
python quick_start.py
```

### 🚨 위험 신호 감지 시 조치
다음 증상 발견 시 **즉시 작업 중단**하고 이전 커밋으로 롤백:

1. `python test_new_structure.py` 실행 실패
2. 실제 샘플 DB 데이터 로드 실패 (5천만원대 가격으로 돌아감)
3. Import 오류 대량 발생
4. 기존 기능 동작 불가

### 📞 에이전트 간 인수인계 정보

#### 현재 DB 연동 상태
- ✅ 샘플 DB 경로: `upbit_auto_trading/ui/desktop/screens/strategy_management/trigger_builder/engines/data/sampled_market_data.sqlite3`
- ✅ 데이터 개수: 2,862개 레코드
- ✅ 가격대: 161백만원 (실제 비트코인 데이터)
- ✅ 최신 데이터: 2025-07-23

#### 핵심 아키텍처 파일
```
shared_simulation/
├── engines/
│   └── simulation_engines.py  ✅ 완성 (실제 DB 연동)
├── data_sources/
│   └── market_data_manager.py  ✅ 완성
└── charts/
    └── simulation_panel.py     ✅ 완성
```

#### Git 상태
- 마지막 커밋: "✅ 시뮬레이션 시스템 완성: 실제 샘플 DB 데이터 통합"
- 브랜치: master
- 푸시 완료: origin/master

### 🎯 성공 기준
1. `python test_new_structure.py` → 모든 시나리오 ✅
2. `python verify_real_data.py` → 161백만원대 가격 확인
3. GitHub Clone → requirements 설치 → 즉시 실행 가능
4. Junction 링크 완전 제거
5. 코드 중복 최소화

### 💡 중요 참고사항
- **사용자는 "폴더만 짜놓고 아무것도 옮기지 않았다"고 명시**
- **구조가 두 번 꼬였다고 경고**
- **매우 보수적이고 안정적으로 접근 필요**
- **실제 작업은 파일 이동/통합이 핵심**

---
**작성일**: 2025-07-29  
**작성자**: AI Agent Session  
**우선순위**: CRITICAL  
**예상 소요시간**: 4-6시간  
**위험도**: HIGH

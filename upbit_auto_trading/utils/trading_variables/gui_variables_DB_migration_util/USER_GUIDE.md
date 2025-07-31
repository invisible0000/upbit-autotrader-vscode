# 🎯 Trading Variables DB Migration Tool - 사용자 가이드

**버전**: 1.1.0 (Phase 3 완료)  
**작성일**: 2025-07-31  
**최종 업데이트**: 2025-07-31

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [설치 및 실행](#설치-및-실행)
3. [GUI 사용법](#gui-사용법)
4. [주요 기능](#주요-기능)
5. [성능 최적화](#성능-최적화)
6. [문제 해결](#문제-해결)
7. [개발자 정보](#개발자-정보)

---

## 🎯 시스템 개요

### 목적
Trading Variables Database Migration Tool은 매매 변수 관리를 위한 GUI 도구입니다. YAML 형태의 데이터를 SQLite 데이터베이스로 마이그레이션하고, Python 코드를 자동 생성합니다.

### 주요 특징
- **5개 통합 탭**: 체계적인 워크플로우 제공
- **실시간 미리보기**: 변경사항을 즉시 확인
- **안전한 백업**: 모든 작업에 대한 자동 백업
- **성능 최적화**: DB 연결 풀링 및 캐싱 시스템
- **사용자 친화적**: 직관적인 GUI 인터페이스

---

## 🚀 설치 및 실행

### 시스템 요구사항
- **운영체제**: Windows 10+ (PowerShell 지원)
- **Python**: 3.8 이상
- **필수 패키지**: tkinter, sqlite3 (내장)

### 실행 방법

#### 1. 기본 실행
```powershell
# 프로젝트 디렉토리로 이동
Set-Location "d:\projects\upbit-autotrader-vscode\upbit_auto_trading\utils\trading_variables\gui_variables_DB_migration_util"

# GUI 실행
python run_gui_trading_variables_DB_migration.py
```

#### 2. 빠른 실행 (바로가기)
```powershell
# 한 줄 명령어
Set-Location "d:\projects\upbit-autotrader-vscode\upbit_auto_trading\utils\trading_variables\gui_variables_DB_migration_util"; python run_gui_trading_variables_DB_migration.py
```

---

## 📱 GUI 사용법

### 메인 인터페이스 구조

```
🎯 Trading Variables Database Migration Tool
├── 📁 Tab 1: DB 선택 & 상태
├── 📊 Tab 2: 변수 & 파라미터  
├── 🚀 Tab 3: 마이그레이션
│   ├── 🔍 미리보기
│   ├── ⚡ 실행
│   └── 📊 데이터 마이그레이션
├── 💾 Tab 4: 백업 관리
└── ⚙️ Tab 5: 시스템 정보
    ├── 🤖 에이전트
    ├── 📋 JSON 뷰어
    └── 🔄 코드 동기화
```

### 단계별 사용 가이드

#### Step 1: DB 선택 (Tab 1)
1. **기본 경로 사용**: `🏠 기본 경로 사용` 버튼 클릭
2. **수동 선택**: `📂 DB 파일 선택` 버튼으로 직접 선택
3. **새 DB 생성**: `➕ 새 DB 생성` 버튼으로 새 파일 생성
4. **상태 확인**: DB 정보 및 테이블 목록 확인

#### Step 2: 변수 조회 (Tab 2)
1. **변수 목록**: 현재 DB의 모든 변수 확인
2. **파라미터 관리**: 변수별 파라미터 설정 검토
3. **필터링**: 카테고리별 변수 필터링

#### Step 3: 마이그레이션 (Tab 3)

##### 🔍 미리보기 서브탭
1. **변경사항 검토**: 마이그레이션될 내용 미리보기
2. **스키마 확인**: 새로운 테이블 구조 검토
3. **충돌 해결**: 데이터 충돌 사항 확인

##### ⚡ 실행 서브탭
1. **백업 생성**: 자동 백업 실행
2. **마이그레이션**: 실제 데이터 마이그레이션 실행
3. **결과 확인**: 마이그레이션 결과 및 로그 확인

##### 📊 데이터 마이그레이션 서브탭
1. **YAML → DB**: data_info의 YAML 파일을 DB로 마이그레이션
2. **상태 모니터링**: 실시간 진행 상황 확인
3. **개별 컴포넌트**: 필요시 개별 요소 마이그레이션

#### Step 4: 백업 관리 (Tab 4)
1. **백업 목록**: 자동 생성된 백업 파일 목록
2. **복원 기능**: 이전 상태로 롤백
3. **백업 정리**: 오래된 백업 파일 관리

#### Step 5: 시스템 정보 (Tab 5)

##### 🤖 에이전트 서브탭
- LLM 에이전트 워크플로우 정보
- 시스템 상태 및 성능 정보

##### 📋 JSON 뷰어 서브탭
- 구조화된 데이터 JSON 형태로 조회
- 디버깅 및 데이터 검증

##### 🔄 코드 동기화 서브탭
- DB → Python 코드 자동 생성
- `variable_definitions.py` 파일 업데이트

---

## ⚡ 주요 기능

### 1. 자동 백업 시스템
- **타임스탬프 파일명**: `variable_definitions_new_YYYYMMDD_HHMMSS.py`
- **충돌 방지**: 동일 이름 파일 존재 시 자동으로 타임스탬프 추가
- **안전 보장**: 모든 변경 작업 전 자동 백업

### 2. YAML → DB 마이그레이션
```yaml
# 지원하는 YAML 파일들
data_info/
├── tv_indicator_categories.yaml    # 지표 카테고리
├── tv_parameter_types.yaml        # 파라미터 유형  
├── tv_indicator_library.yaml      # 지표 라이브러리
├── tv_help_texts.yaml            # 도움말 텍스트
└── tv_placeholder_texts.yaml     # 플레이스홀더 텍스트
```

### 3. 자동 코드 생성
- **입력**: SQLite 데이터베이스
- **출력**: Python 변수 정의 파일
- **특징**: 타입 힌트 포함, 구조화된 클래스 생성

### 4. 실시간 미리보기
- 마이그레이션 전 변경사항 미리보기
- 데이터 충돌 및 문제점 사전 확인
- 스키마 변경사항 시각화

---

## 🚀 성능 최적화

### DB 연결 풀링
- **최대 연결 수**: 5개 (설정 가능)
- **자동 정리**: 유휴 연결 자동 해제 (5분)
- **스레드 안전**: 멀티스레딩 환경 지원

### 쿼리 캐싱
- **캐시 크기**: 최대 100개 쿼리 결과
- **TTL**: 5분 (Time To Live)
- **자동 무효화**: 데이터 변경 시 캐시 자동 삭제

### UI 반응성
- **비동기 작업**: 장시간 작업을 백그라운드에서 실행
- **진행률 표시**: 실시간 작업 진행 상황 표시
- **논블로킹**: UI 스레드 차단 방지

---

## 🔧 문제 해결

### 일반적인 문제들

#### 1. GUI가 시작되지 않음
```
문제: ModuleNotFoundError 또는 import 오류
해결: 
1. Python 경로 확인
2. 프로젝트 루트 디렉토리에서 실행
3. 필요한 모듈 설치 확인
```

#### 2. DB 파일을 찾을 수 없음
```
문제: "기본 DB 파일을 찾을 수 없음"
해결:
1. Tab 1에서 "📂 DB 파일 선택" 버튼으로 수동 선택
2. "➕ 새 DB 생성" 버튼으로 새 DB 생성
3. 기본 경로 설정 확인
```

#### 3. 마이그레이션 실패
```
문제: 데이터 마이그레이션 중 오류 발생
해결:
1. 백업 파일에서 복원
2. YAML 파일 형식 확인
3. DB 스키마 호환성 검토
4. 로그 메시지 확인
```

#### 4. 성능 저하
```
문제: GUI 반응 속도 저하
해결:
1. Tab 5 → 시스템 정보에서 성능 통계 확인
2. 불필요한 캐시 정리
3. DB 최적화 실행 (VACUUM, ANALYZE)
```

### 디버깅 정보

#### 로그 위치
- **콘솔 출력**: 실시간 상태 메시지
- **GUI 내 로그**: 각 탭의 로그 섹션
- **성능 로그**: 1초 이상 소요 작업 자동 로깅

#### 시스템 정보 확인
1. Tab 5 → 🤖 에이전트 → 시스템 정보
2. DB 연결 상태, 캐시 통계 확인
3. 파일 존재 여부 및 크기 정보

---

## 🔄 워크플로우 가이드

### 표준 작업 순서

#### 1. 초기 설정 (첫 실행 시)
```
1. GUI 실행
2. Tab 1: DB 선택 (기본 경로 또는 새 DB 생성)
3. Tab 2: 기존 변수 확인
4. Tab 4: 백업 정책 확인
```

#### 2. 데이터 추가/수정
```
1. data_info/ 폴더에서 YAML 파일 편집
2. Tab 3 → 📊 데이터 마이그레이션 → YAML → DB 마이그레이션
3. Tab 3 → 🔍 미리보기 → 변경사항 확인
4. Tab 3 → ⚡ 실행 → 마이그레이션 실행
```

#### 3. 코드 생성
```
1. Tab 5 → 🔄 코드 동기화
2. "🔄 DB → 코드 동기화" 버튼 클릭
3. variable_definitions.py 파일 자동 생성 확인
```

#### 4. 백업 및 복원
```
백업:
- 모든 변경 작업 시 자동 백업

복원:
1. Tab 4 → 백업 목록에서 복원할 파일 선택
2. 복원 버튼 클릭
3. 확인 후 시스템 재시작
```

---

## 👥 개발자 정보

### 아키텍처 개요

#### 모듈 구조
```
components/
├── gui_utils.py           # 공통 GUI 유틸리티
├── performance_utils.py   # 성능 최적화 도구
├── db_selector.py         # DB 선택 컴포넌트
├── variables_viewer.py    # 변수 조회 컴포넌트
├── migration_*.py         # 마이그레이션 컴포넌트들
├── backup_manager.py      # 백업 관리
├── data_info_migrator.py  # YAML → DB 마이그레이션
└── unified_code_generator.py  # 코드 생성
```

#### 설계 원칙
1. **단일 책임 원칙**: 각 모듈이 명확한 역할 담당
2. **표준화**: 모든 GUI 컴포넌트가 tk.Frame 기반
3. **성능 최적화**: 연결 풀링, 캐싱, 비동기 처리
4. **사용자 친화성**: 직관적 인터페이스와 명확한 피드백

### 확장 가이드

#### 새 컴포넌트 추가
```python
from components.gui_utils import StandardFrame

class NewComponentFrame(StandardFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, title="새 컴포넌트", **kwargs)
        self.setup_ui()
    
    def setup_ui(self):
        # UI 구성 코드
        pass
```

#### 성능 최적화 활용
```python
from components.performance_utils import monitor_performance, get_db_manager

@monitor_performance
def database_operation():
    db_manager = get_db_manager("path/to/database.sqlite3")
    return db_manager.execute_query("SELECT * FROM table")
```

---

## 📝 변경 이력

### v1.1.0 (2025-07-31) - Phase 3 완료
- ✅ GUI 프레임워크 표준화
- ✅ 성능 최적화 (DB 풀링, 캐싱)
- ✅ 모듈 구조 정리

### v1.0.0 (2025-07-30) - Phase 1&2 완료  
- ✅ 기본 GUI 구현
- ✅ YAML → DB 마이그레이션
- ✅ 자동 백업 시스템
- ✅ 코드 생성 기능

---

## 📞 지원 및 문의

### 문제 신고
- 콘솔 출력의 에러 메시지 포함
- 재현 단계 상세 기술
- 시스템 환경 정보 (OS, Python 버전)

### 개선 제안
- 새로운 기능 요청
- UI/UX 개선 아이디어
- 성능 최적화 제안

---

**© 2025 Trading Variables DB Migration Team**  
*안정성과 사용편의성을 추구하는 데이터 마이그레이션 도구*

# 🏗️ TASK-20250810-00: UI Desktop 레거시 완전 정리 및 DDD 기반 구조 선행 작업

## 📋 **작업 개요**
**목표**: upbit_auto_trading\ui\desktop 폴더의 모든 레거시 요소를 완전히 정리하여 DDD/DTO/MVP 원칙 기반 개발의 발목을 잡는 요소들을 선행 제거
**중요도**: ⭐⭐⭐⭐⭐ (최우선 - 모든 설정 화면 작업의 전제조건)
**예상 기간**: 1-2일
**담당자**: 개발팀

## 🎯 **작업 목표**
- 기존 274개 Python 파일 중 레거시 요소 완전 식별 및 처리
- DDD 원칙에 위배되는 폴더 구조 및 파일들 정리
- MVP 패턴 적용을 방해하는 기존 코드 정리
- 새로운 7탭 설정 시스템 구현을 위한 깨끗한 기반 마련

## 🔍 **현재 상황 분석**

### **문제점 식별**
1. **아키텍처 위반**: UI Layer에 비즈니스 로직 (models/) 혼재
2. **순환 참조**: 복잡한 내부 import 체인 (50+ 건)
3. **레거시 컴포넌트**: 사용되지 않는 팩토리 및 유틸리티
4. **구조 혼재**: 기존 탭 시스템과 새 MVP 구조 공존
5. **네이밍 불일치**: DDD 원칙에 맞지 않는 폴더명

### **영향 범위**
- **직접 영향**: 274개 Python 파일
- **참조 영향**: 50+ import 관계
- **아키텍처 영향**: Domain/Application Layer 경계 침범

## 🏗️ **아키텍처 설계**

### **정리 후 목표 구조**
```
📁 upbit_auto_trading/ui/desktop/
├── main_window.py                          # 메인 윈도우 (MVP 적용)
├── screens/                                # 화면별 MVP 구조
│   ├── settings/                           # ✅ 이미 MVP 구조 완성
│   │   ├── presenters/                     # MVP - Presenter
│   │   ├── views/                          # MVP - View Interface
│   │   ├── widgets/                        # MVP - View Implementation
│   │   ├── dtos/                           # Data Transfer Objects
│   │   └── interfaces/                     # View Interfaces
│   └── [other_screens]/                    # 점진적 MVP 적용 예정
├── common/                                 # 공통 UI 컴포넌트
│   ├── widgets/                            # 재사용 가능한 위젯
│   ├── styles/                             # 테마 및 스타일 관리
│   └── presenters/                         # 공통 프레젠터
└── __pycache__/                            # Python 캐시 (유지)
```

### **제거 대상 구조**
```
❌ components/          → legacy/ (DDD 위반)
❌ factories/           → legacy/ (사용되지 않음)
❌ models/              → domain/ (아키텍처 위반)
❌ [legacy_screens]/    → legacy/ (구조 미정리)
```

## 📝 **작업 단계**

### **Sub-Task 0.1: 레거시 폴더 완전 정리** (0.5일)
**목표**: DDD 원칙에 위배되는 폴더들의 완전한 정리

#### **Step 0.1.1**: 아키텍처 위반 폴더 처리
- [ ] `components/` 폴더 → `legacy/ui_components_archive_20250810/`
  - `database_config_tab.py` (1개 파일)
  - 새 위치: `screens/settings/widgets/database_settings_widget.py`
- [ ] `factories/` 폴더 → `legacy/ui_factories_archive_20250810/`
  - `screen_factory.py` (사용되지 않음)
  - 현재 어디서도 참조되지 않음 확인됨
- [ ] `models/` 폴더 → `domain/models/` (Domain Layer로 이동)
  - `notification.py` (7개 파일에서 참조 중)
  - 모든 참조 경로 업데이트 필요

#### **Step 0.1.2**: 레거시 화면 파일 식별 및 처리
- [ ] MVP 패턴 미적용 화면들 식별
- [ ] 중복 기능 파일 정리 (`*_backup.py`, `*_v2.py`)
- [ ] 사용되지 않는 예제 파일 정리 (`*_example.py`)
- [ ] 테스트용 임시 파일 정리 (`*_test.py`)

#### **Step 0.1.3**: 순환 참조 해결
- [ ] 50+ import 관계 분석 및 정리
- [ ] 상대 import를 절대 import로 변경
- [ ] 불필요한 내부 참조 제거

**예상 산출물**:
- 정리된 폴더 구조
- 레거시 파일 백업 보고서
- import 관계 정리 보고서

---

### **Sub-Task 0.2: Domain Layer 분리 작업** (0.5일)
**목표**: UI Layer에 잘못 위치한 비즈니스 로직을 Domain Layer로 이동

#### **Step 0.2.1**: Notification 모델 Domain Layer 이동
- [ ] `upbit_auto_trading/domain/models/notification.py` 생성
- [ ] 기존 `ui.desktop.models.notification` 참조 업데이트:
  - `business_logic/monitoring/alert_manager.py`
  - `business_logic/monitoring/market_monitor.py`
  - `business_logic/monitoring/trade_monitor.py`
  - `business_logic/monitoring/system_monitor.py`
  - `screens/notification_center/notification_center.py`
  - `screens/notification_center/notification_filter.py`
  - `screens/notification_center/notification_list.py`

#### **Step 0.2.2**: 기타 비즈니스 로직 분리
- [ ] UI 컴포넌트에서 비즈니스 로직 식별
- [ ] Domain/Application Layer로 이동할 로직 추출
- [ ] DTO 패턴 적용으로 데이터 전달 최적화

#### **Step 0.2.3**: 의존성 역전 원칙 적용
- [ ] UI → Domain 의존성을 Application Layer 경유로 변경
- [ ] Interface 기반 의존성 주입 적용
- [ ] 순수한 Presentation Layer 구현

**예상 산출물**:
- Domain Layer 모델 파일들
- 업데이트된 import 구조
- 의존성 다이어그램

---

### **Sub-Task 0.3: 중복 및 미사용 파일 정리** (0.5일)
**목표**: 개발 과정에서 생성된 중복, 백업, 테스트 파일들의 체계적 정리

#### **Step 0.3.1**: 백업 파일 정리
- [ ] `*_backup.py` 파일들 식별 및 처리:
  - `chart_view_screen_backup.py` → legacy/
  - `database_settings_presenter_backup.py` → legacy/
  - `database_settings_presenter_broken.py` → legacy/
  - `condition_dialog_backup.py` → legacy/
- [ ] 현재 사용 중인 파일과 비교하여 안전성 확인
- [ ] 필요시 주요 변경사항 문서화

#### **Step 0.3.2**: 버전 파일 정리
- [ ] `*_v2.py` 파일들 처리:
  - `chart_view_screen_v2.py` → 메인 파일과 통합 or legacy/
- [ ] 최신 버전 확인 및 구버전 정리
- [ ] 기능 중복 제거

#### **Step 0.3.3**: 예제 및 테스트 파일 정리
- [ ] 개발용 예제 파일들:
  - `plotly_chart_example.py` → examples/ or legacy/
  - `dynamic_chart_data_guide.py` → docs/ or legacy/
- [ ] 임시 테스트 파일들 정리
- [ ] 정식 테스트는 `tests/` 폴더로 이동

**예상 산출물**:
- 정리된 파일 목록
- 보존된 중요 변경사항 문서
- 정리 작업 보고서

---

### **Sub-Task 0.4: 새로운 구조 검증 및 안정화** (0.5일)
**목표**: 정리 후 시스템 무결성 검증 및 안정화

#### **Step 0.4.1**: Import 관계 검증
- [ ] 모든 import 문 정상 동작 확인
- [ ] 순환 참조 완전 제거 검증
- [ ] 누락된 의존성 확인 및 수정

#### **Step 0.4.2**: 시스템 무결성 테스트
- [ ] 메인 윈도우 정상 실행 확인
- [ ] 설정 화면 정상 동작 확인
- [ ] 각 화면 전환 기능 정상 확인
- [ ] 에러 로그 모니터링

#### **Step 0.4.3**: 문서화 및 가이드 작성
- [ ] 새로운 폴더 구조 문서화
- [ ] DDD 원칙 준수 가이드 작성
- [ ] 향후 개발 시 주의사항 정리
- [ ] 레거시 처리 완료 보고서

**예상 산출물**:
- 시스템 무결성 검증 보고서
- 새로운 구조 가이드 문서
- 완료된 정리 작업 요약

---

## 🧪 **테스트 계획**

### **Regression Tests**
- [ ] 메인 윈도우 실행 테스트
- [ ] 모든 화면 전환 테스트
- [ ] 설정 저장/로드 테스트
- [ ] 알림 시스템 동작 테스트

### **Architecture Tests**
- [ ] Import 순환 참조 검사
- [ ] DDD Layer 분리 검증
- [ ] MVP 패턴 적용 확인

### **Performance Tests**
- [ ] 애플리케이션 시작 시간 측정
- [ ] 메모리 사용량 비교 (정리 전/후)
- [ ] 화면 전환 속도 측정

---

## 📊 **성공 기준**

### **구조적 요구사항**
- ✅ DDD 원칙 100% 준수하는 폴더 구조
- ✅ UI Layer에서 Domain Logic 완전 분리
- ✅ 순환 참조 0건
- ✅ 미사용 파일 0개

### **기능적 요구사항**
- ✅ 모든 기존 기능 정상 동작
- ✅ 설정 화면 완전 동작
- ✅ 알림 시스템 정상 동작
- ✅ 에러 발생 0건

### **성능 요구사항**
- ✅ 시작 시간 유지 또는 개선
- ✅ 메모리 사용량 감소 또는 유지
- ✅ 화면 전환 속도 개선

---

## 🔗 **의존성 및 연관 작업**

### **선행 작업**
- 없음 (독립적으로 실행 가능)

### **연관 작업 (이 작업 완료 후 진행)**
- TASK-20250809-01: 환경&로깅 탭 구현
- TASK-20250809-02: 매매설정 탭 구현
- TASK-20250809-03: 시스템 설정 탭 구현
- TASK-20250809-04: UI설정 탭 정리
- TASK-20250809-05: API키 탭 보안 강화
- TASK-20250809-06: 고급 설정 탭 구현
- TASK-20250809-07: 통합 설정 마이그레이션

### **Blocking Tasks**
- **모든 설정 화면 관련 작업은 이 작업 완료가 필수 전제조건**

---

## 🚀 **완료 후 기대효과**

1. **개발 효율성 극대화**: 레거시 코드로 인한 개발 지연 완전 해소
2. **아키텍처 순수성**: DDD/MVP 원칙에 완전히 부합하는 깨끗한 구조
3. **유지보수성 향상**: 명확한 책임 분리로 코드 수정 영향 범위 최소화
4. **새 기능 개발 가속**: 7탭 설정 시스템 구현을 위한 완벽한 기반 마련

## 📝 **중요 주의사항**

### **데이터 안전성**
- [ ] 모든 레거시 파일은 삭제하지 않고 `legacy/` 폴더에 백업
- [ ] 중요한 기능 변경사항은 별도 문서화
- [ ] 롤백 계획 수립 및 테스트

### **호환성 보장**
- [ ] 기존 설정 파일 호환성 유지
- [ ] 사용자 데이터 무손실 보장
- [ ] 외부 모듈과의 인터페이스 유지

### **점진적 적용**
- [ ] 대규모 변경은 단계별 진행
- [ ] 각 단계별 검증 포인트 설정
- [ ] 문제 발생 시 즉시 중단 및 검토

---

## ⚡ **즉시 실행 가능한 PowerShell 스크립트**

```powershell
# UI Desktop 레거시 정리 스크립트
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$legacyDir = "legacy\ui_desktop_cleanup_$timestamp"

# 레거시 디렉토리 생성
New-Item -ItemType Directory -Path $legacyDir -Force

# 1. 안전한 폴더들 즉시 이동
Write-Host "🔄 레거시 폴더 이동 중..."
if (Test-Path "upbit_auto_trading\ui\desktop\factories") {
    Move-Item "upbit_auto_trading\ui\desktop\factories" "$legacyDir\factories"
    Write-Host "✅ factories 폴더 이동 완료"
}

if (Test-Path "upbit_auto_trading\ui\desktop\components") {
    Move-Item "upbit_auto_trading\ui\desktop\components" "$legacyDir\components"
    Write-Host "✅ components 폴더 이동 완료"
}

# 2. 백업 파일들 정리
Write-Host "🔄 백업 파일 정리 중..."
Get-ChildItem -Path "upbit_auto_trading\ui\desktop" -Recurse -Filter "*_backup.py" | ForEach-Object {
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
    $targetPath = "$legacyDir\backup_files\$($_.Name)"
    New-Item -ItemType Directory -Path (Split-Path $targetPath) -Force
    Move-Item $_.FullName $targetPath
    Write-Host "📦 백업됨: $relativePath"
}

# 3. 버전 파일들 정리
Get-ChildItem -Path "upbit_auto_trading\ui\desktop" -Recurse -Filter "*_v2.py" | ForEach-Object {
    $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
    $targetPath = "$legacyDir\version_files\$($_.Name)"
    New-Item -ItemType Directory -Path (Split-Path $targetPath) -Force
    Move-Item $_.FullName $targetPath
    Write-Host "📦 백업됨: $relativePath"
}

Write-Host "🎉 UI Desktop 레거시 정리 1단계 완료!"
Write-Host "📁 백업 위치: $legacyDir"
Write-Host "⚠️  다음: Domain Layer 이동 작업 수행 필요"
```

---

## 🎯 **최종 검증 체크리스트**

### **정리 완료 확인**
- [ ] `components/` 폴더 제거 완료
- [ ] `factories/` 폴더 제거 완료
- [ ] `models/` 폴더 Domain Layer로 이동 완료
- [ ] 모든 백업 파일 정리 완료
- [ ] 순환 참조 완전 제거

### **기능 정상 동작 확인**
- [ ] `python run_desktop_ui.py` 정상 실행
- [ ] 모든 화면 전환 정상 동작
- [ ] 설정 화면 접근 및 기능 정상
- [ ] 에러 로그 0건

### **아키텍처 순수성 확인**
- [ ] UI Layer에 Domain Logic 없음
- [ ] MVP 패턴 적용 가능한 깨끗한 구조
- [ ] DDD 원칙에 부합하는 폴더 구조

**이 작업 완료 후, 모든 설정 화면 TASK 작업이 깨끗한 환경에서 진행 가능합니다!** 🚀

# TASK-20250801-03: YAML 추출 개선 및 편집-검증-통합 워크플로우 구축

## 📋 **작업 개요**
DB → YAML 추출 도구에 메타데이터 주석 추가와 사용자/에이전트 편집 후 검증 및 통합 워크플로우 구축

## 🎯 **주요 목표**

### 1️⃣ **추출 도구 개선** (super_db_extraction_db_to_yaml.py)
- ✅ **메타데이터 주석 자동 추가**: 추출 소스, 시점, 대상 정보
- ✅ **추출 경로 명시**: DB 파일 → 테이블 → YAML 파일 전체 경로
- ✅ **추출 조건 기록**: 필터링, 범위, 특수 옵션 등

### 2️⃣ **편집-검증-통합 워크플로우**
- 📝 **편집용 YAML**: 사용자/에이전트가 수정할 작업본
- 🔍 **변경 검증**: 수정 사항을 DB에 반영하기 전 검증
- 🔄 **자동 통합**: 검증 후 최종 YAML 생성 및 기존 파일 정리

### 3️⃣ **새로운 도구 개발**
- 🆕 **super_db_yaml_editor_workflow.py**: 편집-검증-통합 자동화
- 🆕 **super_db_yaml_diff_analyzer.py**: 변경 사항 분석 및 검증

## 📊 **작업 단계**

### Phase 1: 추출 도구 개선 ⭐ 우선순위
```bash
# 개선 대상: tools/super_db_extraction_db_to_yaml.py
# 목표: 상세한 메타데이터 주석이 포함된 YAML 생성
```

#### **1.1 메타데이터 주석 템플릿 설계**
```yaml
# ════════════════════════════════════════════════════════════════
# 🔄 Super DB Extraction - Metadata
# ════════════════════════════════════════════════════════════════
# 추출 소스: D:\projects\upbit-autotrader-vscode\upbit_auto_trading\data\settings.sqlite3
# 소스 테이블: tv_trading_variables (20개 레코드)
# 추출 시점: 2025-08-01 14:17:55
# 추출 모드: 백업 모드 (특정 테이블)
# 대상 파일: tv_trading_variables_backup_20250801_141755.yaml
# 추출 도구: super_db_extraction_db_to_yaml.py v1.0
# ────────────────────────────────────────────────────────────────
# 📝 편집 안내:
# - 이 파일은 DB에서 추출된 실제 데이터입니다
# - 편집 후 super_yaml_editor_workflow.py로 DB 반영 가능
# - 변경 전 반드시 백업을 확인하세요
# ════════════════════════════════════════════════════════════════

trading_variables:
  # ... 실제 데이터 ...
```

#### **1.2 추출 정보 수집 및 포매팅**
- **추출 컨텍스트 클래스** 생성
- **메타데이터 생성 메서드** 구현
- **YAML 헤더 자동 생성** 로직

#### **1.3 파일 저장 시 주석 삽입**
- **기존 _save_yaml_file() 메서드** 확장
- **주석 + 데이터 결합** 로직 구현

### Phase 2: 편집 워크플로우 도구 개발 🔧

#### **2.1 super_db_yaml_editor_workflow.py 개발**
```bash
# 사용 예시:
python tools/super_db_yaml_editor_workflow.py --start-edit tv_trading_variables_backup_20250801_141755.yaml
# → tv_trading_variables_EDIT_20250801_141755.yaml 생성 (편집용)

python tools/super_db_yaml_editor_workflow.py --validate-changes tv_trading_variables_EDIT_20250801_141755.yaml
# → 변경사항 분석 및 DB 반영 가능성 검증

python tools/super_db_yaml_editor_workflow.py --apply-changes tv_trading_variables_EDIT_20250801_141755.yaml
# → DB 반영 → 새로운 추출 → 최종 YAML 생성 → 임시 파일 정리
```

**핵심 기능:**
- **편집용 복사본 생성**: `_EDIT_` 태그로 구분
- **변경 사항 diff 분석**: 무엇이 바뀌었는지 상세 보고
- **DB 반영 전 검증**: 무결성, 타입, 제약조건 검사
- **자동 백업 및 복구**: 실패 시 롤백 지원

#### **2.2 super_db_yaml_diff_analyzer.py 개발**
```bash
# 변경 사항 상세 분석
python tools/super_db_yaml_diff_analyzer.py --compare original.yaml edited.yaml
# → 추가/수정/삭제 항목 상세 리포트

python tools/super_db_yaml_diff_analyzer.py --validate-schema edited.yaml
# → DB 스키마 호환성 검증
```

**핵심 기능:**
- **구조적 diff 분석**: 필드별 변경 내역
- **타입 검증**: 데이터 타입 일치성 확인
- **제약조건 검증**: FK, 유니크 등 DB 제약사항
- **위험도 평가**: 변경의 영향도 분석

### Phase 3: 통합 및 자동화 🔄

#### **3.1 원클릭 편집 워크플로우**
```bash
# 완전 자동화된 편집 프로세스
python tools/super_db_yaml_complete_workflow.py --table tv_trading_variables
# → 추출 → 편집용 복사 → (사용자 편집) → 검증 → 적용 → 정리
```

#### **3.2 백업 및 버전 관리**
- **자동 백업 시스템**: 모든 변경 전 백업 생성
- **버전 히스토리**: 변경 이력 추적
- **롤백 지원**: 이전 상태로 복구 기능

## 🔧 **구현 상세**

### **1. 메타데이터 주석 구조**
```python
class ExtractionMetadata:
    def __init__(self, source_db, source_table, target_file, record_count, extraction_mode):
        self.source_db_path = Path(source_db).resolve()
        self.source_table = source_table
        self.target_file = target_file
        self.record_count = record_count
        self.extraction_time = datetime.now()
        self.extraction_mode = extraction_mode
        self.tool_version = "super_db_extraction_db_to_yaml.py v1.1"
    
    def generate_header_comment(self) -> str:
        return f"""# ════════════════════════════════════════════════════════════════
# 🔄 Super DB Extraction - Metadata
# ════════════════════════════════════════════════════════════════
# 추출 소스: {self.source_db_path}
# 소스 테이블: {self.source_table} ({self.record_count}개 레코드)
# 추출 시점: {self.extraction_time.strftime('%Y-%m-%d %H:%M:%S')}
# 추출 모드: {self.extraction_mode}
# 대상 파일: {self.target_file}
# 추출 도구: {self.tool_version}
# ────────────────────────────────────────────────────────────────
# 📝 편집 안내:
# - 이 파일은 DB에서 추출된 실제 데이터입니다
# - 편집 후 super_db_yaml_editor_workflow.py로 DB 반영 가능
# - 변경 전 반드시 백업을 확인하세요
# ════════════════════════════════════════════════════════════════

"""
```

### **2. 편집 워크플로우 클래스**
```python
class SuperDBYAMLEditorWorkflow:
    def __init__(self):
        self.backup_dir = Path("data_info/backups")
        self.edit_dir = Path("data_info/editing")
        self.final_dir = Path("data_info")
    
    def start_editing_session(self, source_yaml: str) -> str:
        """편집 세션 시작 - 편집용 복사본 생성"""
        pass
    
    def validate_changes(self, edited_yaml: str) -> Dict[str, Any]:
        """변경사항 검증"""
        pass
    
    def apply_changes_to_db(self, edited_yaml: str) -> bool:
        """DB에 변경사항 반영"""
        pass
    
    def finalize_editing_session(self, session_id: str) -> str:
        """편집 세션 완료 - 최종 파일 생성 및 정리"""
        pass
```

### **3. Diff 분석 엔진**
```python
class SuperDBYAMLDiffAnalyzer:
    def __init__(self):
        self.schema_validator = SchemaValidator()
        self.risk_assessor = RiskAssessor()
    
    def analyze_differences(self, original: Dict, edited: Dict) -> DiffReport:
        """상세한 차이점 분석"""
        pass
    
    def validate_db_compatibility(self, yaml_data: Dict, table_name: str) -> ValidationResult:
        """DB 스키마 호환성 검증"""
        pass
    
    def assess_change_risk(self, diff_report: DiffReport) -> RiskAssessment:
        """변경 위험도 평가"""
        pass
```

## 📅 **실행 일정**

### **Week 1 (8/1 - 8/2)**
- [x] ~~작업 계획 수립~~ ✅ 완료
- [x] ~~**Phase 1**: 추출 도구 메타데이터 주석 기능 구현~~ ✅ 완료
- [x] ~~기본 테스트 및 검증~~ ✅ 완료

### **Week 1 (8/2 - 8/3)**  
- [x] ~~**Phase 2**: 편집 워크플로우 도구 개발~~ ✅ 완료 (super_db_yaml_editor_workflow.py)
- [x] ~~편집-검증-적용-정리 전체 워크플로우 테스트~~ ✅ 완료
- [x] ~~RSI 데이터 수정 테스트 성공~~ ✅ 완료

### **Week 2 (8/4 - 8/5)**
- [x] ~~**Phase 3**: 완전 자동화 워크플로우 구축~~ ✅ 완료
- [x] ~~문서화 및 사용자 가이드 작성~~ ✅ 완료 (tools/README.md 업데이트)
- [x] ~~전체 시스템 검증~~ ✅ 완료

## 🎯 **성공 기준**

### **기능적 목표**
- ✅ 모든 추출 YAML에 상세한 메타데이터 주석 포함
- ✅ 편집 → 검증 → 적용 → 정리 완전 자동화
- ✅ 변경사항 추적 및 롤백 지원
- ✅ 사용자 친화적 에러 메시지 및 가이드

### **운영적 목표**  
- ✅ 편집 작업 시간 50% 단축
- ✅ 데이터 손실 위험 제거 (자동 백업)
- ✅ 변경 추적 가능성 100% 확보
- ✅ 에이전트/사용자 모두 직관적 사용 가능

## 💡 **기대 효과**

### **단기 효과**
- 🎯 **편집 안전성 확보**: 메타데이터로 추적성 보장
- 🚀 **작업 효율성 향상**: 자동화된 워크플로우
- 🛡️ **데이터 무결성 보장**: 검증 및 백업 시스템

### **장기 효과**
- 🧠 **AI 에이전트 학습 최적화**: 명확한 메타데이터
- 🔄 **지속적 개선 가능**: 변경 히스토리 기반 최적화
- 📈 **확장성 확보**: 다른 데이터 소스에도 적용 가능

---

## 🚀 **즉시 시작할 작업**

**다음 명령어로 Phase 1 개시:**
```bash
# 1. 현재 추출 도구 백업
cp tools/super_db_extraction_db_to_yaml.py tools/super_db_extraction_db_to_yaml_v1.0_backup.py

# 2. 메타데이터 주석 기능 개발 시작
# tools/super_db_extraction_db_to_yaml.py 편집

# 3. 테스트 실행
python tools/super_db_extraction_db_to_yaml.py --tables tv_trading_variables --backup
```

---

**작성일**: 2025-08-01  
**담당**: Super 에이전트 시스템  
**우선순위**: 높음 ⭐⭐⭐  
**예상 완료**: 2025-08-05

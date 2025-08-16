# 📚 Legacy Tools - 이전 도구 보관소

이 폴더는 **Super 도구 시스템 v4.0 이전의 개별 도구들**을 보관합니다.

## 📝 보관 목적

- 📚 **참고 자료**: 과거 구현 방식 학습
- 🔄 **기능 복원**: 필요시 특정 기능 복원
- 📊 **발전 과정**: 도구 개발 히스토리 보존
- 🛠️ **백업**: 긴급 상황 시 대안 확보

## 🔄 Super 도구로의 통합 매핑

### 📊 **DB 관련 도구들 → `super_db_inspector.py`**
- `super_db_table_viewer.py` → `--quick-status`, `--table-details`
- `super_db_analyze_parameter_table.py` → `--tv-variables`
- `super_db_extraction_db_to_yaml.py` → `--export-current`
- `super_db_schema_extractor.py` → `--schema-info`

### 🔄 **마이그레이션 도구들 → `super_db_migrator.py`**
- `super_db_migration_yaml_to_db.py` → `--yaml-to-db`
- `super_db_yaml_merger.py` → `--smart-merge`
- `super_db_rollback_manager.py` → `--auto-backup`, `--rollback`
- `super_db_structure_generator.py` → `--create-tables`

### 🔍 **코드 분석 도구들 → `super_code_tracker.py`**
- `super_db_table_reference_code_analyzer.py` → `--feature-discovery`
- `super_file_dependency_analyzer.py` → `--layer-analysis`
- `super_files_unused_detector.py` → `--unused-cleanup`
- `super_import_tracker.py` → `--dependency-graph`

### 🤖 **개발 지원 도구들 → `super_dev_assistant.py`**
- 새로운 AI 기반 기능으로 대체
- 자연어 검색 및 의미론적 분석
- 아키텍처 건강도 측정

## 🚀 새 도구 시스템 사용 권장

```powershell
# 이전 방식 (복잡함)
python tools/legacy_tools/super_db_table_viewer.py settings
python tools/legacy_tools/super_db_analyze_parameter_table.py

# 새 방식 (간단함)
python tools/super_db_inspector.py --quick-status
```

## ⚠️ 중요 안내

- **새 개발**: 반드시 Super 도구 시스템 사용
- **문제 발생**: legacy 도구 임시 사용 후 이슈 리포트
- **기능 요청**: Super 도구에 추가 요청

---

*📅 보관일: 2025-08-16*
*🎯 목적: Super 도구 시스템 v4.0 전환 완료*

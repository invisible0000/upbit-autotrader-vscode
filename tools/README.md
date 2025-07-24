# 🛠️ Tools Directory

## 📁 개요
이 디렉터리는 트리거 정규화 및 파라미터 복원 시스템 개발 과정에서 생성된 유용한 도구들을 보관합니다.

## 📅 생성일시
- **정리일시**: 2025-07-24 19:24:04
- **이관 파일 수**: 12개

## 🔧 주요 도구들

### 트리거 정규화 도구
- `fix_trigger_formats.py` - 비정상적인 트리거를 올바른 외부변수 형식으로 변환
- `fix_macd_triggers.py` - MACD 트리거 특별 수정
- `fix_external_params.py` - 외부변수 파라미터 수정

### 진단 및 검증 도구  
- `investigate_triggers.py` - 트리거 이상 상태 조사
- `diagnose_external_params.py` - 외부변수 파라미터 진단
- `verify_final_state.py` - 최종 상태 검증

### 테스트 도구
- `test_parameter_restoration.py` - 파라미터 복원 시스템 테스트
- `test_ui_parameter_restoration.py` - UI 파라미터 복원 테스트
- `check_db_state.py` - 데이터베이스 상태 확인

### 백업 및 로그 파일
- `trigger_backup_*.json` - 원본 트리거 데이터 백업
- `trigger_conversion_log_*.json` - 변환 작업 로그
- `trigger_examples_reference_*.json` - 외부변수 사용법 예시

## 🚀 사용법

### 트리거 정규화 실행
```bash
python tools/fix_trigger_formats.py
```

### 상태 검증
```bash
python tools/verify_final_state.py
```

### 파라미터 복원 테스트
```bash
python tools/test_parameter_restoration.py
```

## ⚠️ 주의사항
- 이 도구들은 데이터베이스를 직접 수정할 수 있습니다
- 실행 전 반드시 백업을 생성하세요
- 프로덕션 환경에서는 신중하게 사용하세요

## 📝 관련 문서
- `TRIGGER_NORMALIZATION_REPORT.md` - 트리거 정규화 작업 보고서
- `PARAMETER_RESTORATION_COMPLETION_REPORT.md` - 파라미터 복원 구현 보고서

## 🎯 향후 활용
- 유사한 데이터 정규화 작업 시 참고 자료로 활용
- 트리거 시스템 유지보수 시 진단 도구로 사용
- 새로운 외부변수 추가 시 예시 참고

---
*이 도구들은 2025년 7월 24일 트리거 정규화 및 파라미터 복원 시스템 개발 과정에서 생성되었습니다.*

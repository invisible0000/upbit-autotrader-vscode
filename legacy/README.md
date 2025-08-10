# 🗂️ Legacy Files Archive

## 📋 **보관 목적**
이 폴더는 DDD + MVP 구조로 마이그레이션된 파일들의 백업본을 저장합니다.

## 📂 **폴더 구조**
```
legacy/
└── ui/
    └── desktop/
        └── screens/
            └── settings/
                ├── database_settings_view_legacy.py          # 원본 database settings view
                ├── presenters/
                │   └── database_settings_presenter_legacy.py # 원본 presenter
                └── widgets/
                    ├── database_backup_widget_legacy.py      # 원본 backup widget
                    └── database_status_widget_legacy.py      # 원본 status widget
```

## 🔄 **마이그레이션 기록**

### **Phase 1: Database Settings (2025-08-10)**
- **마이그레이션 완료**: ✅
- **백업 파일들**: 4개 파일
- **새 구조**: `upbit_auto_trading/ui/desktop/screens/settings/database_settings/`
- **상태**: 정상 동작 확인됨

## ⚠️ **주의사항**
- 이 파일들은 **참조용**으로만 사용하세요
- 실제 시스템에서는 새로운 DDD + MVP 구조를 사용합니다
- 롤백이 필요한 경우에만 이 파일들을 사용하세요

## 🗑️ **정리 계획**
- 모든 마이그레이션 완료 후 안전성 확인되면 삭제 예정
- 예상 보관 기간: 1-2주 (테스트 완료 후)

---
**📅 생성일**: 2025-08-10
**📋 용도**: DDD+MVP 마이그레이션 백업
**🔗 관련 태스크**: TASK-20250810-02

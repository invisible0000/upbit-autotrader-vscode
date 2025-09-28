# 🚨 MVP 패턴 분석 보고서

**분석 일시**: 2025-09-28 22:31:26
**총 위반 수**: 50건

## 📊 심각도별 위반 현황

- 🚨 **Critical**: 47건 (즉시 해결 필요)
- ⚠️ **High**: 3건 (단기 해결 필요)
- 📋 **Medium**: 0건 (중기 해결 대상)
- 📝 **Low**: 0건 (장기 개선 대상)

## 🚨 CRITICAL 위반 사항

### 1. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\settings_screen.py:25`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 2. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\api_key_manager_secure_legacy.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 3. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\environment_profile_view.py:22`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 4. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\logging_management_view.py:25`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 5. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py:49`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 6. 계층 경계 위반: from upbit_auto_trading.infrastructure.configuration import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py:50`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.configuration import get_path_service
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 7. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\presenters\ui_settings_presenter.py:13`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 8. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\views\ui_settings_view.py:16`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 9. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\widgets\animation_settings_widget.py:14`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 10. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\widgets\chart_settings_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 11. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\widgets\theme_selector_widget.py:16`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 12. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\ui_settings\widgets\window_settings_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 13. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\presenters\notification_settings_presenter.py:12`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 14. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\views\notification_settings_view.py:13`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 15. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\widgets\alert_types_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 16. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\widgets\notification_frequency_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 17. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\widgets\notification_methods_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 18. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\notification_settings\widgets\quiet_hours_widget.py:18`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 19. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_config_presenter.py:20`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 20. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger, get_logging_service
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 21. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging.terminal.terminal_capturer import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py:16`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging.terminal.terminal_capturer import (
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 22. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging.live.ui_live_log_handler import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter.py:21`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging.live.ui_live_log_handler import (
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 23. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter_backup.py:23`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 24. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_management_presenter_backup.py:24`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 25. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\widgets\console_viewer_widget.py:19`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 26. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\widgets\logging_settings_widget.py:20`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 27. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\widgets\log_viewer_widget.py:20`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 28. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\dialogs\component_selector\component_selector_dialog.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 29. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\dialogs\profile_metadata_dialog.py:28`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 30. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\presenters\environment_profile_presenter.py:22`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 31. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\widgets\profile_selector_section.py:24`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 32. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\widgets\quick_environment_buttons.py:22`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 33. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\environment_profile\widgets\yaml_editor_section.py:22`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 34. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\presenters\database_settings_presenter.py:47`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 35. 계층 경계 위반: from upbit_auto_trading.infrastructure.configuration import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\presenters\database_settings_presenter.py:48`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.configuration import get_path_service
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 36. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\views\database_settings_view.py:16`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 37. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\widgets\database_backup_widget.py:24`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 38. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\widgets\database_path_selector.py:22`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 39. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\widgets\database_status_widget.py:23`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 40. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\widgets\database_task_progress_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 41. 계층 경계 위반: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\presenters\api_settings_presenter.py:23`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 42. 계층 경계 위반: from upbit_auto_trading.infrastructure.dependency_injection.container import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\presenters\api_settings_presenter.py:24`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.dependency_injection.container import ApplicationContainer
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 43. 계층 경계 위반: from upbit_auto_trading.infrastructure.services.api_key_service import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\presenters\api_settings_presenter.py:28`

**🔍 문제 코드**:

```python
    from upbit_auto_trading.infrastructure.services.api_key_service import ApiKeyService
```

**💡 개선 방안**: 올바른 계층 순서를 따라 의존성을 설정하세요

---

### 44. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\views\api_settings_view.py:17`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 45. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\widgets\api_connection_widget.py:15`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 46. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\widgets\api_credentials_widget.py:16`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

### 47. View에서 Infrastructure 직접 접근: from upbit_auto_trading.infrastructure.logging import

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\api_settings\widgets\api_permissions_widget.py:14`

**🔍 문제 코드**:

```python
from upbit_auto_trading.infrastructure.logging import create_component_logger
```

**💡 개선 방안**: Infrastructure 접근을 Application Service로 위임하세요

---

## ⚠️ HIGH 위반 사항

### 1. Presenter에서 UI 직접 조작: .setText(

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\presenters\database_settings_presenter.py:650`

**🔍 문제 코드**:

```python
                        msg_box.setText(success_msg)
```

**💡 개선 방안**: View 인터페이스 메서드를 통해 UI를 조작하세요

---

### 2. Presenter에서 UI 직접 조작: .setText(

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\logging_management\presenters\logging_config_presenter.py:118`

**🔍 문제 코드**:

```python
            self.view.component_focus_edit.setText(component_focus)
```

**💡 개선 방안**: View 인터페이스 메서드를 통해 UI를 조작하세요

---

### 3. Presenter에서 UI 직접 조작: .setText(

**📍 위치**: `upbit_auto_trading\ui\desktop\screens\settings\database_settings\presenters\database_settings_presenter.py:426`

**🔍 문제 코드**:

```python
                        msg_box.setText(success_msg)
```

**💡 개선 방안**: View 인터페이스 메서드를 통해 UI를 조작하세요

---

## 🎯 다음 단계

1. **즉시 해결**: Critical 위반 사항부터 우선 해결
2. **단기 계획**: High 위반 사항 해결 태스크 생성

## 📋 위반 사항 등록

발견된 위반 사항을 다음 위치에 등록하세요:

- `docs/architecture_review/violation_registry/active_violations.md`
- 템플릿: `docs/architecture_review/violation_registry/templates/violation_report_template.md`

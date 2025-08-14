# DDD Domain 계층 의존성 위반 분석 리포트
============================================================
📊 총 위반 사항: 245개

## Infrastructure Imports: 13개

### 📍 upbit_auto_trading\domain\events\domain_event_publisher.py:10
**유형**: Infrastructure Import
**영향도**: HIGH
**코드**: `from upbit_auto_trading.infrastructure.logging import create_component_logger`
**해결방안**: Domain Events 또는 Repository 인터페이스 사용

### 📍 upbit_auto_trading\domain\events\__init__.py:11
**유형**: Infrastructure Import
**영향도**: HIGH
**코드**: `from upbit_auto_trading.infrastructure.logging import create_component_logger`
**해결방안**: Domain Events 또는 Repository 인터페이스 사용

### 📍 upbit_auto_trading\domain\logging\domain_logger.py:99
**유형**: Infrastructure Import
**영향도**: HIGH
**코드**: `from upbit_auto_trading.infrastructure.logging import get_logging_service`
**해결방안**: Domain Events 또는 Repository 인터페이스 사용

### 📍 upbit_auto_trading\domain\profile_management\entities\profile_editor_session.py:19
**유형**: Infrastructure Import
**영향도**: HIGH
**코드**: `from upbit_auto_trading.infrastructure.logging import create_component_logger`
**해결방안**: Domain Events 또는 Repository 인터페이스 사용

### 📍 upbit_auto_trading\domain\profile_management\entities\profile_metadata.py:19
**유형**: Infrastructure Import
**영향도**: HIGH
**코드**: `from upbit_auto_trading.infrastructure.logging import create_component_logger`
**해결방안**: Domain Events 또는 Repository 인터페이스 사용

... 외 8개 사례

## External Dependencies: 2개

### 📍 upbit_auto_trading\domain\profile_management\value_objects\yaml_content.py:14
**유형**: External Dependency
**영향도**: MEDIUM
**코드**: `import yaml`
**해결방안**: 의존성 역전(DI) 적용

### 📍 upbit_auto_trading\domain\configuration\services\unified_config_service.py:10
**유형**: External Dependency
**영향도**: MEDIUM
**코드**: `import yaml`
**해결방안**: 의존성 역전(DI) 적용

## Logging Violations: 230개

### 📍 upbit_auto_trading\domain\logging.py:26
**유형**: Infrastructure Logging
**영향도**: HIGH
**코드**: `if not self._logger.handlers:`
**해결방안**: Domain Logger (Events 기반) 사용

### 📍 upbit_auto_trading\domain\logging.py:33
**유형**: Infrastructure Logging
**영향도**: HIGH
**코드**: `self._logger.addHandler(handler)`
**해결방안**: Domain Logger (Events 기반) 사용

### 📍 upbit_auto_trading\domain\logging.py:34
**유형**: Infrastructure Logging
**영향도**: HIGH
**코드**: `self._logger.setLevel(logging.INFO)`
**해결방안**: Domain Logger (Events 기반) 사용

### 📍 upbit_auto_trading\domain\logging.py:38
**유형**: Infrastructure Logging
**영향도**: HIGH
**코드**: `self._logger.debug(message, *args)`
**해결방안**: Domain Logger (Events 기반) 사용

### 📍 upbit_auto_trading\domain\logging.py:42
**유형**: Infrastructure Logging
**영향도**: HIGH
**코드**: `self._logger.info(message, *args)`
**해결방안**: Domain Logger (Events 기반) 사용

... 외 225개 사례

## 🎯 수정 우선순위
1. **CRITICAL (0개)**: 직접 DB 접근 → Repository 패턴
2. **HIGH (243개)**: Infrastructure 의존성 → Domain Events

# 📁 Config 폴더 - 설정 관리 시스템

> **현재 상태**: 분산형 설정 파일 시스템 (Phase 1)
> **향후 계획**: 통합 설정 관리 시스템으로 발전 (Phase 2-3)

## 🎯 개요

업비트 자동매매 시스템의 모든 설정을 관리하는 중앙 집중식 폴더입니다. 현재는 기능별로 분리된 YAML 파일들을 사용하며, 향후 기반 기능이 안정화되면 통합 설정 시스템으로 진화할 예정입니다.

## 📋 현재 설정 파일 구조

### 🎚️ 환경별 설정 (Environment-based)

```yaml
config.yaml              # 기본 설정 (Base Configuration)
config.development.yaml  # 개발 환경 오버라이드
config.testing.yaml      # 테스트 환경 오버라이드
config.production.yaml   # 프로덕션 환경 오버라이드
config.staging.yaml      # 스테이징 환경 오버라이드
config.demo.yaml         # 데모 환경 오버라이드
config.debug.yaml        # 디버그 환경 오버라이드
```

### 🔧 기능별 설정 (Feature-specific)

```yaml
logging_config.yaml      # 로깅 시스템 (✅ 완성된 표준 사례)
database_config.yaml     # 데이터베이스 연결 설정
websocket_config.yaml    # WebSocket 통신 설정
rate_limiter_config.yaml # API 호출 제한 설정
paths_config.yaml        # 경로 설정 (프로젝트 구조 관리)
```

### 🔒 보안 및 사용자 설정

```json
secure/api_credentials.json  # API 키 암호화 저장소
user_settings.json          # 사용자 개별 설정
local_env_vars.json         # 로컬 환경변수 (개발용)
```

### 📁 조직화된 하위 폴더

```text
custom/                  # 커스텀 설정 파일들
custom_profiles/         # 사용자 정의 프로파일
legacy/                  # 레거시 설정 파일 보관
metadata/               # 설정 메타데이터
secure/                 # 보안 관련 설정 파일
```

## 🏗️ 아키텍처 진화 계획

### Phase 1: 분산형 설정 (현재) ✅

- **특징**: 기능별 개별 YAML 파일
- **장점**: 단순하고 명확한 구조, 기능별 독립성
- **사용례**: `LoggingConfigManager`, `ConfigLoader`
- **상태**: 안정적 운영 중

### Phase 2: 부분 통합 (중기 계획) 🔄

- **목표**: 관련 설정들의 논리적 그룹핑
- **변경점**:

  ```yaml
  application.yaml        # 핵심 애플리케이션 설정 통합
  infrastructure.yaml     # 인프라 설정 통합
  trading.yaml           # 매매 관련 설정 통합
  ```

- **하위 호환**: 기존 개별 파일 유지

### Phase 3: 완전 통합 (장기 계획) 🎯

- **목표**: 단일 설정 DB + 프로파일 시스템
- **구조**:

  ```text
  settings.sqlite3        # 모든 설정의 중앙 저장소
  ├── profiles 테이블     # 환경/사용자별 프로파일
  ├── settings 테이블     # 키-값 설정 저장
  └── history 테이블      # 설정 변경 이력
  ```

## 🔗 주요 연결 컴포넌트

### 설정 로더 시스템

- [`ConfigLoader`](../upbit_auto_trading/infrastructure/config/loaders/config_loader.py) - 환경별 설정 병합
- [`UnifiedConfigService`](../upbit_auto_trading/domain/configuration/services/unified_config_service.py) - 도메인 통합 설정
- [`LoggingConfigManager`](../upbit_auto_trading/infrastructure/logging/config/logging_config_manager.py) - 로깅 전용 관리자

### UI 설정 관리

- [`EnvironmentProfileView`](../upbit_auto_trading/ui/desktop/screens/settings/environment_profile/environment_profile_view.py) - 환경 프로파일 전환 UI
- [`LoggingManagementView`](../upbit_auto_trading/ui/desktop/screens/settings/logging_management/) - 로깅 설정 실시간 관리

### 경로 및 DB 설정

- [`ConfigPathRepository`](../upbit_auto_trading/infrastructure/persistence/config_path_repository.py) - 경로 설정 관리
- [`DatabaseConfigRepository`](../upbit_auto_trading/infrastructure/repositories/database_config_repository.py) - DB 설정 관리

## 💡 개발자 가이드

### 🎯 새로운 설정 추가 시

**현재 (Phase 1) - 개별 파일 방식:**

```python
# 1. config/{feature}_config.yaml 생성
# 2. {Feature}ConfigManager 클래스 구현
# 3. 실시간 변경 핸들러 추가
# 4. 표준 패턴 준수 ([UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md] 참조)
```

**권장 패턴:**

```yaml
# config/new_feature_config.yaml
new_feature:
  enabled: true
  main_setting: "value"

  detailed_options:
    option1: value1

  advanced:
    performance_monitoring: false

runtime:
  watch_config_file: true
  notify_on_change: true
```

### 🔧 환경별 설정 오버라이드

```yaml
# config.development.yaml
logging:
  level: "DEBUG"
  console_output: true

# config.production.yaml
logging:
  level: "WARNING"
  console_output: false
```

### 🔒 보안 설정 관리

```python
# API 키는 반드시 암호화 저장
from upbit_auto_trading.infrastructure.external_apis.upbit.upbit_auth import UpbitAuthenticator
auth = UpbitAuthenticator()  # secure/api_credentials.json 자동 암호화 처리
```

## 📚 참고 문서

- **통합 설정 가이드**: [`UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md`](../docs/UNIFIED_CONFIGURATION_MANAGEMENT_GUIDE.md)
- **로깅 시스템 사례**: [`logging_config.yaml`](./logging_config.yaml) - 표준 패턴의 완성된 구현
- **DDD 아키텍처**: 설정도 Domain/Infrastructure 계층 분리 원칙 준수

## ⚠️ 중요 사항

### ✅ DO (권장)

- 표준 YAML 구조 사용
- 실시간 변경 지원 구현
- 환경별 오버라이드 활용
- 보안 파일은 `secure/` 폴더 사용

### ❌ DON'T (금지)

- 하드코딩된 설정값 사용
- 개별 `setStyleSheet()` 방식 UI 설정
- 환경변수 직접 의존 (설정 파일 우선)
- 표준 패턴 무시한 독자적 구현

---

## 🚀 빠른 시작

```python
# 1. 환경별 설정 로드
from upbit_auto_trading.infrastructure.config import ConfigLoader
loader = ConfigLoader()
config = loader.load_config("development")

# 2. 로깅 설정 관리
from upbit_auto_trading.infrastructure.logging.config.logging_config_manager import LoggingConfigManager
logging_manager = LoggingConfigManager()
current_config = logging_manager.get_current_config()

# 3. UI에서 환경 전환
# Environment Profile View 통해 실시간 프로파일 전환 가능
```

> **💡 GitHub Copilot 활용 팁**: 이 README를 참조하여 설정 관련 작업 시 현재의 분산 구조를 이해하고, 향후 통합 계획을 고려한 확장 가능한 코드를 생성하세요.

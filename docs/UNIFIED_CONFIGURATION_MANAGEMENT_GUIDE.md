# 통합 설정 관리 시스템 가이드

> **Version**: 1.0
> **Last Updated**: 2025-08-13
> **Status**: 📋 확립된 표준 패턴

## 📖 개요

이 문서는 업비트 자동매매 시스템의 **통합 설정 관리 방법론**을 다룹니다.
복잡한 설정 관리의 혼란을 해결하고, 모든 기능이 따라야 할 **단일 표준 패턴**을 제시합니다.

## 🎯 핵심 원칙

### 1. **설정 파일 기반 아키텍처**

- 모든 설정은 `config/` 폴더의 YAML 파일로 관리
- 실시간 변경 가능, 파일 감시 지원
- 명확한 구조와 타입 안전성 확보

### 2. **단계적 통합 전략**

```
Phase 1: 개별 설정 파일 (현재) ✅
├── config/logging_config.yaml      # 로깅 설정
├── config/trading_config.yaml      # 매매 설정 (예정)
├── config/ui_config.yaml          # UI 설정 (예정)
└── config/api_config.yaml         # API 설정 (예정)

Phase 2: 통합 설정 (중기)
├── config/application.yaml        # 통합 설정
├── config/profile_overrides/      # 프로파일별 오버라이드
└── 개별 설정 파일 (하위 호환)

Phase 3: DB 통합 (장기)
├── settings.sqlite3               # 모든 설정 DB 통합
├── 프로파일 테이블                # 환경별 설정 관리
└── 설정 히스토리 테이블            # 변경 이력 관리
```

### 3. **안정성 우선 개발**

- 명확히 동작하는 기능만 유지
- 불완전한 기능은 제거하고 나중에 재구현
- 각 단계에서 이전 버전 호환성 유지

## 🔧 표준 설정 패턴

### **기본 구조**

```yaml
# config/{feature}_config.yaml
{feature_name}:
  # === 핵심 설정 ===
  enabled: true
  main_option: "value"

  # === 세부 설정 ===
  detailed_options:
    option1: value1
    option2: value2

  # === 고급 설정 ===
  advanced:
    performance_monitoring: false

# === 런타임 설정 ===
runtime:
  watch_config_file: true
  notify_on_change: true
  last_modified: "timestamp"
```

### **구현 클래스 패턴**

```python
class FeatureConfigManager:
    def __init__(self, config_file: str = "config/feature_config.yaml"):
        self._config_file = Path(config_file)
        self._change_handlers = []
        self._cached_config = None

    def get_feature_config(self) -> Dict[str, Any]:
        """기능 설정 조회"""

    def update_feature_config(self, config: Dict[str, Any], save_to_file: bool = True):
        """실시간 설정 업데이트"""

    def add_change_handler(self, handler: Callable):
        """변경 핸들러 등록"""
```

## ✅ 로깅 시스템 - 완성된 표준 사례

### **설정 파일 구조**

```yaml
# config/logging_config.yaml
logging:
  level: "INFO"                    # 전체 로그 레벨
  console_output: "auto"           # auto/true/false
  component_focus: ""              # 특정 컴포넌트만 콘솔 출력

  file_logging:
    enabled: true
    path: "logs"
    level: "DEBUG"
    max_size_mb: 10
    backup_count: 5

  advanced:
    performance_monitoring: false

runtime:
  watch_config_file: true
  notify_on_change: true
```

### **주요 기능**

- ✅ **console_output: auto** - 프로파일에 따라 자동 결정
- ✅ **component_focus** - 특정 컴포넌트만 콘솔 출력
- ✅ **실시간 변경** - 파일 수정 시 즉시 적용
- ✅ **파일 감시** - 설정 파일 변경 자동 감지

### **권장 사용법**

```yaml
# 일반 개발
console_output: "auto"
level: "INFO"

# 디버깅
console_output: true
component_focus: "문제컴포넌트"

# 운영환경
console_output: "auto"  # production 프로파일에서 자동 비활성화
level: "WARNING"
```

## 🚀 다른 기능 적용 가이드

### **매매 설정 예시**

```yaml
# config/trading_config.yaml
trading:
  paper_trading: true
  max_position_size_krw: 100000
  max_orders_per_minute: 10

  strategy:
    enabled: true
    auto_mode: "conservative"     # conservative/aggressive/auto

  risk_management:
    stop_loss_percentage: 5.0
    take_profit_percentage: 10.0

  advanced:
    performance_monitoring: true

runtime:
  watch_config_file: true
  notify_on_change: true
```

### **UI 설정 예시**

```yaml
# config/ui_config.yaml
ui:
  theme: "auto"                   # auto/light/dark
  auto_refresh_interval_seconds: 5

  chart:
    update_interval_seconds: 2
    max_candles: 500

  layout:
    save_window_state: true
    default_tab: "dashboard"

  advanced:
    debug_mode: false

runtime:
  watch_config_file: true
  notify_on_change: true
```

## 📋 구현 체크리스트

### **새 기능 설정 시스템 구현**

- [ ] config/{feature}_config.yaml 파일 생성
- [ ] {Feature}ConfigManager 클래스 구현
- [ ] 실시간 변경 핸들러 구현
- [ ] 파일 감시 시스템 연동
- [ ] 기본값/검증 로직 구현
- [ ] 테스트 코드 작성

### **통합 준비**

- [ ] 표준 패턴 준수 확인
- [ ] 설정 구조 문서화
- [ ] 하위 호환성 고려
- [ ] 마이그레이션 계획 수립

## 🔍 최종 목표 아키텍처

### **DB 통합 설계 (Phase 3)**

```sql
-- 설정 테이블
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,        -- 'logging', 'trading', 'ui'
    key TEXT NOT NULL,
    value TEXT NOT NULL,           -- JSON 형태
    profile TEXT DEFAULT 'default',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 프로파일 테이블
CREATE TABLE profiles (
    name TEXT PRIMARY KEY,
    description TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

-- 설정 히스토리
CREATE TABLE setting_history (
    id INTEGER PRIMARY KEY,
    setting_id INTEGER,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,
    changed_at TIMESTAMP
);
```

## 💡 개발 가이드라인

### **DO (권장사항)**

- ✅ 표준 YAML 구조 사용
- ✅ 실시간 변경 지원 구현
- ✅ 명확한 기본값 제공
- ✅ 타입 안전성 확보
- ✅ 설정 검증 로직 구현

### **DON'T (금지사항)**

- ❌ 하드코딩된 설정값 사용
- ❌ 환경변수에 의존
- ❌ 복잡한 중첩 구조
- ❌ 불완전한 기능 포함
- ❌ 표준 패턴 무시

## 📚 참고 자료

- **로깅 시스템**: `upbit_auto_trading/infrastructure/logging/`
- **설정 관리자**: `upbit_auto_trading/infrastructure/logging/config/logging_config_manager.py`
- **테스트 사례**: `test_final_console_control.py`

---

## 📞 문의 및 기여

이 설정 관리 시스템에 대한 질문이나 개선 제안이 있으시면:

1. 로깅 시스템의 구현 사례를 먼저 참고
2. 표준 패턴을 준수하여 구현
3. 테스트 코드와 함께 제출

**📌 중요**: 이 문서는 모든 설정 관리의 **단일 참조 표준**입니다.
다른 설정 관련 문서보다 이 문서를 우선 참조하세요.

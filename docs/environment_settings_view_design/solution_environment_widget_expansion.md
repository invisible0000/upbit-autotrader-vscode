# 환경변수 위젯 vs Config YAML 통합 방안

## 🎯 문제 정의
현재 환경변수 위젯은 Config YAML의 전체 구조를 포함할 수 없습니다.

## 💡 해결 방안

### Option 1: 환경변수 위젯 확장 (권장)
```
기존:                    확장 후:
┌─ 로깅 ✅               ┌─ 로깅 설정 ✅ (YAML + 환경변수)
├─ 거래 ❌               ├─ 데이터베이스 설정 🆕
├─ API ❌                ├─ API 설정 🆕 (YAML + 환경변수)
└─ 시스템 ❌             ├─ 매매 설정 🆕
                        ├─ Event Bus 설정 🆕
                        ├─ UI 설정 🆕
                        └─ 시스템 설정 🆕
```

#### 구현 방법:
1. **탭 재구성**: 7개 섹션에 맞춰 탭 재설계
2. **데이터 소스 통합**: YAML + 환경변수 + user_settings.json
3. **실시간 미리보기**: 변경 전후 비교
4. **프로파일별 관리**: Development/Testing/Production

### Option 2: 분리된 설정 관리
```
환경변수 위젯:  순수 환경변수 (UPBIT_*)
설정 위젯:     YAML 설정 관리
프로파일 위젯:  환경별 프로파일 관리
```

### Option 3: 통합 설정 대시보드
```
하나의 위젯에서 모든 설정 타입 통합:
- 환경변수 (UPBIT_*)
- Config YAML (7개 섹션)
- User Settings (커스터마이징)
- Environment Profiles (3개 환경)
```

## 🏗️ 권장 구현 (Option 1 확장)

### 새로운 탭 구조:
```python
class AdvancedEnvironmentVariablesWidget(QTabWidget):
    """확장된 환경변수 위젯"""

    def __init__(self):
        super().__init__()

        # 1. 로깅 설정 (기존 + YAML 통합)
        self.addTab(LoggingConfigurationTab(), "로깅")

        # 2. 데이터베이스 설정 (YAML)
        self.addTab(DatabaseConfigurationTab(), "데이터베이스")

        # 3. API 설정 (YAML + 환경변수)
        self.addTab(ApiConfigurationTab(), "API")

        # 4. 매매 설정 (YAML)
        self.addTab(TradingConfigurationTab(), "매매")

        # 5. Event Bus 설정 (YAML)
        self.addTab(EventBusConfigurationTab(), "Event Bus")

        # 6. UI 설정 (YAML + user_settings)
        self.addTab(UiConfigurationTab(), "UI")

        # 7. 시스템 설정 (환경변수 + YAML)
        self.addTab(SystemConfigurationTab(), "시스템")
```

### 각 탭의 데이터 소스:
```
로깅:      YAML logging + UPBIT_LOG_* 환경변수
데이터베이스: YAML database 섹션
API:       YAML upbit_api + UPBIT_ACCESS_KEY/SECRET_KEY
매매:      YAML trading 섹션
Event Bus: YAML event_bus 섹션
UI:        YAML ui + user_settings.json
시스템:    YAML app + OS 환경변수
```

## 🔄 데이터 흐름 설계

### 읽기:
```
1. Config YAML (기본값) 로드
2. Environment Override 적용
3. User Settings 적용
4. 환경변수 적용
5. UI에 통합 표시
```

### 쓰기:
```
1. UI에서 값 변경
2. 적절한 저장소 선택:
   - YAML 설정 → user_settings.json
   - 환경변수 → OS 환경변수 또는 .env 파일
3. 실시간 미리보기 제공
4. 프로파일별 저장
```

## 🎯 구현 우선순위

### Phase 1: 기반 확장
1. 기존 로깅 탭 YAML 통합
2. 데이터베이스 설정 탭 추가
3. API 설정 탭 추가

### Phase 2: 고급 기능
1. 매매 설정 탭 추가
2. Event Bus 설정 탭 추가
3. UI 설정 탭 추가

### Phase 3: 통합 완성
1. 시스템 설정 탭 완성
2. 프로파일 연동 완성
3. 실시간 미리보기 완성

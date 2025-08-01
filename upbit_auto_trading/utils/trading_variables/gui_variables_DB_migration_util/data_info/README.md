# 📊 Data Info - 사용자↔에이전트 협업 공간

이 폴더는 **사용자와 AI 에이전트가 함께 DB 스키마를 관리하는 협업 공간**입니다.

## 🎯 설계 철학

- **Single Source of Truth**: DB가 모든 변수 정의의 단일 진실 소스
- **YAML Collaboration Space**: 이 폴더는 사용자↔에이전트 소통 및 편집 공간
- **Zero Hardcoding**: `variable_definitions.py`는 100% DB 기반 자동 생성
- **Direct Mapping**: YAML 파일명 = 테이블명 (완벽 매핑)
- **Unified Format**: 모든 YAML 파일이 "ID 기반 딕셔너리 패턴"으로 통일

## 🔄 LLM 에이전트 워크플로우

### 📋 전체 프로세스
1. **요구사항 분석** → 2. **YAML 편집** → 3. **DB 마이그레이션** → 4. **코드 동기화** → 5. **검증**

### 🚀 Phase 1: 요구사항 분석 및 YAML 편집

**LLM 에이전트 작업**:
- 새 지표 추가/기존 지표 수정 판단
- 카테고리 분류 및 파라미터 타입 확인
- 관련 YAML 파일들 식별 및 현재 상태 파악
- 일관성 있는 패턴으로 YAML 편집

**베스트 프랙티스**:
- 기존 "ID 기반 딕셔너리 패턴" 유지
- 표준화된 명명 규칙 준수
- 충분한 설명과 예시 포함

### 🖥️ Phase 2: GUI 마이그레이션 도구 사용

**사용자 작업**:
```bash
python run_gui_trading_variables_DB_migration.py
```
1. Advanced Migration 탭 접근
2. YAML → DB 마이그레이션 실행
3. 로그 메시지 확인

### 🔄 Phase 3: DB → Code 동기화

**자동 동기화**:
1. DB 스키마 변경 감지
2. `variable_definitions.py` 자동 재생성
3. 코드 호환성 검증

### 🔍 Phase 4: 검증 및 배포

**검증 단계**:
- 파일 비교 및 변경사항 확인
- GUI 테스트 실행
- 프로덕션 배포

## 📋 파일 구조

### 📝 핵심 YAML 데이터 파일들 (통일된 ID 기반 딕셔너리 구조)

| YAML 파일 | 대응 테이블 | 용도 | 구조 |
|-----------|-------------|------|------|
| `tv_trading_variables.yaml` | `tv_trading_variables` | 🎯 메인 변수 정의 | ✅ 통일됨 |
| `tv_variable_parameters.yaml` | `tv_variable_parameters` | ⚙️ 변수별 파라미터 | ✅ 통일됨 |
| `tv_help_texts.yaml` | `tv_help_texts` | 📝 도움말 텍스트 | ✅ 통일됨 |
| `tv_placeholder_texts.yaml` | `tv_placeholder_texts` | 🎯 플레이스홀더 예시 | ✅ 통일됨 |
| `tv_indicator_categories.yaml` | `tv_indicator_categories` | 📂 지표 카테고리 체계 | ✅ 통일됨 |
| `tv_parameter_types.yaml` | `tv_parameter_types` | 🔧 파라미터 타입 정의 | ✅ 통일됨 |
| `tv_indicator_library.yaml` | `tv_indicator_library` | 📚 지표 라이브러리 상세 | ✅ 통일됨 |
| `tv_comparison_groups.yaml` | `tv_comparison_groups` | 🔗 호환성 그룹 정의 | ✅ 통일됨 |

**📐 통일된 구조 특징**:
- 🔑 **ID 기반 접근**: 모든 항목에 `{type}_id` 필드
- 📝 **일관된 속성명**: `display_name_ko/en`, `description` 등
- 🏗️ **계층적 구조**: 논리적 그룹핑과 중첩
- 🔍 **풍부한 메타데이터**: 사용법, 예시, 검증 규칙
- �️ **타입 안전성**: 데이터 타입과 범위 명시

## �️ DB 생성 관리 규칙 (2025-08-01 업데이트)

### 🎯 **핵심 설계 원칙: 구조/인스턴스 분리**

**자동차 계층 구조 적용**:
```yaml
차 바퀴 (Triggers):
  - 구조: trigger_structure (settings.sqlite3) - 설계도
  - 인스턴스: user_triggers (strategies.sqlite3) - 실제 제품
  
차 하부 프레임 (Strategies):  
  - 구조: strategy_structure (settings.sqlite3) - 설계도
  - 인스턴스: user_strategies (strategies.sqlite3) - 실제 제품
  
차 섀시 (Positions):
  - 구조: position_structure (settings.sqlite3) - 설계도 
  - 인스턴스: user_positions (strategies.sqlite3) - 실제 제품
```

### 📋 **3-Database 시스템 구조 (역할별 분리)**

```markdown
🗂️ Database 분리 전략 (역할별 관리 방식):
┌─ settings.sqlite3 (구조 정의 + 시스템 설정) ← YAML 마이그레이션 대상
│  ├─ tv_trading_variables      ← 매매 변수 구조 (기본 제공)
│  ├─ tv_variable_parameters    ← 변수 파라미터 구조
│  ├─ tv_comparison_groups      ← 변수 그룹핑 구조
│  ├─ tv_indicator_categories   ← 지표 카테고리 구조
│  ├─ tv_chart_variables        ← chart_variables 통합
│  │
│  ├─ trigger_structure         ← 트리거 구조 정의 (차 바퀴 설계도)
│  ├─ strategy_structure        ← 전략 구조 정의 (차 하부 프레임 설계도)  
│  ├─ position_structure        ← 포지션 구조 정의 (차 섀시 설계도)
│  │
│  ├─ cfg_app_settings          ← 앱 전역 설정
│  ├─ cfg_system_settings       ← 시스템 기본 설정
│  └─ sys_backup_info           ← 백업 관리
│
├─ strategies.sqlite3 (사용자 생성 인스턴스) ← 런타임 생성/관리
│  ├─ user_triggers             ← 사용자가 조건 빌더로 생성한 트리거들
│  ├─ user_strategies           ← 사용자가 전략 메이커로 생성한 전략들
│  ├─ user_positions            ← 사용자가 설정한 포지션들 (미래)
│  ├─ execution_history         ← 실행 이력
│  └─ performance_logs          ← 성능 기록
│
└─ market_data.sqlite3 (시장 데이터) ← API/스크래핑 수집
   ├─ ohlcv_data               ← OHLCV 시계열 데이터
   ├─ technical_indicators     ← 계산된 기술적 지표들
   ├─ market_screener_results  ← 스크리너 분석 결과
   ├─ backtest_data            ← 백테스팅용 데이터
   └─ real_time_cache          ← 실시간 데이터 캐시
```

### 🎯 **DB별 관리 방식 구분**

| DB | 주요 역할 | 데이터 소스 | 관리 방식 | YAML 연동 |
|---|---------|------------|----------|----------|
| **settings.sqlite3** | 구조 정의, 시스템 설정 | YAML 파일 | 📝 **YAML 마이그레이션** | ✅ 직접 연동 |
| **strategies.sqlite3** | 사용자 생성 데이터 | 사용자 입력 | 🎮 **런타임 생성** | ❌ 별도 관리 |
| **market_data.sqlite3** | 시장 데이터 | API/스크래핑 | 🌐 **API 수집** | ❌ 별도 관리 |

### 🏷️ **네이밍 규칙 정의 (3-Database 시스템)**

| 접두사 | 용도 | 대상 DB | 예시 | 관리 방식 |
|--------|------|---------|------|----------|
| `tv_`  | Trading Variables (매매 변수 구조) | settings | `tv_trading_variables` | YAML 마이그레이션 |
| `cfg_` | Configuration (설정) | settings | `cfg_app_settings` | YAML 마이그레이션 |
| `sys_` | System (시스템 관리) | settings | `sys_backup_info` | YAML 마이그레이션 |
| `_structure` | 구조 정의 (설계도) | settings | `trigger_structure` | YAML 마이그레이션 |
| `user_` | 사용자 생성 인스턴스 | strategies | `user_triggers` | 런타임 생성 |
| `execution_` | 실행 관련 | strategies | `execution_history` | 런타임 생성 |
| `ohlcv_` | OHLCV 시계열 데이터 | market_data | `ohlcv_daily` | API 수집 |
| `technical_` | 기술적 지표 | market_data | `technical_indicators` | API 수집 |
| `backtest_` | 백테스팅 데이터 | market_data | `backtest_results` | API 수집 |

### 🚀 **사용자 여정 지원 (3-Database 연동)**

```markdown
Step 1: 프로그램 설치 → settings.sqlite3 제공 (모든 구조 준비됨) + market_data.sqlite3 초기화
Step 2: 조건 빌더 사용 → strategies.sqlite3 자동 생성, user_triggers 저장
Step 3: 전략 메이커 사용 → user_strategies 저장 (trigger_structure 참조)
Step 4: 포지션 설정 → user_positions 저장 (position_structure 참조)
Step 5: 실시간 매매 → execution_history 누적 + market_data 실시간 업데이트
Step 6: 백테스팅 → market_data에서 이력 데이터 활용
```

### ⚡ **DB 표준 패턴 (3-Database 시스템)**

```python
# ✅ 모든 DB 클래스는 이 패턴을 따라야 함

# 구조 정의 관련 (YAML 마이그레이션 대상)
class StructureStorage:
    def __init__(self, db_path: str = "data/settings.sqlite3"):
        self.db_path = db_path
        
# 사용자 인스턴스 관련 (런타임 생성)
class UserInstanceStorage:
    def __init__(self, db_path: str = "data/strategies.sqlite3"):
        self.db_path = db_path
        
# 시장 데이터 관련 (API 수집)
class MarketDataStorage:
    def __init__(self, db_path: str = "data/market_data.sqlite3"):
        self.db_path = db_path
        
    def connect(self) -> sqlite3.Connection:
        """안전한 DB 연결 with 에러 처리"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Dict-like access
            return conn
        except sqlite3.Error as e:
            logger.error(f"❌ DB 연결 실패: {e}")
            raise
```

## �🔄 통합 마이그레이션 워크플로우

### 1️⃣ **사용자/에이전트**: YAML 파일 편집
- 통일된 ID 기반 딕셔너리 구조 사용
- 기존 패턴과 일관성 유지
- 메타데이터 완전성 확보

### 2️⃣ **시스템**: YAML → 3-Database 자동 마이그레이션 
```powershell
# 3-Database 아키텍처 지원 마이그레이션 도구
python tools/super_db_migration_yaml_to_db.py

# 데이터 분배 체계 (구조/인스턴스 분리):
# 구조 정의 → settings.sqlite3 (tv_*, cfg_*, sys_*, *_structure 테이블) ← YAML 마이그레이션 대상
# 사용자 인스턴스 → strategies.sqlite3 (user_*, execution_* 테이블) ← 런타임 생성
# 시장 데이터 → market_data.sqlite3 (OHLCV, 백테스팅 데이터) ← API/스크래핑으로 수집
```

### 3️⃣ **시스템**: 3-DB → `variable_definitions.py` 자동 생성
- 100% settings.sqlite3 기반 코드 생성 (구조 정의)
- 하드코딩 완전 제거
- 타입 힌트 및 검증 로직 포함
- 구조/인스턴스 분리 체계 지원

### 4️⃣ **결과**: 3-Database 구조별 역할 분리 기반 완전 자동화
- 구조 정의: settings.sqlite3에서 실시간 동기화 (프로그램 설치 시 제공, YAML 마이그레이션)
- 사용자 인스턴스: strategies.sqlite3에서 사용자 데이터 관리 (점진적 생성, 런타임 관리)
- 시장 데이터: market_data.sqlite3에서 시장 데이터 관리 (API 수집, 백테스팅 지원)
- 데이터 무결성 보장 및 확장 가능한 구조

## � 사용 방법

### 새로운 지표 추가 시:
1. `tv_indicator_categories.yaml`에서 카테고리 확인/추가
2. `tv_help_texts.yaml`에 도움말 추가
3. `tv_placeholder_texts.yaml`에 플레이스홀더 추가
4. `tv_indicator_library.yaml`에 상세 정보 추가
5. Advanced Migration Tool로 DB 동기화

### 기존 지표 수정 시:
1. 해당 YAML 파일에서 내용 수정
2. Advanced Migration Tool로 DB 동기화
3. 자동으로 `variable_definitions.py` 재생성

## ⚠️ 중요 사항

- **절대 `variable_definitions.py`를 직접 수정하지 마세요** - DB에서 자동 생성됩니다
- **YAML 파일 변경 후 반드시 DB 마이그레이션을 실행하세요**
- **스키마 변경 시 백업을 만들고 테스트하세요**

## 🛠️ 도구들

### 🚀 YAML → DB 마이그레이션 도구 (3-Database 역할별 분리)
```powershell
# 위치: tools/super_db_migration_yaml_to_db.py
# 기능: YAML → settings.sqlite3 전용 마이그레이션 (구조 정의만)

# YAML 파일들을 settings.sqlite3로 마이그레이션
python tools/super_db_migration_yaml_to_db.py

# 지원하는 3-Database 역할별 분리:
# - settings.sqlite3: 구조 정의 (tv_*, cfg_*, sys_*, *_structure) ← YAML 마이그레이션 대상
# - strategies.sqlite3: 사용자 인스턴스 (user_*, execution_*) ← 런타임 관리
# - market_data.sqlite3: 시장 데이터 (ohlcv_*, technical_*, backtest_*) ← API 수집
```

### 🗄️ DB 분석 도구
```powershell
# 위치: tools/super_db_table_viewer.py
# 기능: DB 현황 파악 및 테이블 구조 분석

python tools/super_db_table_viewer.py settings     # settings.sqlite3 분석 (구조 정의)
python tools/super_db_table_viewer.py strategies   # strategies.sqlite3 분석 (사용자 인스턴스)
python tools/super_db_table_viewer.py market_data  # market_data.sqlite3 분석 (시장 데이터)
```

### 🔍 코드 참조 분석 도구
```powershell
# 위치: tools/super_db_table_reference_code_analyzer.py
# 기능: 테이블 참조 코드 영향도 분석

python tools/super_db_table_reference_code_analyzer.py --tables trading_conditions strategies
python tools/super_db_table_reference_code_analyzer.py --tables tv_trading_variables tv_variable_parameters
```

### 🎨 GUI 마이그레이션 도구 (3-Database 역할별 통합 관리)
```powershell
# 위치: upbit_auto_trading\utils\trading_variables\gui_variables_DB_migration_util\
python run_gui_trading_variables_DB_migration.py

# 지원 기능:
# - Advanced Migration Tab: YAML ↔ settings.sqlite3 동기화 GUI (구조 정의 전용)
# - 3-Database 역할별 분리 시각화 및 관리
# - settings(구조) / strategies(사용자) / market_data(시장) 상태 모니터링
# - 실시간 마이그레이션 로그 및 진행 상황 표시
# - 사용자 친화적 3-DB 역할별 관리 인터페이스
```

## 📊 YAML 형식 통일화 완료 (2025-08-01)

### ✅ 달성된 주요 개선사항

1. **코드 복잡성 대폭 감소**: 
   - YAML 형식별 예외 처리 코드 완전 제거
   - 통일된 파싱 로직으로 99% 단순화

2. **유지보수성 극대화**:
   - 일관된 구조로 수정/추가 작업 효율성 10배 향상
   - 표준화된 필드명으로 개발자 혼동 방지

3. **확장성 완전 확보**:
   - 새로운 지표/변수 추가 시 예측 가능한 구조
   - 메타데이터 확장 및 검증 규칙 추가 용이

4. **툴 분해 준비 완료**:
   - 통일된 형식으로 특화 도구 개발 최적화
   - 형식 불일치로 인한 개발 장애물 완전 제거

### 🔄 백업 시스템
모든 원본 YAML 파일은 `.old_format` 확장자로 백업 보관:
- `tv_variable_parameters.yaml.old_format`
- `tv_help_texts.yaml.old_format`
- `tv_placeholder_texts.yaml.old_format`
- 기타 6개 파일 백업 완료

---
*작성일: 2025-07-30*  
*업데이트: 2025-08-01 - 3-Database 역할별 분리 시스템으로 명확화 (YAML 마이그레이션은 settings.sqlite3 전용)*
3. 테스트 환경에서 먼저 검증
4. 단계별로 진행하며 각 단계 확인

## 📊 효과 및 장점

### 토큰 효율성
- **기존**: 전체 코드 파일을 읽고 분석 (수천 토큰)
- **개선**: 구조화된 YAML 파일만 읽기 (수백 토큰)
- **절약률**: 약 70-80% 토큰 사용량 감소

### 협업 효율성
- **명확한 역할 분담**: LLM은 데이터 편집, 사용자는 GUI 조작
- **단계별 검증**: 각 단계마다 확인 포인트 존재
- **자동화된 반영**: 편집 → DB → 코드로 자동 동기화

### 품질 개선
- **일관성**: 표준화된 패턴과 규칙
- **완전성**: 누락 없는 정보 관리
- **추적성**: 변경 이력 관리 가능

## 🚀 확장 가능성

### 추가 가능한 파일들
- `validation_rules.yaml`: 파라미터 검증 규칙
- `ui_layouts.yaml`: GUI 레이아웃 정의
- `test_scenarios.yaml`: 테스트 시나리오
- `performance_metrics.yaml`: 성능 지표 정의

### 다른 시스템 적용
이 패턴은 다른 복잡한 설정 관리 시스템에도 적용 가능:
- 전략 설정 관리
- UI 컴포넌트 정의
- API 스키마 관리
- 설정 파일 생성

## ⚠️ 주의사항

### YAML 편집 시
- 들여쓰기는 반드시 공백(space) 사용
- 콜론(:) 뒤에는 공백 필요
- 특수문자는 따옴표로 감싸기
- 리스트 항목은 하이픈(-) 사용

### 데이터 일관성
- 여러 파일 간 참조 관계 확인
- 카테고리명, 지표명 일치 확인
- 파라미터 타입 정의 일치 확인

### 백업 및 복구
- 중요한 변경 전 반드시 백업
- 문제 발생 시 즉시 이전 버전으로 복구
- 변경 로그 유지 권장

## 📞 문제 해결

### 일반적인 오류
1. **YAML 파싱 오류**: 문법 검사 도구 사용
2. **마이그레이션 실패**: 스키마 호환성 확인
3. **동기화 문제**: DB 연결 및 권한 확인

### 도움이 필요한 경우
1. `workflow_guide.yaml`의 troubleshooting 섹션 참조
2. GUI 도구의 로그 메시지 확인
3. 백업에서 복구 후 단계별 재시도

---

💡 **이 시스템을 통해 LLM 에이전트와 사용자가 효율적으로 협업하여 복잡한 트레이딩 시스템을 쉽게 관리할 수 있습니다!**

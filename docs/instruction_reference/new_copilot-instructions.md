# 🤖 LLM 에이전트 개발 지침 (토큰 최적화 버전)

## 🎯 절대 원칙 (Golden Rules)

### 1. 기본 7규칙 전략 검증 (최우선)
**모든 개발은 기본 7규칙 전략 완전 구현을 목표로 합니다.**
- RSI 과매도 진입, 수익시 불타기, 계획된 익절, 트레일링 스탑, 하락시 물타기, 급락 감지, 급등 감지

### 2. PowerShell 전용 (Windows 환경)
```powershell
# ✅ 필수 사용
cmd1; cmd2                    # 명령어 연결
Get-ChildItem                 # 디렉토리 목록
$env:VAR = "value"           # 환경 변수

cmd1 && cmd2
ls -la
export VAR=value
```

### 3. 3-DB 아키텍처 (절대 변경 금지)
- `data/settings.sqlite3`: 변수 정의, 파라미터
- `data/strategies.sqlite3`: 사용자 전략, 백테스팅 결과
- `data/market_data.sqlite3`: 시장 데이터, 지표 캐시

### 4. Infrastructure 스마트 로깅 v4.0 (필수 사용)
```python
# v4.0 Enhanced Logging (권장)
from upbit_auto_trading.infrastructure.logging import get_enhanced_logging_service
logging_service = get_enhanced_logging_service()
logger = logging_service.get_logger("ComponentName")

# 환경변수 제어
$env:UPBIT_LLM_BRIEFING_ENABLED='true'     # 자동 LLM 브리핑
$env:UPBIT_AUTO_DIAGNOSIS='true'           # 자동 문제 감지
$env:UPBIT_CONSOLE_OUTPUT='true'           # 실시간 출력
```

### 5. 폴백 코드 금지 (에러 투명성)
```python
# ❌ 금지: 에러 숨김
try:
    from some_module import SomeClass
except ImportError:
    class SomeClass: pass  # 폴백으로 에러 숨김

# ✅ 필수: 에러 즉시 노출
from some_module import SomeClass  # 실패 시 즉시 ModuleNotFoundError
```

## 🔧 필수 검증 절차

### 모든 작업 완료 후
```powershell
# 핵심 검증: 메인 UI 실행
python run_desktop_ui.py

# 7규칙 전략 테스트
# → 전략 관리 → 트리거 빌더에서 7규칙 구성 가능해야 함
```

### 개발 중 실시간 확인
- Infrastructure 로깅 시스템이 모든 에러를 즉시 기록
- LLM 브리핑 파일 `logs/llm_briefing_*.md` 자동 생성
- JSON 대시보드 `logs/dashboard_data.json` 실시간 업데이트

## 💡 빠른 참조

- **의심스러우면**: CORE_ARCHITECTURE.md의 프로젝트 명세 확인
- **UI 작업 시**: UI_THEME_SYSTEM.md의 테마 시스템 준수
- **전략 개발 시**: OPERATIONAL_SYSTEM.md의 전략 시스템 활용
- **에러 발생 시**: Infrastructure 로깅 출력 확인

**모든 개발 작업은 다음 3개 통합 문서를 기준으로 합니다:**

1. **[🏗️ 핵심 아키텍처](../docs/instruction_reference/CORE_ARCHITECTURE.md)**
   - 시스템 아키텍처, DDD 설계, 개발 표준, 에러 처리, DB 스키마
   - 301줄, 모든 시스템 구조의 기준
   - **참조 컨텍스트**: `DDD 4계층, 3-DB구조, 에러투명성, 개발체크리스트, DB스키마`

2. **[🎨 UI 테마 시스템](../docs/instruction_reference/UI_THEME_SYSTEM.md)**
   - PyQt6 UI 개발, QSS 테마 시스템, 트리거 빌더, 호환성 시스템
   - 278줄, 모든 UI 개발의 기준
   - **참조 컨텍스트**: `PyQt6 UI, QSS테마, 트리거빌더, 변수호환성, 차트시스템`

3. **[🚀 운영 시스템](../docs/instruction_reference/OPERATIONAL_SYSTEM.md)**
   - 전략 시스템, 로깅 v4.0, 7규칙 전략, 기여 가이드, LLM 최적화
   - 412줄, 모든 운영/전략의 기준
   - **참조 컨텍스트**: `6진입+6관리전략, 로깅v4.0, 7규칙검증, 기여가이드, LLM최적화`
---

**🎯 성공 기준**: 기본 7규칙 전략이 완벽하게 동작하는 시스템!

# 🤝 기여 가이드

## 🚀 빠른 시작

### 환경 설정
```powershell
# 1. 저장소 포크 후 클론
git clone <your-forked-repository-url>
cd upbit-autotrader-vscode

# 2. 가상환경 설정 (Windows)
python -m venv venv
venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt
```

### 개발 검증
```powershell
# 핵심 검증: 기본 7규칙 전략이 완전히 작동해야 함
python run_desktop_ui.py
# → 전략 관리 → 트리거 빌더에서 7규칙 전략 구성 가능한지 확인
```

## 📋 브랜치 전략

- `master`: 안정적인 릴리스 버전
- `feature/*`: 새로운 기능 개발
- `bugfix/*`: 버그 수정

### 기여 워크플로
```bash
# 1. 기능 브랜치 생성
git checkout -b feature/your-feature-name

# 2. 개발 및 커밋
git add .
git commit -m "feat: 기능 구현 설명"

# 3. 푸시 및 PR 생성
git push origin feature/your-feature-name
```

## ✅ 커밋 컨벤션

```
<type>: <subject>

<body>

<footer>
```

### Type 분류
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 코드 리팩토링
- `test`: 테스트 코드 추가/수정
- `chore`: 빌드/설정 변경

### 예시
```
feat: RSI 과매도 진입 전략 구현

- 기본 7규칙 전략의 첫 번째 규칙 구현
- RSI 20 이하 진입 로직 추가
- UI 파라미터 설정 인터페이스 완성

Closes #42
```

## 🎯 개발 원칙

### 필수 검증 기준
**모든 변경사항은 [기본 7규칙 전략](basic_7_rule_strategy_guide.md) 수행 가능해야 함**

1. RSI 과매도 진입 (ENTRY)
2. 수익 시 불타기 (SCALE_IN)
3. 계획된 익절 (EXIT)
4. 트레일링 스탑 (EXIT)
5. 하락 시 물타기 (SCALE_IN)
6. 급락 감지 (RISK_MGMT)
7. 급등 감지 (MANAGEMENT)

### 코딩 표준
- **PEP 8 준수**: 79자 제한, 타입 힌트 필수
- **테스트 필수**: 신규 기능은 단위테스트 작성
- **문서화**: 복잡한 로직은 주석 필수

### 데이터베이스 작업
- **스키마 변경**: `data_info/*.sql` 파일 수정
- **변수 정의**: `data_info/*.yaml` 파일 수정  
- **DB 파일**: `data/*.sqlite3` (Git 추적 안함)

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 테스트 커버리지 확인
pytest --cov=upbit_auto_trading

# 특정 모듈 테스트
pytest tests/test_trigger_builder.py -v
```

## 📝 Pull Request 가이드

### PR 생성 시 포함 사항
1. **목적**: 해결하는 문제와 구현한 기능
2. **검증**: 기본 7규칙 전략 테스트 결과
3. **스크린샷**: UI 변경 시 Before/After
4. **이슈 링크**: 관련 이슈 번호

### PR 템플릿
```markdown
## 변경 사항
- [ ] RSI 진입 전략 구현
- [ ] 트리거 빌더 UI 업데이트

## 테스트 결과
- [ ] 기본 7규칙 전략 구성 가능
- [ ] 백테스팅 정상 동작
- [ ] UI 응답성 정상

## 스크린샷
(UI 변경 시 첨부)

Closes #42
```

## 📚 주요 문서

개발 전 반드시 확인할 문서들:
- [프로젝트 명세서](PROJECT_SPECIFICATIONS.md)
- [아키텍처 개요](ARCHITECTURE_OVERVIEW.md) 
- [개발 가이드](DEVELOPMENT_GUIDE_COMPACT.md)
- [기본 7규칙 전략](basic_7_rule_strategy_guide.md)

## 📞 도움 요청

- **이슈 생성**: 버그 리포트나 기능 요청
- **토론**: 설계 관련 의견 교환
- **문서**: 개발 가이드 숙지 후 질문

---
**💡 참고**: 모든 기여는 MIT 라이선스 하에 배포됩니다.
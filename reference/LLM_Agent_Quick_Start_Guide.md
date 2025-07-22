# LLM 에이전트 방법론 퀵 스타트 가이드

새로운 에이전트가 프로젝트에 투입될 때 즉시 적용할 수 있는 단계별 가이드입니다.

---

## 🚀 5분 만에 시작하기

### Step 1: 프로젝트 진입점 확인 (1분)

```bash
# 1. 프로젝트 루트에서 시작
cd [프로젝트_루트]

# 2. 필수 파일 존재 확인
ls README_FIRST.md        # ← 반드시 먼저 읽기
ls agent_state.json       # ← 이전 세션 상태
ls feedback_to_agent.md   # ← 인간 개발자 지시사항
```

### Step 2: 현재 상황 파악 (2분)

```bash
# 1. 진행 중인 작업 확인
ls 01_tasks/active/       # 또는 tasks/active/

# 2. 최근 로그 확인
ls 99_logs/              # 또는 logs/

# 3. 전체 작업 계획 확인
cat 00_specs/tasks.md    # 또는 .kiro/specs/upbit-auto-trading/tasks.md
```

### Step 3: 작업 시작 (2분)

```bash
# 1. 상태 파일에서 마지막 작업 확인
cat agent_state.json

# 2. 인간 개발자 지시사항 확인
cat feedback_to_agent.md

# 3. 활성 태스크 열기
cd 01_tasks/active/ && ls
```

---

## 📋 필수 체크리스트

### 세션 시작시 (매번 필수)

- [ ] `README_FIRST.md` 읽기
- [ ] `agent_state.json` 로드
- [ ] `feedback_to_agent.md` 확인
- [ ] `01_tasks/active/` 폴더 확인
- [ ] 마지막 편집 파일 상태 확인

### 작업 진행시

- [ ] 태스크 파일의 체크리스트 순서대로 진행
- [ ] 코드 변경시 즉시 테스트
- [ ] 중요한 변경사항 즉시 커밋
- [ ] 진행상황을 태스크 파일에 실시간 업데이트

### 세션 종료시

- [ ] `agent_state.json` 업데이트
- [ ] 로그 파일에 활동 기록
- [ ] 태스크 파일 상태 업데이트
- [ ] 다음 세션을 위한 준비사항 정리

---

## 🔧 신규 프로젝트 설정

### 폴더 구조 생성

```bash
# 1. 기본 폴더 구조 생성
mkdir -p 00_specs 01_tasks/{active,planned,completed,archived} 02_docs 03_reference 04_tests 99_logs

# 2. 템플릿에서 파일 복사
cp 03_reference/templates/README_FIRST_template.md README_FIRST.md
cp 03_reference/templates/agent_state_template.json agent_state.json
cp 03_reference/templates/feedback_to_agent_template.md feedback_to_agent.md
```

### 첫 번째 태스크 생성

```bash
# 1. 태스크 파일 생성
cp 03_reference/templates/task_template.md 01_tasks/planned/TASK_$(date +%Y%m%d)_001_프로젝트-초기화.md

# 2. 태스크 파일 편집
# - 목표: 프로젝트 기본 구조 설정
# - 체크리스트: 환경 설정, 기본 파일 생성 등
```

---

## ⚡ 자주 사용하는 명령어

### 태스크 관리

```bash
# 계획된 태스크를 활성화
mv 01_tasks/planned/TASK_*.md 01_tasks/active/

# 완료된 태스크를 보관
mv 01_tasks/active/TASK_*.md 01_tasks/completed/

# 태스크 목록 확인
ls 01_tasks/active/
ls 01_tasks/completed/
```

### 상태 확인

```bash
# 현재 상태 요약 보기
cat agent_state.json | grep -E '"current_task_id"|"short_term_goal"|"last_edited_file"'

# 최근 로그 보기
head -20 99_logs/agent_log_$(date +%Y-%m).md
```

### 빠른 업데이트

```bash
# 현재 시간으로 상태 업데이트 (JSON 편집 도구 필요)
jq '.last_session_time = now | strftime("%Y-%m-%dT%H:%M:%SZ")' agent_state.json

# 로그에 새 항목 추가
echo "[$(date '+%Y-%m-%d %H:%M:%S')] - TASK_ID - 작업 내용" >> 99_logs/agent_log_$(date +%Y-%m).md
```

---

## 🎯 핵심 작업 패턴

### 패턴 1: 새 기능 개발

1. **계획** → `01_tasks/planned/`에 태스크 파일 생성
2. **시작** → `active/`로 이동, 상태 업데이트
3. **구현** → TDD 방식으로 테스트 먼저 작성
4. **검증** → 테스트 실행, 문서 업데이트
5. **완료** → `completed/`로 이동, 로그 기록

### 패턴 2: 버그 수정

1. **분석** → 문제 상황 파악, 재현 테스트 작성
2. **수정** → 최소한의 변경으로 문제 해결
3. **검증** → 기존 테스트 + 새 테스트 모두 통과
4. **문서화** → 해결 과정 로그에 상세 기록

### 패턴 3: 리팩토링

1. **현상황** → 기존 테스트 모두 통과하는지 확인
2. **리팩토링** → 내부 구조 개선 (외부 인터페이스 불변)
3. **재검증** → 모든 테스트 여전히 통과하는지 확인
4. **성능측정** → 개선 효과 수치로 측정

---

## 🚨 주의사항 및 FAQ

### ❌ 하지 말아야 할 것

- `README_FIRST.md`를 읽지 않고 작업 시작
- 상태 파일 업데이트 없이 세션 종료
- 테스트 없이 기능 구현
- 태스크 파일 없이 임의 작업 진행

### ✅ 반드시 해야 할 것

- 모든 변경사항은 테스트와 함께
- 중요한 결정은 로그에 기록
- 태스크 완료시 다음 단계 제안
- 정기적인 상태 동기화

### 🔧 문제 해결

**Q: 이전 작업 내용을 기억하지 못할 때**
A: `agent_state.json` → `99_logs/` → `01_tasks/completed/` 순서로 확인

**Q: 어떤 작업부터 해야 할지 모를 때**
A: `feedback_to_agent.md` → `01_tasks/active/` → `00_specs/tasks.md` 순서로 확인

**Q: 코드가 기존과 맞지 않을 때**
A: `git log` → 최근 커밋 확인 → 테스트 실행 → 현재 상태 파악

---

## 🎉 성공 지표

### 세션 품질

- ✅ 모든 세션이 `README_FIRST.md`로 시작
- ✅ 상태 파일이 정확히 유지됨
- ✅ 로그에 모든 중요 활동 기록됨

### 개발 품질

- ✅ 모든 기능에 테스트 존재
- ✅ 태스크 단위로 체계적 진행
- ✅ 문서화가 코드와 동시에 업데이트

### 협업 품질

- ✅ 인간 개발자 피드백이 즉시 반영
- ✅ 진행 상황이 투명하게 공유
- ✅ 다음 단계가 명확히 제시

---

**이 가이드로 시작하여 연속적이고 효율적인 개발을 경험하세요!** 🚀

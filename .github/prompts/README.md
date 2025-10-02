# 📋 VS Code Prompt Files 사용 가이드

## 🎯 개요

업비트 자동매매 프로젝트를 위한 재사용 가능한 Copilot Chat 프롬프트 파일들입니다.

## ⚙️ 설정 확인

`.vscode/settings.json`에서 다음 설정이 활성화되어 있는지 확인:

```json
{
    "chat.promptFiles": true,
    "github.copilot.chat.codeGeneration.useInstructionFiles": true
}
```

## 📁 사용 가능한 프롬프트들

### 🚀 태스크 관리

#### 1. `quick-task.prompt.md` - ⚡ 빠른 태스크 등록

**사용법**: Chat에서 📎 → Prompt... → quick-task 선택 후

```
"UI 설정 화면 MVP 구조 정리" 태스크를 urgent로 등록해 주세요.
문제: Presenter가 잘못된 위치에 있음
목표: 올바른 MVP 구조로 이동
```

#### 2. `upbit-task-register.prompt.md` - 📋 상세 태스크 등록

**사용법**: Chat에서 📎 → Prompt... → upbit-task-register 선택 후

```
새 태스크를 등록하고 싶습니다.
```

→ 단계별 질문을 통해 완전한 태스크 문서 생성

#### 3. `task-completion.prompt.md` - 🎉 완료 보고서 생성

**사용법**: Chat에서 📎 → Prompt... → task-completion 선택 후

```
TASK_20250930_01-correct_container_usage.md 완료 보고서를 생성해 주세요.
```

### 🏗️ 아키텍처 & 개발

#### 4. `ddd-mvp-architecture.prompt.md` - 🏗️ DDD + MVP 구현

**사용법**: Chat에서 📎 → Prompt... → ddd-mvp-architecture 선택 후

```
DatabaseSettingsComponent를 DDD + MVP 패턴으로 구현해 주세요.
```

## 💡 사용 팁

### 기본 사용 방법

1. **Copilot Chat 열기** (Ctrl+Alt+I 또는 사이드바 아이콘)
2. **Attach context 클릭** (📎 아이콘)
3. **Prompt... 선택**
4. **원하는 프롬프트 파일 선택**
5. **추가 컨텍스트 입력** (필요한 경우)
6. **Submit** (Enter)

### 고급 활용법

#### 파일과 함께 사용

```
📎 → Prompt... → quick-task 선택
📎 → Files → 관련 파일들 추가
추가 요청사항 입력
```

#### 여러 프롬프트 조합

```
📎 → Prompt... → ddd-mvp-architecture 선택
📎 → Prompt... → quick-task 선택
특정 컴포넌트에 대한 구현과 태스크 등록을 동시에
```

### 프로젝트 특화 활용

#### MVP 구조 정리 작업

```
Prompt: ddd-mvp-architecture
Input: "현재 잘못된 위치의 Presenter들을 올바른 MVP 구조로 이동"
```

#### 긴급 버그 수정

```
Prompt: quick-task
Input: "설정 화면 진입 불가 버그 수정 태스크 urgent로 등록"
```

#### 완료 작업 정리

```
Prompt: task-completion
Input: "방금 완료한 Container 사용법 수정 작업 보고서 생성"
```

## 📊 프롬프트 파일 구조

### 표준 형식

```markdown
# [프롬프트 제목]

#file:../../[관련파일경로]  # 컨텍스트 파일 자동 로드

[프롬프트 설명 및 사용법]

## [섹션들]
[구체적인 지침들]
```

### 컨텍스트 파일 참조

- `#file:../../tasks/README.md` - 태스크 관리 규칙 자동 로드
- `#file:../../.github/copilot-instructions.md` - 프로젝트 지침 자동 로드

## 🎯 실제 사용 예시

### 시나리오 1: 새 기능 개발

```
1. ddd-mvp-architecture → 아키텍처 설계
2. quick-task → 개발 태스크 등록
3. [개발 진행]
4. task-completion → 완료 보고서
```

### 시나리오 2: 버그 수정

```
1. quick-task → 버그 수정 태스크 등록 (urgent)
2. [수정 작업]
3. task-completion → 수정 완료 보고서
```

### 시나리오 3: 리팩터링

```
1. ddd-mvp-architecture → 리팩터링 계획
2. upbit-task-register → 상세 리팩터링 태스크 등록
3. [리팩터링 진행]
4. task-completion → 리팩터링 완료 보고서
```

## 🚀 다음 단계

### 추가 프롬프트 개발 가능

- `code-review.prompt.md` - 코드 리뷰 요청
- `testing.prompt.md` - 테스트 케이스 생성
- `documentation.prompt.md` - 문서화 자동 생성
- `troubleshooting.prompt.md` - 문제 해결 가이드

### 팀 공유

프롬프트 파일들은 Git으로 관리되므로 팀 전체가 동일한 품질의 프롬프트를 사용할 수 있습니다.

---

**VS Code Prompt Files로 일관되고 효율적인 개발 워크플로우를 구축하세요!** 🚀

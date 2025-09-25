# 인코딩/공백 이슈 트러블 슈팅 가이드

## 1. 최근 작업 사례 요약
- **UTF-16 저장 문제**: PowerShell `Set-Content` 기본 인코딩을 그대로 썼다가 UTF-16 파일이 생성되어 Python 파싱이 실패했고, 이후 `-Encoding utf8` 또는 단일 따옴표 here-string으로 강제 UTF-8로 저장해 해결했습니다.
- **패턴 치환 기반 스크립트의 부작용**: 대형 `re.sub` 스크립트가 기존 공백과 주석을 정확히 매치하지 못해 반복 실패하거나 예기치 않은 위치에 빈 줄을 추가했습니다. 라인 단위 블록 편집으로 전환하면서 문제를 해소했습니다.
- **제어 문자 혼입**: 자동 치환 스크립트 실행 후 `\x01` 제어 문자가 남아 공백이 크게 보였고, 재가공 스크립트로 해당 문자를 제거했습니다.
- **라인 엔딩 재변환 중복**: 텍스트를 `text.replace('\n', '\r\n')`로 변환하기 전에 `\r\n`을 `\n`으로 정규화하지 않으면 `\r\r\n`이 되어 화면상 빈 줄이 2배 이상 늘어날 수 있습니다.

## 2. 다른 에이전트에서 자주 목격한 패턴
| 증상 | 추정 원인 | 확인 방법 | 대응 |
| --- | --- | --- | --- |
| 줄마다 5~8개의 빈 줄 | `\r\n`이 포함된 텍스트에 다시 `\n→\r\n` 변환 적용 | `python - <<'PY'`로 `repr(line)` 확인 | 저장 전 `text = text.replace('\r\n', '\n')` 수행 후 최종 변환 |
| 코드 앞뒤로 BOM 삽입 | UTF-8-BOM 또는 UTF-16 상태에서 다시 UTF-8 저장 | `Get-Content -Encoding Byte`로 헤더 확인 | `-Encoding utf8` 지정, 또는 `Path.write_text(..., encoding='utf-8')` 사용 |
| 특정 줄만 공백 2~3배 | 정규식 치환 시 캡처 그룹을 놓쳐 `\n\n` 삽입 | `git diff`로 영향 범위 확인 | 치환 전에 테스트, `re.sub(..., count=1)` + 실패 시 경고 |
| 전체 파일이 탭-스페이스 혼합 | 자동 포매터 미적용, 에디터 기본 탭 사용 | `python -m tabnanny` 또는 `rg '\t'` | `.editorconfig` 준수, 저장 전 `expandtabs` |

## 3. 진단 체크리스트
1. `git diff --word-diff`로 실제 변경 줄의 공백 변화를 확인합니다.
2. `python - <<'PY'`로 특정 줄의 바이트 시퀀스를 직접 출력해 제어 문자를 점검합니다.
3. `python -m compileall ...` 또는 `python -m py_compile ...`으로 구문 오류가 없는지 즉시 검증합니다.
4. Windows 환경에서는 `Get-Content -Encoding Byte path | Select-Object -First 4`로 BOM을 확인합니다.

## 4. 예방 가이드라인
- **쓰기 전 정규화**: `text = text.replace('\r\n', '\n')`로 정규화 → 편집 → 저장 직전에 필요한 경우만 `replace('\n', '\r\n')` 적용.
- **인코딩 명시**: PowerShell `Set-Content`/`Out-File` 사용 시 `-Encoding utf8`을 필수로 지정하고, Python에서는 `path.write_text(..., encoding='utf-8', newline='\n')` 형태를 사용합니다.
- **점진적 편집**: 대규모 `re.sub` 대신 블록 단위 삽입/교체 로직을 사용해 예상치 못한 공백 삽입을 줄입니다.
- **미세 검증**: 수정 직후 `rg "\s+$"`와 같은 명령으로 불필요한 공백을 검색하고, IDE 포맷터에 의존하지 않는 수동 검증을 병행합니다.

## 5. 참고 스니펫
```powershell
# PowerShell에서 안전한 UTF-8 쓰기 예시
Set-Content -Path $path -Value $content -Encoding utf8
```
```python
from pathlib import Path
text = Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")
# ... 편집 로직 ...
Path(path).write_text(text, encoding="utf-8", newline="\n")
```

## 6. 향후 제안
- 공통 스크립트 템플릿을 저장하여 모든 에이전트가 동일한 읽기/쓰기 패턴을 사용하도록 합니다.
- 저장 직후 `python -m compileall`을 기본 루틴으로 포함시켜 인코딩·공백 오류를 조기 발견합니다.
- 필요 시 pre-commit 훅에 라인 엔딩/인코딩 검사 스크립트를 추가해 자동으로 방지합니다.

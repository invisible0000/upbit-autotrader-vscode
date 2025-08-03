# 🔧 Core Utils - 핵심 유틸리티 함수

## 📋 모듈 목적

이 `upbit_auto_trading/core/utils.py` 모듈은 프로젝트 전반에서 사용되는 핵심 유틸리티 함수들을 제공합니다.

## 🛠️ 제공 함수들

### 🔐 보안 함수
- `encrypt_api_key()`: API 키 암호화
- `decrypt_api_key()`: API 키 복호화

### 📁 파일/디렉토리 관리
- `ensure_directory()`: 디렉토리 자동 생성 ⭐ **가장 많이 사용**
- `load_config()`: 설정 파일 로드 (YAML/JSON)
- `save_config()`: 설정 파일 저장

### 🔢 데이터 처리
- `generate_id()`: 고유 ID 생성
- `format_number()`: 숫자 포맷팅
- `format_timestamp()`: 시간 포맷팅
- `parse_timeframe()`: 시간대 문자열 파싱

## 💡 사용법

### 권장 방식 (새로운 코드)
```python
from upbit_auto_trading.core.utils import ensure_directory, load_config
```

### 레거시 호환 방식 (기존 코드)
```python
from upbit_auto_trading.utils import ensure_directory  # 경고 표시됨
```

## 🎯 핵심 함수: ensure_directory

**가장 자주 사용되는 함수**로, 백업 파일, 로그 파일, 설정 파일 저장 전에 디렉토리를 안전하게 생성합니다.

```python
# 예시: 백업 디렉토리 생성
ensure_directory("data/backups/2025/08")
# 결과: data → backups → 2025 → 08 전체 경로 생성
```

---

*마지막 업데이트: 2025-08-03*

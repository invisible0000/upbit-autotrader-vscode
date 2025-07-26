# 빠른 시작 가이드

## 🚀 5분 만에 시작하기

### 1. 기본 호환성 확인
```python
from upbit_auto_trading.utils.trading_variables import SimpleVariableManager

manager = SimpleVariableManager()

# SMA와 EMA가 호환되는지 확인
if manager.check_compatibility('SMA', 'EMA'):
    print("✅ SMA ↔ EMA 호환 가능!")
else:
    print("❌ 호환되지 않음")
```

### 2. 새 지표 추가 (CLI)
```bash
cd tools
python trading_variables_cli.py add HULL_MA "헐 이동평균"
```

### 3. 모든 지표 목록 보기
```bash
python trading_variables_cli.py list
```

### 4. 카테고리별 지표 조회
```bash
python trading_variables_cli.py category trend
```

### 5. 파라미터 확인
```python
from upbit_auto_trading.utils.trading_variables import ParameterManager

param_manager = ParameterManager()
defaults = param_manager.get_default_parameters('SMA')
print(f"SMA 기본 파라미터: {defaults}")
```

## 🎯 주요 명령어

| 작업 | 명령어 |
|------|--------|
| 지표 목록 | `python trading_variables_cli.py list` |
| 새 지표 추가 | `python trading_variables_cli.py add <ID> "<이름>"` |
| 호환성 확인 | `python trading_variables_cli.py check <ID1> <ID2>` |
| 시스템 상태 | `python trading_variables_cli.py stats` |

자세한 내용은 [README.md](README.md)를 참조하세요.

# 🖥️ CLI 모드 개발 계획 - 서버/자동화용 인터페이스

## 📋 이 폴더의 목적

이 폴더는 **미래의 CLI(Command Line Interface) 모드** 개발을 위한 계획과 초기 파일들을 보관합니다.

## 🎯 CLI 모드의 비전

### **왜 CLI 모드가 필요한가?**

1. **서버 환경**: GUI 없는 Linux 서버에서 실행
2. **자동화**: 크론잡, 스케줄러와 연동
3. **배치 처리**: 대량 백테스팅, 데이터 분석
4. **CI/CD**: 개발 파이프라인 통합
5. **헤드리스 운영**: VPS, 클라우드 환경

### **설계 철학**
```
GUI 모드 = 대화형, 실시간 모니터링, 전략 개발
CLI 모드 = 자동화, 배치 처리, 서버 운영
```

## 📁 현재 보관된 파일

### `run_console.py` - 현재 콘솔 실행기
**현재 상태**: 기본적인 콘솔 실행만 가능
**문제점**: GUI 의존적, 비즈니스 로직 미분리

```python
# 현재: 단순 래퍼
from upbit_auto_trading.__main__ import main
sys.exit(main())
```

## 🚧 미래 CLI 아키텍처 설계

### **목표 구조**
```
upbit_auto_trading/
├── cli/                   # CLI 전용 모듈
│   ├── __init__.py
│   ├── commands/          # 명령어별 핸들러
│   │   ├── start.py       # 매매 시작
│   │   ├── stop.py        # 매매 중지
│   │   ├── backtest.py    # 백테스팅
│   │   ├── status.py      # 상태 확인
│   │   └── config.py      # 설정 관리
│   ├── formatters/        # 출력 포매터
│   └── cli_main.py        # CLI 진입점
└── business_logic/        # 공통 비즈니스 로직
```

### **예상 명령어 체계**

```bash
# 매매 관련
upbit-trader start --strategy="rsi_macd" --symbol="KRW-BTC"
upbit-trader stop --all
upbit-trader status --live

# 백테스팅
upbit-trader backtest \
  --strategy="momentum_strategy" \
  --period="2024-01-01,2024-12-31" \
  --initial-balance=1000000 \
  --output=json

# 설정 관리
upbit-trader config set api-key "your_api_key"
upbit-trader config list
upbit-trader config validate

# 데이터 관리
upbit-trader data sync --symbols="KRW-BTC,KRW-ETH"
upbit-trader data clean --older-than="30d"

# 전략 관리
upbit-trader strategy list
upbit-trader strategy create --from-template="rsi_basic"
upbit-trader strategy test --name="my_strategy" --dry-run
```

## 🏗️ 개발 단계별 계획

### **Phase 1**: 비즈니스 로직 분리 (선행 필요)
- GUI에서 로직 분리
- 공통 인터페이스 정의
- API 계층 구축

### **Phase 2**: CLI 기본 골격
```python
# 예상 CLI 진입점
import click

@click.group()
def cli():
    """Upbit Autotrader CLI"""
    pass

@cli.command()
@click.option('--strategy', required=True)
@click.option('--symbol', default='KRW-BTC')
def start(strategy, symbol):
    """매매 시작"""
    trader = AutoTrader()
    trader.start(strategy=strategy, symbol=symbol)

@cli.command()
def status():
    """현재 상태 확인"""
    status = StatusManager.get_current_status()
    click.echo(format_status(status))
```

### **Phase 3**: 고급 기능
- 실시간 로그 스트리밍
- 진행률 표시 (tqdm)
- 컬러 출력 (colorama)
- 설정 마법사

## 🔧 기술 스택

### **CLI 프레임워크**
- **Click**: 명령어 파싱, 옵션 처리
- **Rich**: 테이블, 진행률, 컬러 출력
- **Typer**: 타입 힌트 기반 CLI (대안)

### **출력 포맷**
```python
# JSON 출력 (스크립트 친화적)
upbit-trader status --format=json

# 테이블 출력 (사람 친화적)  
upbit-trader positions --format=table

# CSV 출력 (분석 친화적)
upbit-trader history --format=csv --output=trades.csv
```

## ⚡ 성능 고려사항

### **서버 환경 최적화**
- GUI 라이브러리 의존성 제거
- 메모리 사용량 최소화
- 로그 파일 크기 제한
- 백그라운드 실행 지원

### **자동화 친화적 설계**
```bash
# 스크립트 예시
#!/bin/bash
upbit-trader start --strategy="conservative" --daemon
sleep 3600  # 1시간 대기
upbit-trader stop --graceful
upbit-trader report --last-session > daily_report.txt
```

## 🚀 현재 해야 할 일

### **우선순위 1**: GUI 완성
- CLI는 GUI 이후 개발
- 비즈니스 로직 분리가 선행 조건

### **우선순위 2**: 인터페이스 설계
- 공통 추상화 레이어 정의
- CLI/GUI 모두 사용할 수 있는 API

### **우선순위 3**: CLI 프로토타입
- 기본 명령어 구현
- 설정 파일 호환성

---

## 📚 관련 참고 자료

- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Library](https://github.com/Textualize/rich)
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46)

---

**🎯 핵심 메시지**: "CLI 모드는 미래의 서버/자동화 환경을 위한 필수 인터페이스이지만, 현재는 GUI 완성에 집중"

*마지막 업데이트: 2025-08-03*

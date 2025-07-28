# 📊 데이터베이스 구조 재편성 계획

## 🎯 목표
설치형 프로그램을 위한 사용자 친화적 데이터베이스 구조 구축

## 📋 현재 문제점
- `app_settings.sqlite3` 파일이 3곳에 중복 존재
- 데이터베이스 파일들이 코드 내부 폴더에 분산
- 사용자가 백업해야 할 데이터의 위치가 불분명

## 🏆 목표 구조 (개선안 - 단일 데이터 폴더)

### **권장 구조: 깔끔한 단일 데이터 폴더**
```
📂 upbit-autotrader/
├── 📂 data/ (통합 데이터 폴더 - 기존 유지)
│   ├── 📂 user/                  # 사용자 데이터 (백업 필요)
│   │   ├── settings.sqlite3      # 통합 사용자 설정
│   │   ├── strategies.sqlite3    # 사용자 생성 전략들  
│   │   └── trading_history.sqlite3 # 거래 기록
│   │
│   ├── 📂 market/                # 시장 데이터 (캐시)
│   │   ├── market_data.sqlite3   # 업비트 시장 데이터
│   │   └── indicators.sqlite3    # 계산된 기술적 지표
│   │
│   ├── 📂 system/                # 시스템 데이터
│   │   ├── app_config.sqlite3    # 앱 시스템 설정
│   │   └── trading_variables.sqlite3 # 거래 변수 정의
│   │
│   └── 📂 backups/               # 자동 백업
│       ├── user_backup_YYYYMMDD.sqlite3
│       └── strategies_backup_YYYYMMDD.sqlite3
│
├── 📂 upbit_auto_trading/ (소스코드)
├── 📂 config/ (설정 파일들)
├── 📂 logs/ (로그 파일들)
└── run_desktop_ui.py
```

### **대안: 루트 레벨 분리 (원안)**
```
📂 upbit-autotrader/
├── 📂 UserData/     # 사용자 데이터 - 백업 필요
├── 📂 MarketData/   # 시장 데이터 - 캐시 성격  
├── 📂 AppData/      # 앱 내부 데이터
├── 📂 upbit_auto_trading/ (소스코드)
└── run_desktop_ui.py
```

## 🔄 마이그레이션 단계

### Phase 1: 새 구조 생성
1. 루트에 `UserData/`, `MarketData/`, `AppData/` 폴더 생성
2. 새로운 데이터베이스 스키마 정의
3. 마이그레이션 스크립트 작성

### Phase 2: 데이터 통합
1. 중복된 `app_settings.sqlite3` 파일들 통합
2. 사용자 데이터 vs 시스템 데이터 분리
3. 백업 시스템 구축

### Phase 3: 코드 업데이트  
1. 데이터베이스 경로 상수 업데이트
2. 설정 로더 로직 수정
3. 백업/복원 기능 구현

### Phase 4: 검증 및 정리
1. 모든 기능 테스트
2. 기존 중복 파일 정리
3. 문서 업데이트

## 📝 파일 매핑 계획

### 현재 → 목표
```
data/app_settings.sqlite3 → UserData/settings.sqlite3
data/upbit_auto_trading.sqlite3 → UserData/strategies.sqlite3  
data/market_data.sqlite3 → MarketData/market_data.sqlite3
trading_variables.db → AppData/trading_variables.sqlite3

# 제거 대상 (중복 파일들)
upbit_auto_trading/data/app_settings.sqlite3 (삭제)
upbit_auto_trading/ui/desktop/data/upbit_auto_trading.sqlite3 (삭제)
trigger_builder/components/data/app_settings.sqlite3 (삭제)
```

## 🎯 기대 효과
1. **사용자 편의성**: 백업할 폴더가 명확 (`UserData/`)
2. **유지보수성**: 데이터 역할별 분리로 관리 용이
3. **설치 용이성**: 폴더 구조가 직관적
4. **확장성**: 새로운 데이터 타입 추가 시 적절한 위치 명확

## ⚠️ 주의사항
- 기존 사용자 데이터 손실 방지를 위한 마이그레이션 스크립트 필수
- 설정 파일 경로 하드코딩된 부분 모두 업데이트 필요
- 백업 및 롤백 계획 수립 필요

---
**생성일**: 2025.07.28  
**우선순위**: 중간 (기능에는 문제없으나 UX 개선 필요)  
**예상 소요**: 2-3시간

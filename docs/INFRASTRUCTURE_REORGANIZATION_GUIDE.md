# Infrastructure Layer 구조 재설계 가이드

## 🎯 DDD 원칙에 따른 Infrastructure 계층 구조

### 📁 추천 구조:

```
infrastructure/
├── utilities/              # 🔧 기술적 유틸리티 (Presentation과 무관)
│   ├── file_operations/    # 파일 처리 헬퍼
│   ├── network_helpers/    # 네트워크 유틸리티
│   ├── math_calculations/  # 수학적 계산 헬퍼
│   ├── crypto_helpers/     # 암호화/해시 유틸리티
│   └── time_converters/    # 시간 변환 유틸리티
├── services/               # 🏢 Infrastructure 서비스
│   ├── file_system_service.py
│   ├── notification_service.py
│   └── cache_service.py
├── repositories/           # 📂 Domain 인터페이스 구현체
├── external_apis/          # 🌐 외부 API 연동
├── database/               # 🗄️ DB 기술 구현
├── logging/                # 📝 로깅 기술 구현
└── providers/              # 🎪 시스템 전체 Provider (TimeFrame 등)
```

## 🚫 Presentation으로 이동할 것들:

```
presentation/
├── formatters/             # 🎨 UI 표시용 포맷터
│   ├── orderbook_formatter.py  # 호가창 표시 포맷팅
│   ├── price_formatter.py      # 가격 표시 포맷팅
│   └── chart_formatter.py      # 차트 표시 포맷팅
├── view_models/            # 📊 View에 필요한 데이터 모델
└── presenters/             # 🎭 MVP 패턴 Presenter
```

## ✅ 분류 기준:

### Infrastructure utilities (기술적 유틸리티):
- **파일 시스템 조작**: 복사, 이동, 압축
- **네트워크 통신**: HTTP 클라이언트, 소켓 래퍼
- **암호화/보안**: 해시 계산, 암호화 헬퍼
- **수학적 계산**: 통계, 금융 계산
- **시간 처리**: 타임존 변환, 포맷팅

### Presentation formatters (표시용 포맷터):
- **UI 데이터 변환**: 테이블 형식 변환
- **텍스트 포맷팅**: 가격, 수량 표시용
- **차트 데이터 변환**: 그래프 표시용
- **사용자 친화적 표시**: 스프레드, 거래량 등

## 🎯 이동 작업 계획:

1. `orderbook_formatter.py` → `presentation/formatters/` ✅ 완료
2. Infrastructure utilities 폴더 생성 및 정리
3. 기존 포맷터들 검토 후 적절한 계층 배치
4. Import 경로 업데이트

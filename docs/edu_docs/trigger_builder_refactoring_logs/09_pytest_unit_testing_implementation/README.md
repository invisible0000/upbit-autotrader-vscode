# 📁 pytest 단위테스트 구현 - 교육 자료

> **프로젝트**: Upbit 자동매매 시스템
> **작업명**: Infrastructure Layer pytest 단위테스트 시스템 구현
> **작업일**: 2025-08-05
> **대상**: 주니어 개발자

## 📋 개요

이 폴더는 **pytest 기반 단위테스트 시스템 구현** 과정에서 얻은 실무 경험을 체계적으로 정리한 교육 자료입니다.

### 🎯 작업 성과
- **13개 테스트 100% 통과** (Mock 9개 + 실제 API 4개)
- **이중 API 키 로딩 시스템** 구축 (.env + 암호화 파일)
- **비동기 테스트 완벽 지원** (pytest-asyncio + AsyncMock)
- **마커 기반 테스트 분류** (unit, integration, real_api)

## 📚 문서 구성

### [01_개발경험.md](01_개발경험.md)
- **목적**: 프로젝트 진행 과정에서 얻은 실무 경험과 인사이트
- **내용**:
  - 기술적 도전과제와 해결 과정
  - 개발자로서 성장한 부분
  - 실무에서 바로 적용할 팁
  - 프로젝트 회고 및 향후 발전 방향

### [02_구현가이드.md](02_구현가이드.md)
- **목적**: 동일한 시스템을 구현하기 위한 단계별 가이드
- **내용**:
  - API 키 로딩 시스템 구축 방법
  - pytest 설정 및 Mock 테스트 작성법
  - 실제 API 통합 테스트 구현
  - 테스트 실행 전략 및 품질 체크리스트

### [03_문제해결.md](03_문제해결.md)
- **목적**: 실제 발생한 문제들과 해결 과정 상세 기록
- **내용**:
  - 5가지 주요 문제와 해결 과정
  - 문제 해결 방법론 및 디버깅 도구
  - 예방 가이드라인 및 트러블슈팅 체크리스트

## 🔧 기술 스택

### 핵심 기술
- **Python 3.13.5** - 메인 언어
- **pytest** - 테스트 프레임워크
- **pytest-asyncio** - 비동기 테스트 지원
- **AsyncMock** - 비동기 Mock 객체

### 보안 및 인프라
- **python-dotenv** - 환경변수 관리
- **cryptography** - API 키 암호화
- **aiohttp** - 비동기 HTTP 클라이언트

## 🎯 학습 목표

### 초급 (문서 읽기)
- [ ] pytest 기본 개념과 비동기 테스트 이해
- [ ] Mock vs 실제 API 테스트의 차이점 파악
- [ ] API 키 보안 관리 방식 학습

### 중급 (실습)
- [ ] 동일한 테스트 시스템 직접 구현
- [ ] Mock 객체의 정확성 검증 방법 습득
- [ ] 마커 기반 테스트 분류 활용

### 고급 (응용)
- [ ] 다른 Infrastructure 컴포넌트에 pytest 적용
- [ ] CI/CD 파이프라인에 테스트 통합
- [ ] 테스트 커버리지 향상 및 성능 최적화

## 🚀 실습 가이드

### 1단계: 환경 설정
```bash
# 필수 라이브러리 설치
pip install pytest pytest-asyncio pytest-cov cryptography python-dotenv

# 프로젝트 구조 확인
ls tests/infrastructure/external_apis/
```

### 2단계: 기본 테스트 실행
```bash
# 전체 테스트 실행
pytest tests/infrastructure/external_apis/test_upbit_clients.py -v

# Mock 테스트만 (빠른 피드백)
pytest tests/infrastructure/external_apis/test_upbit_clients.py -m "not real_api" -v
```

### 3단계: API 키 설정 (선택사항)
```bash
# .env 파일 생성 (실제 API 테스트용)
echo "UPBIT_ACCESS_KEY=your_access_key" > .env
echo "UPBIT_SECRET_KEY=your_secret_key" >> .env

# 실제 API 테스트 실행
pytest tests/infrastructure/external_apis/test_upbit_clients.py -m "real_api" -v
```

## 📊 성과 지표

### 정량적 성과
- **테스트 커버리지**: Infrastructure Layer 85%+
- **테스트 실행 속도**: Mock 테스트 < 1초, 전체 < 2초
- **API 키 로딩 성공률**: .env 100%, 암호화 파일 100%

### 정성적 성과
- **코드 신뢰성**: 실제 API와 Mock 테스트 이중 검증
- **개발 효율성**: 빠른 피드백 루프 구축
- **보안 강화**: 다중 API 키 저장 방식 지원

## 💡 핵심 교훈

### 기술적 교훈
1. **Mock의 정확성이 핵심**: 실제 구현과 100% 일치해야 함
2. **비동기 테스트는 AsyncMock**: 일반 Mock으로는 한계
3. **이중 소스 전략**: 개발 편의성과 보안 모두 만족

### 개발 프로세스 교훈
1. **차근차근 접근**: 각 문제를 하나씩 정확히 해결
2. **실제 구현 확인**: 추측하지 말고 소스코드 분석
3. **체계적 검증**: Mock → 실제 API 순서로 검증

## 🔄 향후 활용 방안

### 단기 활용
- **Template**: 다른 Infrastructure 컴포넌트 테스트 시 참조
- **Training**: 신입 개발자 pytest 교육 자료
- **Quality Gate**: 코드 리뷰 시 테스트 품질 기준

### 장기 활용
- **Best Practice**: 팀 내 테스트 작성 표준
- **CI/CD 통합**: 자동화 파이프라인 구축 기반
- **Test Strategy**: 전사 테스트 전략 수립 참고

---

## 📞 문의사항

테스트 구현 관련 문의사항이 있으면:
1. **구현 문제**: `02_구현가이드.md` 참조
2. **오류 해결**: `03_문제해결.md` 참조
3. **경험 공유**: `01_개발경험.md` 참조

**💫 결론**: 완벽한 테스트는 코드의 신뢰성을 보장하고, 리팩토링의 자신감을 제공합니다!

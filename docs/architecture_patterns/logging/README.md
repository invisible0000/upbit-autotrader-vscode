# 🔗 DDD 로깅 시스템 아키텍처 가이드

> **DDD Clean Architecture 원칙을 준수하는 완전한 로깅 시스템 구현**

## 📋 문서 개요

이 폴더는 업비트 자동매매 시스템의 **DDD 로깅 아키텍처** 구현과 관련된 모든 정보를 포함합니다.

### 📚 문서 구성

| 문서 | 목적 | 상태 |
|------|------|------|
| **`ddd_layer_flow.md`** | DDD 계층별 의존성과 데이터 흐름 | ✅ 완료 |
| **`ideal_architecture.md`** | 순수 DDD 설계 시 이상적인 구조 | ✅ 완료 |
| **`current_implementation.md`** | 현재 구현 상황과 실제 코드 | ✅ 완료 |

### 🎯 핵심 목표 달성 상황

- ✅ **Domain Layer 순수성**: Infrastructure 의존성 0개
- ✅ **DDD 원칙 준수**: 올바른 의존성 방향 확립
- ✅ **Domain Events 패턴**: 계층 간 완전한 디커플링
- ✅ **API 호환성**: 기존 로깅 인터페이스 100% 유지

### 🏗️ 아키텍처 요약

```
Domain Layer (순수)
├── Domain Events: 로깅 요청 이벤트 발행
└── Domain Logger: Events 기반 로깅 인터페이스

Infrastructure Layer (외부 연동)
├── Domain Events Subscriber: Domain Events 구독
└── 실제 로깅 수행: 파일/콘솔/DB
```

### 📊 프로젝트 진행 상황

- **Phase 0**: Repository Pattern ✅ (100% 완료)
- **Phase 1**: Domain Events 로깅 ✅ (100% 완료)
- **Phase 2**: Infrastructure 연동 ✅ (100% 완료)
- **Phase 3**: 선택적 마이그레이션 (선택사항)

### 🔍 빠른 참조

**DDD 원칙 이해**: `ddd_layer_flow.md` 먼저 읽기
**이상적 구조 확인**: `ideal_architecture.md` 참조
**실제 구현 확인**: `current_implementation.md` 참조

---

**최종 업데이트**: 2025년 8월 14일
**문서 버전**: v2.0 (Phase 2 완료)

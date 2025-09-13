# 🎯 업비트 API Rate Limit 분석 도구

이 폴더는 업비트 API 서버의 실제 Rate Limit을 정밀 측정하고 분석하는 도구들을 포함합니다.

## 📊 분석 결과 요약

### 🔍 주요 발견사항
- **Burst Capacity**: 10개 요청까지 연속 가능
- **안전한 최대 RPS**: 10.53 RPS (95ms 간격)
- **위험 구간**: 11.11 RPS (90ms 간격)에서 90.5% 성공률
- **현재 GCRA 설정 (10 RPS)**: 적절하지만 **약간 보수적**

### 🎯 최적화 권장사항
- **requests_per_second**: 10.5 (기존 10에서 5% 향상)
- **burst_size**: 10 (서버 측정값 그대로)
- **보수적 마진**: 9.5 RPS (10% 마진)

## 📁 파일 설명

### 🔬 분석 도구
1. **empirical_server_limit_measurement.py**
   - 업비트 서버의 실제 Rate Limit 측정
   - Binary Search로 최적 RPS 찾기
   - Burst 테스트, 다양한 간격 테스트

2. **boundary_precision_analyzer.py**
   - 경계 영역 정밀 분석 (85ms~105ms)
   - Burst + Sustained 조합 패턴 분석
   - 정확한 임계점 발견

### 📈 측정 결과
1. **empirical_server_limit_results_*.json**
   - 전체 서버 한계 측정 결과
   - Binary Search, 고정 간격 테스트 데이터

2. **boundary_precision_results_*.json**
   - 경계 영역 정밀 분석 결과
   - 95ms vs 90ms 임계점 데이터

## 🚀 사용법

```powershell
# 전체 서버 한계 측정
python examples/rate_limit_analysis/empirical_server_limit_measurement.py

# 경계 영역 정밀 분석
python examples/rate_limit_analysis/boundary_precision_analyzer.py
```

## 📊 측정 결과 상세

### 🎯 임계점 분석
| 간격 | RPS | 성공률 | 429 발생 | 상태 |
|------|-----|--------|----------|------|
| 105ms | 9.52 | 100.0% | 없음 | ✅ 매우 안전 |
| 100ms | 10.00 | 100.0% | 없음 | ✅ 안전 |
| 95ms | 10.53 | 100.0% | 없음 | ✅ 안전 |
| 90ms | 11.11 | 90.5% | 0.94초 후 | ❌ 위험 |

### 💥 Burst 패턴
- **연속 10개 요청**: 100% 성공
- **이후 Sustained**: 처음 낮다가 점진적 회복 (96-97%)
- **Token Bucket 리필**: 명확한 패턴 확인

## 🎁 업비트 서버의 관대함

업비트 서버가 **공식 10 RPS 제한**을 넘어서 **10.5+ RPS까지 허용**하는 것을 확인했습니다.
이는 업비트가 사용자에게 **충분한 마진**을 제공한다는 것을 의미합니다.

따라서 **현재 GCRA 설정을 약간 공격적으로 조정**할 수 있는 여지가 있습니다.

---
*측정일: 2025-09-12*
*도구 버전: v1.0*

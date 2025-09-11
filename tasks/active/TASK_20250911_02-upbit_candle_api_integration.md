# 📋 TASK_20250911_02: UpbitPublicClient 캔들 API 연동

## 🎯 태스크 목표
- **주요 목표**: UpbitPublicClient에 캔들 데이터 조회 메서드 구현
- **완료 기준**:
  - get_candles 메서드 구현 (기본 캔들 조회)
  - get_candles_with_end 메서드 구현 (특정 시점까지 조회)
  - 업비트 API Rate Limit 준수 및 백오프 메커니즘
  - CandleData 모델과 완벽 호환

## 📊 현재 상황 분석
### 문제점
1. **캔들 조회 메서드 부재**: UpbitPublicClient에 캔들 관련 메서드가 없음
2. **API Rate Limit 미처리**: 업비트 API 제한사항 미적용
3. **에러 처리 부족**: API 호출 실패시 적절한 처리 메커니즘 필요

### 사용 가능한 리소스
- 기존 UpbitPublicClient 구조
- CandleData 모델 (from_upbit_api 메서드 포함)
- Infrastructure 로깅 시스템

## 🔄 체계적 작업 절차 (필수 준수)
### 8단계 작업 절차
1. **📋 작업 항목 확인**: 태스크 문서에서 구체적 작업 내용 파악
2. **🔍 검토 후 세부 작업 항목 생성**: 작업을 더 작은 단위로 분해
3. **[-] 작업중 마킹**: 해당 작업 항목을 `[-]` 상태로 변경
4. **⚙️ 작업 항목 진행**: 실제 작업 수행
5. **✅ 작업 내용 확인**: 결과물 검증 및 품질 확인
6. **📝 상세 작업 내용 업데이트**: 태스크 문서에 진행사항 기록
7. **[x] 작업 완료 마킹**: 해당 작업 항목을 완료 상태로 변경
8. **⏳ 작업 승인 대기**: 다음 단계 진행 전 검토 및 승인

### 작업 상태 마커
- **[ ]**: 미완료 (미시작)
- **[-]**: 진행 중 (현재 작업)
- **[x]**: 완료

## ⚙️ 작업 계획
### Phase 1: 업비트 캔들 API 분석
- [ ] 업비트 공식 API 문서 분석 (분봉, 시봉, 일봉, 주봉, 월봉)
- [ ] API 엔드포인트 및 파라미터 정리
- [ ] Rate Limit 정책 확인 (초당 요청 제한, 분당 요청 제한)

### Phase 2: get_candles 메서드 구현
- [ ] 기본 캔들 조회 메서드 구현
- [ ] 타임프레임별 엔드포인트 매핑 (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
- [ ] count 파라미터 처리 (최대 200개 제한)
- [ ] 응답 데이터 검증 및 변환

### Phase 3: get_candles_with_end 메서드 구현
- [ ] 특정 시점까지 캔들 조회 메서드 구현
- [ ] to 파라미터 처리 (업비트 API 형식으로 변환)
- [ ] 시간 형식 변환 (datetime → ISO string)
- [ ] 빈 응답 처리

### Phase 4: Rate Limit 및 에러 처리
- [ ] Rate Limit 백오프 메커니즘 구현
- [ ] HTTP 에러 코드별 처리 (429, 500, 503 등)
- [ ] 네트워크 타임아웃 처리
- [ ] 재시도 로직 구현 (최대 3회)

### Phase 5: 최종 검증
- [ ] 기본 API 호출 동작 확인
- [ ] CandleData 변환 검증
- [ ] Rate Limit 동작 확인

## 🛠️ 개발할 도구
- `upbit_public_client.py`: 캔들 조회 메서드 추가

## 🎯 성공 기준
- ✅ 모든 타임프레임에 대해 캔들 데이터 정상 조회
- ✅ Rate Limit 준수 및 백오프 메커니즘 정상 동작
- ✅ CandleData 모델로 정확한 변환
- ✅ 네트워크 에러시 안전한 재시도 처리
- ✅ 로깅을 통한 API 호출 추적

## 💡 작업 시 주의사항
### API 보안
- API 키는 ApiKeyService를 통한 암호화 저장만 사용
- 코드, 로그, 테스트에 API 키 노출 금지
- Rate Limit 엄격 준수로 계정 제재 방지

### 에러 처리
- 업비트 서버 에러시 적절한 백오프
- 네트워크 타임아웃시 재시도 로직
- 잘못된 파라미터시 명확한 에러 메시지

## 🚀 즉시 시작할 작업
1. 현재 UpbitPublicClient 구조 확인
2. 업비트 캔들 API 공식 문서 조사
3. get_candles 메서드 기본 구조 구현

```powershell
# 현재 UpbitPublicClient 확인
Get-Content upbit_auto_trading/infrastructure/external_apis/upbit/upbit_public_client.py | Select-String -Pattern "class|def"

# 업비트 API 문서 확인용 테스트
python -c "
import requests
response = requests.get('https://docs.upbit.com/reference')
print('✅ 업비트 API 문서 접근 확인')
"
```

---
**다음 에이전트 시작점**: Phase 1 - 업비트 캔들 API 분석부터 시작

# 🏗️ **모델 아키텍처 리팩터링 계획**

> **목표**: "소스의 원천이 되는 핵심 모델 + 순수 모니터링 분리" 달성  
> **원칙**: 청크 처리의 자연스러운 흐름 중심으로 모델 구조 단순화

---

## 🎯 **핵심 통찰**

### **올바른 청크 처리 흐름**
```
RequestInfo (시작/요청) → CollectionPlan (계획) → List[ChunkInfo] (처리/결과)
```

### **현재 문제점**
- **소스와 모니터링 혼재**: CollectionState, InternalCollectionState 등 중복 관리 클래스 난립
- **복잡한 상태 추적**: 핵심 비즈니스 로직이 파편화되어 디버깅 어려움
- **메인 로직 오염**: 모니터링 클래스들이 핵심 처리 로직에 개입

---

## 📂 **새로운 모델 아키텍처**

### **핵심 소스 모델** (Single Source of Truth)
```
📁 candle_core_models.py  # 현재 candle_business_models.py 제안을 수정
├── RequestInfo           # 요청/시작의 단일 소스 ✅
├── CollectionPlan        # 계획의 단일 소스 ✅  
├── ChunkInfo            # 개별 처리의 단일 소스 ✅
└── OverlapRequest/Result # 분석 지원 모델들 ✅
```

### **기본 데이터 모델** 
```
📁 candle_data_models.py  # 현재 candle_core_models.py 이름 변경
├── OverlapStatus        # 기본 도메인 열거형
├── ChunkStatus         # 기본 상태 열거형  
├── CandleData          # 기본 캔들 데이터 구조
└── CandleDataResponse  # API 응답 래퍼
```

### **모니터링 전용** (읽기 전용 뷰)
```
📁 candle_monitoring_models.py  # 새로 생성
└── CollectionMonitor    # 핵심 모델들을 참조하는 순수 모니터링
    ├── request_info: RequestInfo      # 참조만, 소유 안함
    ├── plan: CollectionPlan          # 참조만, 소유 안함
    ├── chunks: List[ChunkInfo]       # 참조만, 소유 안함
    └── @property 계산된 정보들 (진행률, 남은 시간 등)
```

### **최종 결과** (불변 스냅샷)
```
📁 candle_result_models.py  # 새로 생성
└── CollectionResult     # 단순하고 명확한 최종 결과
    ├── success: bool
    ├── collected_count: int
    ├── requested_count: int
    └── processing_time_seconds: float
```

---

## 🔄 **청크 처리 로직 단순화**

### **Before (현재 - 복잡)** ❌
```python
# 불필요한 중간 관리자들
collection_state = InternalCollectionState(...)
collection_state.completed_chunks.append(chunk_info)  
collection_state.total_collected += saved_count
collection_state.mark_api_call()
# ... 복잡한 상태 동기화 로직들
```

### **After (목표 - 단순)** ✅
```python
# 핵심 소스 모델만 사용
request_info = RequestInfo(symbol, timeframe, count=15)
plan = create_collection_plan(request_info)  
chunks: List[ChunkInfo] = []

# 자연스러운 청크 처리 흐름
for i in range(plan.estimated_chunks):
    chunk = ChunkInfo.create_chunk(i, request_info)
    
    await process_chunk(chunk)           # 개별 청크 처리
    chunk.mark_completed()               # 상태는 ChunkInfo에서 관리
    chunks.append(chunk)                 # 단순한 리스트 추가
    
    if should_complete(request_info, chunks):  # 단순한 완료 판단
        break

# 모니터링 (필요시에만)
monitor = CollectionMonitor(request_info, plan, chunks)
progress = monitor.progress_percentage  # 계산된 속성으로 파생
```

---

## 📋 **마이그레이션 로드맵**

### **Phase 1: 핵심 모델 통합**
1. **RequestInfo** (candle_request_models.py → candle_core_models.py)
2. **ChunkInfo** (candle_collection_models.py → candle_core_models.py)  
3. **CollectionPlan** (candle_collection_models.py → candle_core_models.py)
4. **OverlapRequest/Result** (candle_request_models.py → candle_core_models.py)

### **Phase 2: 불필요한 클래스 제거**
```python
❌ CollectionState (candle_collection_models.py)
❌ InternalCollectionState (chunk_processor_models.py)
❌ CollectionProgress (chunk_processor_models.py)
❌ ProcessingStats (candle_collection_models.py)  
❌ 중복된 CollectionResult들
```

### **Phase 3: 모니터링 분리**
1. **CollectionMonitor** 생성 (candle_monitoring_models.py)
2. **단순한 CollectionResult** 생성 (candle_result_models.py)

### **Phase 4: 청크 처리 로직 단순화**
```python
class ChunkProcessor:
    async def process_collection(self, request_info: RequestInfo) -> CollectionResult:
        plan = self.create_plan(request_info)
        chunks: List[ChunkInfo] = []
        
        # 단순한 청크 처리 루프  
        for chunk in self.generate_chunks(plan):
            await self.process_single_chunk(chunk)
            chunks.append(chunk)
            
            if should_complete_collection(request_info, chunks):
                break
                
        return create_result(chunks)
```

---

## 🎯 **최종 목표 검증**

### **핵심 소스 모델** (3개만)
- ✅ **RequestInfo**: 요청/시작의 단일 소스
- ✅ **CollectionPlan**: 계획의 단일 소스
- ✅ **ChunkInfo**: 개별 처리의 단일 소스

### **청크 처리 완전성**
```python
RequestInfo + List[ChunkInfo] = 모든 비즈니스 로직의 완전한 소스
```

### **모니터링 분리**
- **CollectionMonitor**: 핵심 모델들을 참조하는 읽기 전용 뷰
- **CollectionResult**: 최종 결과의 단순한 스냅샷

---

## 💡 **기대 효과**

1. **단순성**: 복잡한 상태 관리 클래스들 제거로 코드 복잡도 대폭 감소
2. **일관성**: 단일 소스 원칙으로 데이터 동기화 문제 해결
3. **디버깅**: RequestInfo + ChunkInfo만 추적하면 모든 상태 파악 가능
4. **확장성**: 모니터링 요구사항 변경 시 핵심 로직 영향 없음

**결과**: "소스의 원천이 될 수 있는 몇개의 클래스를 바탕으로만 로직이 설계되고 모니터링은 모니터링만 하는" 구조 완성 ✅

---

## 🔗 **다음 단계**

1. **ChunkInfo 연속 추적 검증**: 현재 ChunkInfo[0] ~ ChunkInfo[-1] 추적 상태 확인
2. **검증 완료 후**: 위 계획에 따른 단계별 리팩터링 실행
3. **최종 목표**: RequestInfo + List[ChunkInfo] 기반의 깔끔한 청크 처리 시스템

---

*Created: 2025-01-23*  
*Status: Ready for Implementation*
# MarketDataBackbone 800라인 분리 실행 계획

## 🚨 **현재 위험 상황**

### **800라인 기준 위험도 분석**
```
🔴 unified_market_data_api.py: 476라인 → 800라인 접근 중
🔴 data_unifier.py: 492라인 → 800라인 접근 중

예상 증가 요인:
- Phase 2.2 실제 API 연동: +100-200라인
- 실거래 최적화 로직: +50-150라인
- 에러 처리 강화: +50-100라인

위험 시점: Phase 2.2 완료 시 (약 7-10일 후)
```

### **분리 실행 트리거**
```python
# 자동 분리 감지 시스템
CRITICAL_FILES = [
    "unified_market_data_api.py",
    "data_unifier.py"
]

for file in CRITICAL_FILES:
    if count_lines(file) > 800:
        trigger_emergency_split(file)
        notify_development_team()
        halt_feature_development()
```

---

## 📋 **즉시 실행 가능한 분리 계획**

### **1단계: unified_market_data_api.py 분리 (우선순위 1)**

#### **현재 구조 분석**
```python
# unified_market_data_api.py (476라인)
├── Exception Classes (50라인)        → exceptions.py
├── SmartChannelRouter (150라인)       → channel_router.py (확장)
├── FieldMapper (80라인)               → field_mapper.py
├── ErrorUnifier (60라인)              → error_unifier.py
├── UnifiedMarketDataAPI (136라인)     → core_api.py
└── Mock Data Generation (50라인)      → 삭제 예정 (Phase 2.2)
```

#### **분리 후 구조**
```
api/
├── core_api.py (150라인)              # 핵심 API 인터페이스
├── exceptions.py (60라인)             # 통합 예외 클래스
├── field_mapper.py (100라인)          # 데이터 변환
├── error_unifier.py (80라인)          # 에러 통합 처리
└── __init__.py (20라인)               # 인터페이스 노출

기존 channel_router.py → 200라인으로 확장 유지
```

### **2단계: data_unifier.py 분리 (우선순위 2)**

#### **현재 구조 분석**
```python
# data_unifier.py (492라인)
├── Cache Classes (120라인)            → cache/
├── Data Validation (100라인)          → validation/
├── Performance Monitor (80라인)       → monitoring/
├── DataUnifier Core (150라인)         → core_unifier.py
└── Utility Functions (42라인)         → utils.py
```

#### **분리 후 구조**
```
storage/
├── core_unifier.py (180라인)          # 핵심 통합 로직
├── cache_manager.py (150라인)         # 캐시 관리
├── data_validator.py (120라인)        # 데이터 검증
├── performance_monitor.py (100라인)   # 성능 모니터링
├── utils.py (50라인)                  # 유틸리티
└── __init__.py (20라인)               # 인터페이스 노출
```

---

## 🔧 **실행 스크립트**

### **분리 자동화 도구**
```python
# tools/split_module.py
import ast
import os
from typing import Dict, List

class ModuleSplitter:
    """모듈 자동 분리 도구"""

    def __init__(self, target_file: str, max_lines: int = 200):
        self.target_file = target_file
        self.max_lines = max_lines
        self.split_plan = {}

    def analyze_split_points(self) -> Dict[str, List]:
        """분리 지점 분석"""
        with open(self.target_file) as f:
            tree = ast.parse(f.read())

        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': self._get_end_line(node)
                })
            elif isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': self._get_end_line(node)
                })

        return {'classes': classes, 'functions': functions}

    def generate_split_plan(self) -> Dict[str, str]:
        """분리 계획 생성"""
        components = self.analyze_split_points()

        # 기능별 그룹핑
        groups = {
            'exceptions': [],
            'core': [],
            'utils': [],
            'monitoring': []
        }

        for cls in components['classes']:
            if 'Exception' in cls['name']:
                groups['exceptions'].append(cls)
            elif 'Monitor' in cls['name'] or 'Stats' in cls['name']:
                groups['monitoring'].append(cls)
            elif 'Mapper' in cls['name'] or 'Unifier' in cls['name']:
                groups['utils'].append(cls)
            else:
                groups['core'].append(cls)

        return groups

    def execute_split(self):
        """분리 실행"""
        plan = self.generate_split_plan()

        for group_name, components in plan.items():
            if components:
                self._create_module(group_name, components)

        # 기존 파일을 legacy로 이동
        legacy_path = f"{self.target_file}.legacy"
        os.rename(self.target_file, legacy_path)

        print(f"✅ {self.target_file} 분리 완료")
        print(f"📁 레거시 파일: {legacy_path}")

# 실행
if __name__ == "__main__":
    # unified_market_data_api.py 분리
    api_splitter = ModuleSplitter(
        "upbit_auto_trading/infrastructure/market_data_backbone/v2/unified_market_data_api.py"
    )
    api_splitter.execute_split()

    # data_unifier.py 분리
    data_splitter = ModuleSplitter(
        "upbit_auto_trading/infrastructure/market_data_backbone/v2/data_unifier.py"
    )
    data_splitter.execute_split()
```

### **테스트 마이그레이션**
```python
# tools/migrate_tests.py
class TestMigrator:
    """테스트 파일 자동 마이그레이션"""

    def migrate_api_tests(self):
        """API 테스트 분리"""
        original_tests = [
            "test_sc01_basic_api_response.py",
            "test_sc10_websocket_integration.py"
        ]

        new_test_structure = {
            "test_core_api.py": ["test_get_ticker", "test_health_check"],
            "test_field_mapper.py": ["test_map_rest_data", "test_map_websocket_data"],
            "test_error_unifier.py": ["test_unify_error", "test_rate_limit_error"]
        }

        for new_test, test_methods in new_test_structure.items():
            self._create_test_file(new_test, test_methods)

    def migrate_storage_tests(self):
        """저장소 테스트 분리"""
        original_tests = [
            "test_sc07_candle_storage.py",
            "test_sc08_fragmented_requests.py"
        ]

        new_test_structure = {
            "test_cache_manager.py": ["test_cache_operations", "test_ttl_expiry"],
            "test_data_validator.py": ["test_data_validation", "test_integrity_check"],
            "test_performance_monitor.py": ["test_metrics_collection", "test_performance_stats"]
        }

        for new_test, test_methods in new_test_structure.items():
            self._create_test_file(new_test, test_methods)

# 실행
migrator = TestMigrator()
migrator.migrate_api_tests()
migrator.migrate_storage_tests()
```

---

## 🎯 **분리 실행 일정**

### **Phase 2.2.1: 긴급 분리 (2-3일)**
```
Day 1: unified_market_data_api.py 분리
  - 오전: 분리 계획 확정
  - 오후: 자동 분리 도구 실행
  - 저녁: 테스트 마이그레이션

Day 2: data_unifier.py 분리
  - 오전: 분리 실행
  - 오후: 테스트 검증
  - 저녁: 통합 테스트

Day 3: 통합 검증
  - 전체 테스트 수행
  - 성능 벤치마크
  - 레거시 파일 정리
```

### **Phase 2.2.2: 기능 개발 재개 (4-7일)**
```
Day 4-7: 원래 Phase 2.2 계획 실행
  - 실제 API 연동
  - 전략적 최적화
  - 실전 패턴 적용
```

---

## ✅ **분리 성공 기준**

### **정량적 기준**
```
✅ 모든 파일 200라인 이하
✅ 기존 테스트 100% 통과
✅ 성능 저하 5% 이내
✅ 메모리 사용량 변화 없음
```

### **정성적 기준**
```
✅ 코드 가독성 향상
✅ 테스트 작성 용이성
✅ LLM 분석 편의성
✅ 기능별 독립성 확보
```

---

## 🚀 **장기 진화 계획**

### **V3 마이크로 서비스화**
```
v3/
├── data_collection_service/    # 데이터 수집 전담
├── data_storage_service/       # 저장 관리 전담
├── data_service_provider/      # 제공 서비스 전담
└── coordination_layer/         # 전체 조정
```

### **지속적 진화 원칙**
```yaml
코드 품질 관리:
  - 주간 라인 수 모니터링
  - 800라인 알림 시스템
  - 자동 분리 트리거

성능 최적화:
  - 벤치마크 자동화
  - 병목 지점 자동 감지
  - 적응형 구조 조정
```

---

**🎯 결론**: **800라인 분리는 선택이 아닌 필수**입니다. Phase 2.2 진행 전에 미리 분리하여 **LLM 친화적이고 유지보수가 용이한 구조**를 확보해야 합니다!

# 🎯 트레이딩 지표 변수 관리 시스템 구현 계획

## 📌 **전체 개요**
현재 **단순이동평균 호환성 문제**를 해결하고, **새로운 지표 추가를 자동화**하는 체계적인 DB 관리 시스템을 구축합니다.

---

## 🎯 **구현 목표**
1. **즉시 해결**: SMA ↔ EMA 호환성 문제 5분 내 해결
2. **자동화**: 새 지표 추가 시 수동 분류 작업 90% 감소
3. **확장성**: 트레이딩뷰 200+ 지표까지 체계적 관리
4. **안정성**: 잘못된 비교 조건 생성 100% 방지

---

## 📋 **3단계 구현 로드맵**

### **🚀 1단계: 기본 DB 스키마 구축 (1일 소요)**

#### **목표**: 현재 지표들을 DB로 관리하여 호환성 문제 해결

#### **구현 작업**
```bash
# 1. DB 스키마 파일 생성 (영구 보관용)
mkdir -p upbit_auto_trading/utils/trading_variables
touch upbit_auto_trading/utils/trading_variables/schema.sql

# 2. 핵심 관리 클래스 구현 (영구 사용)
touch upbit_auto_trading/utils/trading_variables/variable_manager.py
touch upbit_auto_trading/utils/trading_variables/indicator_classifier.py
touch upbit_auto_trading/utils/trading_variables/compatibility_checker.py

# 3. 테스트 및 CLI 도구 (개발/관리용)
touch tests/test_variable_management.py
touch tools/trading_variables_cli.py
```

#### **상세 구현 내용**

##### **1.1 DB 스키마 생성**
```sql
-- trading_variables_schema.sql
CREATE TABLE trading_variables (
    variable_id TEXT PRIMARY KEY,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,          -- '단순이동평균', 'RSI 지표'
    purpose_category TEXT NOT NULL,         -- 'trend', 'momentum'
    chart_category TEXT NOT NULL,           -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,         -- 'price_comparable', 'percentage_comparable'
    is_active BOOLEAN DEFAULT 1,            -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 현재 활성 지표들 데이터 입력
INSERT INTO trading_variables VALUES 
-- 📈 추세 지표 (Trend Indicators)
('SMA', '단순이동평균', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('EMA', '지수이동평균', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('WMA', '가중이동평균', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('BOLLINGER_BANDS', '볼린저 밴드', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('ICHIMOKU', '일목균형표', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('PARABOLIC_SAR', '파라볼릭 SAR', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('ADX', '평균방향성지수', 'trend', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),
('AROON', '아룬 지표', 'trend', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),

-- ⚡ 모멘텀 지표 (Momentum Indicators)
('RSI', 'RSI 지표', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),
('STOCH', '스토캐스틱', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),
('STOCH_RSI', '스토캐스틱 RSI', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),
('WILLIAMS_R', '윌리엄스 %R', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),
('CCI', '상품채널지수', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP),
('MACD', 'MACD 지표', 'momentum', 'subplot', 'signal_conditional', 1, CURRENT_TIMESTAMP),
('ROC', '가격변동률', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP),
('MFI', '자금흐름지수', 'momentum', 'subplot', 'percentage_comparable', 1, CURRENT_TIMESTAMP),

-- 🔥 변동성 지표 (Volatility Indicators)  
('ATR', '평균실제범위', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP),
('BOLLINGER_WIDTH', '볼린저 밴드 폭', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP),
('STANDARD_DEVIATION', '표준편차', 'volatility', 'subplot', 'volatility_comparable', 1, CURRENT_TIMESTAMP),

-- 📦 거래량 지표 (Volume Indicators)
('VOLUME', '거래량', 'volume', 'subplot', 'volume_comparable', 1, CURRENT_TIMESTAMP),
('OBV', '온밸런스 볼륨', 'volume', 'subplot', 'volume_flow', 1, CURRENT_TIMESTAMP),
('VOLUME_PROFILE', '거래량 프로파일', 'volume', 'overlay', 'volume_distribution', 1, CURRENT_TIMESTAMP),
('VWAP', '거래량가중평균가격', 'volume', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),

-- 💰 가격 데이터 (Price Data)
('CURRENT_PRICE', '현재가', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('HIGH_PRICE', '고가', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('LOW_PRICE', '저가', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('OPEN_PRICE', '시가', 'price', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),

-- 🏆 인기 커뮤니티 지표 (Popular Community Indicators)
('SQUEEZE_MOMENTUM', '스퀴즈 모멘텀', 'momentum', 'subplot', 'centered_oscillator', 1, CURRENT_TIMESTAMP),
('SUPERTREND', '슈퍼트렌드', 'trend', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP),
('PIVOT_POINTS', '피봇 포인트', 'support_resistance', 'overlay', 'price_comparable', 1, CURRENT_TIMESTAMP);
```

##### **1.2 기본 변수 관리 클래스**
```python
# variable_manager.py (핵심 기능만)
class SimpleVariableManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_schema()
    
    def get_compatible_variables(self, base_variable_id: str) -> list:
        """기본 변수와 호환 가능한 변수들 조회"""
        query = """
        SELECT v2.variable_id, v2.display_name_ko 
        FROM trading_variables v1
        JOIN trading_variables v2 ON (
            v1.purpose_category = v2.purpose_category 
            AND v1.comparison_group = v2.comparison_group
            AND v2.is_active = 1
            AND v2.variable_id != v1.variable_id
        )
        WHERE v1.variable_id = ? AND v1.is_active = 1
        """
        cursor = self.conn.execute(query, (base_variable_id,))
        return cursor.fetchall()
    
    def check_compatibility(self, var1: str, var2: str) -> dict:
        """호환성 검증"""
        query = """
        SELECT v1.purpose_category, v1.comparison_group,
               v2.purpose_category, v2.comparison_group
        FROM trading_variables v1, trading_variables v2
        WHERE v1.variable_id = ? AND v2.variable_id = ?
        """
        cursor = self.conn.execute(query, (var1, var2))
        result = cursor.fetchone()
        
        if not result:
            return {'compatible': False, 'reason': '변수를 찾을 수 없음'}
        
        v1_purpose, v1_comp, v2_purpose, v2_comp = result
        
        if v1_purpose == v2_purpose and v1_comp == v2_comp:
            return {'compatible': True, 'reason': f'같은 {v1_purpose} 카테고리'}
        else:
            return {'compatible': False, 'reason': f'다른 카테고리 ({v1_purpose} ≠ {v2_purpose})'}
```

##### **1.3 즉시 적용 테스트**
```python
# test_basic_compatibility.py
def test_sma_ema_compatibility():
    """SMA-EMA 호환성 테스트"""
    vm = SimpleVariableManager('test.db')
    
    # SMA와 호환 가능한 변수들 조회
    compatible = vm.get_compatible_variables('SMA')
    
    # EMA가 포함되어 있는지 확인
    variable_ids = [var[0] for var in compatible]
    assert 'EMA' in variable_ids, "SMA와 EMA가 호환되지 않습니다!"
    
    # 직접 호환성 확인
    result = vm.check_compatibility('SMA', 'EMA')
    assert result['compatible'] == True, f"호환성 실패: {result['reason']}"
    
    print("✅ SMA-EMA 호환성 테스트 성공!")

if __name__ == "__main__":
    test_sma_ema_compatibility()
```

---

### **⚡ 2단계: UI 통합 및 자동화 (2일 소요)**

#### **목표**: 기존 UI를 DB 기반으로 전환하고 자동 분류 시스템 구축

#### **구현 작업**

##### **2.1 기존 UI 수정**
```python
# condition_dialog.py 수정 (핵심 부분만)
class ConditionDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.variable_manager = SimpleVariableManager('trading.db')
        self.setup_ui()
    
    def populate_variable_combos(self):
        """DB에서 변수 목록 읽어와서 콤보박스 구성"""
        # 기존 하드코딩된 변수 목록 대신 DB 조회
        query = """
        SELECT variable_id, display_name_ko, purpose_category, chart_category
        FROM trading_variables 
        WHERE is_active = 1
        ORDER BY purpose_category, display_name_ko
        """
        cursor = self.variable_manager.conn.execute(query)
        variables = cursor.fetchall()
        
        # 용도별로 그룹화하여 표시
        current_category = None
        for var_id, display_name, purpose_cat, chart_cat in variables:
            # 새로운 카테고리 그룹 헤더
            if current_category != purpose_cat:
                category_names = {
                    'trend': '📈 추세 지표',
                    'momentum': '⚡ 모멘텀 지표',
                    'volume': '📦 거래량 지표',
                    'price': '💰 가격 데이터'
                }
                header = category_names.get(purpose_cat, purpose_cat)
                self.variable_combo.addItem(header)
                self.variable_combo.model().item(self.variable_combo.count()-1).setEnabled(False)
                current_category = purpose_cat
            
            # 차트 타입 아이콘 추가
            icon = "🔗" if chart_cat == "overlay" else "📊"
            self.variable_combo.addItem(f"   {icon} {display_name}", var_id)
    
    def on_variable_changed(self):
        """기본 변수 변경 시 호환 가능한 외부 변수들만 표시"""
        base_var_id = self.variable_combo.currentData()
        if not base_var_id:
            return
        
        # 외부 변수 콤보박스 초기화
        self.external_variable_combo.clear()
        
        # 호환 가능한 변수들만 추가
        compatible_vars = self.variable_manager.get_compatible_variables(base_var_id)
        for var_id, display_name in compatible_vars:
            self.external_variable_combo.addItem(f"✅ {display_name}", var_id)
        
        # 호환성 상태 업데이트
        if compatible_vars:
            self.show_compatibility_status("✅ 호환 가능한 변수들이 표시됩니다", True)
        else:
            self.show_compatibility_status("⚠️ 호환 가능한 변수가 없습니다", False)
```

##### **2.2 자동 분류 시스템 구축**
```python
# indicator_classifier.py
class SmartIndicatorClassifier:
    """새로운 지표의 카테고리 자동 분류 (30개 지표 학습 기반)"""
    
    def __init__(self):
        # 학습된 키워드 패턴 (30개 지표 분석 결과)
        self.trend_keywords = [
            'ma', 'average', 'moving', 'bollinger', 'ichimoku', 'parabolic', 'sar',
            'adx', 'aroon', 'supertrend', 'pivot', 'trend'
        ]
        self.momentum_keywords = [
            'rsi', 'stoch', 'cci', 'momentum', 'williams', 'roc', 'macd',
            'mfi', 'squeeze', 'oscillator', 'strength'
        ]
        self.volatility_keywords = [
            'atr', 'volatility', 'width', 'deviation', 'standard', 'true range'
        ]
        self.volume_keywords = [
            'volume', 'obv', 'vwap', 'profile', 'flow', 'balance', 'weighted'
        ]
        self.price_keywords = [
            'price', 'open', 'high', 'low', 'close', 'current'
        ]
    
    def classify_indicator(self, name: str, description: str = '') -> dict:
        """30개 지표 패턴 기반 지능형 분류"""
        name_lower = name.lower()
        desc_lower = description.lower()
        combined_text = f"{name_lower} {desc_lower}"
        
        # 1. 키워드 매칭 점수 계산
        scores = {
            'trend': sum(1 for kw in self.trend_keywords if kw in combined_text),
            'momentum': sum(1 for kw in self.momentum_keywords if kw in combined_text),
            'volatility': sum(1 for kw in self.volatility_keywords if kw in combined_text),
            'volume': sum(1 for kw in self.volume_keywords if kw in combined_text),
            'price': sum(1 for kw in self.price_keywords if kw in combined_text)
        }
        
        # 2. 최고 점수 카테고리 선택
        purpose_category = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[purpose_category] / max(sum(scores.values()), 1)
        
        # 3. 예외 처리: 특수 패턴들
        if 'pivot' in name_lower:
            purpose_category = 'support_resistance'
        elif scores[purpose_category] == 0:
            purpose_category = 'momentum'  # 기본값
        
        # 4. 차트 카테고리 결정
        overlay_indicators = ['trend', 'price', 'support_resistance']
        chart_category = 'overlay' if purpose_category in overlay_indicators else 'subplot'
        
        # 5. 비교 그룹 결정 (30개 지표 분석 기반)
        comparison_groups = {
            'price': 'price_comparable',
            'trend': 'price_comparable',
            'support_resistance': 'price_comparable',
            'volume': 'volume_comparable' if 'volume' in name_lower else 'volume_flow',
            'volatility': 'volatility_comparable',
            'momentum': 'percentage_comparable'
        }
        
        # RSI 계열은 percentage_comparable, 센터라인 오실레이터는 centered_oscillator
        if any(kw in name_lower for kw in ['rsi', 'stoch', 'williams', 'mfi']):
            comparison_group = 'percentage_comparable'
        elif any(kw in name_lower for kw in ['cci', 'roc', 'macd', 'squeeze']):
            comparison_group = 'centered_oscillator'
        else:
            comparison_group = comparison_groups.get(purpose_category, 'signal_conditional')
        
        return {
            'purpose_category': purpose_category,
            'chart_category': chart_category,
            'comparison_group': comparison_group,
            'confidence': min(confidence + 0.6, 1.0),  # 베이스 신뢰도 추가
            'keyword_matches': scores
        }
    
    def add_new_indicator(self, variable_id: str, display_name: str, description: str = ''):
        """새 지표 자동 분류 후 DB 추가 (검증 포함)"""
        classification = self.classify_indicator(display_name, description)
        
        # 분류 결과 출력
        print(f"🔍 {display_name} 지표 분석 결과:")
        print(f"   키워드 매칭: {classification['keyword_matches']}")
        print(f"   신뢰도: {classification['confidence']:.1%}")
        print(f"   용도: {classification['purpose_category']}")
        print(f"   차트: {classification['chart_category']}")
        print(f"   비교: {classification['comparison_group']}")
        
        # 낮은 신뢰도 경고
        if classification['confidence'] < 0.7:
            print(f"⚠️  신뢰도가 낮습니다 ({classification['confidence']:.1%}). 수동 확인 권장.")
        
        # DB에 추가 (비활성 상태로)
        from upbit_auto_trading.utils.trading_variables.variable_manager import SimpleVariableManager
        vm = SimpleVariableManager('trading.db')
        
        try:
            vm.conn.execute("""
                INSERT INTO trading_variables 
                (variable_id, display_name_ko, purpose_category, chart_category, comparison_group, is_active)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (
                variable_id, display_name,
                classification['purpose_category'],
                classification['chart_category'], 
                classification['comparison_group']
            ))
            vm.conn.commit()
            
            print(f"✅ DB 추가 완료! activate_indicator('{variable_id}')로 활성화")
            return True
            
        except Exception as e:
            print(f"❌ DB 추가 실패: {e}")
            return False
    
    def batch_add_popular_indicators(self):
        """인기 지표들 일괄 추가"""
        popular_indicators = [
            ('HULL_MA', '헐 이동평균', '매우 부드럽고 반응이 빠른 이동평균'),
            ('KELTNER_CHANNEL', '켈트너 채널', '이동평균과 ATR로 만든 변동성 채널'),
            ('AWESOME_OSCILLATOR', '어썸 오실레이터', '5기간과 34기간 SMA의 차이를 막대그래프로 표시'),
            ('TRUE_STRENGTH_INDEX', 'TSI 지표', '이중 평활화된 모멘텀 지표'),
            ('ULTIMATE_OSCILLATOR', '궁극적 오실레이터', '단기, 중기, 장기 사이클을 모두 반영'),
            ('CHANDE_MOMENTUM', '찬드 모멘텀 오실레이터', '순수 모멘텀 측정 지표')
        ]
        
        success_count = 0
        for var_id, name, desc in popular_indicators:
            if self.add_new_indicator(var_id, name, desc):
                success_count += 1
        
        print(f"\n🎯 {success_count}/{len(popular_indicators)}개 지표 추가 완료!")
        return success_count
```

---

### **🔧 3단계: 고급 기능 및 최적화 (3일 소요)**

#### **목표**: 파라미터 관리, 성능 최적화, 완전한 문서화

#### **구현 작업**

##### **3.1 파라미터 관리 시스템**
```python
# parameter_manager.py
class ParameterManager:
    """변수별 파라미터 관리"""
    
    def add_parameter_definition(self, variable_id: str, param_key: str, 
                               param_name: str, param_type: str, default_value: str):
        """파라미터 정의 추가"""
        # 예: SMA의 'period' 파라미터, '기간', 'integer', '20'
        pass
    
    def get_variable_parameters(self, variable_id: str) -> list:
        """특정 변수의 파라미터 목록 조회"""
        # 예: SMA → [('period', '기간', 'integer', '20')]
        pass
    
    def validate_parameter_value(self, variable_id: str, param_key: str, value: str) -> bool:
        """파라미터 값 유효성 검증"""
        # 예: SMA의 period가 1~100 범위인지 확인
        pass
```

##### **3.2 성능 최적화**
```python
# cached_variable_manager.py
class CachedVariableManager(SimpleVariableManager):
    """캐싱을 통한 성능 최적화"""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
        self._compatibility_cache = {}
        self._variable_cache = {}
    
    def get_compatible_variables(self, base_variable_id: str) -> list:
        """캐시된 호환성 조회"""
        if base_variable_id not in self._compatibility_cache:
            result = super().get_compatible_variables(base_variable_id)
            self._compatibility_cache[base_variable_id] = result
        return self._compatibility_cache[base_variable_id]
```

##### **3.3 CLI 관리 도구**
```bash
# tools/variable_manager_cli.py
python tools/variable_manager_cli.py --add-indicator "윌리엄스 %R" --auto-classify
python tools/variable_manager_cli.py --activate WILLIAMS_R
python tools/variable_manager_cli.py --list-compatible SMA
python tools/variable_manager_cli.py --export-config variables.json
```

---

## 📅 **구체적 일정표**

### **Day 1: 기본 시스템 구축**
- **오전 (2시간)**: DB 스키마 설계 및 생성
- **오후 (3시간)**: SimpleVariableManager 구현 
- **저녁 (1시간)**: 기본 테스트 및 SMA-EMA 호환성 확인

**예상 결과**: ✅ SMA ↔ EMA 호환성 문제 해결

### **Day 2: UI 통합**
- **오전 (3시간)**: condition_dialog.py 수정 (DB 기반으로 전환)
- **오후 (3시간)**: 자동 분류 시스템 구현
- **저녁 (1시간)**: UI 테스트 및 사용자 경험 검증

**예상 결과**: ✅ 그룹화된 변수 선택 UI, 자동 호환성 필터링

### **Day 3: 자동화 시스템**
- **오전 (2시간)**: IndicatorClassifier 고도화
- **오후 (3시간)**: 새 지표 추가 자동화 테스트
- **저녁 (1시간)**: 에러 처리 및 예외 상황 대응

**예상 결과**: ✅ 새 지표 3줄 코드로 추가 가능

### **Day 4-5: 고급 기능**
- **파라미터 관리 시스템 구현**
- **성능 최적화 (캐싱, 인덱싱)**
- **CLI 도구 및 문서화**

**예상 결과**: ✅ 완전한 지표 관리 시스템 완성

---

## 🧪 **검증 시나리오**

### **시나리오 1: 기존 호환성 문제 해결**
```python
# 테스트: SMA와 EMA가 호환되는가?
vm = SimpleVariableManager('trading.db')
result = vm.check_compatibility('SMA', 'EMA')
assert result['compatible'] == True

# 테스트: RSI와 거래량이 비호환인가?
result = vm.check_compatibility('RSI', 'VOLUME')  
assert result['compatible'] == False
```

### **시나리오 2: 새 지표 추가**
```python
# 테스트: 새 지표 '윌리엄스 %R' 자동 분류
classifier = SimpleIndicatorClassifier()
classifier.add_new_indicator('WILLIAMS_R', '윌리엄스 %R', '스토캐스틱과 유사한 모멘텀 지표')

# 확인: 자동으로 momentum/subplot/percentage_comparable로 분류되었는가?
vm = SimpleVariableManager('trading.db')
compatible = vm.get_compatible_variables('RSI')
variable_ids = [var[0] for var in compatible]
assert 'WILLIAMS_R' in variable_ids  # RSI와 호환되어야 함
```

### **시나리오 3: UI 통합**
```python
# 테스트: 콤보박스에 그룹별로 표시되는가?
dialog = ConditionDialog()
dialog.populate_variable_combos()

# 확인: 추세 지표 그룹 안에 SMA, EMA가 있는가?
# 확인: 모멘텀 지표 그룹 안에 RSI, STOCH가 있는가?
```

---

## 💡 **핵심 포인트**

### **즉시 해결 (Day 1)**
- **SMA ↔ EMA 호환성**: `purpose_category = 'trend'`로 통일
- **DB 조회 기반**: 하드코딩된 매핑 테이블 제거
- **간단한 SQL**: 복잡한 로직 없이 JOIN으로 호환성 확인

### **자동화 구현 (Day 2-3)**
- **키워드 기반 분류**: 'moving average' → trend, 'rsi' → momentum
- **UI 자동 그룹화**: DB에서 읽어와서 카테고리별로 표시
- **호환성 필터링**: 기본 변수 선택 시 호환 가능한 것만 표시

### **확장성 확보 (Day 4-5)**
- **신규 지표 3줄 추가**: `add_new_indicator('ID', '이름', '설명')`
- **파라미터 관리**: 각 지표별 설정값 체계화
- **성능 최적화**: 자주 사용하는 조회는 캐싱

---

## 🎯 **성공 기준**

### **기능적 성공**
- ✅ SMA-EMA 호환성 문제 해결 (5분 내)
- ✅ 새 지표 추가 시간 90% 단축 (30분 → 3분)
- ✅ 잘못된 비교 조건 생성 100% 방지

### **기술적 성공**
- ✅ DB 기반 동적 UI 구성
- ✅ 자동 분류 정확도 80% 이상
- ✅ 200개 지표까지 성능 저하 없음

### **사용자 경험 성공**
- ✅ 직관적인 그룹화 및 아이콘 표시
- ✅ 호환성 상태 실시간 안내
- ✅ 3줄 코드로 새 지표 추가 가능

---

## 🚀 **시작하기**

### **1단계 즉시 시작**
```bash
# 1. 작업 디렉토리 생성 (utils - 영구 보관)
mkdir -p upbit_auto_trading/utils/trading_variables
mkdir -p tools

# 2. 핵심 파일 생성
touch upbit_auto_trading/utils/trading_variables/schema.sql
touch upbit_auto_trading/utils/trading_variables/variable_manager.py
touch upbit_auto_trading/utils/trading_variables/indicator_classifier.py

# 3. 개발/관리 도구
touch tools/trading_variables_cli.py
touch tests/test_variable_compatibility.py
```

### **2단계 첫 번째 구현**
1. **스키마 생성**: `schema.sql`에 30개 지표 포함한 테이블 정의
2. **데이터 입력**: 추세/모멘텀/변동성/거래량/가격 지표 30개 입력
3. **기본 클래스**: `SimpleVariableManager` 구현
4. **자동 분류**: `SmartIndicatorClassifier` 구현 (키워드 학습 기반)
5. **테스트**: SMA-EMA 호환성 + 6개 카테고리 분류 확인

### **3단계 점진적 확장**
- **Day 1**: 30개 지표 DB 구축 + 호환성 해결
- **Day 2**: UI 통합 + 그룹화된 선택 인터페이스
- **Day 3**: 자동 분류 시스템 + 신뢰도 검증
- **Day 4-5**: 파라미터 관리 + 성능 최적화 + CLI 도구

### **🎯 즉시 체험 가능한 기능**
```bash
# 새 지표 자동 분류 테스트
python -c "
from upbit_auto_trading.utils.trading_variables.indicator_classifier import SmartIndicatorClassifier
classifier = SmartIndicatorClassifier()

# 테스트: 헐 이동평균 자동 분류
result = classifier.classify_indicator('Hull Moving Average', '매우 부드럽고 반응이 빠른 이동평균')
print(f'분류 결과: {result}')

# 테스트: 30개 인기 지표 일괄 추가
classifier.batch_add_popular_indicators()
"

# 호환성 즉시 확인
python -c "
from upbit_auto_trading.utils.trading_variables.variable_manager import SimpleVariableManager
vm = SimpleVariableManager('trading.db')

# SMA와 호환되는 모든 지표 조회
compatible = vm.get_compatible_variables('SMA')
print('SMA 호환 지표:', [v[1] for v in compatible])

# RSI와 호환되는 모든 지표 조회  
compatible = vm.get_compatible_variables('RSI')
print('RSI 호환 지표:', [v[1] for v in compatible])
"
```

**🎯 결과**: 5일 후 완전한 지표 관리 시스템으로 **더 이상 호환성 문제나 새 지표 추가 고민 없음!** 🚀

# 🗄️ 트레이딩 지표 변수 관리 DB 스키마 설계

## 📌 **핵심 설계 원칙**
- **확장성**: 새로운 지표 추가 시 스키마 변경 최소화
- **호환성**: 용도별/차트별 카테고리 기반 자동 호환성 검증
- **유연성**: 파라미터 추가/변경이 용이한 구조
- **성능**: 빠른 조회와 필터링이 가능한 인덱스 설계

---

## 🏗️ **DB 스키마 구조**

### **1. 변수 정의 테이블 (trading_variables)**
```sql
CREATE TABLE trading_variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL UNIQUE,           -- 'SMA', 'RSI', 'MACD'
    display_name_ko TEXT NOT NULL,              -- '단순이동평균', 'RSI 지표'
    display_name_en TEXT NOT NULL,              -- 'Simple Moving Average'
    purpose_category TEXT NOT NULL,             -- 'trend', 'momentum', 'volatility'
    chart_category TEXT NOT NULL,               -- 'overlay', 'subplot'
    comparison_group TEXT NOT NULL,             -- 'price_comparable', 'percentage_comparable'
    is_active BOOLEAN NOT NULL DEFAULT 0,      -- 활성화 상태
    implementation_status TEXT DEFAULT 'planned', -- 'active', 'development', 'planned'
    description TEXT,                           -- 지표 설명
    calculation_formula TEXT,                   -- 계산 공식 (선택사항)
    data_source TEXT DEFAULT 'price',          -- 'price', 'volume', 'calculated'
    value_range_min REAL,                       -- 값 범위 최소 (예: 0)
    value_range_max REAL,                       -- 값 범위 최대 (예: 100)
    default_period INTEGER,                     -- 기본 기간 (예: 14)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX idx_variables_purpose ON trading_variables(purpose_category);
CREATE INDEX idx_variables_chart ON trading_variables(chart_category);
CREATE INDEX idx_variables_comparison ON trading_variables(comparison_group);
CREATE INDEX idx_variables_active ON trading_variables(is_active);
```

### **2. 변수 파라미터 정의 테이블 (variable_parameters)**
```sql
CREATE TABLE variable_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variable_id TEXT NOT NULL,                  -- 외래키: trading_variables.variable_id
    parameter_key TEXT NOT NULL,                -- 'period', 'multiplier', 'source'
    parameter_name_ko TEXT NOT NULL,            -- '기간', '배수', '데이터 소스'
    parameter_name_en TEXT NOT NULL,            -- 'Period', 'Multiplier', 'Data Source'
    parameter_type TEXT NOT NULL,               -- 'integer', 'float', 'enum', 'boolean'
    default_value TEXT,                         -- 기본값 (문자열로 저장)
    min_value REAL,                            -- 최소값 (숫자 타입용)
    max_value REAL,                            -- 최대값 (숫자 타입용)
    enum_options TEXT,                         -- JSON 형태의 선택 옵션
    is_required BOOLEAN NOT NULL DEFAULT 1,    -- 필수 파라미터 여부
    validation_rule TEXT,                       -- 검증 규칙 (정규식 등)
    display_order INTEGER DEFAULT 0,           -- 표시 순서
    description TEXT,                           -- 파라미터 설명
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (variable_id) REFERENCES trading_variables(variable_id),
    UNIQUE(variable_id, parameter_key)
);

-- 인덱스
CREATE INDEX idx_parameters_variable ON variable_parameters(variable_id);
CREATE INDEX idx_parameters_type ON variable_parameters(parameter_type);
```

### **3. 호환성 규칙 테이블 (compatibility_rules)**
```sql
CREATE TABLE compatibility_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_name TEXT NOT NULL,                    -- 'same_purpose', 'same_comparison_group'
    description TEXT,                           -- 규칙 설명
    rule_type TEXT NOT NULL,                    -- 'purpose', 'chart', 'custom'
    condition_field TEXT NOT NULL,              -- 검증할 필드명
    condition_operator TEXT NOT NULL,           -- '=', '!=', 'IN', 'NOT_IN'
    condition_value TEXT NOT NULL,              -- 비교값 (JSON 배열 형태 가능)
    priority INTEGER DEFAULT 0,                -- 우선순위 (높을수록 먼저 적용)
    is_active BOOLEAN NOT NULL DEFAULT 1,      -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 기본 호환성 규칙 데이터
INSERT INTO compatibility_rules (rule_name, description, rule_type, condition_field, condition_operator, condition_value) VALUES
('same_purpose_category', '같은 용도 카테고리끼리 호환', 'purpose', 'purpose_category', '=', ''),
('same_comparison_group', '같은 비교 그룹끼리 호환', 'chart', 'comparison_group', '=', ''),
('both_active', '둘 다 활성화된 지표만 호환', 'status', 'is_active', '=', '1');
```

### **4. 변수 카테고리 정의 테이블 (variable_categories)**
```sql
CREATE TABLE variable_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_type TEXT NOT NULL,                -- 'purpose', 'chart', 'comparison'
    category_key TEXT NOT NULL,                 -- 'trend', 'overlay', 'price_comparable'
    category_name_ko TEXT NOT NULL,             -- '추세 지표', '오버레이', '가격 비교 가능'
    category_name_en TEXT NOT NULL,             -- 'Trend Indicators', 'Overlay', 'Price Comparable'
    description TEXT,                           -- 카테고리 설명
    icon TEXT,                                  -- UI 아이콘 (예: '📈', '🔗')
    color TEXT,                                 -- UI 색상 (예: '#4CAF50')
    display_order INTEGER DEFAULT 0,           -- 표시 순서
    is_active BOOLEAN NOT NULL DEFAULT 1,      -- 활성화 상태
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(category_type, category_key)
);

-- 기본 카테고리 데이터
INSERT INTO variable_categories (category_type, category_key, category_name_ko, category_name_en, icon, display_order) VALUES
-- 용도 카테고리
('purpose', 'trend', '추세 지표', 'Trend Indicators', '📈', 1),
('purpose', 'momentum', '모멘텀 지표', 'Momentum Indicators', '⚡', 2),
('purpose', 'volatility', '변동성 지표', 'Volatility Indicators', '🔥', 3),
('purpose', 'volume', '거래량 지표', 'Volume Indicators', '📦', 4),
('purpose', 'price', '가격 데이터', 'Price Data', '💰', 5),

-- 차트 카테고리
('chart', 'overlay', '오버레이', 'Overlay', '🔗', 1),
('chart', 'subplot', '서브플롯', 'Subplot', '📊', 2),

-- 비교 가능성 카테고리
('comparison', 'price_comparable', '가격 비교 가능', 'Price Comparable', '💱', 1),
('comparison', 'percentage_comparable', '퍼센트 비교 가능', 'Percentage Comparable', '📊', 2),
('comparison', 'volume_comparable', '거래량 비교 가능', 'Volume Comparable', '📦', 3),
('comparison', 'signal_conditional', '신호선 조건부 비교', 'Signal Conditional', '⚡', 4),
('comparison', 'unique_scale', '비교 불가', 'Not Comparable', '🚫', 5);
```

---

## 🔧 **데이터 관리 클래스 설계**

### **1. 변수 관리 서비스 (VariableManager)**
```python
class VariableManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._initialize_schema()
    
    def add_new_variable(self, variable_data: dict) -> bool:
        """새로운 변수 추가"""
        try:
            with self.conn:
                # 1. 변수 기본 정보 삽입
                self.conn.execute("""
                    INSERT INTO trading_variables 
                    (variable_id, display_name_ko, display_name_en, purpose_category, 
                     chart_category, comparison_group, description, default_period)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    variable_data['variable_id'],
                    variable_data['display_name_ko'],
                    variable_data['display_name_en'],
                    variable_data['purpose_category'],
                    variable_data['chart_category'],
                    self._determine_comparison_group(variable_data),
                    variable_data.get('description', ''),
                    variable_data.get('default_period', 14)
                ))
                
                # 2. 파라미터 정보 삽입
                if 'parameters' in variable_data:
                    self._add_variable_parameters(variable_data['variable_id'], 
                                                variable_data['parameters'])
                
                return True
        except Exception as e:
            print(f"변수 추가 실패: {e}")
            return False
    
    def _determine_comparison_group(self, variable_data: dict) -> str:
        """변수 속성에 따라 비교 그룹 자동 결정"""
        chart_category = variable_data['chart_category']
        purpose_category = variable_data['purpose_category']
        value_range = variable_data.get('value_range_max', None)
        
        # 오버레이는 모두 가격 비교 가능
        if chart_category == 'overlay':
            return 'price_comparable'
        
        # 0-100 범위의 지표는 퍼센트 비교 가능
        if value_range == 100:
            return 'percentage_comparable'
        
        # 거래량 관련은 거래량 비교 가능
        if purpose_category == 'volume':
            return 'volume_comparable'
        
        # 신호선 계열은 조건부 비교
        if purpose_category == 'momentum' and chart_category == 'subplot':
            return 'signal_conditional'
        
        # 기타는 고유 스케일
        return 'unique_scale'
    
    def get_compatible_variables(self, base_variable_id: str) -> list:
        """기본 변수와 호환 가능한 변수들 조회"""
        query = """
        SELECT v2.variable_id, v2.display_name_ko, v2.purpose_category, v2.comparison_group
        FROM trading_variables v1
        JOIN trading_variables v2 ON (
            v1.purpose_category = v2.purpose_category 
            AND v1.comparison_group = v2.comparison_group
            AND v2.is_active = 1
            AND v2.variable_id != v1.variable_id
        )
        WHERE v1.variable_id = ? AND v1.is_active = 1
        ORDER BY v2.purpose_category, v2.display_name_ko
        """
        
        cursor = self.conn.execute(query, (base_variable_id,))
        return cursor.fetchall()
    
    def get_variables_by_category(self, category_type: str, category_key: str = None) -> list:
        """카테고리별 변수 조회"""
        if category_key:
            query = """
            SELECT variable_id, display_name_ko, purpose_category, chart_category, is_active
            FROM trading_variables 
            WHERE {} = ? AND is_active = 1
            ORDER BY display_name_ko
            """.format(f"{category_type}_category")
            cursor = self.conn.execute(query, (category_key,))
        else:
            query = """
            SELECT variable_id, display_name_ko, purpose_category, chart_category, is_active
            FROM trading_variables 
            WHERE is_active = 1
            ORDER BY purpose_category, display_name_ko
            """
            cursor = self.conn.execute(query)
        
        return cursor.fetchall()
    
    def activate_variable(self, variable_id: str) -> bool:
        """변수 활성화"""
        try:
            with self.conn:
                self.conn.execute("""
                    UPDATE trading_variables 
                    SET is_active = 1, implementation_status = 'active', 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE variable_id = ?
                """, (variable_id,))
                return True
        except Exception as e:
            print(f"변수 활성화 실패: {e}")
            return False
```

### **2. 호환성 검증 서비스 (CompatibilityChecker)**
```python
class CompatibilityChecker:
    def __init__(self, variable_manager: VariableManager):
        self.vm = variable_manager
    
    def check_compatibility(self, base_var_id: str, external_var_id: str) -> dict:
        """상세한 호환성 검증"""
        # 변수 정보 조회
        base_var = self._get_variable_info(base_var_id)
        external_var = self._get_variable_info(external_var_id)
        
        if not base_var or not external_var:
            return {
                'compatible': False,
                'reason': '변수 정보를 찾을 수 없습니다',
                'details': None
            }
        
        # 활성화 상태 확인
        if not (base_var['is_active'] and external_var['is_active']):
            return {
                'compatible': False,
                'reason': '비활성화된 변수입니다',
                'details': {
                    'base_active': base_var['is_active'],
                    'external_active': external_var['is_active']
                }
            }
        
        # 용도 카테고리 확인
        if base_var['purpose_category'] != external_var['purpose_category']:
            return {
                'compatible': False,
                'reason': f"다른 용도 카테고리 ({base_var['purpose_category']} ≠ {external_var['purpose_category']})",
                'details': {
                    'base_purpose': base_var['purpose_category'],
                    'external_purpose': external_var['purpose_category']
                }
            }
        
        # 비교 그룹 확인
        if base_var['comparison_group'] != external_var['comparison_group']:
            return {
                'compatible': False,
                'reason': f"다른 비교 그룹 ({base_var['comparison_group']} ≠ {external_var['comparison_group']})",
                'details': {
                    'base_comparison': base_var['comparison_group'],
                    'external_comparison': external_var['comparison_group']
                }
            }
        
        return {
            'compatible': True,
            'reason': f"호환 가능 ({base_var['purpose_category']} 카테고리, {base_var['comparison_group']} 그룹)",
            'details': {
                'shared_purpose': base_var['purpose_category'],
                'shared_comparison': base_var['comparison_group'],
                'chart_categories': [base_var['chart_category'], external_var['chart_category']]
            }
        }
    
    def _get_variable_info(self, variable_id: str) -> dict:
        """변수 정보 조회"""
        query = """
        SELECT variable_id, display_name_ko, purpose_category, chart_category, 
               comparison_group, is_active
        FROM trading_variables 
        WHERE variable_id = ?
        """
        cursor = self.vm.conn.execute(query, (variable_id,))
        row = cursor.fetchone()
        
        if row:
            return {
                'variable_id': row[0],
                'display_name_ko': row[1],
                'purpose_category': row[2],
                'chart_category': row[3],
                'comparison_group': row[4],
                'is_active': bool(row[5])
            }
        return None
```

---

## 📊 **새로운 지표 추가 프로세스**

### **1. 자동 분류 시스템**
```python
class IndicatorClassifier:
    def __init__(self, variable_manager: VariableManager):
        self.vm = variable_manager
    
    def classify_new_indicator(self, indicator_spec: dict) -> dict:
        """새로운 지표의 카테고리 자동 분류"""
        
        # 기본 정보
        name = indicator_spec['name']
        description = indicator_spec.get('description', '')
        calculation_type = indicator_spec.get('calculation_type', '')
        output_range = indicator_spec.get('output_range', {})
        
        # 1. 용도 카테고리 결정
        purpose_category = self._classify_purpose(name, description, calculation_type)
        
        # 2. 차트 카테고리 결정
        chart_category = self._classify_chart_display(output_range, purpose_category)
        
        # 3. 비교 그룹 결정
        comparison_group = self._classify_comparison_group(
            chart_category, purpose_category, output_range
        )
        
        return {
            'purpose_category': purpose_category,
            'chart_category': chart_category,
            'comparison_group': comparison_group,
            'confidence': self._calculate_confidence(indicator_spec),
            'suggested_parameters': self._suggest_parameters(calculation_type)
        }
    
    def _classify_purpose(self, name: str, description: str, calc_type: str) -> str:
        """용도 카테고리 분류"""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        # 키워드 기반 분류
        if any(keyword in name_lower for keyword in ['ma', 'average', 'moving', 'trend', 'bollinger']):
            return 'trend'
        elif any(keyword in name_lower for keyword in ['rsi', 'stoch', 'cci', 'momentum', 'oscillator']):
            return 'momentum'
        elif any(keyword in name_lower for keyword in ['atr', 'volatility', 'deviation', 'width']):
            return 'volatility'
        elif any(keyword in name_lower for keyword in ['volume', 'obv', 'mfi', 'flow']):
            return 'volume'
        elif any(keyword in name_lower for keyword in ['price', 'open', 'high', 'low', 'close']):
            return 'price'
        else:
            return 'momentum'  # 기본값
    
    def _classify_chart_display(self, output_range: dict, purpose: str) -> str:
        """차트 표시 방식 분류"""
        min_val = output_range.get('min', None)
        max_val = output_range.get('max', None)
        
        # 가격 데이터나 추세 지표는 대부분 오버레이
        if purpose in ['price', 'trend']:
            return 'overlay'
        
        # 고정 범위가 있으면 서브플롯
        if min_val is not None and max_val is not None:
            return 'subplot'
        
        # 기타는 서브플롯
        return 'subplot'
    
    def _classify_comparison_group(self, chart_cat: str, purpose_cat: str, output_range: dict) -> str:
        """비교 그룹 분류"""
        if chart_cat == 'overlay':
            return 'price_comparable'
        
        max_val = output_range.get('max', None)
        if max_val == 100:
            return 'percentage_comparable'
        
        if purpose_cat == 'volume':
            return 'volume_comparable'
        
        if purpose_cat == 'momentum':
            return 'signal_conditional'
        
        return 'unique_scale'
```

### **2. 지표 추가 예시**
```python
# 새로운 지표 추가 예시
def add_bollinger_band_width():
    indicator_spec = {
        'variable_id': 'BOLLINGER_WIDTH',
        'display_name_ko': '볼린저밴드폭',
        'display_name_en': 'Bollinger Band Width',
        'description': '볼린저밴드 상단과 하단의 폭으로 변동성을 측정',
        'calculation_type': 'statistical',
        'output_range': {'min': 0, 'max': None},
        'parameters': [
            {
                'parameter_key': 'period',
                'parameter_name_ko': '기간',
                'parameter_type': 'integer',
                'default_value': '20',
                'min_value': 5,
                'max_value': 100
            },
            {
                'parameter_key': 'multiplier',
                'parameter_name_ko': '표준편차 배수',
                'parameter_type': 'float',
                'default_value': '2.0',
                'min_value': 0.5,
                'max_value': 5.0
            }
        ]
    }
    
    # 자동 분류
    classifier = IndicatorClassifier(variable_manager)
    classification = classifier.classify_new_indicator(indicator_spec)
    
    # 분류 결과 적용
    indicator_spec.update(classification)
    
    # DB에 추가
    variable_manager.add_new_variable(indicator_spec)
    
    print(f"✅ {indicator_spec['display_name_ko']} 지표가 추가되었습니다.")
    print(f"   용도: {classification['purpose_category']}")
    print(f"   차트: {classification['chart_category']}")
    print(f"   비교: {classification['comparison_group']}")
```

---

## 🎯 **UI 통합 예시**

### **DB 기반 콤보박스 구성**
```python
class VariableComboBox(QComboBox):
    def __init__(self, variable_manager: VariableManager):
        super().__init__()
        self.vm = variable_manager
        self.populate_variables()
    
    def populate_variables(self):
        """DB에서 변수 목록을 읽어와 콤보박스 구성"""
        # 카테고리별로 그룹화
        categories = self.vm.get_variables_by_category('purpose')
        current_category = None
        
        for var_id, display_name, purpose_cat, chart_cat, is_active in categories:
            # 새로운 카테고리 그룹 헤더
            if current_category != purpose_cat:
                category_info = self.vm.get_category_info('purpose', purpose_cat)
                header_text = f"{category_info['icon']} {category_info['name_ko']}"
                self.addItem(header_text)
                self.model().item(self.count()-1).setEnabled(False)
                current_category = purpose_cat
            
            # 변수 아이템 추가
            chart_icon = "🔗" if chart_cat == "overlay" else "📊"
            item_text = f"   {chart_icon} {display_name}"
            self.addItem(item_text, var_id)
    
    def get_compatible_variables(self, base_variable_id: str):
        """호환 가능한 변수들로 콤보박스 재구성"""
        self.clear()
        compatible_vars = self.vm.get_compatible_variables(base_variable_id)
        
        for var_id, display_name, purpose_cat, comparison_group in compatible_vars:
            self.addItem(f"✅ {display_name}", var_id)
```

---

## 🚀 **구현 우선순위**

### **Phase 1: 기본 스키마 구축**
1. 기본 테이블 생성 (`trading_variables`, `variable_parameters`)
2. 현재 활성 지표들 데이터 입력
3. 기본 호환성 검증 로직 구현

### **Phase 2: 자동 분류 시스템**
1. `IndicatorClassifier` 구현
2. 새 지표 추가 프로세스 자동화
3. UI 통합 (DB 기반 콤보박스)

### **Phase 3: 고급 기능**
1. 비교 그룹별 정규화 기능
2. 호환성 규칙 확장
3. 성능 최적화 및 캐싱

이 DB 스키마를 사용하면 **새로운 지표 추가가 매우 간단**해지고, **호환성 검증이 자동화**되며, **확장성이 크게 향상**됩니다! 🎯

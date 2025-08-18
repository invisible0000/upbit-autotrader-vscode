# 🔄 작업 승계 가이드 - 매매 변수 파라미터 강화 프로젝트

## 📋 **작업 현황 요약**

### ✅ **완료된 작업**
1. **22개 매매 변수 도움말 완성** - 전문가 수준의 200줄 구성 (concept/usage/advanced)
2. **DB 업데이트 완료** - 모든 도움말이 DB에 저장됨 (`tv_variable_help_documents` 테이블)
3. **YAML 백업 생성** - `data_info/trading_variables/` 폴더에 카테고리별 구조로 백업
4. **카테고리 정리** - `dynamic_management` → `meta`로 변경
5. **프로젝트 태스크 등록** - `tasks/active/trading_variables_parameter_enhancement.md`

### 🎯 **다음 에이전트가 해야 할 작업**

---

## 🚀 **즉시 시작 가능한 작업 단계**

### **1단계: 핵심 변수 5개 우선 분석 (첫 번째 작업)**

다음 명령어로 현재 파라미터 현황을 파악하세요:

```powershell
# 전체 변수별 파라미터 현황 확인
$pythonScript = @"
import sqlite3
conn = sqlite3.connect('data/settings.sqlite3')
cursor = conn.cursor()

print('=== 전체 매매 변수 현황 ===')
cursor.execute('''
    SELECT tv.variable_id, tv.purpose_category,
           COUNT(tp.parameter_id) as param_count,
           tv.description
    FROM tv_trading_variables tv
    LEFT JOIN tv_variable_parameters tp ON tv.variable_id = tp.parameter_id
    GROUP BY tv.variable_id, tv.purpose_category
    ORDER BY tv.purpose_category, tv.variable_id
''')

results = cursor.fetchall()
for row in results:
    var_id, category, param_count, description = row
    status = f'({param_count}개)' if param_count > 0 else '(없음)'
    print(f'{var_id:20} {category:12} {status:8} | {description}')

conn.close()
"@

python -c $pythonScript
```

### **2단계: 우선순위 변수 5개 도움말 분석**

**필수 분석 대상 (높은 우선순위):**
1. **ATR** - 변동성 레짐 감지, 정규화 ATR 기능
2. **RSI** - 다이버전스 감지, 확률적 RSI 기능
3. **MACD** - 히스토그램 분석, 다중 시간대 기능
4. **VOLUME_SMA** - 상대 거래량, 추세 분석 기능
5. **LOW_PRICE** - 지지선 분석, 바닥 패턴 인식 기능

**분석 방법:**
```bash
# 각 변수의 도움말 확인
code data_info/_management/help_guides_for_editing/ATR_help_guide.yaml
code data_info/_management/help_guides_for_editing/RSI_help_guide.yaml
# ... (나머지 변수들도 동일)
```

### **3단계: 기능 분류 작업**

각 변수의 도움말에서 발견되는 고급 기능들을 다음 3가지로 분류:

**📊 Type A: 파라미터 확장**
- 기존 변수에 2-3개 파라미터 추가로 해결 가능
- 예: RSI에 `divergence_period`, `overbought_level` 추가

**🚀 Type B: 새로운 고급 변수**
- 복잡한 계산으로 별도 변수 필요
- 예: `ATR_VOLATILITY_REGIME`, `RSI_DIVERGENCE_DETECTOR`

**🔄 Type C: 메타 변수**
- 여러 기존 변수를 조합
- 예: `MARKET_REGIME_DETECTOR` (ATR + RSI + VOLUME 조합)

---

## 📁 **중요한 파일 위치**

### **도움말 원본 파일**
```
data_info/_management/help_guides_for_editing/
├── ATR_help_guide.yaml
├── RSI_help_guide.yaml
├── MACD_help_guide.yaml
├── VOLUME_SMA_help_guide.yaml
├── LOW_PRICE_help_guide.yaml
└── ... (총 22개 파일)
```

### **DB 데이터 확인**
```
data/settings.sqlite3
├── tv_trading_variables (변수 정의)
├── tv_variable_parameters (현재 파라미터)
├── tv_variable_help_documents (완성된 도움말)
└── tv_help_texts, tv_placeholder_texts
```

### **백업 YAML 구조**
```
data_info/trading_variables/
├── volatility/ATR/, BOLLINGER_BAND/
├── momentum/RSI/, MACD/, STOCHASTIC/
├── volume/VOLUME/, VOLUME_SMA/
└── ... (카테고리별 구조)
```

---

## 🎯 **구체적인 다음 액션**

### **Step 1: ATR 변수 분석 (예시)**

1. **도움말 확인:**
```bash
code data_info/_management/help_guides_for_editing/ATR_help_guide.yaml
```

2. **고급 기능 추출:**
- `ATR > ATR[5]` → 과거 값과 비교 기능
- `ATR > ATR의 20일 평균 * 1.5` → 평균 대비 비교
- `정규화 ATR = ATR / CURRENT_PRICE * 100` → 정규화 기능
- `ATR > ATR의 50일 평균 + (표준편차 * 2)` → 레짐 감지

3. **분류 결정:**
- **Type A**: `trend_period`, `trend_method` 파라미터 추가
- **Type B**: `ATR_NORMALIZED`, `ATR_REGIME` 별도 변수

4. **다음 변수로 진행:** RSI → MACD → VOLUME_SMA → LOW_PRICE

### **Step 2: 분석 결과 문서화**

`tasks/active/trading_variables_parameter_enhancement.md` 파일에 결과 기록:

```markdown
## 📊 변수별 분석 결과

### ATR 분석 완료 ✅
**Type A 파라미터 추가:**
- trend_period: integer, 기본값 5, 범위 2-20
- trend_method: enum, 기본값 "average", 옵션 ["average", "max", "min"]

**Type B 새 변수 필요:**
- ATR_NORMALIZED: 정규화 ATR (ATR/PRICE*100)
- ATR_REGIME: 변동성 레짐 감지 (low/normal/high/extreme)

**우선순위:** 높음 (많은 전략에서 활용)
**복잡도:** 중간
```

---

## ⚡ **작업 효율성 팁**

### **PowerShell 유틸리티 활용**
```powershell
# 모든 도움말 파일 한번에 확인
Get-ChildItem "data_info\_management\help_guides_for_editing\*.yaml" | ForEach-Object {
    Write-Host "=== $($_.Name) ==="
    Get-Content $_.FullName | Select-String "조건|IF|THEN|ATR\[|RSI\[|MACD\[" | Select-Object -First 5
}
```

### **DB 쿼리 템플릿**
```powershell
$pythonScript = @"
import sqlite3
conn = sqlite3.connect('data/settings.sqlite3')
cursor = conn.cursor()

# 특정 변수의 현재 파라미터 확인
cursor.execute('SELECT * FROM tv_variable_parameters WHERE variable_id = "ATR"')
results = cursor.fetchall()
for row in results:
    print(f'{row[2]:15} | {row[3]:10} | {row[4]:15} | {row[10]}')

conn.close()
"@

python -c $pythonScript
```

---

## 🎯 **성공 기준**

**1주 후 달성 목표:**
- [ ] 5개 핵심 변수 분석 완료
- [ ] Type A/B/C 분류 기준 확정
- [ ] 구현 우선순위 순서 결정
- [ ] 첫 번째 변수(ATR) 파라미터 추가 제안 완성

**최종 목표 (3주 후):**
- [ ] 22개 모든 변수 분석 완료
- [ ] 필요한 새 변수 목록 확정
- [ ] 계산기 클래스 아키텍처 설계
- [ ] 구현 로드맵 수립

---

## 🚨 **주의사항**

1. **사용자 복잡도 최우선** - 파라미터 3개 이하 유지
2. **기존 호환성** - 현재 전략이 깨지지 않도록 주의
3. **성능 고려** - 복잡한 계산은 별도 변수로 분리
4. **실용성 검증** - 도움말의 아이디어가 실제로 유용한지 판단

---

**다음 에이전트에게: 화이팅! 정말 혁신적인 시스템이 될 것 같습니다! 🚀**

**이전 작업자 노트:**
- 22개 도움말 작성이 정말 큰 작업이었습니다
- 각 도움말에는 정말 혁신적인 아이디어들이 많이 포함되어 있어요
- 특히 ATR, RSI, MACD의 고급 기능들이 인상적입니다
- 화이팅하세요! 🎉

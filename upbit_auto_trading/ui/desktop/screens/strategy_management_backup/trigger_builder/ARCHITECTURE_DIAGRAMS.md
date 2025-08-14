# 트리거 빌더 시스템 아키텍처 다이어그램

## 🏗️ **전체 시스템 아키텍처**

```mermaid
graph TB
    subgraph "Strategy Management Screen"
        SMS[StrategyManagementScreen]
        SMS --> TBS[TriggerBuilderScreen]
        SMS --> SMTab[StrategyMaker Tab]
        SMS --> BTTab[Backtest Tab]
        SMS --> MTTab[Monitor Tab]
    end

    subgraph "TriggerBuilder Main (trigger_builder_screen.py)"
        TBS --> CD[ConditionDialog<br/>조건 생성/편집]
        TBS --> TLW[TriggerListWidget<br/>트리거 목록]
        TBS --> SCW[SimulationControlWidget<br/>시뮬레이션 제어]
        TBS --> TDW[TriggerDetailWidget<br/>트리거 상세]
        TBS --> SRW[SimulationResultWidget<br/>시뮬레이션 결과]
    end

    subgraph "Core Components (components/core/)"
        CD --> CS[ConditionStorage<br/>조건 저장/로드]
        TLW --> CS
        TDW --> CS
        SCW --> DSS[DataSourceSelector<br/>데이터 소스 선택]
        SRW --> CV[ChartVisualizer<br/>차트 시각화]
    end

    subgraph "Shared Components (components/shared/)"
        CV --> TC[TriggerCalculator<br/>트리거 계산]
        CV --> CVS[ChartVariableService<br/>차트 변수 서비스]
        SCW --> TSS[TriggerSimulationService<br/>트리거 시뮬레이션]
        TSS --> TC
    end

    subgraph "Shared Simulation (shared_simulation/)"
        TSS --> SE[SimulationEngines<br/>시뮬레이션 엔진]
        DSS --> DSM[DataSourceManager<br/>데이터 소스 관리]
        SE --> ESE[EmbeddedSimulationEngine]
        SE --> RSE[RobustSimulationEngine]
        SE --> RDS[RealDataSimulation]
    end

    subgraph "Data Layer"
        CS --> DB[(SQLite Database<br/>app_settings.sqlite3)]
        DSM --> MDB[(Market Data<br/>sampled_market_data.sqlite3)]
        ESE --> IDD[Internal Data<br/>내장 데이터셋]
    end

    classDef mainScreen fill:#e1f5fe
    classDef coreComp fill:#f3e5f5
    classDef sharedComp fill:#e8f5e8
    classDef simulation fill:#fff3e0
    classDef dataLayer fill:#fce4ec

    class TBS mainScreen
    class CD,TLW,SCW,TDW,SRW coreComp
    class TC,CVS,TSS sharedComp
    class SE,ESE,RSE,RDS,DSM simulation
    class DB,MDB,IDD dataLayer
```

## 🔄 **데이터 플로우 다이어그램**

```mermaid
sequenceDiagram
    participant User as 👤 사용자
    participant TBS as TriggerBuilderScreen
    participant CD as ConditionDialog
    participant CS as ConditionStorage
    participant SCW as SimulationControlWidget
    participant SE as SimulationEngine
    participant SRW as SimulationResultWidget

    Note over User,SRW: 트리거 생성 및 시뮬레이션 플로우

    User->>CD: 1. 조건 입력
    CD->>CS: 2. 조건 저장
    CS->>TBS: 3. 저장 완료 이벤트
    TBS->>SCW: 4. 트리거 선택
    
    User->>SCW: 5. 시뮬레이션 버튼 클릭
    SCW->>SE: 6. 시뮬레이션 요청
    SE->>SE: 7. 데이터 로드 & 계산
    SE->>SRW: 8. 결과 반환
    SRW->>User: 9. 차트 & 결과 표시
```

## 🧩 **컴포넌트 의존성 그래프**

```mermaid
graph LR
    subgraph "UI Layer"
        A[TriggerBuilderScreen] --> B[ConditionDialog]
        A --> C[TriggerListWidget]
        A --> D[SimulationControlWidget]
        A --> E[TriggerDetailWidget]
        A --> F[SimulationResultWidget]
    end

    subgraph "Business Logic"
        B --> G[ConditionStorage]
        C --> G
        E --> G
        D --> H[DataSourceSelector]
        F --> I[ChartVisualizer]
        D --> J[TriggerSimulationService]
    end

    subgraph "Core Services"
        I --> K[TriggerCalculator]
        J --> K
        J --> L[SimulationEngines]
        H --> M[DataSourceManager]
    end

    subgraph "Data Sources"
        L --> N[EmbeddedEngine]
        L --> O[RobustEngine]
        L --> P[RealDataEngine]
        M --> Q[(Market Data DB)]
        G --> R[(App Settings DB)]
    end

    classDef ui fill:#bbdefb
    classDef business fill:#c8e6c9
    classDef core fill:#ffecb3
    classDef data fill:#ffcdd2

    class A,B,C,D,E,F ui
    class G,H,I,J business
    class K,L,M core
    class N,O,P,Q,R data
```

## 🚨 **폴백 제거 정책 적용 흐름**

```mermaid
flowchart TD
    Start([코드 실행 시작]) --> ImportTry{Import 시도}
    
    ImportTry -->|성공| Success[✅ 정상 실행]
    ImportTry -->|실패| ErrorDecision{폴백 있음?}
    
    ErrorDecision -->|폴백 있음<br/>❌ Before| HideError[에러 숨김<br/>더미 객체 생성]
    ErrorDecision -->|폴백 없음<br/>✅ After| ShowError[명확한 에러 표시<br/>ModuleNotFoundError]
    
    HideError --> Debug30[🐌 디버깅 30분<br/>원인 불명]
    ShowError --> Debug3[⚡ 디버깅 3분<br/>정확한 경로 문제]
    
    Debug30 --> Eventually[결국 해결]
    Debug3 --> QuickFix[빠른 해결]
    
    Success --> Running[시스템 정상 동작]
    QuickFix --> Running
    Eventually --> Running
    
    classDef success fill:#c8e6c9
    classDef error fill:#ffcdd2
    classDef good fill:#e1f5fe
    classDef bad fill:#fff3e0
    
    class Success,Running,QuickFix success
    class HideError,Debug30 bad
    class ShowError,Debug3 good
    class ImportTry,ErrorDecision error
```

## 📊 **현재 상태 대시보드**

```mermaid
pie title 트리거 빌더 완성도
    "완료된 기능" : 85
    "미세 조정 필요" : 10
    "남은 작업" : 5
```

```mermaid
gantt
    title 트리거 빌더 개발 진행상황
    dateFormat X
    axisFormat %s

    section 핵심 기능
    폴백 코드 제거    :done, fallback, 0, 1
    Import 경로 수정  :done, import, 1, 2
    데이터 소스 복구  :done, datasource, 2, 3
    트리거 리스트     :done, triggerlist, 3, 4
    시뮬레이션 엔진   :done, simulation, 4, 5
    
    section 미세 조정
    MiniSimulation   :active, mini, 5, 6
    차트 개선        :crit, chart, 6, 7
    에러 UI          :error, 7, 8
```

---

## 🎯 **다음 에이전트 작업 가이드**

### 1️⃣ **즉시 확인할 파일들**
```
📁 trigger_builder/
├── 📄 trigger_builder_screen.py (1616 lines) - 메인 화면
├── 📁 components/core/condition_storage.py - 조건 저장
├── 📁 components/shared/__init__.py - 공유 컴포넌트 
└── 📁 shared_simulation/engines/ - 시뮬레이션 엔진
```

### 2️⃣ **남은 에러 해결**
```python
# 1. MiniSimulationService import 경로 정리
# 위치: components/mini_simulation/__init__.py
from .services.mini_simulation_service import MiniSimulationService

# 2. 시뮬레이션 결과 차트 미세 조정
# 위치: trigger_builder_screen.py:569
ax.text(0.5, 0.5, f"❌ 시뮬레이션 실패\n\n{str(e)[:100]}...")
```

### 3️⃣ **성공 기준**
- [ ] 모든 시뮬레이션 버튼 정상 동작
- [ ] 미니 차트에 실제 데이터 표시  
- [ ] 에러 시에도 명확한 메시지 표시

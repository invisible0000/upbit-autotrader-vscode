# **시스템 아키텍처 설계서: 업비트 자동매매 시스템**

## **1. 개요**

이 문서는 업비트 자동매매 시스템의 전체적인 기술 아키텍처를 정의합니다. 시스템을 구성하는 주요 컴포넌트, 계층 구조, 데이터 흐름, 그리고 기술 스택을 설명하여 프로젝트의 구조적 이해를 돕고 일관성 있는 개발을 지원하는 것을 목표로 합니다.

## **2. 아키텍처 목표**

본 시스템은 다음과 같은 아키텍처 목표를 가집니다.

* **모듈성 (Modularity)**: 각 기능(데이터 수집, 전략, 백테스팅 등)을 독립적인 모듈로 분리하여 개발 및 유지보수가 용이하도록 합니다.  
* **확장성 (Scalability)**: 새로운 거래 전략, 기술적 지표, 또는 데이터 소스를 쉽게 추가할 수 있는 유연한 구조를 지향합니다.  
* **안정성 (Stability)**: API 요청 제한, 예외 처리, 데이터 무결성 유지를 통해 시스템이 안정적으로 운영되도록 합니다.  
* **테스트 용이성 (Testability)**: 각 컴포넌트가 독립적으로 테스트 가능하도록 설계하여 코드의 신뢰성을 높입니다.

## **3. 시스템 아키텍처 (C4 모델 기반)**

### **3.1. Level 1: 시스템 컨텍스트 (System Context)**

시스템의 최상위 레벨 다이어그램으로, 자동매매 시스템과 외부 시스템 및 사용자 간의 관계를 보여줍니다.

```mermaid
graph LR
    subgraph "사용자 그룹"
        User["사용자<br>(Web/CLI 이용)"]
    end

    subgraph "업비트 거래소 시스템"
        UpbitExchange["업비트 거래소<br>(REST API & WSS)"]
    end

    subgraph "내부 자동매매 시스템"
        AutoTradingSystem("업비트 자동매매 시스템<br>(Python 기반)")
    end

    User <--> AutoTradingSystem
    AutoTradingSystem <--> UpbitExchange

    style User fill:#E6F2F8,stroke:#6CB6D8,stroke-width:2px,color:#000
    style UpbitExchange fill:#FFE0B2,stroke:#FF8C00,stroke-width:2px,color:#000
    style AutoTradingSystem fill:#DDEECC,stroke:#6B8E23,stroke-width:2px,color:#000
```

* **사용자**: 웹 브라우저나 CLI를 통해 시스템과 상호작용하며, 전략을 설정하고 거래 현황을 모니터링합니다.  
* **업비트 자동매매 시스템**: 본 프로젝트의 핵심 시스템으로, 시장 데이터를 분석하고 거래를 실행합니다.  
* **업비트 거래소**: REST API를 통해 시세 정보, 계좌 정보, 주문 실행 등의 기능을 제공하는 외부 시스템입니다.

### **3.2. Level 2: 컨테이너 다이어그램 (Container Diagram)**

시스템 내부를 구성하는 주요 실행 단위(컨테이너)들을 보여줍니다.

+----------------------------------------------------------------------+  
| 사용자 (Web Browser / Command Line)                                  |  
+----------------------------------------------------------------------+  
       | ▲                                                       | ▲  
       | | HTTP/API 요청                                         | | CLI 명령어  
       ▼ |                                                       ▼ |  
+------------------+       +---------------------------------------------+  
|                  |       |                                             |  
|   UI 계층         |------>|             핵심 애플리케이션 (Python)            |  
| (Flask Web / CLI)|       |                                             |  
|                  |       +---------------------------------------------+  
+------------------+                         | ▲  
                                             | | SQL (SQLAlchemy)  
                                             ▼ |  
                                     +------------------+  
                                     |                  |  
                                     |    데이터베이스     |  
                                     | (SQLite / MySQL) |  
                                     |                  |  
                                     +------------------+

* **UI 계층 (User Interface Layer)**: 사용자의 입력을 받아 핵심 애플리케이션에 전달하고, 그 결과를 사용자에게 보여주는 역할을 합니다. ui/web/app.py (Flask) 또는 ui/cli/app.py로 구성됩니다.  
* **핵심 애플리케이션 (Core Application)**: 모든 비즈니스 로직과 데이터 처리를 담당하는 시스템의 심장부입니다. business\_logic과 data\_layer가 여기에 해당합니다.  
* **데이터베이스 (Database)**: 시장 데이터, 전략 설정, 백테스트 결과, 거래 기록 등 모든 영구 데이터를 저장합니다. DatabaseManager를 통해 관리되며, config.yaml 설정에 따라 SQLite, MySQL 등으로 구성될 수 있습니다.

### **3.3. Level 3: 컴포넌트 다이어그램 (Component Diagram)**

'핵심 애플리케이션' 컨테이너 내부를 더 상세한 컴포넌트 단위로 분해합니다.

\+---------------------------------------------------------------------------------+  
| 핵심 애플리케이션 (Python)                                                      |  
|                                                                                 |  
|   \+---------------------------------------------------------------------------+ |  
|   | 비즈니스 로직 계층 (Business Logic Layer)                                   | |  
|   |                                                                           | |  
|   | \+----------+ \+----------+ \+-----------+ \+------------+ \+----------+      | |  
|   | | Screener | | Strategy | | Portfolio | | Backtester | |  Trader  |      | |  
|   | \+----------+ \+----------+ \+-----------+ \+------------+ \+----------+      | |  
|   \+--------------------------------|------------------------------------------+ |  
|                                    | ▲                                          |  
|   \+--------------------------------|------------------------------------------+ |  
|   | 데이터 계층 (Data Layer)         | |                                          |  
|   |                                  | |                                          |  
|   | \+------------+ \+-------------+ \+-----------------------------------------+ |  
|   | | Collectors | | Processors  | |                 Storage                 | |  
|   | | (UpbitAPI) | |(Indicators) | | (DB Manager, Models, Backup, Migration) | |  
|   | \+------------+ \+-------------+ \+-----------------------------------------+ |  
|   \+---------------------------------------------------------------------------+ |  
|                                                                                 |  
\+---------------------------------------------------------------------------------+

* **UI 계층 (상위)**: 사용자의 요청을 받아 비즈니스 로직 계층의 각 컴포넌트에 전달합니다.  
* **비즈니스 로직 계층 (business\_logic/)**: 시스템의 핵심 로직을 수행합니다.  
  * **Screener**: BaseScreener를 통해 거래량, 변동성 등 조건에 맞는 코인을 필터링합니다.  
  * **Strategy**: StrategyManager와 StrategyFactory를 통해 MovingAverageCrossStrategy와 같은 매매 전략을 생성, 관리, 저장합니다.  
  * **Portfolio**: PortfolioManager와 PortfolioPerformance를 통해 여러 자산과 전략의 조합을 구성하고 성과를 분석합니다.  
  * **Backtester**: BacktestRunner와 BacktestAnalyzer를 통해 전략을 과거 데이터로 검증하고 결과를 분석/저장합니다.  
  * **Trader**: (구현 예정) 실시간 거래를 실행하고 포지션을 관리합니다.  
* **데이터 계층 (data\_layer/)**: 데이터의 수집, 처리, 저장을 담당합니다.  
  * **Collectors**: UpbitAPI를 통해 업비트로부터 실시간/과거 시장 데이터를 수집하고, DataCollector가 이를 관리합니다.  
  * **Processors**: DataProcessor가 수집된 데이터로부터 이동평균선(SMA), RSI 등 기술적 지표를 계산합니다.  
  * **Storage**: DatabaseManager가 데이터베이스 연결을 관리하고, models.py에 정의된 스키마에 따라 데이터를 저장/조회합니다. BackupManager와 MigrationManager는 데이터베이스의 유지보수를 담당합니다.

## **4. 데이터 흐름 예시**

### **시나리오 1: 백테스트 실행**

1. **UI 계층**: 사용자가 '백테스팅' 화면에서 전략, 기간, 초기 자본을 설정하고 '실행' 버튼을 클릭합니다.  
2. **Backtester**: BacktestRunner가 요청을 받아 config 객체를 생성합니다.  
3. **Data Layer**: BacktestRunner는 DataCollector를 통해 해당 기간의 시장 데이터를 데이터베이스에서 로드합니다. 데이터가 부족하면 UpbitAPI를 통해 추가 수집합니다.  
4. **Data Layer**: DataProcessor가 로드된 데이터에 대해 전략에 필요한 기술적 지표(예: SMA, RSI)를 계산합니다.  
5. **Strategy**: BacktestRunner는 Strategy 컴포넌트의 generate\_signals()를 호출하여 매수/매도 신호를 생성합니다.  
6. **Backtester**: BacktestRunner는 신호에 따라 가상 거래를 시뮬레이션하고, 거래 내역과 자본 변화 곡선을 생성합니다.  
7. **Backtester**: BacktestAnalyzer가 최종 결과를 분석하여 수익률, MDD 등 성과 지표를 계산하고 시각화 자료를 만듭니다.  
8. **UI 계층**: 분석된 결과 리포트가 사용자 화면에 표시됩니다.

## **5. 기술 스택**

* **언어**: Python 3.8+  
* **API 통신**: requests, websockets  
* **데이터 처리**: pandas, numpy  
* **데이터베이스**: SQLAlchemy (ORM), SQLite (기본), PyMySQL (MySQL 지원)  
* **웹 프레임워크**: Flask  
* **설정/로깅**: PyYAML, logging  
* **테스트**: unittest, pytest
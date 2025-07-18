# **API 명세서 (API Specification)**

## **1\. 개요**

이 문서는 업비트 자동매매 시스템의 웹 UI와 백엔드 서버 간의 통신을 위한 RESTful API를 정의합니다. 각 API 엔드포인트의 요청(Request) 및 응답(Response) 형식을 명확히 하여 프론트엔드와 백엔드 개발의 일관성을 유지하는 것을 목표로 합니다.

**기본 URL**: http://\<your-domain\>/api

**공통 응답 형식**:

* **성공**:  
  {  
    "status": "success",  
    "data": { ... }  
  }

* **실패**:  
  {  
    "status": "error",  
    "message": "Error description message."  
  }

## **2\. 종목 스크리닝 (Screener)**

### **POST /screener/run**

* **설명**: 설정된 조건으로 새로운 종목 스크리닝을 실행합니다.  
* **관련 코드**: BaseScreener.screen\_coins()  
* **요청 본문 (Request Body)**:  
  {  
    "criteria": \[  
      {  
        "type": "volume",  
        "params": { "min\_volume": 1000000000 }  
      },  
      {  
        "type": "volatility",  
        "params": { "min\_volatility": 0.05, "max\_volatility": 0.2 }  
      }  
    \]  
  }

* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": \[  
      {  
        "symbol": "KRW-BTC",  
        "name": "비트코인",  
        "current\_price": 50000000,  
        "volume\_24h": 5000000000,  
        "matched\_criteria": \["volume", "volatility"\]  
      }  
    \]  
  }

### **GET /screener/results**

* **설명**: 저장된 모든 스크리닝 결과 목록을 조회합니다.  
* **관련 코드**: ScreenerResult.get\_screening\_results()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": \[  
      {  
        "id": 1,  
        "name": "고거래량 스크리닝",  
        "description": "...",  
        "criteria": "\[...\]",  
        "created\_at": "2025-07-18T10:00:00",  
        "coin\_count": 5  
      }  
    \]  
  }

### **POST /screener/results**

* **설명**: 현재 스크리닝 결과를 저장합니다.  
* **관련 코드**: ScreenerResult.save\_screening\_result()  
* **요청 본문 (Request Body)**:  
  {  
    "name": "나의 첫 스크리닝",  
    "description": "거래량과 변동성 동시 만족",  
    "criteria": \[ ... \],  
    "results": \[ ... \]  
  }

* **성공 응답 (201 Created)**:  
  {  
    "status": "success",  
    "data": {  
      "result\_id": 1  
    }  
  }

## **3\. 매매 전략 (Strategies)**

### **GET /strategies**

* **설명**: 저장된 모든 매매 전략 목록을 조회합니다.  
* **관련 코드**: StrategyManager.get\_strategy\_list()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": \[  
      {  
        "id": "strategy-uuid-1",  
        "name": "나의 이동평균 전략",  
        "description": "단기/장기 이동평균 교차 전략",  
        "strategy\_type": "moving\_average\_cross",  
        "updated\_at": "2025-07-18T11:00:00"  
      }  
    \]  
  }

### **POST /strategies**

* **설명**: 새로운 매매 전략을 생성하고 저장합니다.  
* **관련 코드**: StrategyManager.save\_strategy()  
* **요청 본문 (Request Body)**:  
  {  
    "strategy\_id": "strategy-uuid-new",  
    "strategy\_type": "moving\_average\_cross",  
    "name": "새로운 전략",  
    "description": "...",  
    "parameters": {  
      "short\_window": 10,  
      "long\_window": 30  
    }  
  }

* **성공 응답 (201 Created)**:  
  {  
    "status": "success",  
    "data": {  
      "strategy\_id": "strategy-uuid-new"  
    }  
  }

### **GET /strategies/{strategy\_id}**

* **설명**: 특정 ID의 전략 상세 정보를 불러옵니다.  
* **관련 코드**: StrategyManager.load\_strategy() (반환된 객체를 dict로 변환)  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "id": "strategy-uuid-1",  
      "name": "나의 이동평균 전략",  
      "description": "...",  
      "strategy\_type": "moving\_average\_cross",  
      "parameters": { "short\_window": 10, "long\_window": 30 }  
    }  
  }

### **PUT /strategies/{strategy\_id}**

* **설명**: 특정 ID의 전략 정보를 수정합니다.  
* **관련 코드**: StrategyManager.update\_strategy()  
* **요청 본문 (Request Body)**:  
  {  
    "name": "수정된 전략 이름",  
    "parameters": { "short\_window": 15, "long\_window": 40 }  
  }

* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "strategy\_id": "strategy-uuid-1"  
    }  
  }

### **DELETE /strategies/{strategy\_id}**

* **설명**: 특정 ID의 전략을 삭제합니다.  
* **관련 코드**: StrategyManager.delete\_strategy()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "strategy\_id": "strategy-uuid-1"  
    }  
  }

## **4\. 백테스팅 (Backtesting)**

### **POST /backtest/run**

* **설명**: 새로운 백테스트를 실행합니다.  
* **관련 코드**: BacktestRunner.execute\_backtest(), PortfolioBacktest.run\_portfolio\_backtest()  
* **요청 본문 (Request Body)**:  
  {  
    "target\_type": "strategy", // "strategy" or "portfolio"  
    "target\_id": "strategy-uuid-1",  
    "symbol": "KRW-BTC", // strategy일 경우 필수  
    "config": {  
      "start\_date": "2024-01-01T00:00:00",  
      "end\_date": "2024-12-31T23:59:59",  
      "initial\_capital": 10000000,  
      "timeframe": "1h",  
      "fee\_rate": 0.0005,  
      "slippage": 0.0002  
    }  
  }

* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "id": "backtest-result-uuid-1",  
      "performance\_metrics": { ... },  
      "equity\_curve": { ... },  
      "trades": \[ ... \]  
    }  
  }

### **GET /backtest/results**

* **설명**: 저장된 모든 백테스트 결과 목록을 조회합니다.  
* **관련 코드**: BacktestResultsManager.list\_backtest\_results()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": \[  
      {  
        "id": "backtest-result-uuid-1",  
        "symbol": "KRW-BTC",  
        "strategy\_id": "strategy-uuid-1",  
        "total\_return\_percent": 15.7,  
        "created\_at": "2025-07-18T12:00:00"  
      }  
    \]  
  }

### **GET /backtest/results/{result\_id}**

* **설명**: 특정 ID의 백테스트 상세 결과를 불러옵니다.  
* **관련 코드**: BacktestResultsManager.load\_backtest\_result()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "id": "backtest-result-uuid-1",  
      "performance\_metrics": { ... },  
      "equity\_curve": { ... },  
      "trades": \[ ... \]  
    }  
  }

## **5\. 포트폴리오 (Portfolios)**

### **GET /portfolios**

* **설명**: 저장된 모든 포트폴리오 목록을 조회합니다.  
* **관련 코드**: PortfolioManager.get\_all\_portfolios()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": \[  
      {  
        "id": "portfolio-uuid-1",  
        "name": "안정 성장형 포트폴리오",  
        "description": "...",  
        "coin\_count": 3,  
        "updated\_at": "2025-07-18T13:00:00"  
      }  
    \]  
  }

### **POST /portfolios**

* **설명**: 새로운 포트폴리오를 생성합니다.  
* **관련 코드**: PortfolioManager.create\_portfolio()  
* **요청 본문 (Request Body)**:  
  {  
    "name": "새 포트폴리오",  
    "description": "분산 투자 목적"  
  }

* **성공 응답 (201 Created)**:  
  {  
    "status": "success",  
    "data": {  
      "portfolio\_id": "portfolio-uuid-new"  
    }  
  }

### **GET /portfolios/{portfolio\_id}**

* **설명**: 특정 ID의 포트폴리오 상세 정보를 불러옵니다.  
* **관련 코드**: PortfolioManager.get\_portfolio()  
* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "id": "portfolio-uuid-1",  
      "name": "안정 성장형 포트폴리오",  
      "coins": \[  
        { "symbol": "KRW-BTC", "strategy\_id": "strategy-uuid-1", "weight": 0.5 },  
        { "symbol": "KRW-ETH", "strategy\_id": "strategy-uuid-2", "weight": 0.5 }  
      \]  
    }  
  }

### **POST /portfolios/{portfolio\_id}/coins**

* **설명**: 특정 포트폴리오에 코인을 추가합니다.  
* **관련 코드**: PortfolioManager.add\_coin\_to\_portfolio()  
* **요청 본문 (Request Body)**:  
  {  
    "symbol": "KRW-XRP",  
    "strategy\_id": "strategy-uuid-3",  
    "weight": 0.2  
  }

* **성공 응답 (200 OK)**:  
  {  
    "status": "success",  
    "data": {  
      "portfolio\_id": "portfolio-uuid-1"  
    }  
  }  

# **배포 및 운영 가이드 (Deployment & Operations Guide)**

## **1\. 개요**

이 문서는 업비트 자동매매 시스템을 실제 서버 환경에 배포하고 안정적으로 운영하기 위한 절차와 방법을 안내합니다. 시스템 설치, 설정, 실행부터 데이터베이스 관리(마이그레이션, 백업) 및 주요 운영 작업까지의 전 과정을 다룹니다.

## **2\. 시스템 요구사항**

* **소프트웨어**:  
  * Python 3.8 이상  
  * Git  
  * (선택) MySQL 또는 PostgreSQL 데이터베이스 서버  
* **API 키**:  
  * 업비트(Upbit) 거래소의 Access Key와 Secret Key

## **3\. 배포 절차**

### **3.1. 소스 코드 복제 및 환경 설정**

1. **Git 저장소 복제**:  
   git clone \<your-repository-url\>  
   cd upbit-auto-trading

2. **가상환경 생성 및 활성화**:  
   \# 가상환경 생성  
   python \-m venv venv

   \# 가상환경 활성화 (Linux/macOS)  
   source venv/bin/activate

   \# 가상환경 활성화 (Windows)  
   venv\\Scripts\\activate

3. **필수 라이브러리 설치**:  
   pip install \-r requirements.txt

### **3.2. 환경 변수 설정**

시스템의 민감한 정보(API 키)는 .env 파일을 통해 관리합니다. 프로젝트 루트 디렉토리에 .env 파일을 생성하고 다음 내용을 추가하세요.

**.env 파일 예시:**

UPBIT\_ACCESS\_KEY=your\_access\_key\_here  
UPBIT\_SECRET\_KEY=your\_secret\_key\_here

* **관련 코드**: upbit\_auto\_trading/data\_layer/collectors/upbit\_api.py에서 os.environ.get()을 통해 이 키들을 불러옵니다.

### **3.3. 시스템 설정**

config/config.yaml 파일은 시스템의 주요 동작을 제어합니다. 운영 환경에 맞게 이 파일을 수정해야 합니다.

**config/config.yaml 주요 설정:**

\# 데이터베이스 설정  
database:  
  type: "sqlite"  \# 운영 환경에서는 "mysql" 또는 "postgresql" 권장  
  path: "data/upbit\_auto\_trading.db"  
  \# host: "localhost"  
  \# username: "user"  
  \# password: "password"  
  \# database\_name: "upbit\_auto\_trading"

\# 로깅 설정  
logging:  
  level: "INFO"  \# 운영 환경에서는 "INFO", 개발/디버깅 시 "DEBUG"  
  file: "logs/upbit\_auto\_trading.log"

### **3.4. 데이터베이스 초기화 및 마이그레이션**

1. **데이터베이스 생성**: config.yaml에 설정된 정보에 따라 데이터베이스(예: MySQL에서 upbit\_auto\_trading 스키마)를 미리 생성해야 합니다.  
2. **테이블 초기화**: 시스템을 처음 실행하면 DatabaseManager가 models.py에 정의된 스키마에 따라 필요한 모든 테이블을 자동으로 생성합니다.  
   * **관련 코드**: upbit\_auto\_trading/data\_layer/storage/database\_manager.py  
3. **데이터베이스 마이그레이션**: 향후 데이터베이스 스키마가 변경될 경우, MigrationManager를 사용하여 안전하게 변경사항을 적용해야 합니다.  
   * **새 마이그레이션 파일 생성**:  
     \# 예시: python \-m upbit\_auto\_trading.data\_layer.storage.migration\_manager \--create "add\_user\_email\_column"  
     \# (별도의 실행 스크립트 구현 필요)

   * **마이그레이션 적용**: 시스템 시작 시 보류 중인 마이그레이션을 자동으로 적용하거나, 별도의 관리 스크립트를 통해 수동으로 적용할 수 있습니다.  
   * **관련 코드**: upbit\_auto\_trading/data\_layer/storage/migration\_manager.py

## **4\. 시스템 실행**

시스템은 run.py 스크립트를 통해 실행할 수 있으며, CLI 모드와 웹 UI 모드를 지원합니다.

### **4.1. 실행 명령어**

\# 기본 실행 (CLI 모드)  
python run.py

\# 웹 UI 모드로 실행  
python run.py \--mode web

\# 다른 설정 파일 사용  
python run.py \--config config/production\_config.yaml

\# 디버그 모드로 실행  
python run.py \--debug

* **관련 코드**: upbit\_auto\_trading/\_\_main\_\_.py

## **5\. 운영 및 유지보수**

### **5.1. 데이터 수집**

시스템은 DataCollector를 통해 주기적으로 시장 데이터를 수집하고 데이터베이스에 저장합니다. 실시간 거래 및 분석을 위해 이 프로세스가 백그라운드에서 안정적으로 실행되어야 합니다.

* **주요 기능**: start\_ohlcv\_collection(), start\_orderbook\_collection()  
* **관련 코드**: upbit\_auto\_trading/data\_layer/collectors/data\_collector.py

### **5.2. 데이터베이스 백업 및 복원**

BackupManager는 데이터베이스의 스냅샷을 생성하고 필요시 복원하는 기능을 제공합니다. 정기적인 백업은 필수입니다.

* **백업 실행 (예시)**:  
  \# 별도의 관리 스크립트에서 실행  
  from upbit\_auto\_trading.data\_layer.storage.backup\_manager import BackupManager  
  bm \= BackupManager()  
  backup\_file\_path \= bm.backup()  
  print(f"백업 완료: {backup\_file\_path}")

* **복원 실행 (예시)**:  
  \# 시스템 중지 후 실행 필요  
  bm.restore("/path/to/your/backup\_file.db")  
  print("복원 완료")

* **관련 코드**: upbit\_auto\_trading/data\_layer/storage/backup\_manager.py

### **5.3. 로그 모니터링**

시스템의 모든 주요 활동과 오류는 로그 파일에 기록됩니다. 시스템 상태를 확인하고 문제를 해결하기 위해 정기적으로 로그를 확인해야 합니다.

* **일반 로그**: logs/upbit\_auto\_trading.log  
* **오류 로그**: logs/error.log (설정에 따라 다름)  
* **관련 설정**: config/logging\_config.yaml

### **5.4. 시스템 상태 확인 및 테스트**

시스템이 정상적으로 동작하는지 확인하기 위해 run\_tests\_in\_order.py 스크립트를 사용하여 전체 유닛 테스트를 실행할 수 있습니다. 배포 후 또는 주요 변경사항 적용 후 실행을 권장합니다.

python run\_tests\_in\_order.py

* 실행 결과는 upbit\_auto\_trading/docs/test\_results\_summary.md 파일에 요약됩니다.
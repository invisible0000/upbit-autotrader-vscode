# 📋 Infrastructure Layer 서비스 배치 적절성 검토

## 🎯 분석 대상: upbit_auto_trading/infrastructure/services/ 폴더

### 📊 **서비스별 Infrastructure Layer 적절성 평가**

---

## ✅ **Infrastructure Layer에 적절한 서비스들 (외부 연결 관점)**

### **1. 🔑 api_key_service.py** - ⭐⭐⭐⭐⭐ **완벽 적합**

```python
# ✅ 외부 라이브러리: cryptography.fernet (외부 암호화 시스템)
# ✅ 외부 저장소: 파일 시스템 (OS 레벨 보안 저장소)
# ✅ 외부 보안 정책: OS 메모리 관리, GC와 연동
# ✅ 하드웨어 의존: 암호화 키 생성, 보안 엔트로피
```

**Infrastructure 배치 근거 (외부 연결 관점)**:

- **외부 암호화 라이브러리**: cryptography는 외부 보안 시스템
- **외부 파일 시스템**: OS 레벨 보안 저장소와 연동
- **외부 하드웨어**: 보안 엔트로피, 메모리 보안 정책

### **2. 🗄️ database_connection_service.py** - ⭐⭐⭐⭐⭐ **완벽 적합**

```python
# ✅ 외부 시스템 연동: SQLite3 데이터베이스
# ✅ 리소스 관리: 연결 풀, Circuit Breaker 패턴
# ✅ 인프라 관심사: 연결 상태 모니터링, Health Check
# ✅ 기술적 복잡성: Threading, Context Manager
```

**Infrastructure 배치 근거**:

- **외부 시스템**: 데이터베이스 연결 및 관리
- **리소스 관리**: Connection Pooling, Thread Safety
- **기술적 패턴**: Circuit Breaker, Health Check

### **3. 📁 file_system_service.py** - ⭐⭐⭐⭐⭐ **완벽 적합**

```python
# ✅ 외부 시스템 연동: 파일 시스템, OS 레벨 작업
# ✅ 어댑터 패턴: Domain 요구사항 → OS API 변환
# ✅ 원자적 연산: 파일 안전성 보장
# ✅ 에러 처리: OS 예외 → Domain 예외 변환
```

**Infrastructure 배치 근거**:

- **외부 의존성**: 파일 시스템, OS API
- **기술적 복잡성**: 원자적 파일 연산, 체크섬 검증
- **어댑터 역할**: Domain과 OS 사이의 격리

### **4. 🌐 websocket_market_data_service.py** - ⭐⭐⭐⭐⭐ **완벽 적합**

```python
# ✅ 외부 API 연동: Upbit WebSocket API
# ✅ 비동기 처리: asyncio 기반 실시간 통신
# ✅ 이벤트 발행: Infrastructure → Domain Event 전파
# ✅ 네트워크 리소스 관리: 연결 상태, 재연결 로직
```

**Infrastructure 배치 근거**:

- **외부 API**: Upbit WebSocket 프로토콜
- **비동기 I/O**: 네트워크 통신 기술적 복잡성
- **이벤트 브리지**: 외부 데이터 → Domain Event 변환

### **5. 📊 websocket_status_service.py** - ⭐⭐⭐⭐ **적합**

```python
# ✅ 인프라 모니터링: WebSocket 연결 상태 추적
# ✅ 리소스 효율성: 상태 캐싱, 이벤트 기반 업데이트
# ✅ 기술적 관심사: 연결 모니터링, Health Check
```

**Infrastructure 배치 근거**:

- **기술 모니터링**: WebSocket 인프라 상태 관리
- **성능 최적화**: 상태 캐싱 및 효율적 폴링

---

## ⚠️ **배치 재검토가 필요한 서비스들**

### **6. 🎨 theme_service.py** - ⭐⭐ **부적절 (외부 연결 관점에서)**

```python
# ❌ 내부 UI 로직: 테마 변경, 스타일 적용 (외부 연결 아님)
# ❌ 사용자 비즈니스: 선호도 관리 (도메인/애플리케이션 관심사)
# ❓ Configuration 의존성: 설정 파일 읽기만 하는 정도
# ❌ PyQt6 결합: UI 프레임워크는 애플리케이션 내부
```

**외부 연결 관점에서 부적절한 이유**:

- **내부 로직**: 테마 선택과 적용은 애플리케이션 내부 워크플로우
- **사용자 비즈니스**: UI 선호도는 비즈니스 규칙 (외부 시스템 아님)
- **PyQt6는 내부**: UI 프레임워크는 애플리케이션의 일부

**개선 제안**:

```python
# 현재: Infrastructure Layer
upbit_auto_trading/infrastructure/services/theme_service.py

# 제안: Application Layer로 이동
upbit_auto_trading/application/services/ui_theme_service.py
```

### **7. ⚙️ settings_service.py** - ⭐ **완전 부적절 (외부 연결 관점에서)**

```python
# ❌ 내부 비즈니스: UI 설정, 매매 설정 관리 (외부 시스템 아님)
# ❌ 사용자 워크플로우: 애플리케이션 내부 로직 (외부 연결 무관)
# ❓ Configuration 파일: 단순 파일 읽기는 외부지만 주된 관심사 아님
# ❌ 도메인 개념: UIConfig, TradingConfig는 비즈니스 모델
```

**외부 연결 관점에서 완전 부적절**:

- **사용자 설정 관리**: 애플리케이션 내부 비즈니스 로직
- **UI/Trading Config**: 도메인 개념이며 외부 시스템과 무관
- **설정 워크플로우**: 사용자 Use Case (외부 연결이 아님)

**이동 제안**:

```python
# 현재: Infrastructure Layer (부적절)
upbit_auto_trading/infrastructure/services/settings_service.py

# 제안: Application Layer로 이동
upbit_auto_trading/application/services/settings_application_service.py
```

### **8. 📈 orderbook_data_service.py** - ⭐⭐⭐ **경계선 (하이브리드)**

```python
# ✅ Infrastructure 측면: WebSocket, REST API 연동
# ❓ Application 측면: 호가창 데이터는 비즈니스 도메인
# ❓ UI 결합: PyQt6 QObject, pyqtSignal 사용
# ✅ 이벤트 통합: 여러 데이터 소스 통합
```

**복잡성 분석**:

- **기술적 통합**: WebSocket + REST API 조합은 Infrastructure 관심사
- **데이터 의미**: 호가창은 Domain/Application 개념
- **UI 결합**: PyQt6 의존성으로 Presentation 성격도 있음

**현재 위치 유지 근거**:

- 외부 API 통합의 기술적 복잡성이 주된 관심사
- Infrastructure에서 데이터 수집 후 Application으로 전달하는 패턴

---

## 🎯 **개선 권장사항**

### **즉시 이동 권장 (Priority 1)**

#### **settings_service.py → Application Layer**

```bash
# 이동 경로
upbit_auto_trading/infrastructure/services/settings_service.py
→ upbit_auto_trading/application/services/settings_application_service.py
```

**이동 근거**:

- 사용자 설정 관리는 핵심 비즈니스 로직
- UIConfig, TradingConfig는 Domain 모델
- Infrastructure Configuration을 의존성으로 주입받아 사용

### **검토 후 결정 (Priority 2)**

#### **theme_service.py 위치 재평가**

```bash
# 옵션 1: Application Layer로 이동
upbit_auto_trading/application/services/ui_theme_service.py

# 옵션 2: 현재 위치 유지 (Configuration 중심 관점)
upbit_auto_trading/infrastructure/services/theme_service.py
```

**결정 기준**: 테마 서비스의 주된 역할이 Configuration 관리냐, UI 비즈니스 로직이냐

---

## 📊 **최종 평가 요약**

| 서비스 | 현재 위치 | 적절성 | 권장 조치 | 우선순위 |
|--------|-----------|--------|-----------|----------|
| api_key_service | Infrastructure | ⭐⭐⭐⭐⭐ | 유지 | - |
| database_connection_service | Infrastructure | ⭐⭐⭐⭐⭐ | 유지 | - |
| file_system_service | Infrastructure | ⭐⭐⭐⭐⭐ | 유지 | - |
| websocket_market_data_service | Infrastructure | ⭐⭐⭐⭐⭐ | 유지 | - |
| websocket_status_service | Infrastructure | ⭐⭐⭐⭐ | 유지 | - |
| orderbook_data_service | Infrastructure | ⭐⭐⭐ | 현재 유지 | 검토 |
| theme_service | Infrastructure | ⭐⭐⭐ | 재검토 | 중간 |
| settings_service | Infrastructure | ⭐⭐ | Application으로 이동 | **높음** |

---

## 💡 **레이어 배치 원칙 정리**

### ✅ **Infrastructure Layer에 적합한 서비스**

- 외부 시스템 연동 (DB, API, File System)
- 기술적 리소스 관리 (Connection Pool, Memory)
- 네트워크/보안/암호화 처리
- OS/하드웨어 레벨 작업
- Cross-cutting 기술 서비스

### ❌ **Infrastructure Layer에 부적합한 서비스**

- 비즈니스 로직 처리
- 사용자 워크플로우 관리
- Domain 모델 조작
- Application Use Case 구현
- UI 비즈니스 규칙

### 🤔 **경계선 케이스 판단 기준**

1. **주된 관심사**: 기술적 vs 비즈니스적
2. **외부 의존성**: 외부 시스템 연동 여부
3. **재사용성**: Cross-cutting vs 특정 도메인
4. **변경 이유**: 기술 변경 vs 비즈니스 요구사항 변경

---

> **🎯 결론**: 8개 서비스 중 6개는 Infrastructure Layer 배치가 적절하며,
> **settings_service.py**는 Application Layer로 이동 권장,
> **theme_service.py**는 추가 검토 필요

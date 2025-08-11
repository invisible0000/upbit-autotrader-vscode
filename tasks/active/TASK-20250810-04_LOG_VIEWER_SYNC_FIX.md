# TASK-20250810-04: 로그 뷰어 표시 내용 동기화

## 📋 작업 개요
**우선순위**: 🟢 보통
**담당자**: GitHub Copilot
**생성일**: 2025-08-10
**예상 소요**: 1-2시간

## 🎯 문제 정의
로그 뷰어에 표시되는 내용과 실제 로그 파일의 내용이 일치하지 않아 개발자의 디버깅 효율성이 크게 저하되고 있음. 실시간 로그 모니터링의 신뢰성 문제.

## 🔍 현재 상태 분석
- ❌ 로그 뷰어 표시 내용 ≠ 실제 로그 파일 내용
- ❌ 실시간 업데이트 누락 또는 지연 발생
- ❌ 로그 필터링 로직 오류 가능성
- ✅ 로그 파일 자체는 정상적으로 생성됨

## 📊 서브 태스크 분할

### **서브태스크 4.1: 로그 파일 읽기 로직 검증** (난이도: ⭐⭐)
- [ ] **4.1.1**: LogViewerWidget의 파일 읽기 메서드 정확성 검증
- [ ] **4.1.2**: 파일 인코딩 및 줄바꿈 처리 확인
- [ ] **4.1.3**: 대용량 로그 파일 처리 성능 테스트

**TDD 테스트**:
```python
def test_log_file_reading_accuracy():
    """로그 파일 읽기 정확성 테스트"""
    # 테스트용 로그 파일 생성
    test_log_content = [
        "2025-08-10 21:16:46 - INFO - Test message 1",
        "2025-08-10 21:16:47 - DEBUG - Test message 2",
        "2025-08-10 21:16:48 - ERROR - Test message 3"
    ]
    test_log_path = Path("test_session.log")
    test_log_path.write_text("\n".join(test_log_content), encoding='utf-8')

    # LogViewerWidget으로 읽기
    viewer = LogViewerWidget()
    read_content = viewer._read_log_file(test_log_path)

    # 내용 일치 확인
    assert len(read_content) == 3
    assert "Test message 1" in read_content[0]
    assert "Test message 2" in read_content[1]
    assert "Test message 3" in read_content[2]
```

### **서브태스크 4.2: 실시간 모니터링 메커니즘 수정** (난이도: ⭐⭐⭐)
- [ ] **4.2.1**: 파일 변경 감지 로직 (QFileSystemWatcher) 검증
- [ ] **4.2.2**: 증분 읽기 vs 전체 읽기 로직 최적화
- [ ] **4.2.3**: 메모리 효율적인 로그 버퍼 관리

**TDD 테스트**:
```python
def test_real_time_log_monitoring():
    """실시간 로그 모니터링 테스트"""
    viewer = LogViewerWidget()
    test_log_path = Path("test_realtime.log")

    # 초기 로그 작성
    test_log_path.write_text("Initial log line\n", encoding='utf-8')
    viewer.start_monitoring(test_log_path)

    # 로그 추가 작성
    with open(test_log_path, 'a', encoding='utf-8') as f:
        f.write("New log line\n")
        f.flush()

    # 업데이트 대기 (최대 2초)
    QTest.qWait(2000)

    # 뷰어에 새 로그 표시 확인
    displayed_content = viewer.get_displayed_content()
    assert "New log line" in displayed_content
```

### **서브태스크 4.3: 로그 필터링 및 파싱 검증** (난이도: ⭐⭐)
- [ ] **4.3.1**: 로그 레벨별 필터링 정확성 확인
- [ ] **4.3.2**: 시간 범위 필터링 로직 검증
- [ ] **4.3.3**: 컴포넌트별 필터링 동작 확인

**TDD 테스트**:
```python
def test_log_filtering_accuracy():
    """로그 필터링 정확성 테스트"""
    viewer = LogViewerWidget()

    # 다양한 레벨의 로그 샘플
    sample_logs = [
        "2025-08-10 21:16:46 - DEBUG - Debug message",
        "2025-08-10 21:16:47 - INFO - Info message",
        "2025-08-10 21:16:48 - ERROR - Error message"
    ]

    # INFO 레벨 필터 적용
    viewer.set_log_level_filter("INFO")
    filtered_logs = viewer.apply_filters(sample_logs)

    # DEBUG는 제외, INFO와 ERROR는 포함
    assert len(filtered_logs) == 2
    assert any("Info message" in log for log in filtered_logs)
    assert any("Error message" in log for log in filtered_logs)
    assert not any("Debug message" in log for log in filtered_logs)
```

### **서브태스크 4.4: UI 업데이트 동기화** (난이도: ⭐⭐)
- [ ] **4.4.1**: 로그 텍스트 위젯 스크롤 위치 관리
- [ ] **4.4.2**: 새 로그 추가시 자동 스크롤 옵션
- [ ] **4.4.3**: 대량 로그 업데이트시 UI 응답성 유지

**TDD 테스트**:
```python
def test_ui_update_synchronization():
    """UI 업데이트 동기화 테스트"""
    viewer = LogViewerWidget()
    text_widget = viewer.findChild(QTextEdit, "log_text_display")

    # 초기 로그 설정
    initial_logs = ["Log line 1", "Log line 2"]
    viewer.update_log_display(initial_logs)

    # 표시된 내용 확인
    displayed_text = text_widget.toPlainText()
    assert "Log line 1" in displayed_text
    assert "Log line 2" in displayed_text

    # 새 로그 추가
    new_logs = initial_logs + ["Log line 3"]
    viewer.update_log_display(new_logs)

    # 업데이트된 내용 확인
    updated_text = text_widget.toPlainText()
    assert "Log line 3" in updated_text
```

## 🧪 통합 테스트 시나리오

### **시나리오 A: 실시간 로그 생성 및 표시**
1. 프로그램 시작하여 로그 뷰어 활성화
2. 다른 컴포넌트에서 로그 메시지 생성 (INFO, DEBUG, ERROR)
3. 로그 뷰어에 1초 이내 새 메시지 표시 확인
4. 로그 파일과 뷰어 내용 100% 일치 확인

### **시나리오 B: 대용량 로그 처리**
1. 1000줄 이상의 기존 로그 파일로 테스트
2. 로그 뷰어 시작 속도 3초 이내 확인
3. 메모리 사용량 100MB 이하 유지 확인
4. 스크롤 성능 및 검색 기능 정상 동작

### **시나리오 C: 로그 레벨 필터링**
1. 모든 레벨(DEBUG, INFO, WARNING, ERROR) 로그 혼재 상황
2. INFO 레벨 필터 적용시 DEBUG 로그 숨김 확인
3. ERROR 레벨 필터 적용시 INFO/DEBUG 로그 숨김 확인
4. 필터 변경시 즉시 뷰어 업데이트 확인

## ✅ 완료 조건
- [ ] 로그 뷰어 표시 내용과 파일 내용 100% 일치
- [ ] 실시간 로그 업데이트 지연 1초 이내
- [ ] 로그 필터링 정확성 100% (모든 레벨)
- [ ] 대용량 로그 파일 처리 성능 기준 충족
- [ ] 모든 TDD 테스트 통과 (커버리지 85% 이상)

## 🎨 UX 개선 요구사항
1. **응답성**: 새 로그 표시 지연 1초 이내
2. **사용성**: 자동 스크롤 on/off 토글 기능
3. **검색**: 로그 내용 실시간 검색 기능
4. **시각성**: 로그 레벨별 색상 구분 표시

**UX 테스트**:
```python
def test_user_experience_features():
    """UX 기능 테스트"""
    viewer = LogViewerWidget()

    # 자동 스크롤 토글
    auto_scroll_btn = viewer.findChild(QPushButton, "auto_scroll_toggle")
    assert auto_scroll_btn is not None
    assert auto_scroll_btn.isCheckable()

    # 검색 기능
    search_box = viewer.findChild(QLineEdit, "log_search_box")
    assert search_box is not None

    # 색상 구분 (ERROR는 빨간색)
    viewer.add_log_line("ERROR - Test error message")
    text_widget = viewer.findChild(QTextEdit, "log_text_display")
    html_content = text_widget.toHtml()
    assert "color: red" in html_content or "error-style" in html_content
```

## 🚨 성능 요구사항
1. **메모리**: 10MB 로그 파일 처리시 추가 메모리 50MB 이하
2. **CPU**: 로그 업데이트시 CPU 사용률 10% 이하
3. **응답성**: UI 블로킹 없이 백그라운드 처리
4. **확장성**: 100MB까지 로그 파일 처리 가능

## 📝 검증 체크리스트
- [ ] 실제 로그 파일과 뷰어 내용 바이트 단위 일치
- [ ] 실시간 모니터링 누락 없음 (100% 캐치)
- [ ] 로그 레벨 필터링 정확성 (모든 조합)
- [ ] 대용량 파일 처리 성능 기준 충족
- [ ] UI 응답성 및 사용자 편의 기능 동작
- [ ] 메모리 누수 없음 (장시간 실행 테스트)

## 🔄 다음 태스크 연계
성공시 → **TASK-20250810-06** (환경변수 시작 설정 UX 개선)
실패시 → 로그 시스템 아키텍처 재검토 필요

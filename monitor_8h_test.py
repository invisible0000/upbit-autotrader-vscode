#!/usr/bin/env python3
"""
Ultra Quiet 8시간 테스트 모니터링 도구
실시간 로그 파일 추적 및 요약 정보 제공
"""

import time
import os
from datetime import datetime
import re


def monitor_8h_test():
    """8시간 테스트 모니터링"""
    log_file = "ultra_quiet_8h_test.log"

    print("🔍 Ultra Quiet 8시간 테스트 모니터링 시작")
    print("=" * 60)

    if not os.path.exists(log_file):
        print(f"❌ 로그 파일 없음: {log_file}")
        print("테스트가 아직 시작되지 않았거나 오류가 발생했습니다.")
        return

    last_size = 0
    message_count = 0
    start_time = None
    last_report_time = None

    print(f"📁 로그 파일: {log_file}")
    print("📊 실시간 모니터링 중... (Ctrl+C로 종료)")
    print("-" * 60)

    try:
        while True:
            current_size = os.path.getsize(log_file)

            if current_size > last_size:
                # 새로운 내용 읽기
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()

                # 메시지 수 카운트
                quiet_messages = re.findall(r'메시지 #(\d+):', new_content)
                if quiet_messages:
                    message_count = max([int(m) for m in quiet_messages])

                # 시작 시간 추출
                if start_time is None:
                    start_match = re.search(r'시작 시각: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', new_content)
                    if start_match:
                        start_time = datetime.strptime(start_match.group(1), '%Y-%m-%d %H:%M:%S')

                # 중간 리포트 추출
                reports = re.findall(r'중간 리포트 \[(\d+\.\d+)h / (\d+)h\]', new_content)
                if reports:
                    last_report_time = float(reports[-1][0])

                last_size = current_size

            # 현재 상태 표시
            current_time = datetime.now()

            if start_time:
                elapsed = (current_time - start_time).total_seconds() / 3600
                remaining = max(0, 8 - elapsed)
                progress = min(100, (elapsed / 8) * 100)

                print(f"\r⏰ {current_time.strftime('%H:%M:%S')} | "
                      f"진행: {elapsed:.1f}h/{8}h ({progress:.1f}%) | "
                      f"메시지: {message_count}개 | "
                      f"남은시간: {remaining:.1f}h", end="", flush=True)
            else:
                print(f"\r⏰ {current_time.strftime('%H:%M:%S')} | "
                      f"테스트 시작 대기 중...", end="", flush=True)

            time.sleep(5)  # 5초마다 체크

    except KeyboardInterrupt:
        print("\n\n🛑 모니터링 중단")

    except Exception as e:
        print(f"\n❌ 모니터링 오류: {e}")

    finally:
        print("\n" + "=" * 60)
        print("📊 최종 상태:")

        if start_time:
            elapsed = (datetime.now() - start_time).total_seconds() / 3600
            print(f"  - 경과 시간: {elapsed:.2f}시간")

        print(f"  - 수신 메시지: {message_count}개")

        if message_count > 0 and start_time:
            msg_per_hour = message_count / elapsed if elapsed > 0 else 0
            print(f"  - 시간당 메시지: {msg_per_hour:.2f}개/h")

            # 예상 대비 효율성
            expected_per_hour = 0.25  # 240분마다 1개
            if msg_per_hour <= expected_per_hour * 2:
                print("  - 상태: ✅ Ultra Quiet 모드 정상 동작")
            else:
                print("  - 상태: ⚠️ 예상보다 활발함")

        print("\n😴 Good night! 좋은 밤 되세요!")


def show_recent_log(lines=20):
    """최근 로그 내용 표시"""
    log_file = "ultra_quiet_8h_test.log"

    print(f"📄 최근 로그 내용 (마지막 {lines}줄):")
    print("-" * 60)

    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

                for line in recent_lines:
                    print(line.rstrip())

        except Exception as e:
            print(f"❌ 로그 읽기 오류: {e}")
    else:
        print("❌ 로그 파일이 없습니다.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "log":
        show_recent_log()
    else:
        monitor_8h_test()

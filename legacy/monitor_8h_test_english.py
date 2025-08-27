#!/usr/bin/env python3
"""
Ultra Quiet 8-Hour Test Monitoring Tool (English Version)
Real-time log file tracking and summary information
"""

import time
import os
from datetime import datetime
import re


def monitor_8h_test_english():
    """Monitor 8-hour test (English version)"""
    log_file = "ultra_quiet_8h_test_english.log"

    print("🔍 Ultra Quiet 8-Hour Test Monitoring Started")
    print("=" * 60)

    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        print("Test has not started yet or an error occurred.")
        return

    last_size = 0
    message_count = 0
    start_time = None
    last_report_time = None

    print(f"📁 Log file: {log_file}")
    print("📊 Real-time monitoring... (Ctrl+C to exit)")
    print("-" * 60)

    try:
        while True:
            current_size = os.path.getsize(log_file)

            if current_size > last_size:
                # Read new content
                with open(log_file, 'r', encoding='utf-8') as f:
                    f.seek(last_size)
                    new_content = f.read()

                # Count messages
                quiet_messages = re.findall(r'Message #(\d+):', new_content)
                if quiet_messages:
                    message_count = max([int(m) for m in quiet_messages])

                # Extract start time
                if start_time is None:
                    start_match = re.search(r'Start time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', new_content)
                    if start_match:
                        start_time = datetime.strptime(start_match.group(1), '%Y-%m-%d %H:%M:%S')

                # Extract intermediate reports
                reports = re.findall(r'Intermediate report \[(\d+\.\d+)h / (\d+)h\]', new_content)
                if reports:
                    last_report_time = float(reports[-1][0])

                last_size = current_size

            # Display current status
            current_time = datetime.now()

            if start_time:
                elapsed = (current_time - start_time).total_seconds() / 3600
                remaining = max(0, 8 - elapsed)
                progress = min(100, (elapsed / 8) * 100)

                print(f"\r⏰ {current_time.strftime('%H:%M:%S')} | "
                      f"Progress: {elapsed:.1f}h/8h ({progress:.1f}%) | "
                      f"Messages: {message_count} | "
                      f"Remaining: {remaining:.1f}h", end="", flush=True)
            else:
                print(f"\r⏰ {current_time.strftime('%H:%M:%S')} | "
                      f"Waiting for test to start...", end="", flush=True)

            time.sleep(5)  # Check every 5 seconds

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped")

    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

    finally:
        print("\n" + "=" * 60)
        print("📊 Final status:")

        if start_time:
            elapsed = (datetime.now() - start_time).total_seconds() / 3600
            print(f"  - Elapsed time: {elapsed:.2f} hours")

        print(f"  - Messages received: {message_count}")

        if message_count > 0 and start_time:
            msg_per_hour = message_count / elapsed if elapsed > 0 else 0
            print(f"  - Messages per hour: {msg_per_hour:.2f}/h")

            # Efficiency vs expected
            expected_per_hour = 0.25  # 1 per 240min
            if msg_per_hour <= expected_per_hour * 2:
                print("  - Status: ✅ Ultra Quiet mode working normally")
            else:
                print("  - Status: ⚠️ More active than expected")

        print("\n😴 Good night! Sleep well!")


def show_recent_log_english(lines=20):
    """Show recent log content (English version)"""
    log_file = "ultra_quiet_8h_test_english.log"

    print(f"📄 Recent log content (last {lines} lines):")
    print("-" * 60)

    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

                for line in recent_lines:
                    print(line.rstrip())

        except Exception as e:
            print(f"❌ Log reading error: {e}")
    else:
        print("❌ Log file does not exist.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "log":
        show_recent_log_english()
    else:
        monitor_8h_test_english()

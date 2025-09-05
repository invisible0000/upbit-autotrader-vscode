#!/usr/bin/env python3
"""
Python 백그라운드 프로세스 정리 스크립트
=====================================

백그라운드에서 실행 중인 Python 프로세스를 확인하고 안전하게 종료합니다.
특히 WebSocket 관련 백그라운드 태스크나 테스트 프로세스를 정리할 때 사용합니다.
"""

import psutil
import os
import sys
from typing import List, Dict, Any


def get_current_process_info() -> Dict[str, Any]:
    """현재 실행 중인 프로세스 정보 반환"""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)

    return {
        'pid': current_pid,
        'name': current_process.name(),
        'cmdline': current_process.cmdline(),
        'cwd': current_process.cwd() if hasattr(current_process, 'cwd') else None
    }


def find_python_processes() -> List[Dict[str, Any]]:
    """시스템에서 실행 중인 모든 Python 프로세스 찾기"""
    python_processes = []
    current_pid = os.getpid()

    print("🔍 시스템에서 Python 프로세스 검색 중...")

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd', 'create_time']):
        try:
            # Python 프로세스인지 확인
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                # 현재 스크립트는 제외
                if proc.info['pid'] == current_pid:
                    continue

                # 명령행 정보 가져오기
                cmdline = proc.info.get('cmdline', [])
                if not cmdline:
                    continue

                # 작업 디렉토리 가져오기
                try:
                    cwd = proc.cwd() if hasattr(proc, 'cwd') else proc.info.get('cwd', 'N/A')
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cwd = 'Access Denied'

                process_info = {
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cmdline': cmdline,
                    'cwd': cwd,
                    'create_time': proc.info.get('create_time', 0),
                    'is_upbit_related': is_upbit_related_process(cmdline, cwd)
                }

                python_processes.append(process_info)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # 프로세스가 사라지거나 접근 권한이 없는 경우 무시
            continue

    return python_processes


def is_upbit_related_process(cmdline: List[str], cwd: str) -> bool:
    """업비트 자동매매 관련 프로세스인지 확인"""
    if not cmdline:
        return False

    cmdline_str = ' '.join(cmdline).lower()
    cwd_str = str(cwd).lower() if cwd else ''

    # 업비트 관련 키워드
    upbit_keywords = [
        'upbit',
        'autotrader',
        'websocket',
        'simple_private_test',
        'run_desktop_ui',
        'test_websocket_service',
        'test_real_api_key_service'
    ]

    # 명령행이나 작업 디렉토리에 업비트 관련 키워드가 포함되어 있는지 확인
    for keyword in upbit_keywords:
        if keyword in cmdline_str or keyword in cwd_str:
            return True

    return False


def display_processes(processes: List[Dict[str, Any]]) -> None:
    """프로세스 목록을 보기 좋게 출력"""
    if not processes:
        print("✅ Python 프로세스가 발견되지 않았습니다.")
        return

    print(f"\n📊 발견된 Python 프로세스: {len(processes)}개")
    print("=" * 80)

    for i, proc in enumerate(processes, 1):
        upbit_mark = "🎯" if proc['is_upbit_related'] else "📄"
        print(f"{upbit_mark} 프로세스 {i}:")
        print(f"   ├─ PID: {proc['pid']}")
        print(f"   ├─ 이름: {proc['name']}")
        print(f"   ├─ 명령: {' '.join(proc['cmdline'][:3])}{'...' if len(proc['cmdline']) > 3 else ''}")
        print(f"   ├─ 디렉토리: {proc['cwd']}")
        print(f"   └─ 업비트 관련: {'예' if proc['is_upbit_related'] else '아니오'}")
        print()


def kill_processes(processes: List[Dict[str, Any]], force: bool = False) -> None:
    """선택된 프로세스들을 종료"""
    if not processes:
        return

    upbit_processes = [p for p in processes if p['is_upbit_related']]
    other_processes = [p for p in processes if not p['is_upbit_related']]

    killed_count = 0

    # 업비트 관련 프로세스 자동 종료
    if upbit_processes:
        print(f"\n🎯 업비트 관련 프로세스 {len(upbit_processes)}개 자동 종료 중...")
        for proc in upbit_processes:
            if kill_single_process(proc['pid'], proc['name']):
                killed_count += 1

    # 다른 프로세스는 사용자 확인 후 종료
    if other_processes and not force:
        print(f"\n📄 기타 Python 프로세스 {len(other_processes)}개 발견")
        response = input("이 프로세스들도 종료하시겠습니까? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            for proc in other_processes:
                if kill_single_process(proc['pid'], proc['name']):
                    killed_count += 1
    elif other_processes and force:
        print(f"\n📄 기타 Python 프로세스 {len(other_processes)}개 강제 종료 중...")
        for proc in other_processes:
            if kill_single_process(proc['pid'], proc['name']):
                killed_count += 1

    print(f"\n✅ 총 {killed_count}개 프로세스 종료 완료")


def kill_single_process(pid: int, name: str) -> bool:
    """단일 프로세스 종료"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # 정상 종료 시도

        # 3초 대기 후 강제 종료
        try:
            proc.wait(timeout=3)
            print(f"   ✅ {name} (PID: {pid}) 정상 종료")
            return True
        except psutil.TimeoutExpired:
            proc.kill()  # 강제 종료
            print(f"   ⚠️  {name} (PID: {pid}) 강제 종료")
            return True

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        print(f"   ❌ {name} (PID: {pid}) 종료 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("🔧 Python 백그라운드 프로세스 정리 도구")
    print("=" * 50)

    # 현재 프로세스 정보 출력
    current = get_current_process_info()
    print(f"📍 현재 프로세스: {current['name']} (PID: {current['pid']})")
    print(f"📁 작업 디렉토리: {current['cwd']}")

    # Python 프로세스 검색
    processes = find_python_processes()

    # 프로세스 목록 출력
    display_processes(processes)

    if not processes:
        print("\n🎉 정리할 프로세스가 없습니다!")
        return

    # 명령행 인수 확인
    force_kill = '--force' in sys.argv or '-f' in sys.argv
    auto_kill = '--auto' in sys.argv or '-a' in sys.argv

    if auto_kill:
        # 자동 모드: 업비트 관련 프로세스만 종료
        upbit_processes = [p for p in processes if p['is_upbit_related']]
        if upbit_processes:
            print(f"\n🤖 자동 모드: 업비트 관련 프로세스 {len(upbit_processes)}개만 종료")
            kill_processes(upbit_processes, force=True)
        else:
            print("\n✅ 업비트 관련 프로세스가 없습니다.")
    else:
        # 대화형 모드
        print("\n🤔 어떤 프로세스를 종료하시겠습니까?")
        print("1. 업비트 관련 프로세스만")
        print("2. 모든 Python 프로세스")
        print("3. 종료하지 않음")

        choice = input("선택 (1-3): ").strip()

        if choice == '1':
            upbit_processes = [p for p in processes if p['is_upbit_related']]
            kill_processes(upbit_processes, force=True)
        elif choice == '2':
            kill_processes(processes, force=force_kill)
        else:
            print("✅ 종료하지 않습니다.")

    print("\n🏁 프로세스 정리 완료!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

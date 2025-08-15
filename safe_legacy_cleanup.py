#!/usr/bin/env python3
"""
안전한 레거시 폴더 정리 실행기

분석 결과를 바탕으로 안전하게 확인된 폴더들만 정리합니다.
"""

from pathlib import Path
import shutil
from datetime import datetime


def safe_cleanup_legacy_folders():
    """안전하게 확인된 레거시 폴더들만 정리"""

    print("🧹 안전한 레거시 폴더 정리 시작")
    print("="*50)

    # 백업 디렉토리 준비
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = Path(f"_legacy_backup_{timestamp}")
    backup_root.mkdir(exist_ok=True)

    # 안전하게 삭제 가능한 폴더들 (import 의존성 없음 확인됨)
    safe_targets = [
        {
            "path": "data_info/indicators",
            "reason": "trading_variables로 완전 이관됨, import 의존성 없음",
            "content": "SMA 정의만 남음 (18KB)"
        },
        {
            "path": "data_info/tv_variable_help_guides",
            "reason": "새로운 help_documents 구조로 이관됨",
            "content": "구 도움말 가이드 (16KB)"
        }
    ]

    results = {
        "timestamp": timestamp,
        "backup_location": str(backup_root),
        "processed": [],
        "errors": []
    }

    for target in safe_targets:
        folder_path = Path(target["path"])

        if not folder_path.exists():
            print(f"⏭️  건너뛰기: {target['path']} (존재하지 않음)")
            continue

        print(f"\n📂 처리 중: {target['path']}")
        print(f"   💡 이유: {target['reason']}")
        print(f"   📄 내용: {target['content']}")

        try:
            # 백업 생성
            backup_dest = backup_root / target["path"]
            backup_dest.parent.mkdir(parents=True, exist_ok=True)

            print(f"   📦 백업 중: {backup_dest}")
            shutil.copytree(folder_path, backup_dest)

            # 원본 삭제
            print(f"   🗑️  삭제 중: {folder_path}")
            shutil.rmtree(folder_path)

            results["processed"].append({
                "original": str(folder_path),
                "backup": str(backup_dest),
                "reason": target["reason"]
            })

            print(f"   ✅ 완료!")

        except Exception as e:
            error_msg = f"폴더 {target['path']} 처리 실패: {e}"
            print(f"   ❌ 오류: {error_msg}")
            results["errors"].append(error_msg)

    # 결과 요약
    print("\n" + "="*50)
    print("📊 정리 결과")
    print("="*50)

    print(f"📁 백업 위치: {backup_root}")
    print(f"✅ 처리된 폴더: {len(results['processed'])}개")
    print(f"❌ 오류: {len(results['errors'])}개")

    if results["processed"]:
        print("\n🗑️  삭제된 폴더들:")
        for item in results["processed"]:
            print(f"  - {item['original']}")
            print(f"    백업: {item['backup']}")
            print(f"    이유: {item['reason']}")

    if results["errors"]:
        print("\n❌ 오류 목록:")
        for error in results["errors"]:
            print(f"  - {error}")

    # 다음 단계 안내
    print(f"\n💡 다음 단계:")
    print(f"1. 백업 확인: {backup_root}")
    print(f"2. 트리거 빌더 테스트: python run_desktop_ui.py")
    print(f"3. 문제없으면 백업 폴더 삭제 고려")
    print(f"4. DB 테이블 정리는 별도 검토 필요")

    return results


def main():
    print("🔧 안전한 레거시 폴더 정리 도구")
    print("대상: import 의존성 없는 확인된 폴더만")

    # 사용자 확인
    print("\n📋 정리 대상:")
    print("  - data_info/indicators (18KB)")
    print("  - data_info/tv_variable_help_guides (16KB)")
    print("\n⚠️  모든 파일은 백업됩니다.")

    response = input("\n계속 진행하시겠습니까? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        results = safe_cleanup_legacy_folders()
        print("\n🎉 정리 완료!")
    else:
        print("❌ 취소됨")


if __name__ == "__main__":
    main()

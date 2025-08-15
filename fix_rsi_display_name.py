#!/usr/bin/env python3
"""
🔧 RSI 지표 표시명 수정 스크립트
'RSI 지표 (수정됨)' → 'RSI 지표'로 정정
'Relative Strength Index (Modified)' → 'Relative Strength Index'로 정정

작성일: 2025-08-15
목적: UI에서 '(수정됨)' 및 '(Modified)' 표기 제거
"""

import sqlite3
from pathlib import Path


def fix_rsi_display_name():
    """RSI 지표의 display_name_ko와 display_name_en 수정"""
    db_path = Path("data/settings.sqlite3")

    if not db_path.exists():
        print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
        return False

    print("🔧 === RSI 지표 표시명 수정 ===")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 현재 상태 확인
            print("📋 수정 전 상태:")
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en
                FROM tv_trading_variables
                WHERE variable_id = 'RSI'
            """)
            before = cursor.fetchone()

            if before:
                print(f"  variable_id: {before[0]}")
                print(f"  display_name_ko: {before[1]}")
                print(f"  display_name_en: {before[2]}")
            else:
                print("❌ RSI 변수를 찾을 수 없습니다.")
                return False

            # 수정이 필요한지 확인
            needs_ko_fix = "(수정됨)" in before[1] if before[1] else False
            needs_en_fix = "(Modified)" in before[2] if before[2] else False

            if not needs_ko_fix and not needs_en_fix:
                print("✅ 이미 올바른 상태입니다. 수정할 필요가 없습니다.")
                return True

            # 수정 대상 표시
            print("\n🔍 수정 대상:")
            if needs_ko_fix:
                print(f"  ✓ 한국어명: '{before[1]}' → 'RSI 지표'")
            if needs_en_fix:
                print(f"  ✓ 영문명: '{before[2]}' → 'Relative Strength Index'")

            # 수정 실행
            print("\n🔄 수정 중...")
            cursor.execute("""
                UPDATE tv_trading_variables
                SET display_name_ko = 'RSI 지표',
                    display_name_en = 'Relative Strength Index',
                    description = '상승압력과 하락압력 간의 상대적 강도를 나타내는 모멘텀 지표',
                    updated_at = datetime('now')
                WHERE variable_id = 'RSI'
            """)

            # 수정 후 상태 확인
            print("📋 수정 후 상태:")
            cursor.execute("""
                SELECT variable_id, display_name_ko, display_name_en, description
                FROM tv_trading_variables
                WHERE variable_id = 'RSI'
            """)
            after = cursor.fetchone()

            if after:
                print(f"  variable_id: {after[0]}")
                print(f"  display_name_ko: {after[1]}")
                print(f"  display_name_en: {after[2]}")
                print(f"  description: {after[3]}")

            # 변경사항 커밋
            conn.commit()

            print("✅ RSI 지표 표시명이 성공적으로 수정되었습니다.")
            return True

    except Exception as e:
        print(f"❌ 수정 중 오류 발생: {e}")
        return False


def main():
    """메인 실행"""
    print("🔍 RSI 지표 표시명 수정 스크립트 시작")
    print()

    success = fix_rsi_display_name()

    print()
    if success:
        print("🎉 수정 완료! UI에서 더 이상 '(수정됨)' 표기가 나타나지 않습니다.")
        print("💡 UI 확인: python run_desktop_ui.py → 트리거 빌더에서 RSI 지표 확인")
    else:
        print("❌ 수정 실패. 수동으로 확인이 필요합니다.")


if __name__ == "__main__":
    main()

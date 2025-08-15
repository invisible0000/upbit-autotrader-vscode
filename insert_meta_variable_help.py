#!/usr/bin/env python3
"""
메타 변수 도움말 텍스트를 DB에 삽입하는 스크립트
"""

import sqlite3
import yaml
from pathlib import Path


def insert_meta_variable_help_texts():
    """메타 변수 도움말 텍스트를 DB에 삽입"""
    # YAML 파일 로드
    yaml_path = Path("data_info/tv_help_texts.yaml")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # DB 연결
    db_path = Path("data/settings.sqlite3")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 메타 변수 도움말만 추출하여 삽입
    meta_help_texts = [
        "META_TRAILING_STOP_variable",
        "META_TRAILING_STOP_percentage",
        "META_TRAILING_STOP_target",
        "META_PYRAMID_TARGET_variable",
        "META_PYRAMID_TARGET_step_size",
        "META_PYRAMID_TARGET_target"
    ]

    inserted_count = 0
    for key in meta_help_texts:
        if key in data['help_texts']:
            help_data = data['help_texts'][key]

            # 중복 체크
            cursor.execute("""
                SELECT id FROM tv_help_texts
                WHERE variable_id = ? AND parameter_name = ?
            """, (help_data['variable_id'], help_data['parameter_name']))

            if cursor.fetchone():
                print(f"⚠️  이미 존재함: {help_data['variable_id']} - {help_data['parameter_name']}")
                continue

            # 삽입
            cursor.execute("""
                INSERT INTO tv_help_texts (
                    variable_id, parameter_name, help_text_ko, help_text_en,
                    tooltip_ko, tooltip_en, language, context_type
                ) VALUES (?, ?, ?, ?, ?, ?, 'ko', 'tooltip')
            """, (
                help_data['variable_id'],
                help_data['parameter_name'],
                help_data['help_text_ko'],
                help_data.get('help_text_en', ''),
                help_data.get('tooltip_ko', ''),
                help_data.get('tooltip_en', '')
            ))

            inserted_count += 1
            print(f"✅ 삽입 완료: {help_data['variable_id']} - {help_data['parameter_name']}")

    conn.commit()
    conn.close()

    print(f"\n🎉 메타 변수 도움말 삽입 완료: {inserted_count}개")


if __name__ == "__main__":
    insert_meta_variable_help_texts()

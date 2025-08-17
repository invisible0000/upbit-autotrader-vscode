#!/usr/bin/env python3
"""
Help Guide Extractor - DB to YAML for Manual Editing
이모티콘 정리를 위한 헬프 가이드 추출 도구
"""

import sqlite3
import yaml
import os
from pathlib import Path
from datetime import datetime

def get_db_path():
    """데이터베이스 경로 반환"""
    current_dir = Path(__file__).parent
    db_path = current_dir.parent.parent / "data" / "settings.sqlite3"
    return str(db_path)

def extract_help_guides():
    """DB에서 헬프 가이드를 추출하여 YAML 파일로 저장"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()

    try:
        # 모든 변수의 헬프 문서 가져오기
        cursor.execute("""
            SELECT DISTINCT variable_id
            FROM tv_variable_help_documents
            ORDER BY variable_id
        """)
        variables = [row[0] for row in cursor.fetchall()]

        print(f"📚 총 {len(variables)}개 변수의 헬프 가이드 추출 시작...")

        # 출력 폴더 생성
        output_dir = Path("help_guides_for_editing")
        output_dir.mkdir(exist_ok=True)

        for variable_id in variables:
            # 각 변수의 헬프 문서 가져오기
            cursor.execute("""
                SELECT help_category, title_ko, content_ko
                FROM tv_variable_help_documents
                WHERE variable_id = ?
                ORDER BY help_category
            """, (variable_id,))

            help_docs = cursor.fetchall()

            if help_docs:
                # YAML 구조 생성
                yaml_data = {
                    'variable_id': variable_id,
                    'help_documents': {}
                }

                for category, title, content in help_docs:
                    yaml_data['help_documents'][category] = {
                        'title': title,
                        'content': content
                    }

                # YAML 파일로 저장
                output_file = output_dir / f"{variable_id}_help_guide.yaml"
                with open(output_file, 'w', encoding='utf-8') as f:
                    yaml.dump(yaml_data, f, default_flow_style=False,
                             allow_unicode=True, sort_keys=False, indent=2)

                print(f"✅ {variable_id} 헬프 가이드 추출 완료")

        # 사용법 안내 파일 생성
        readme_content = f"""# 📚 Help Guides for Manual Editing

## 📅 추출 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 목적
- 이모티콘이 많은 헬프 가이드 내용 정리
- 사용성 개선을 위한 텍스트 최적화

## 📋 추출된 파일들
총 {len(variables)}개 변수의 헬프 가이드:

{chr(10).join(f"- {var}_help_guide.yaml" for var in variables)}

## ✏️ 편집 가이드라인
1. **이모티콘 제거**: 🔧📊💡 등 과도한 이모티콘 정리
2. **내용 간소화**: 핵심 정보 위주로 재작성
3. **일관성 유지**: 3개 카테고리 구조 유지 (concept/usage/advanced)

## 🔄 편집 완료 후
편집이 완료되면 `yaml_to_db_updater.py`로 다시 DB에 반영
"""

        with open(output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"\n🎉 모든 헬프 가이드 추출 완료!")
        print(f"📁 출력 폴더: {output_dir.absolute()}")
        print(f"📄 총 {len(variables)}개 YAML 파일 생성")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    extract_help_guides()

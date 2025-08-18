#!/usr/bin/env python3
"""
매매 변수 도움말 YAML 파일을 DB에 업데이트하는 스크립트
"""

import sqlite3
import yaml
from datetime import datetime
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
YAML_DIR = PROJECT_ROOT / "data_info" / "_management" / "help_guides_for_editing"
DB_PATH = PROJECT_ROOT / "data" / "settings.sqlite3"


def load_yaml_file(file_path):
    """YAML 파일을 로드하여 파싱된 데이터 반환"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ YAML 파일 로드 실패: {file_path} - {e}")
        return None


def update_help_document(cursor, variable_id, help_category, title, content):
    """DB의 도움말 문서 업데이트"""
    current_time = datetime.now().isoformat()

    # 기존 레코드 확인
    cursor.execute("""
        SELECT id FROM tv_variable_help_documents
        WHERE variable_id = ? AND help_category = ?
    """, (variable_id, help_category))

    existing = cursor.fetchone()

    if existing:
        # 기존 레코드 업데이트
        cursor.execute("""
            UPDATE tv_variable_help_documents
            SET title_ko = ?, content_ko = ?, updated_at = ?
            WHERE variable_id = ? AND help_category = ?
        """, (title, content, current_time, variable_id, help_category))
        return "updated"
    else:
        # 새 레코드 삽입
        cursor.execute("""
            INSERT INTO tv_variable_help_documents
            (variable_id, help_category, content_type, title_ko, content_ko,
             display_order, created_at, updated_at)
            VALUES (?, ?, 'markdown', ?, ?, 1, ?, ?)
        """, (variable_id, help_category, title, content, current_time, current_time))
        return "inserted"


def process_yaml_files():
    """모든 YAML 파일을 처리하여 DB 업데이트"""

    if not YAML_DIR.exists():
        print(f"❌ YAML 디렉토리가 존재하지 않습니다: {YAML_DIR}")
        return False

    if not DB_PATH.exists():
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {DB_PATH}")
        return False

    # YAML 파일 목록 가져오기
    yaml_files = list(YAML_DIR.glob("*_help_guide.yaml"))
    yaml_files.sort()

    if not yaml_files:
        print("❌ 처리할 YAML 파일이 없습니다.")
        return False

    print(f"🔍 발견된 YAML 파일: {len(yaml_files)}개")

    # DB 연결
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 업데이트 통계
        stats = {"updated": 0, "inserted": 0, "errors": 0}

        for yaml_file in yaml_files:
            print(f"\n📝 처리 중: {yaml_file.name}")

            # YAML 데이터 로드
            data = load_yaml_file(yaml_file)
            if not data:
                stats["errors"] += 1
                continue

            variable_id = data.get('variable_id')
            help_documents = data.get('help_documents', {})

            if not variable_id:
                print(f"❌ variable_id가 없습니다: {yaml_file.name}")
                stats["errors"] += 1
                continue

            # 각 섹션(concept, usage, advanced) 처리
            for help_category in ['concept', 'usage', 'advanced']:
                section_data = help_documents.get(help_category)
                if not section_data:
                    print(f"⚠️  {help_category} 섹션이 없습니다: {variable_id}")
                    continue

                title = section_data.get('title', f'{help_category.title()} Guide')
                content = section_data.get('content', '')

                if not content.strip():
                    print(f"⚠️  {help_category} 섹션 내용이 비어있습니다: {variable_id}")
                    continue

                try:
                    result = update_help_document(cursor, variable_id, help_category, title, content)
                    stats[result] += 1
                    print(f"   ✅ {help_category}: {result}")

                except Exception as e:
                    print(f"   ❌ {help_category} 업데이트 실패: {e}")
                    stats["errors"] += 1

        # 변경사항 커밋
        conn.commit()
        conn.close()

        # 결과 출력
        print(f"\n🎉 업데이트 완료!")
        print("   📊 통계:")
        print(f"   - 업데이트된 레코드: {stats['updated']}개")
        print(f"   - 새로 삽입된 레코드: {stats['inserted']}개")
        print(f"   - 오류 발생: {stats['errors']}개")
        print(f"   - 총 처리된 레코드: {stats['updated'] + stats['inserted']}개")

        return stats["errors"] == 0

    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def verify_update():
    """업데이트 결과 검증"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # 각 변수별 섹션 개수 확인
        cursor.execute("""
            SELECT variable_id, COUNT(*) as section_count
            FROM tv_variable_help_documents
            GROUP BY variable_id
            ORDER BY variable_id
        """)

        results = cursor.fetchall()

        print(f"\n🔍 업데이트 검증:")
        incomplete_variables = []

        for variable_id, section_count in results:
            if section_count < 3:
                incomplete_variables.append(f"{variable_id} ({section_count}/3)")
                print(f"   ⚠️  {variable_id}: {section_count}/3 섹션")
            else:
                print(f"   ✅ {variable_id}: {section_count}/3 섹션")

        if incomplete_variables:
            print(f"\n⚠️  불완전한 변수들: {len(incomplete_variables)}개")
            for var in incomplete_variables:
                print(f"   - {var}")
        else:
            print(f"\n🎉 모든 변수가 완전히 업데이트되었습니다!")

        # 총 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM tv_variable_help_documents")
        total_records = cursor.fetchone()[0]
        print(f"\n📊 총 도움말 레코드: {total_records}개")

        conn.close()
        return len(incomplete_variables) == 0

    except Exception as e:
        print(f"❌ 검증 실패: {e}")
        return False

if __name__ == "__main__":
    print("🚀 매매 변수 도움말 DB 업데이트 시작")
    print("=" * 50)

    # YAML 파일들을 DB에 업데이트
    success = process_yaml_files()

    if success:
        # 업데이트 결과 검증
        verify_update()
        print("\n✅ 업데이트 완료!")
    else:
        print("\n❌ 업데이트 실패!")

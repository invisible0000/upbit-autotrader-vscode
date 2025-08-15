"""
SMA 변수의 헬프 문서 수동 추가 스크립트
"""

import sqlite3
import yaml
from pathlib import Path

def add_sma_help_documents():
    # SMA help_guide.yaml 파일 읽기
    sma_file = Path("data_info/trading_variables/trend/SMA/help_guide.yaml")

    if not sma_file.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {sma_file}")
        return

    # YAML 파일 로드
    with open(sma_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # SMA 데이터 추출
    sma_data = data.get('SMA', {})

    # DB 연결
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()

    records_added = 0

    # concept 추가
    if 'concept' in sma_data:
        concept_data = sma_data['concept']

        # 기본 개념
        cursor.execute("""
            INSERT INTO tv_variable_help_documents
            (variable_id, help_category, content_type, title_ko, title_en, content_ko, content_en, display_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            'SMA',
            'concept',
            'markdown',
            concept_data.get('title_ko', 'SMA 기본 개념'),
            concept_data.get('title_en'),
            concept_data.get('overview_ko', ''),
            concept_data.get('overview_en'),
            10
        ))
        records_added += 1

        # 거래 활용법
        if concept_data.get('trading_applications_ko'):
            cursor.execute("""
                INSERT INTO tv_variable_help_documents
                (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'SMA',
                'usage',
                'markdown',
                'SMA 실전 활용 전략',
                concept_data.get('trading_applications_ko'),
                8
            ))
            records_added += 1

        # 시장 상황별 활용
        if concept_data.get('market_context_ko'):
            cursor.execute("""
                INSERT INTO tv_variable_help_documents
                (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'SMA',
                'advanced',
                'markdown',
                'SMA 시장 상황별 고급 활용법',
                concept_data.get('market_context_ko'),
                6
            ))
            records_added += 1

    # parameter_guides 추가
    if 'parameter_guides' in sma_data:
        param_guides = sma_data['parameter_guides']

        # period 가이드
        if 'period' in param_guides:
            period_guide = param_guides['period']

            if period_guide.get('selection_guide_ko'):
                cursor.execute("""
                    INSERT INTO tv_variable_help_documents
                    (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    'SMA',
                    'advanced',
                    'markdown',
                    'SMA 기간 선택 완전 가이드',
                    period_guide.get('selection_guide_ko'),
                    4
                ))
                records_added += 1

            if period_guide.get('practical_examples_ko'):
                cursor.execute("""
                    INSERT INTO tv_variable_help_documents
                    (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    'SMA',
                    'usage',
                    'markdown',
                    'SMA 실전 설정 예시',
                    period_guide.get('practical_examples_ko'),
                    7
                ))
                records_added += 1

    # examples 추가
    if 'examples' in sma_data:
        examples = sma_data['examples']

        if examples.get('chart_examples'):
            cursor.execute("""
                INSERT INTO tv_variable_help_documents
                (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'SMA',
                'usage',
                'markdown',
                'SMA 차트 패턴 예시',
                examples.get('chart_examples'),
                6
            ))
            records_added += 1

        if examples.get('combination_strategies'):
            cursor.execute("""
                INSERT INTO tv_variable_help_documents
                (variable_id, help_category, content_type, title_ko, content_ko, display_order)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                'SMA',
                'advanced',
                'markdown',
                'SMA 조합 전략',
                examples.get('combination_strategies'),
                3
            ))
            records_added += 1

    # 커밋
    conn.commit()
    conn.close()

    print(f"✅ SMA 헬프 문서 {records_added}개 추가 완료!")

    # 확인
    conn = sqlite3.connect('data/settings.sqlite3')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM tv_variable_help_documents WHERE variable_id = ?', ('SMA',))
    count = cursor.fetchone()[0]
    print(f"📊 SMA 관련 문서 총 {count}개")
    conn.close()

if __name__ == "__main__":
    add_sma_help_documents()

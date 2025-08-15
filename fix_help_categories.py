#!/usr/bin/env python3
"""
헬프 카테고리 일괄 수정 및 거래 변수 통합 스크립트

주요 기능:
1. 헬프 카테고리 정규화 (concept, usage, advanced로 통일)
2. 기존 잘못된 카테고리 데이터 정리
3. YAML 파일 기반 헬프 문서 재생성

사용법:
    python fix_help_categories.py --fix-all
    python fix_help_categories.py --dry-run
    python fix_help_categories.py --variable SMA
"""

import argparse
import sqlite3
import yaml
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from upbit_auto_trading.infrastructure.logging import create_component_logger

logger = create_component_logger("HelpCategoryFixer")


class HelpCategoryFixer:
    """헬프 카테고리 정규화 도구"""

    def __init__(self, db_path: str = "data/settings.sqlite3"):
        self.db_path = db_path
        self.trading_variables_path = Path("data_info/trading_variables")

    def analyze_current_categories(self):
        """현재 헬프 카테고리 상태 분석"""
        logger.info("🔍 현재 헬프 카테고리 상태 분석")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 전체 카테고리 분포
            cursor.execute("""
                SELECT help_category, COUNT(*) as count
                FROM tv_variable_help_documents
                GROUP BY help_category
                ORDER BY count DESC
            """)
            categories = cursor.fetchall()

            logger.info("📊 카테고리 분포:")
            for category, count in categories:
                logger.info(f"  - {category}: {count}개")

            # 변수별 카테고리 수 확인
            cursor.execute("""
                SELECT variable_id, COUNT(DISTINCT help_category) as category_count,
                       GROUP_CONCAT(DISTINCT help_category) as categories
                FROM tv_variable_help_documents
                GROUP BY variable_id
                HAVING category_count != 3
                ORDER BY category_count DESC
            """)
            problematic_vars = cursor.fetchall()

            logger.info(f"\n⚠️  비정상 카테고리 수를 가진 변수들 ({len(problematic_vars)}개):")
            for var_id, count, categories in problematic_vars:
                logger.info(f"  - {var_id}: {count}개 카테고리 ({categories})")

            return categories, problematic_vars

    def get_correct_help_data_from_yaml(self, variable_id: str) -> Dict[str, Any]:
        """YAML 파일에서 올바른 헬프 데이터 가져오기"""
        # 변수가 있는 카테고리 찾기
        for category_dir in self.trading_variables_path.iterdir():
            if not category_dir.is_dir():
                continue

            variable_dir = category_dir / variable_id
            if variable_dir.exists():
                help_guide_file = variable_dir / "help_guide.yaml"
                if help_guide_file.exists():
                    with open(help_guide_file, 'r', encoding='utf-8') as f:
                        return yaml.safe_load(f)

        logger.warning(f"YAML 파일을 찾을 수 없습니다: {variable_id}")
        return None

    def fix_variable_help_categories(self, variable_id: str, dry_run: bool = False):
        """특정 변수의 헬프 카테고리 수정"""
        logger.info(f"🔧 헬프 카테고리 수정 시작: {variable_id}")

        # YAML에서 올바른 데이터 가져오기
        yaml_data = self.get_correct_help_data_from_yaml(variable_id)
        if not yaml_data:
            logger.error(f"❌ YAML 데이터를 로드할 수 없습니다: {variable_id}")
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 기존 데이터 삭제
            if not dry_run:
                cursor.execute(
                    "DELETE FROM tv_variable_help_documents WHERE variable_id = ?",
                    (variable_id,)
                )
                logger.info(f"  🗑️  기존 데이터 삭제: {variable_id}")
            else:
                logger.info(f"  [DRY-RUN] 기존 데이터 삭제 예정: {variable_id}")

            # 새 데이터 삽입
            success_count = 0

            # help_guide 구조 확인
            if 'help_guide' in yaml_data:
                guides = yaml_data['help_guide']
            elif variable_id in yaml_data:
                guides = yaml_data[variable_id]
            else:
                logger.error(f"❌ 예상치 못한 YAML 구조: {variable_id}")
                return False

            # 표준 카테고리 매핑
            category_mapping = {
                'concept': {'concept', 'basic', 'basics', '기본', '개념'},
                'usage': {'usage', 'use', 'application', '사용', '활용'},
                'advanced': {'advanced', 'expert', 'pro', '고급', '전문가'}
            }

            for guide_key, guide_content in guides.items():
                if not isinstance(guide_content, dict):
                    continue

                # 카테고리 결정
                category = self._determine_category(guide_key, guide_content, category_mapping)

                # 표시 순서 결정
                display_orders = {'concept': 1, 'usage': 2, 'advanced': 3}
                display_order = display_orders.get(category, 99)

                # 제목과 내용 추출
                title = guide_content.get('title', guide_key)
                content = guide_content.get('content', '')

                if not dry_run:
                    cursor.execute("""
                        INSERT INTO tv_variable_help_documents
                        (variable_id, help_category, content_type, title_ko, content_ko, display_order, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        variable_id, category, 'markdown', title, content,
                        display_order, datetime.now(), datetime.now()
                    ))
                    success_count += 1
                    logger.info(f"  ✅ 문서 삽입: {variable_id} - {category} ({title})")
                else:
                    logger.info(f"  [DRY-RUN] 문서 삽입 예정: {variable_id} - {category} ({title})")
                    success_count += 1

            if not dry_run:
                conn.commit()

            logger.info(f"✅ 완료: {variable_id}, {success_count}개 문서 처리")
            return True

    def _determine_category(self, guide_key: str, guide_content: Dict, category_mapping: Dict) -> str:
        """가이드 키와 내용을 기반으로 카테고리 결정"""
        guide_key_lower = guide_key.lower()

        # 키 기반 매핑
        for category, keywords in category_mapping.items():
            if any(keyword in guide_key_lower for keyword in keywords):
                return category

        # 제목 기반 매핑
        title = guide_content.get('title', '').lower()
        for category, keywords in category_mapping.items():
            if any(keyword in title for keyword in keywords):
                return category

        # 내용 기반 추론 (간단한 규칙)
        content = guide_content.get('content', '').lower()
        if any(word in content for word in ['기본', '개념', '이해', '소개']):
            return 'concept'
        elif any(word in content for word in ['전문가', '고급', '심화', '최적화']):
            return 'advanced'
        else:
            return 'usage'

    def fix_all_help_categories(self, dry_run: bool = False):
        """모든 변수의 헬프 카테고리 수정"""
        logger.info("🚀 모든 변수 헬프 카테고리 수정 시작")

        if dry_run:
            logger.info("🔍 DRY-RUN 모드 (실제 변경 없음)")

        # 현재 상태 분석
        categories, problematic_vars = self.analyze_current_categories()

        # 모든 변수 목록 가져오기
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT variable_id FROM tv_variable_help_documents ORDER BY variable_id")
            all_variables = [row[0] for row in cursor.fetchall()]

        logger.info(f"📊 처리할 변수 수: {len(all_variables)}개")

        success_count = 0
        failed_count = 0

        for variable_id in all_variables:
            try:
                if self.fix_variable_help_categories(variable_id, dry_run):
                    success_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"❌ 오류 발생: {variable_id} - {e}")
                failed_count += 1

        logger.info(f"📈 처리 완료: {success_count}개 성공, {failed_count}개 실패")

        if not dry_run:
            logger.info("✅ 데이터베이스 업데이트 완료")
            # 결과 확인
            self.analyze_current_categories()

    def clean_duplicate_categories(self, dry_run: bool = False):
        """중복 카테고리 정리"""
        logger.info("🧹 중복 카테고리 정리 시작")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 중복 usage 카테고리 확인
            cursor.execute("""
                SELECT variable_id, COUNT(*) as usage_count
                FROM tv_variable_help_documents
                WHERE help_category = 'usage'
                GROUP BY variable_id
                HAVING usage_count > 1
            """)
            duplicates = cursor.fetchall()

            logger.info(f"🔍 중복 usage 카테고리 발견: {len(duplicates)}개 변수")

            for variable_id, count in duplicates:
                logger.info(f"  - {variable_id}: {count}개의 usage 문서")

                if not dry_run:
                    # 가장 오래된 것만 남기고 삭제
                    cursor.execute("""
                        DELETE FROM tv_variable_help_documents
                        WHERE variable_id = ? AND help_category = 'usage'
                        AND id NOT IN (
                            SELECT id FROM tv_variable_help_documents
                            WHERE variable_id = ? AND help_category = 'usage'
                            ORDER BY created_at ASC LIMIT 1
                        )
                    """, (variable_id, variable_id))

                    # 남은 문서를 advanced로 변경
                    cursor.execute("""
                        UPDATE tv_variable_help_documents
                        SET help_category = 'advanced',
                            title_ko = CASE WHEN title_ko LIKE '%활용%' THEN REPLACE(title_ko, '활용', '고급 활용') ELSE title_ko END,
                            display_order = 3,
                            updated_at = ?
                        WHERE variable_id = ? AND help_category = 'usage'
                        AND id = (
                            SELECT id FROM tv_variable_help_documents
                            WHERE variable_id = ? AND help_category = 'usage'
                            ORDER BY created_at DESC LIMIT 1
                        )
                    """, (datetime.now(), variable_id, variable_id))

                    logger.info(f"  ✅ {variable_id}: 중복 정리 및 advanced 카테고리 생성")

            if not dry_run:
                conn.commit()


def main():
    parser = argparse.ArgumentParser(description="헬프 카테고리 정규화 도구")
    parser.add_argument("--dry-run", action="store_true", help="실제 변경 없이 시뮬레이션만 실행")
    parser.add_argument("--fix-all", action="store_true", help="모든 변수의 헬프 카테고리 수정")
    parser.add_argument("--variable", help="특정 변수만 수정 (예: SMA)")
    parser.add_argument("--analyze", action="store_true", help="현재 상태만 분석")
    parser.add_argument("--clean-duplicates", action="store_true", help="중복 카테고리 정리")
    args = parser.parse_args()

    fixer = HelpCategoryFixer()

    if args.analyze:
        fixer.analyze_current_categories()
    elif args.clean_duplicates:
        fixer.clean_duplicate_categories(args.dry_run)
    elif args.variable:
        fixer.fix_variable_help_categories(args.variable, args.dry_run)
    elif args.fix_all:
        fixer.fix_all_help_categories(args.dry_run)
    else:
        logger.info("❓ 옵션을 선택해주세요. --help로 사용법을 확인하세요.")
        fixer.analyze_current_categories()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
📚 변수 헬프 가이드 로더 유틸리티
분산된 YAML 파일들을 로드하고 DB에 저장하는 도구

작성일: 2025-08-15
목적: 1000줄 제한 해결 및 체계적 헬프 컨텐츠 관리
"""

import os
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from upbit_auto_trading.infrastructure.logging import create_component_logger


@dataclass
class HelpContent:
    """헬프 컨텐츠 데이터 클래스"""
    variable_id: str
    help_category: str  # 'concept', 'parameter_guide', 'examples'
    content_type: str   # 'overview', 'trading_guide', 'selection_guide', etc.
    title_ko: Optional[str]
    title_en: Optional[str]
    content_ko: str
    content_en: Optional[str]
    display_order: int = 0


class HelpGuideLoader:
    """헬프 가이드 로더 클래스"""

    def __init__(self):
        self._logger = create_component_logger("HelpGuideLoader")
        self._base_path = Path("data_info/tv_variable_help_guides")
        self._db_path = Path("data/settings.sqlite3")

    def load_all_guides(self) -> Dict[str, List[HelpContent]]:
        """모든 헬프 가이드 파일을 로드"""
        if not self._base_path.exists():
            self._logger.warning(f"헬프 가이드 폴더가 존재하지 않음: {self._base_path}")
            return {}

        # 인덱스 파일 로드
        index_path = self._base_path / "_index.yaml"
        if not index_path.exists():
            self._logger.error("인덱스 파일이 존재하지 않음")
            return {}

        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = yaml.safe_load(f)

        all_contents = {}

        # 카테고리별 파일 로드
        for category, info in index_data['file_structure'].items():
            category_path = self._base_path / category
            if not category_path.exists():
                continue

            for file_name in info['files']:
                file_path = category_path / file_name
                if file_path.exists():
                    contents = self._load_single_file(file_path)
                    for variable_id, help_contents in contents.items():
                        if variable_id not in all_contents:
                            all_contents[variable_id] = []
                        all_contents[variable_id].extend(help_contents)

        self._logger.info(f"총 {len(all_contents)}개 변수의 헬프 가이드 로드 완료")
        return all_contents

    def _load_single_file(self, file_path: Path) -> Dict[str, List[HelpContent]]:
        """단일 YAML 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            result = {}

            for variable_id, guide_data in data.items():
                contents = []

                # concept 섹션 처리
                if 'concept' in guide_data:
                    concept = guide_data['concept']

                    # 개요
                    if 'overview_ko' in concept:
                        contents.append(HelpContent(
                            variable_id=variable_id,
                            help_category='concept',
                            content_type='overview',
                            title_ko=concept.get('title_ko'),
                            title_en=concept.get('title_en'),
                            content_ko=concept['overview_ko'],
                            content_en=concept.get('overview_en'),
                            display_order=1
                        ))

                    # 실전 활용법
                    if 'trading_applications_ko' in concept:
                        contents.append(HelpContent(
                            variable_id=variable_id,
                            help_category='concept',
                            content_type='trading_applications',
                            title_ko="실전 활용법",
                            title_en="Trading Applications",
                            content_ko=concept['trading_applications_ko'],
                            content_en=concept.get('trading_applications_en'),
                            display_order=2
                        ))

                    # 시장 상황별 해석
                    if 'market_context_ko' in concept:
                        contents.append(HelpContent(
                            variable_id=variable_id,
                            help_category='concept',
                            content_type='market_context',
                            title_ko="시장 상황별 해석",
                            title_en="Market Context",
                            content_ko=concept['market_context_ko'],
                            content_en=concept.get('market_context_en'),
                            display_order=3
                        ))

                # parameter_guides 섹션 처리
                if 'parameter_guides' in guide_data:
                    param_guides = guide_data['parameter_guides']

                    for param_name, param_guide in param_guides.items():
                        order = 10  # 매개변수 가이드는 10부터 시작

                        if 'selection_guide_ko' in param_guide:
                            contents.append(HelpContent(
                                variable_id=variable_id,
                                help_category='parameter_guide',
                                content_type=f'{param_name}_selection_guide',
                                title_ko=f"{param_name} 선택 가이드",
                                title_en=f"{param_name} Selection Guide",
                                content_ko=param_guide['selection_guide_ko'],
                                content_en=param_guide.get('selection_guide_en'),
                                display_order=order
                            ))
                            order += 1

                        if 'practical_examples_ko' in param_guide:
                            contents.append(HelpContent(
                                variable_id=variable_id,
                                help_category='parameter_guide',
                                content_type=f'{param_name}_practical_examples',
                                title_ko=f"{param_name} 실전 예시",
                                title_en=f"{param_name} Practical Examples",
                                content_ko=param_guide['practical_examples_ko'],
                                content_en=param_guide.get('practical_examples_en'),
                                display_order=order
                            ))
                            order += 1

                        if 'common_mistakes_ko' in param_guide:
                            contents.append(HelpContent(
                                variable_id=variable_id,
                                help_category='parameter_guide',
                                content_type=f'{param_name}_common_mistakes',
                                title_ko=f"{param_name} 주의사항",
                                title_en=f"{param_name} Common Mistakes",
                                content_ko=param_guide['common_mistakes_ko'],
                                content_en=param_guide.get('common_mistakes_en'),
                                display_order=order
                            ))

                # examples 섹션 처리
                if 'examples' in guide_data:
                    examples = guide_data['examples']
                    order = 20  # 예시는 20부터 시작

                    for example_type, example_content in examples.items():
                        if isinstance(example_content, str) and example_content.strip():
                            contents.append(HelpContent(
                                variable_id=variable_id,
                                help_category='examples',
                                content_type=example_type,
                                title_ko=self._get_korean_title(example_type),
                                title_en=example_type.replace('_', ' ').title(),
                                content_ko=example_content,
                                content_en=None,
                                display_order=order
                            ))
                            order += 1

                result[variable_id] = contents

            return result

        except Exception as e:
            self._logger.error(f"파일 로드 실패 {file_path}: {e}")
            return {}

    def _get_korean_title(self, example_type: str) -> str:
        """예시 타입을 한국어 제목으로 변환"""
        type_map = {
            'chart_examples': '차트 예시',
            'backtesting_cases': '백테스팅 사례',
            'combination_strategies': '조합 전략'
        }
        return type_map.get(example_type, example_type)

    def save_to_database(self, help_contents: Dict[str, List[HelpContent]]) -> bool:
        """헬프 컨텐츠를 데이터베이스에 저장"""
        try:
            if not self._db_path.exists():
                self._logger.error(f"DB 파일이 존재하지 않음: {self._db_path}")
                return False

            # 테이블 생성 (존재하지 않는 경우)
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tv_variable_help_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        variable_id TEXT NOT NULL,
                        help_category TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        title_ko TEXT,
                        title_en TEXT,
                        content_ko TEXT NOT NULL,
                        content_en TEXT,
                        display_order INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (variable_id) REFERENCES tv_trading_variables(variable_id)
                    )
                ''')

                # 기존 데이터 삭제 (업데이트용)
                cursor.execute('DELETE FROM tv_variable_help_documents')

                # 새 데이터 삽입
                total_count = 0
                for variable_id, contents in help_contents.items():
                    for content in contents:
                        cursor.execute('''
                            INSERT INTO tv_variable_help_documents
                            (variable_id, help_category, content_type, title_ko, title_en,
                             content_ko, content_en, display_order)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            content.variable_id,
                            content.help_category,
                            content.content_type,
                            content.title_ko,
                            content.title_en,
                            content.content_ko,
                            content.content_en,
                            content.display_order
                        ))
                        total_count += 1

                # 인덱스 생성
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_help_docs_variable_category
                    ON tv_variable_help_documents(variable_id, help_category)
                ''')

                conn.commit()
                self._logger.info(f"총 {total_count}개 헬프 컨텐츠를 DB에 저장 완료")
                return True

        except Exception as e:
            self._logger.error(f"DB 저장 실패: {e}")
            return False

    def get_variable_help(self, variable_id: str, help_category: Optional[str] = None) -> List[HelpContent]:
        """DB에서 변수 헬프 조회"""
        try:
            if not self._db_path.exists():
                return []

            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                if help_category:
                    cursor.execute('''
                        SELECT variable_id, help_category, content_type, title_ko, title_en,
                               content_ko, content_en, display_order
                        FROM tv_variable_help_documents
                        WHERE variable_id = ? AND help_category = ?
                        ORDER BY display_order, id
                    ''', (variable_id, help_category))
                else:
                    cursor.execute('''
                        SELECT variable_id, help_category, content_type, title_ko, title_en,
                               content_ko, content_en, display_order
                        FROM tv_variable_help_documents
                        WHERE variable_id = ?
                        ORDER BY display_order, id
                    ''', (variable_id,))

                results = []
                for row in cursor.fetchall():
                    results.append(HelpContent(
                        variable_id=row[0],
                        help_category=row[1],
                        content_type=row[2],
                        title_ko=row[3],
                        title_en=row[4],
                        content_ko=row[5],
                        content_en=row[6],
                        display_order=row[7]
                    ))

                return results

        except Exception as e:
            self._logger.error(f"헬프 조회 실패: {e}")
            return []


def main():
    """메인 실행 함수"""
    print("📚 변수 헬프 가이드 로더 시작")

    loader = HelpGuideLoader()

    # 모든 가이드 로드
    print("🔄 헬프 가이드 파일들을 로드 중...")
    help_contents = loader.load_all_guides()

    if not help_contents:
        print("❌ 로드할 헬프 가이드가 없습니다.")
        return

    # 통계 출력
    total_contents = sum(len(contents) for contents in help_contents.values())
    print(f"✅ {len(help_contents)}개 변수, {total_contents}개 컨텐츠 로드 완료")

    # DB에 저장
    print("🔄 데이터베이스에 저장 중...")
    if loader.save_to_database(help_contents):
        print("✅ 데이터베이스 저장 완료")

        # 샘플 조회 테스트
        print("\n🧪 샘플 조회 테스트:")
        sma_helps = loader.get_variable_help("SMA", "concept")
        for help_content in sma_helps[:2]:  # 처음 2개만
            print(f"  📖 {help_content.title_ko}")
            print(f"     컨텐츠 길이: {len(help_content.content_ko)}자")
    else:
        print("❌ 데이터베이스 저장 실패")


if __name__ == "__main__":
    main()

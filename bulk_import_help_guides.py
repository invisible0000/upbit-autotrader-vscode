#!/usr/bin/env python3
"""
Help Guide 대량 DB 이관 도구

data_info/trading_variables/**/help_guide.yaml → tv_variable_help_documents 테이블
모든 28개 변수의 상세 가이드를 DB로 이관합니다.
"""

import sqlite3
import yaml
from pathlib import Path
from datetime import datetime
import json


class HelpGuideImporter:
    """Help Guide 대량 이관기"""

    def __init__(self):
        self.db_path = "data/settings.sqlite3"
        self.trading_variables_path = Path("data_info/trading_variables")

    def scan_help_guide_files(self):
        """모든 help_guide.yaml 파일 스캔"""
        print("🔍 help_guide.yaml 파일 스캔 중...")

        help_files = []
        for help_file in self.trading_variables_path.rglob("help_guide.yaml"):
            # 경로에서 변수 ID 추출: data_info/trading_variables/{category}/{variable}/help_guide.yaml
            parts = help_file.parts
            if len(parts) >= 4:
                category = parts[-3]
                variable_folder = parts[-2]

                # 변수 ID 매핑 (폴더명 → 변수 ID)
                variable_id = self.folder_to_variable_id(variable_folder)

                help_files.append({
                    "variable_id": variable_id,
                    "category": category,
                    "folder": variable_folder,
                    "file_path": help_file
                })

        print(f"📁 발견된 파일: {len(help_files)}개")
        return help_files

    def folder_to_variable_id(self, folder_name):
        """폴더명을 변수 ID로 변환"""
        # 폴더명 → 변수 ID 매핑
        mapping = {
            # Trend
            "sma": "SMA",
            "ema": "EMA",
            "bollinger_bands": "BOLLINGER_BANDS",
            "parabolic_sar": "PARABOLIC_SAR",
            "ichimoku": "ICHIMOKU",
            "pivot_points": "PIVOT_POINTS",
            "linear_regression": "LINEAR_REGRESSION",

            # Momentum
            "rsi": "RSI",
            "macd": "MACD",
            "stochastic": "STOCHASTIC",
            "cci": "CCI",
            "williams_r": "WILLIAMS_R",
            "roc": "ROC",
            "tsi": "TSI",

            # Volume
            "volume_sma": "VOLUME_SMA",
            "volume_weighted_price": "VOLUME_WEIGHTED_PRICE",
            "on_balance_volume": "ON_BALANCE_VOLUME",
            "chaikin_money_flow": "CHAIKIN_MONEY_FLOW",

            # Volatility
            "atr": "ATR",
            "standard_deviation": "STANDARD_DEVIATION",
            "bollinger_width": "BOLLINGER_WIDTH",
            "vix": "VIX",

            # Price
            "current_price": "CURRENT_PRICE",
            "price_change_rate": "PRICE_CHANGE_RATE",

            # Capital
            "cash_balance": "CASH_BALANCE",
            "position_size": "POSITION_SIZE",

            # State
            "market_phase": "MARKET_PHASE",

            # Meta
            "external_variable": "EXTERNAL_VARIABLE"
        }

        return mapping.get(folder_name, folder_name.upper())

    def load_help_guide_yaml(self, file_path):
        """help_guide.yaml 파일 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ {file_path} 로드 실패: {e}")
            return None

    def parse_help_guide_content(self, yaml_content, variable_id):
        """YAML 내용을 DB 레코드 형태로 파싱"""
        if not yaml_content:
            return []

        records = []

        # guides 구조: 리스트 형태의 가이드들
        if "guides" in yaml_content and isinstance(yaml_content["guides"], list):
            for i, guide in enumerate(yaml_content["guides"]):
                if isinstance(guide, dict):
                    title = guide.get("title", f"{variable_id} Guide {i+1}")
                    content = guide.get("content", "")
                    target_audience = guide.get("target_audience", "general")
                    priority = guide.get("priority", 5)
                    tags = guide.get("tags", [])

                    # 카테고리 결정 (title 기반)
                    category = self.determine_category_from_title(title)

                    records.append({
                        "variable_id": variable_id,
                        "help_category": category,
                        "title": title,
                        "content": content,
                        "display_order": priority,
                        "help_level": target_audience,
                        "content_type": "markdown",
                        "tags": f"{variable_id},{','.join(tags) if isinstance(tags, list) else tags}",
                        "examples": "",
                        "related_links": "",
                        "last_updated": datetime.now().isoformat()
                    })

        # 기존 help_guide 구조도 지원 (하위 호환성)
        elif "help_guide" in yaml_content and isinstance(yaml_content["help_guide"], dict):
            for category, content in yaml_content["help_guide"].items():
                if isinstance(content, str):
                    records.append({
                        "variable_id": variable_id,
                        "help_category": category,
                        "title": f"{variable_id} {category.title()}",
                        "content": content,
                        "display_order": self.get_category_order(category),
                        "help_level": "detailed",
                        "content_type": "text",
                        "tags": f"{variable_id},{category}",
                        "examples": "",
                        "related_links": "",
                        "last_updated": datetime.now().isoformat()
                    })

        return records

    def determine_category_from_title(self, title):
        """제목에서 카테고리 추론"""
        title_lower = title.lower()

        if any(word in title_lower for word in ["이해", "정의", "개념", "기본"]):
            return "concept"
        elif any(word in title_lower for word in ["전략", "활용", "사용법", "적용"]):
            return "usage"
        elif any(word in title_lower for word in ["고급", "전문", "심화", "기법"]):
            return "advanced"
        elif any(word in title_lower for word in ["예시", "예제", "사례"]):
            return "examples"
        elif any(word in title_lower for word in ["주의", "경고", "위험"]):
            return "warnings"
        elif any(word in title_lower for word in ["팁", "노하우", "비법"]):
            return "tips"
        else:
            return "general"

    def get_category_order(self, category):
        """카테고리별 표시 순서"""
        order_map = {
            "concept": 1,
            "usage": 2,
            "parameter_guide": 3,
            "examples": 4,
            "notes": 5,
            "tips": 6,
            "warnings": 7
        }
        return order_map.get(category, 99)

    def clear_existing_help_documents(self):
        """기존 help documents 삭제 (SMA 중복 제거)"""
        print("🗑️  기존 help documents 정리 중...")

        try:
            with sqlite3.connect(self.db_path) as conn:
                # 기존 데이터 삭제
                conn.execute("DELETE FROM tv_variable_help_documents")
                print("✅ 기존 데이터 삭제 완료")
        except Exception as e:
            print(f"❌ 기존 데이터 삭제 실패: {e}")

    def insert_help_documents(self, records):
        """DB에 help documents 대량 삽입"""
        print(f"💾 DB에 {len(records)}개 레코드 삽입 중...")

        try:
            with sqlite3.connect(self.db_path) as conn:
                insert_sql = """
                INSERT INTO tv_variable_help_documents (
                    variable_id, help_category, content_type, title_ko,
                    content_ko, display_order
                ) VALUES (?, ?, ?, ?, ?, ?)
                """

                for record in records:
                    conn.execute(insert_sql, (
                        record["variable_id"],
                        record["help_category"],
                        record["content_type"],
                        record["title"],  # title → title_ko
                        record["content"],  # content → content_ko
                        record["display_order"]
                    ))

                print(f"✅ {len(records)}개 레코드 삽입 완료")

                # 결과 확인
                cursor = conn.execute("SELECT COUNT(*) FROM tv_variable_help_documents")
                total_count = cursor.fetchone()[0]
                print(f"📊 총 help documents: {total_count}개")

                # 변수별 개수 확인
                cursor = conn.execute("""
                    SELECT variable_id, COUNT(*) as count
                    FROM tv_variable_help_documents
                    GROUP BY variable_id
                    ORDER BY variable_id
                """)
                variable_counts = cursor.fetchall()

                print(f"📋 변수별 도움말 개수:")
                for var_id, count in variable_counts:
                    print(f"  - {var_id}: {count}개")

        except Exception as e:
            print(f"❌ DB 삽입 실패: {e}")
            raise

    def run_bulk_import(self):
        """대량 이관 실행"""
        print("🚀 Help Guide 대량 DB 이관 시작")
        print("=" * 60)

        # 1. 파일 스캔
        help_files = self.scan_help_guide_files()

        if not help_files:
            print("❌ help_guide.yaml 파일을 찾을 수 없습니다.")
            return

        # 2. 기존 데이터 정리
        self.clear_existing_help_documents()

        # 3. YAML 파일들 처리
        all_records = []
        processed_variables = set()

        for file_info in help_files:
            variable_id = file_info["variable_id"]
            file_path = file_info["file_path"]

            print(f"\n📖 처리 중: {variable_id} ({file_path.name})")

            # YAML 로드
            yaml_content = self.load_help_guide_yaml(file_path)

            if yaml_content:
                # 레코드 파싱
                records = self.parse_help_guide_content(yaml_content, variable_id)

                if records:
                    all_records.extend(records)
                    processed_variables.add(variable_id)
                    print(f"  ✅ {len(records)}개 섹션 파싱 완료")
                else:
                    print(f"  ⚠️  파싱된 레코드 없음")
            else:
                print(f"  ❌ YAML 로드 실패")

        # 4. DB 삽입
        if all_records:
            print(f"\n" + "=" * 60)
            print(f"📊 이관 요약")
            print(f"=" * 60)
            print(f"처리된 변수: {len(processed_variables)}개")
            print(f"생성된 레코드: {len(all_records)}개")

            self.insert_help_documents(all_records)

            print(f"\n🎉 대량 이관 완료!")
            print(f"다음: 트리거 빌더에서 헬프 버튼 연결")
        else:
            print(f"❌ 처리할 레코드가 없습니다.")

        return len(processed_variables), len(all_records)


def main():
    print("🔧 Help Guide 대량 DB 이관 도구")
    print("목표: 28개 변수의 help_guide.yaml → tv_variable_help_documents")

    importer = HelpGuideImporter()
    importer.run_bulk_import()


if __name__ == "__main__":
    main()

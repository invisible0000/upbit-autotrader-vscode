#!/usr/bin/env python3
"""
data_info 폴더의 YAML 파일과 실제 데이터베이스 간의 정밀 검증 스크립트
- YAML과 DB 데이터 일치성 검증
- 누락된 데이터 식별
- 데이터 무결성 검증
"""

import yaml
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json

class DataIntegrityValidator:
    def __init__(self):
        self.data_info_path = Path("data_info")
        self.db_path = Path("data/settings.sqlite3")
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "yaml_analysis": {},
            "db_analysis": {},
            "mismatches": [],
            "missing_data": [],
            "recommendations": []
        }

    def run_integrity_check(self):
        """데이터 무결성 전체 검사"""
        print("=== DATA_INFO ↔ DATABASE 무결성 검증 ===\n")

        if not self.db_path.exists():
            print(f"❌ 데이터베이스 파일 없음: {self.db_path}")
            return

        # 1. 핵심 YAML 파일들 분석
        self.analyze_yaml_files()

        # 2. 데이터베이스 분석
        self.analyze_database()

        # 3. 데이터 일치성 검증
        self.verify_data_consistency()

        # 4. 리포트 생성
        self.generate_integrity_report()

    def analyze_yaml_files(self):
        """YAML 파일들의 상세 분석"""
        print("1. YAML 파일 상세 분석")

        # tv_trading_variables.yaml 분석
        self.analyze_trading_variables_yaml()

        # tv_variable_parameters.yaml 분석
        self.analyze_variable_parameters_yaml()

        # 기타 YAML 파일들 분석
        self.analyze_support_yaml_files()

    def analyze_trading_variables_yaml(self):
        """trading_variables YAML 분석"""
        yaml_file = self.data_info_path / "tv_trading_variables.yaml"
        print(f"  📄 분석: {yaml_file.name}")

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if 'trading_variables' in data:
                variables = data['trading_variables']
                analysis = {
                    "total_count": len(variables),
                    "categories": {},
                    "meta_variables": [],
                    "required_parameters": [],
                    "missing_fields": []
                }

                for var_id, var_data in variables.items():
                    # 카테고리별 분류
                    category = var_data.get('purpose_category', 'unknown')
                    if category not in analysis["categories"]:
                        analysis["categories"][category] = 0
                    analysis["categories"][category] += 1

                    # META 변수 식별
                    if var_id.startswith('META_') or var_id in ['PYRAMID_TARGET']:
                        analysis["meta_variables"].append(var_id)

                    # 파라미터 필요 변수
                    if var_data.get('parameter_required', False):
                        analysis["required_parameters"].append(var_id)

                    # 필수 필드 검사
                    required_fields = ['display_name_ko', 'display_name_en', 'description']
                    for field in required_fields:
                        if field not in var_data:
                            analysis["missing_fields"].append(f"{var_id}.{field}")

                self.report["yaml_analysis"]["trading_variables"] = analysis

                print(f"    ✅ 변수 총 개수: {analysis['total_count']}")
                print(f"    🏷️  카테고리: {len(analysis['categories'])}")
                for cat, count in analysis["categories"].items():
                    print(f"      - {cat}: {count}")
                print(f"    🔧 META 변수: {len(analysis['meta_variables'])}")
                print(f"    ⚙️  파라미터 필요: {len(analysis['required_parameters'])}")

                if analysis["missing_fields"]:
                    print(f"    ⚠️  누락 필드: {len(analysis['missing_fields'])}")
                    for field in analysis["missing_fields"][:5]:  # 처음 5개만 표시
                        print(f"      - {field}")

        except Exception as e:
            print(f"    ❌ 오류: {e}")
            self.report["yaml_analysis"]["trading_variables"] = {"error": str(e)}

    def analyze_variable_parameters_yaml(self):
        """variable_parameters YAML 분석"""
        yaml_file = self.data_info_path / "tv_variable_parameters.yaml"
        print(f"  📄 분석: {yaml_file.name}")

        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if 'variable_parameters' in data:
                parameters = data['variable_parameters']
                analysis = {
                    "total_count": len(parameters),
                    "by_variable": {},
                    "by_type": {},
                    "meta_parameters": [],
                    "invalid_types": []
                }

                valid_types = {'boolean', 'integer', 'string', 'decimal'}

                for param_key, param_data in parameters.items():
                    var_id = param_data.get('variable_id', 'unknown')
                    param_type = param_data.get('parameter_type', 'unknown')

                    # 변수별 파라미터 수
                    if var_id not in analysis["by_variable"]:
                        analysis["by_variable"][var_id] = 0
                    analysis["by_variable"][var_id] += 1

                    # 타입별 분류
                    if param_type not in analysis["by_type"]:
                        analysis["by_type"][param_type] = 0
                    analysis["by_type"][param_type] += 1

                    # META 변수 파라미터
                    if var_id.startswith('META_') or var_id in ['PYRAMID_TARGET']:
                        analysis["meta_parameters"].append(param_key)

                    # 잘못된 타입 검사
                    if param_type not in valid_types:
                        analysis["invalid_types"].append(f"{param_key}: {param_type}")

                self.report["yaml_analysis"]["variable_parameters"] = analysis

                print(f"    ✅ 파라미터 총 개수: {analysis['total_count']}")
                print(f"    📊 변수별 분포: {len(analysis['by_variable'])}")
                print(f"    🔧 META 파라미터: {len(analysis['meta_parameters'])}")

                if analysis["invalid_types"]:
                    print(f"    ⚠️  잘못된 타입: {len(analysis['invalid_types'])}")
                    for invalid in analysis["invalid_types"][:5]:
                        print(f"      - {invalid}")

        except Exception as e:
            print(f"    ❌ 오류: {e}")
            self.report["yaml_analysis"]["variable_parameters"] = {"error": str(e)}

    def analyze_support_yaml_files(self):
        """지원 YAML 파일들 분석"""
        support_files = [
            "tv_parameter_types.yaml",
            "tv_indicator_categories.yaml",
            "tv_comparison_groups.yaml"
        ]

        for filename in support_files:
            yaml_file = self.data_info_path / filename
            if yaml_file.exists():
                print(f"  📄 분석: {filename}")
                try:
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    # 파일별 간단한 통계
                    file_analysis = {"sections": len(data) if isinstance(data, dict) else 0}
                    if isinstance(data, dict):
                        for key, value in data.items():
                            if isinstance(value, dict):
                                file_analysis[f"{key}_count"] = len(value)

                    self.report["yaml_analysis"][filename] = file_analysis
                    print(f"    ✅ 섹션: {file_analysis['sections']}")

                except Exception as e:
                    print(f"    ❌ 오류: {e}")
                    self.report["yaml_analysis"][filename] = {"error": str(e)}

    def analyze_database(self):
        """데이터베이스 분석"""
        print("\n2. 데이터베이스 분석")

        try:
            conn = sqlite3.connect(self.db_path)

            # tv_trading_variables 테이블 분석
            self.analyze_db_trading_variables(conn)

            # tv_variable_parameters 테이블 분석
            self.analyze_db_variable_parameters(conn)

            conn.close()

        except Exception as e:
            print(f"❌ 데이터베이스 연결 오류: {e}")
            self.report["db_analysis"]["error"] = str(e)

    def analyze_db_trading_variables(self, conn):
        """DB의 trading_variables 테이블 분석"""
        print("  🗄️  tv_trading_variables 테이블")

        try:
            df = pd.read_sql_query("""
                SELECT variable_id, purpose_category, parameter_required, is_active,
                       display_name_ko, display_name_en, description
                FROM tv_trading_variables
            """, conn)

            analysis = {
                "total_count": len(df),
                "active_count": len(df[df['is_active'] == 1]),
                "categories": df['purpose_category'].value_counts().to_dict(),
                "meta_variables": list(df[df['variable_id'].str.startswith('META_') |
                                          (df['variable_id'] == 'PYRAMID_TARGET')]['variable_id']),
                "parameter_required_count": len(df[df['parameter_required'] == 1]),
                "missing_display_names": []
            }

            # 누락된 표시명 확인
            for _, row in df.iterrows():
                if pd.isna(row['display_name_ko']) or pd.isna(row['display_name_en']):
                    analysis["missing_display_names"].append(row['variable_id'])

            self.report["db_analysis"]["trading_variables"] = analysis

            print(f"    ✅ 총 변수: {analysis['total_count']}")
            print(f"    🟢 활성 변수: {analysis['active_count']}")
            print(f"    🔧 META 변수: {len(analysis['meta_variables'])}")
            print(f"    ⚙️  파라미터 필요: {analysis['parameter_required_count']}")

            if analysis["missing_display_names"]:
                print(f"    ⚠️  표시명 누락: {len(analysis['missing_display_names'])}")

        except Exception as e:
            print(f"    ❌ 오류: {e}")
            self.report["db_analysis"]["trading_variables"] = {"error": str(e)}

    def analyze_db_variable_parameters(self, conn):
        """DB의 variable_parameters 테이블 분석"""
        print("  🗄️  tv_variable_parameters 테이블")

        try:
            df = pd.read_sql_query("""
                SELECT variable_id, parameter_name, parameter_type,
                       is_required, default_value
                FROM tv_variable_parameters
            """, conn)

            analysis = {
                "total_count": len(df),
                "by_variable": df['variable_id'].value_counts().to_dict(),
                "by_type": df['parameter_type'].value_counts().to_dict(),
                "meta_count": len(df[df['variable_id'].str.startswith('META_') |
                                    (df['variable_id'] == 'PYRAMID_TARGET')]),
                "required_count": len(df[df['is_required'] == 1])
            }

            # 잘못된 타입 확인
            valid_types = {'boolean', 'integer', 'string', 'decimal'}
            invalid_types = df[~df['parameter_type'].isin(valid_types)]
            analysis["invalid_types"] = list(invalid_types['parameter_type'].unique())

            self.report["db_analysis"]["variable_parameters"] = analysis

            print(f"    ✅ 총 파라미터: {analysis['total_count']}")
            print(f"    🔧 META 파라미터: {analysis['meta_count']}")
            print(f"    ⚙️  필수 파라미터: {analysis['required_count']}")

            if analysis["invalid_types"]:
                print(f"    ⚠️  잘못된 타입: {analysis['invalid_types']}")

        except Exception as e:
            print(f"    ❌ 오류: {e}")
            self.report["db_analysis"]["variable_parameters"] = {"error": str(e)}

    def verify_data_consistency(self):
        """YAML과 DB 데이터 일치성 검증"""
        print("\n3. 데이터 일치성 검증")

        yaml_vars = self.report["yaml_analysis"].get("trading_variables", {})
        db_vars = self.report["db_analysis"].get("trading_variables", {})

        yaml_params = self.report["yaml_analysis"].get("variable_parameters", {})
        db_params = self.report["db_analysis"].get("variable_parameters", {})

        # 변수 개수 비교
        if yaml_vars.get("total_count") != db_vars.get("total_count"):
            mismatch = {
                "type": "variable_count_mismatch",
                "yaml_count": yaml_vars.get("total_count", 0),
                "db_count": db_vars.get("total_count", 0)
            }
            self.report["mismatches"].append(mismatch)
            print(f"  ⚠️  변수 개수 불일치: YAML({mismatch['yaml_count']}) vs DB({mismatch['db_count']})")

        # 파라미터 개수 비교
        if yaml_params.get("total_count") != db_params.get("total_count"):
            mismatch = {
                "type": "parameter_count_mismatch",
                "yaml_count": yaml_params.get("total_count", 0),
                "db_count": db_params.get("total_count", 0)
            }
            self.report["mismatches"].append(mismatch)
            print(f"  ⚠️  파라미터 개수 불일치: YAML({mismatch['yaml_count']}) vs DB({mismatch['db_count']})")

        # META 변수 비교
        yaml_meta = set(yaml_vars.get("meta_variables", []))
        db_meta = set(db_vars.get("meta_variables", []))

        if yaml_meta != db_meta:
            mismatch = {
                "type": "meta_variables_mismatch",
                "yaml_only": list(yaml_meta - db_meta),
                "db_only": list(db_meta - yaml_meta)
            }
            self.report["mismatches"].append(mismatch)
            print(f"  ⚠️  META 변수 불일치:")
            if mismatch["yaml_only"]:
                print(f"    YAML에만 있음: {mismatch['yaml_only']}")
            if mismatch["db_only"]:
                print(f"    DB에만 있음: {mismatch['db_only']}")

        if not self.report["mismatches"]:
            print("  ✅ 모든 데이터가 일치합니다!")

    def generate_integrity_report(self):
        """무결성 검증 리포트 생성"""
        print("\n4. 무결성 검증 리포트 생성")

        # 권장사항 생성
        self.generate_recommendations()

        # 리포트 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data_integrity_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)

        print(f"  📄 리포트 저장: {report_file}")

        # 요약 출력
        print("\n=== 무결성 검증 요약 ===")
        print(f"불일치 발견: {len(self.report['mismatches'])}")
        print(f"누락 데이터: {len(self.report['missing_data'])}")
        print(f"권장사항: {len(self.report['recommendations'])}")

        if self.report["recommendations"]:
            print("\n💡 주요 권장사항:")
            for i, rec in enumerate(self.report["recommendations"][:3], 1):
                print(f"  {i}. {rec}")

    def generate_recommendations(self):
        """권장사항 생성"""
        recommendations = []

        # 잘못된 파라미터 타입이 있으면
        yaml_params = self.report["yaml_analysis"].get("variable_parameters", {})
        if yaml_params.get("invalid_types"):
            recommendations.append("YAML의 잘못된 parameter_type을 수정하세요")

        db_params = self.report["db_analysis"].get("variable_parameters", {})
        if db_params.get("invalid_types"):
            recommendations.append("데이터베이스의 잘못된 parameter_type을 수정하세요")

        # 불일치가 있으면
        if self.report["mismatches"]:
            recommendations.append("YAML과 데이터베이스 간의 불일치를 해결하세요")

        # 누락된 필드가 있으면
        yaml_vars = self.report["yaml_analysis"].get("trading_variables", {})
        if yaml_vars.get("missing_fields"):
            recommendations.append("YAML의 누락된 필수 필드를 추가하세요")

        self.report["recommendations"] = recommendations

if __name__ == "__main__":
    validator = DataIntegrityValidator()
    validator.run_integrity_check()

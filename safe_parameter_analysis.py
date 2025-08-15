#!/usr/bin/env python3
"""
안전한 파라미터 타입 복원 및 로직 분석 스크립트

목표:
1. 기존 변경사항을 원래대로 되돌리기
2. 각 파라미터의 실제 사용 목적 분석
3. 로직적으로 enum vs string 판단
4. float vs decimal 분석
"""

import sqlite3
import yaml
import json
from pathlib import Path
from datetime import datetime
import shutil

class SafeParameterTypeAnalyzer:
    def __init__(self):
        self.db_path = "data/settings.sqlite3"
        self.yaml_path = Path("data_info/tv_variable_parameters.yaml")
        self.backup_folder = Path("legacy")

        # 유효한 타입들
        self.valid_types = {'boolean', 'integer', 'string', 'decimal', 'enum'}

        # 분석 결과
        self.analysis_result = {
            "reverted_changes": [],
            "logical_analysis": {},
            "enum_candidates": [],
            "decimal_vs_float": [],
            "final_recommendations": {}
        }

    def run_full_analysis(self):
        """전체 분석 프로세스 실행"""
        print("=== 안전한 파라미터 타입 복원 및 분석 ===\n")

        # 1. 현재 상태 백업
        self.create_safety_backup()

        # 2. 변경사항 되돌리기 (DB + YAML)
        self.revert_all_changes()

        # 3. 각 파라미터의 로직 분석
        self.analyze_parameter_logic()

        # 4. enum 후보 식별
        self.identify_enum_candidates()

        # 5. decimal vs float 분석
        self.analyze_decimal_vs_float()

        # 6. 최종 권장사항 생성
        self.generate_final_recommendations()

        # 7. 리포트 저장
        self.save_analysis_report()

    def create_safety_backup(self):
        """안전 백업 생성"""
        print("1. 안전 백업 생성")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # DB 백업
        db_backup = self.backup_folder / f"settings_before_revert_{timestamp}.sqlite3"
        shutil.copy2(self.db_path, db_backup)
        print(f"  📁 DB 백업: {db_backup.name}")

        # YAML 백업
        yaml_backup = self.backup_folder / f"tv_variable_parameters_before_revert_{timestamp}.yaml"
        shutil.copy2(self.yaml_path, yaml_backup)
        print(f"  📁 YAML 백업: {yaml_backup.name}")

        self.analysis_result["backup_files"] = [str(db_backup), str(yaml_backup)]

    def revert_all_changes(self):
        """모든 변경사항을 원래대로 되돌리기"""
        print("\n2. 변경사항 되돌리기")

        # A. 데이터베이스 복원
        self.revert_database_changes()

        # B. YAML 파일 복원
        self.revert_yaml_changes()

    def revert_database_changes(self):
        """데이터베이스 변경사항 복원"""
        print("  A. 데이터베이스 복원")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 이전에 string으로 변경된 것들을 원래 타입으로 복원
        revert_mappings = [
            # external_variable 관련
            ("tracking_variable", "external_variable"),
            ("source_variable", "external_variable"),
            ("reference_value", "external_variable"),

            # 방향/방법 관련
            ("direction", "trail_direction"),
            ("trail_direction", "trail_direction"),
            ("calculation_method", "calculation_method"),
            ("reset_trigger", "reset_trigger"),

            # timeframe은 enum으로
            ("timeframe", "enum"),

            # band_position 등도 enum으로
            ("band_position", "enum"),
            ("detection_type", "enum"),
            ("breakout_type", "enum"),
            ("detection_sensitivity", "enum")
        ]

        for param_name, original_type in revert_mappings:
            cursor.execute("""
                UPDATE tv_variable_parameters
                SET parameter_type = ?
                WHERE parameter_name = ?
            """, (original_type, param_name))

            affected = cursor.rowcount
            if affected > 0:
                print(f"    ✅ {param_name}: string → {original_type} ({affected}개)")
                self.analysis_result["reverted_changes"].append(f"{param_name} → {original_type}")

        conn.commit()
        conn.close()

    def revert_yaml_changes(self):
        """YAML 파일 변경사항 복원"""
        print("  B. YAML 파일 복원")

        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        parameters = data.get('variable_parameters', {})
        changes_made = 0

        # 원래 타입으로 복원
        for param_key, param_data in parameters.items():
            # timeframe들을 enum으로
            if param_data.get('parameter_name') == 'timeframe':
                param_data['parameter_type'] = 'enum'
                changes_made += 1
                print(f"    ✅ {param_key}.timeframe: string → enum")

            # band_position 등을 enum으로
            elif param_data.get('parameter_name') in ['band_position', 'detection_type', 'breakout_type']:
                param_data['parameter_type'] = 'enum'
                changes_made += 1
                print(f"    ✅ {param_key}.{param_data.get('parameter_name')}: string → enum")

            # external_variable 관련
            elif param_data.get('parameter_name') in ['tracking_variable', 'source_variable', 'reference_value']:
                param_data['parameter_type'] = 'external_variable'
                changes_made += 1
                print(f"    ✅ {param_key}.{param_data.get('parameter_name')}: string → external_variable")

        if changes_made > 0:
            # 수정된 내용 저장
            with open(self.yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                         sort_keys=False, indent=2)
            print(f"    📄 YAML 파일 저장됨 ({changes_made}개 변경)")

    def analyze_parameter_logic(self):
        """각 파라미터의 사용 로직 분석"""
        print("\n3. 파라미터 로직 분석")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 모든 파라미터 조회
        cursor.execute("""
            SELECT variable_id, parameter_name, parameter_type,
                   default_value, enum_values, description
            FROM tv_variable_parameters
            ORDER BY variable_id, parameter_name
        """)

        results = cursor.fetchall()

        for var_id, param_name, param_type, default_value, enum_values, description in results:
            analysis = self.analyze_single_parameter(
                var_id, param_name, param_type, default_value, enum_values, description
            )

            key = f"{var_id}.{param_name}"
            self.analysis_result["logical_analysis"][key] = analysis

            print(f"  📊 {key}: {param_type} → {analysis['recommendation']}")

        conn.close()

    def analyze_single_parameter(self, var_id, param_name, param_type, default_value, enum_values, description):
        """개별 파라미터 분석"""

        # enum_values 파싱
        parsed_enum_values = []
        if enum_values:
            try:
                parsed_enum_values = json.loads(enum_values)
            except:
                pass

        # 분석 로직
        analysis = {
            "current_type": param_type,
            "has_enum_values": bool(parsed_enum_values),
            "enum_count": len(parsed_enum_values),
            "recommendation": param_type,
            "reason": "현재 타입 유지"
        }

        # timeframe 분석
        if param_name == 'timeframe':
            analysis["recommendation"] = "enum"
            analysis["reason"] = "업비트 API에서 고정된 timeframe 사용, 사용자 실수 방지 필수"

        # band_position 등 위치 관련
        elif 'position' in param_name or 'band' in param_name:
            analysis["recommendation"] = "enum"
            analysis["reason"] = "상단/하단 등 고정된 위치값, 실수 입력 방지"

        # tracking_variable 등 변수 참조
        elif 'variable' in param_name:
            analysis["recommendation"] = "external_variable"
            analysis["reason"] = "다른 변수를 참조하는 특수 타입"

        # detection, breakout 등 방법론
        elif param_name in ['detection_type', 'breakout_type', 'calculation_method']:
            analysis["recommendation"] = "enum"
            analysis["reason"] = "미리 정의된 알고리즘 방법, 선택지 제한 필요"

        # period, multiplier 등 숫자값
        elif param_name in ['period', 'multiplier', 'factor']:
            if param_type in ['float', 'decimal']:
                analysis["recommendation"] = "decimal"
                analysis["reason"] = "정밀도가 중요한 금융 계산"
            else:
                analysis["recommendation"] = param_type

        # enum_values가 있으면 enum 추천
        elif parsed_enum_values and len(parsed_enum_values) > 1:
            analysis["recommendation"] = "enum"
            analysis["reason"] = f"enum_values에 {len(parsed_enum_values)}개 선택지 정의됨"

        return analysis

    def identify_enum_candidates(self):
        """enum으로 변경해야 할 후보들 식별"""
        print("\n4. ENUM 후보 식별")

        for key, analysis in self.analysis_result["logical_analysis"].items():
            if analysis["recommendation"] == "enum" and analysis["current_type"] != "enum":
                self.analysis_result["enum_candidates"].append({
                    "parameter": key,
                    "current_type": analysis["current_type"],
                    "reason": analysis["reason"]
                })
                print(f"  🎯 {key}: {analysis['current_type']} → enum ({analysis['reason']})")

    def analyze_decimal_vs_float(self):
        """decimal vs float 분석"""
        print("\n5. DECIMAL vs FLOAT 분석")

        print("  💰 Decimal의 장점:")
        print("    - 정확한 부동소수점 연산 (0.1 + 0.2 = 0.3)")
        print("    - 금융 계산에서 반올림 오차 없음")
        print("    - 사용자 설정값 그대로 저장/표시")

        print("  ⚡ Float의 장점:")
        print("    - 메모리 효율적")
        print("    - 연산 속도 빠름")
        print("    - 일반적인 숫자 처리에 적합")

        print("  🎯 금융 자동매매에서는 Decimal 권장!")

    def generate_final_recommendations(self):
        """최종 권장사항 생성"""
        print("\n6. 최종 권장사항")

        # enum 변경 권장사항
        enum_changes = {}
        for candidate in self.analysis_result["enum_candidates"]:
            param = candidate["parameter"]
            enum_changes[param] = {
                "from": candidate["current_type"],
                "to": "enum",
                "reason": candidate["reason"]
            }

        self.analysis_result["final_recommendations"] = {
            "enum_changes": enum_changes,
            "decimal_policy": "float → decimal for financial precision",
            "external_variable_policy": "keep for variable references"
        }

        print(f"  📋 ENUM 변경 권장: {len(enum_changes)}개")
        for param, change in enum_changes.items():
            print(f"    - {param}: {change['from']} → {change['to']}")

    def save_analysis_report(self):
        """분석 리포트 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"parameter_type_analysis_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_result, f, ensure_ascii=False, indent=2)

        print(f"\n📄 분석 리포트 저장: {report_file}")

if __name__ == "__main__":
    analyzer = SafeParameterTypeAnalyzer()
    analyzer.run_full_analysis()

    print("\n" + "="*60)
    print("🎯 분석 완료! 다음 단계:")
    print("1. 분석 리포트 검토")
    print("2. enum 변경사항 적용")
    print("3. UI에서 enum 타입 지원 구현")
    print("="*60)

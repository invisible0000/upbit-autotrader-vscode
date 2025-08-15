#!/usr/bin/env python3
"""
기존 YAML 데이터 기반 Trading Variables 구조 자동 생성기

tv_trading_variables.yaml의 정보를 기반으로 누락된 변수들의
완전한 파일 구조를 자동 생성합니다.
"""

import yaml
from pathlib import Path
from typing import Dict, Any


class TradingVariableGenerator:
    """거래 변수 구조 자동 생성기"""

    def __init__(self):
        self.source_file = Path("data_info/tv_trading_variables.yaml")
        self.base_path = Path("data_info/trading_variables")
        self.registry_path = Path("data_info/_management/trading_variables_registry.yaml")

    def load_source_data(self) -> Dict[str, Any]:
        """기존 YAML 데이터 로드"""
        with open(self.source_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def create_definition_yaml(self, var_name: str, var_data: Dict[str, Any]) -> str:
        """definition.yaml 내용 생성"""
        return f"""# ═══════════════════════════════════════════════════════════════
# {var_data.get('display_name_ko', var_name)} ({var_name}) - 정의 파일
# ═══════════════════════════════════════════════════════════════

variable_name: "{var_name}"
display_name: "{var_data.get('display_name_ko', '')}"
description: "{var_data.get('description', '')}"
purpose_category: "{var_data.get('purpose_category', '')}"
chart_category: "{var_data.get('chart_category', '')}"
comparison_group: "{var_data.get('comparison_group', '')}"
ui_component_type: "input_field"
is_customizable: {str(var_data.get('parameter_required', True)).lower()}
is_active: {str(var_data.get('is_active', True)).lower()}
sort_order: 100
tooltip: "{var_data.get('description', '')}"
source_type: "built_in"
"""

    def create_parameters_yaml(self, var_name: str, var_data: Dict[str, Any]) -> str:
        """parameters.yaml 내용 생성"""
        parameter_required = var_data.get('parameter_required', True)

        if not parameter_required:
            return f"""# ═══════════════════════════════════════════════════════════════
# {var_data.get('display_name_ko', var_name)} ({var_name}) - 파라미터 파일
# ═══════════════════════════════════════════════════════════════

# {var_data.get('display_name_ko', var_name)}는 파라미터가 필요 없는 변수입니다
# 시스템에서 자동으로 계산되거나 API에서 가져오는 값입니다

parameters: []

# 메타 정보
variable_info:
  parameter_required: false
  data_source: "system_calculated"
  update_frequency: "realtime"
  precision: 8
"""
        else:
            return f"""# ═══════════════════════════════════════════════════════════════
# {var_data.get('display_name_ko', var_name)} ({var_name}) - 파라미터 파일
# ═══════════════════════════════════════════════════════════════

parameters:
  - name: "period"
    display_name: "기간"
    type: "int"
    default_value: 14
    min_value: 1
    max_value: 200
    step_value: 1
    description: "계산에 사용할 기간"
    tooltip: "값이 클수록 더 안정적이지만 느린 반응을 보입니다"
    required: true
    sort_order: 1

# 메타 정보
variable_info:
  parameter_required: true
  calculation_type: "technical_indicator"
  update_frequency: "realtime"
"""

    def create_help_texts_yaml(self, var_name: str, var_data: Dict[str, Any]) -> str:
        """help_texts.yaml 내용 생성"""
        display_name = var_data.get('display_name_ko', var_name)
        description = var_data.get('description', '')

        return f"""# ═══════════════════════════════════════════════════════════════
# {display_name} ({var_name}) - 도움말 텍스트
# ═══════════════════════════════════════════════════════════════

help_texts:
  - title: "{display_name}란?"
    content: "{description}"
    target_audience: "beginner"
    priority: 10
    tags: ["기본개념", "정의"]

  - title: "{display_name} 활용법"
    content: "{display_name}을(를) 활용하여 매매 조건을 설정하거나 다른 지표와 조합하여 전략을 구성할 수 있습니다."
    target_audience: "general"
    priority: 8
    tags: ["활용법", "전략구성"]

  - title: "{display_name} 주의사항"
    content: "{display_name} 사용 시 시장 상황과 다른 지표들을 함께 고려하여 신중하게 판단하세요."
    target_audience: "intermediate"
    priority: 6
    tags: ["주의사항", "리스크"]
"""

    def create_placeholders_yaml(self, var_name: str, var_data: Dict[str, Any]) -> str:
        """placeholders.yaml 내용 생성"""
        parameter_required = var_data.get('parameter_required', True)
        display_name = var_data.get('display_name_ko', var_name)

        if not parameter_required:
            return f"""# ═══════════════════════════════════════════════════════════════
# {display_name} ({var_name}) - 플레이스홀더 텍스트
# ═══════════════════════════════════════════════════════════════

# {display_name}는 파라미터가 없으므로 플레이스홀더도 비어있습니다

placeholders: []

# 메타 정보
metadata:
  note: "{display_name}는 시스템에서 자동으로 계산되는 값이므로 사용자 입력이 필요 없습니다"
  display_format: "{{value:,.2f}}"
  example_value: "예시 값"
"""
        else:
            return f"""# ═══════════════════════════════════════════════════════════════
# {display_name} ({var_name}) - 플레이스홀더 텍스트
# ═══════════════════════════════════════════════════════════════

placeholders:
  - parameter_name: "period"
    placeholder_text: "기간을 입력하세요 (예: 14)"
    example_value: "14"
    tooltip: "계산 기간 (1-200)"

# 메타 정보
metadata:
  note: "{display_name} 계산을 위한 파라미터 입력 가이드"
  input_validation: "1 ≤ 값 ≤ 200"
"""

    def create_help_guide_yaml(self, var_name: str, var_data: Dict[str, Any]) -> str:
        """help_guide.yaml 내용 생성"""
        display_name = var_data.get('display_name_ko', var_name)
        description = var_data.get('description', '')
        purpose_category = var_data.get('purpose_category', '')

        category_names = {
            'trend': '추세',
            'momentum': '모멘텀',
            'volume': '거래량',
            'volatility': '변동성',
            'price': '가격',
            'capital': '자본',
            'state': '상태',
            'meta': '메타',
            'dynamic_management': '동적 관리'
        }

        category_ko = category_names.get(purpose_category, purpose_category)

        return f"""# ═══════════════════════════════════════════════════════════════
# {display_name} ({var_name}) - 상세 가이드
# ═══════════════════════════════════════════════════════════════

guides:
  - title: "{display_name}의 이해"
    content: |
      ## 📊 {display_name}란?

      {display_name}는 **{category_ko} 관련 정보**를 제공하는 변수입니다.

      ### 📋 기본 정보
      - **설명**: {description}
      - **카테고리**: {category_ko}
      - **차트 표시**: {var_data.get('chart_category', '')}
      - **비교 그룹**: {var_data.get('comparison_group', '')}

      ### 💡 주요 특징
      - 실시간 업데이트되는 값
      - 다른 지표와 조합 가능
      - 전략 조건 설정에 활용
    target_audience: "beginner"
    priority: 10
    tags: ["기본개념", "{category_ko}", "정의"]

  - title: "{display_name} 활용 전략"
    content: |
      ## 🎯 전략 구성 방법

      ### 1. 조건 설정 예시
      ```
      {display_name} > 기준값 일 때 매수
      {display_name} < 기준값 일 때 매도
      ```

      ### 2. 다른 지표와 조합
      - **추세 확인**: SMA, EMA와 함께 사용
      - **모멘텀 확인**: RSI, MACD와 조합
      - **변동성 체크**: ATR, 볼린저밴드 참고

      ### 3. 리스크 관리
      - 단일 지표만으로 판단 금지
      - 시장 상황 고려 필수
      - 손절 조건 반드시 설정

      ⚠️ **주의**: 과거 데이터 기반이므로 미래를 보장하지 않습니다.
    target_audience: "intermediate"
    priority: 8
    tags: ["전략", "활용법", "조합"]

  - title: "고급 활용 기법"
    content: |
      ## 🔧 전문가 활용법

      ### 1. 다중 시간대 분석
      ```
      1분봉 {display_name} vs 5분봉 {display_name}
      → 단기 vs 중기 신호 비교
      ```

      ### 2. 동적 임계값 설정
      ```
      {display_name} 변화율 기반 조건
      급격한 변화 감지 시 특별 대응
      ```

      ### 3. 백테스팅 검증
      - 과거 데이터로 전략 성과 확인
      - 다양한 시장 상황에서 테스트
      - 최적 파라미터 탐색

      💡 **팁**: 실제 거래 전 반드시 시뮬레이션으로 검증하세요.
    target_audience: "advanced"
    priority: 6
    tags: ["고급기법", "최적화", "백테스팅"]
"""

    def get_category_from_purpose(self, purpose_category: str) -> str:
        """purpose_category를 실제 폴더명으로 매핑"""
        mapping = {
            'dynamic_management': 'meta'
        }
        return mapping.get(purpose_category, purpose_category)

    def create_variable_structure(self, var_name: str, var_data: Dict[str, Any]):
        """단일 변수의 완전한 구조 생성"""
        purpose_category = var_data.get('purpose_category', 'other')
        category = self.get_category_from_purpose(purpose_category)

        # 폴더명은 소문자로
        folder_name = var_name.lower()
        if folder_name.startswith('meta_'):
            folder_name = folder_name[5:]  # META_ 제거

        var_path = self.base_path / category / folder_name

        print(f"📁 생성 중: {var_name} → {var_path}")

        # 폴더 생성
        var_path.mkdir(parents=True, exist_ok=True)

        # 각 파일 생성
        files_to_create = {
            'definition.yaml': self.create_definition_yaml(var_name, var_data),
            'parameters.yaml': self.create_parameters_yaml(var_name, var_data),
            'help_texts.yaml': self.create_help_texts_yaml(var_name, var_data),
            'placeholders.yaml': self.create_placeholders_yaml(var_name, var_data),
            'help_guide.yaml': self.create_help_guide_yaml(var_name, var_data)
        }

        for filename, content in files_to_create.items():
            file_path = var_path / filename
            if not file_path.exists():  # 기존 파일은 덮어쓰지 않음
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ {filename}")
            else:
                print(f"  ⏭️  {filename} (이미 존재함)")

    def generate_all_missing_structures(self):
        """모든 누락된 변수 구조 생성"""
        print("🚀 Trading Variables 구조 자동 생성 시작...\n")

        # 기존 데이터 로드
        source_data = self.load_source_data()
        trading_variables = source_data.get('trading_variables', {})

        print(f"📊 총 {len(trading_variables)}개 변수 발견")

        created_count = 0
        skipped_count = 0

        for var_name, var_data in trading_variables.items():
            # 이미 존재하는지 확인
            purpose_category = var_data.get('purpose_category', 'other')
            category = self.get_category_from_purpose(purpose_category)

            folder_name = var_name.lower()
            if folder_name.startswith('meta_'):
                folder_name = folder_name[5:]

            var_path = self.base_path / category / folder_name

            if var_path.exists() and len(list(var_path.glob('*.yaml'))) >= 4:
                print(f"⏭️  {var_name} (이미 완성됨)")
                skipped_count += 1
            else:
                self.create_variable_structure(var_name, var_data)
                created_count += 1

            print()  # 빈 줄

        print(f"📈 생성 완료!")
        print(f"  - 새로 생성: {created_count}개")
        print(f"  - 기존 유지: {skipped_count}개")
        print(f"  - 총 변수: {len(trading_variables)}개")


def main():
    generator = TradingVariableGenerator()
    generator.generate_all_missing_structures()


if __name__ == "__main__":
    main()

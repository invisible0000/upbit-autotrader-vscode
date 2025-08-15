#!/usr/bin/env python3
"""
Trading Variables 구조 검증 스크립트

새로운 trading_variables 구조가 올바르게 생성되었는지 확인합니다.
"""

import yaml
from pathlib import Path


def validate_trading_variables_structure():
    """Trading Variables 구조 검증"""
    print("🔍 Trading Variables 구조 검증 시작...")

    base_path = Path("data_info/trading_variables")
    registry_path = Path("data_info/_management/trading_variables_registry.yaml")

    # 레지스트리 로드
    if not registry_path.exists():
        print(f"❌ 레지스트리 파일이 없습니다: {registry_path}")
        return False

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    print(f"📊 레지스트리 로드 완료: v{registry['metadata']['version']}")

    # 카테고리 확인
    categories = list(registry['categories'].keys())
    print(f"📁 등록된 카테고리: {categories}")

    actual_categories = [d.name for d in base_path.iterdir() if d.is_dir()]
    print(f"📁 실제 카테고리: {actual_categories}")

    # 거래 변수들 확인
    variables = registry.get('trading_variables', {})
    print(f"\n📋 등록된 거래 변수: {len(variables)}개")

    complete_count = 0
    for var_name, var_info in variables.items():
        category = var_info['category']

        # 폴더명 매핑 (META_ prefix 제거)
        folder_name = var_name.lower()
        if folder_name.startswith('meta_'):
            folder_name = folder_name[5:]  # META_ 제거

        var_path = base_path / category / folder_name

        print(f"\n🔍 검증 중: {var_name} ({category})")

        # 폴더 존재 확인
        if not var_path.exists():
            print(f"  ❌ 폴더 없음: {var_path}")
            continue

        # 필수 파일들 확인
        required_files = ['definition.yaml', 'parameters.yaml', 'help_texts.yaml', 'placeholders.yaml']
        optional_files = ['help_guide.yaml']

        files_status = {}
        for file_name in required_files + optional_files:
            file_path = var_path / file_name
            exists = file_path.exists()
            files_status[file_name] = exists
            status = "✅" if exists else "❌"
            req_status = "(필수)" if file_name in required_files else "(선택)"
            print(f"  {status} {file_name} {req_status}")

        # 완성도 평가
        required_complete = all(files_status[f] for f in required_files)
        optional_complete = all(files_status[f] for f in optional_files)

        if required_complete and optional_complete:
            print("  🌟 완전 ✅")
            complete_count += 1
        elif required_complete:
            print("  ⚡ 기본 ✅ (선택 파일 추가 가능)")
        else:
            print("  ❌ 불완전")

    print("\n📈 완성 통계:")
    print(f"  - 전체 변수: {len(variables)}개")
    print(f"  - 완전 구현: {complete_count}개")
    print(f"  - 완성률: {complete_count / len(variables) * 100:.1f}%")    # 새로 추가된 가격 변수 확인
    price_path = base_path / "price"
    if price_path.exists():
        price_vars = [d.name for d in price_path.iterdir() if d.is_dir()]
        print(f"\n💰 가격 변수들: {price_vars}")

        # CURRENT_PRICE 상세 확인
        current_price_path = price_path / "current_price"
        if current_price_path.exists():
            print(f"\n📊 CURRENT_PRICE 상세 검증:")
            for file_name in ['definition.yaml', 'parameters.yaml', 'help_guide.yaml', 'help_texts.yaml', 'placeholders.yaml']:
                file_path = current_price_path / file_name
                if file_path.exists():
                    print(f"  ✅ {file_name}")

                    # definition.yaml 내용 확인
                    if file_name == 'definition.yaml':
                        with open(file_path, 'r', encoding='utf-8') as f:
                            definition = yaml.safe_load(f)
                        print(f"    - 변수명: {definition.get('variable_name')}")
                        print(f"    - 표시명: {definition.get('display_name')}")
                        print(f"    - 카테고리: {definition.get('purpose_category')}")
                else:
                    print(f"  ❌ {file_name}")

    print(f"\n🎉 Trading Variables 구조 검증 완료!")
    return True


if __name__ == "__main__":
    validate_trading_variables_structure()

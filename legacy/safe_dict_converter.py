#!/usr/bin/env python3
"""
Smart Data Provider 파일들의 dict 형식 통일 - 안전한 변환
"""
import os
import re

def fix_smart_data_provider():
    """안전하게 smart_data_provider.py 수정"""

    base_path = "upbit_auto_trading/infrastructure/market_data_backbone/smart_data_provider"

    # 1. responses.py 수정
    responses_path = f"{base_path}/models/responses.py"
    if os.path.exists(responses_path):
        print(f"✓ {responses_path} 이미 수정됨")

    # 2. requests.py 수정
    requests_path = f"{base_path}/models/requests.py"
    if os.path.exists(requests_path):
        print(f"✓ {requests_path} 이미 수정됨")

    # 3. smart_data_provider.py의 핵심 변경사항
    core_path = f"{base_path}/core/smart_data_provider.py"

    # 먼저 backup에서 복사
    backup_path = f"{base_path}/core/smart_data_provider copy.py"
    with open(backup_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 핵심 변경사항만 적용
    print("핵심 변경사항 적용 중...")

    # import에서 레거시 모델 제거 필요 확인
    lines = content.split('\n')
    new_lines = []

    for line in lines:
        # DataResponse나 ResponseMetadata import 제거
        if 'from ..models.responses import DataResponse, ResponseMetadata' in line:
            continue
        elif 'from ..models.responses import' in line and 'DataResponse' in line:
            # UnifiedDataResponse만 import하도록 수정
            line = 'from ..models.responses import UnifiedDataResponse'

        new_lines.append(line)

    content = '\n'.join(new_lines)

    # 파일 저장
    with open(core_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ {core_path} 기본 수정 완료")

    # 오류 체크
    print("\n오류 확인 중...")
    import subprocess
    try:
        result = subprocess.run(['python', '-m', 'py_compile', core_path],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ 문법 오류 없음")
        else:
            print(f"✗ 문법 오류 발견: {result.stderr}")
    except Exception as e:
        print(f"오류 체크 실패: {e}")

def main():
    """메인 함수"""
    print("Smart Data Provider dict 형식 통일 시작...")
    fix_smart_data_provider()
    print("완료!")

if __name__ == "__main__":
    main()

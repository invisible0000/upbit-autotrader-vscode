#!/usr/bin/env python3
"""smart_data_provider.py 파일에서 dict 문법 오류 수정"""

import re

def fix_dict_syntax():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\core\smart_data_provider.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # { 로 시작하는 dict에서 잘못된 ) 를 } 로 수정
    # 다중라인 dict 패턴을 찾아서 수정

    lines = content.split('\n')
    in_dict = False
    dict_start_line = -1

    for i, line in enumerate(lines):
        stripped = line.strip()

        # dict 시작 감지
        if (('metadata={' in line or 'metadata = {' in line) and
            not '}' in line):
            in_dict = True
            dict_start_line = i
            continue

        # dict 내부에 있을 때
        if in_dict:
            # 잘못된 ) 를 } 로 수정
            if stripped == ')':
                lines[i] = line.replace(')', '}')
                in_dict = False
            elif stripped.startswith('}'):
                in_dict = False

    content = '\n'.join(lines)

    # 다른 잘못된 패턴들 수정
    # metadata 딕셔너리 내부의 키들에서 따옴표 수정
    content = re.sub(r"'(\w+)':\s*", r"'\1': ", content)

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("dict 문법 오류 수정 완료")

if __name__ == "__main__":
    fix_dict_syntax()

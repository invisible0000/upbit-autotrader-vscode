#!/usr/bin/env python3
"""dict 문법 오류 안전 수정 스크립트"""

def safe_dict_fix():
    file_path = r"upbit_auto_trading\infrastructure\market_data_backbone\smart_data_provider\core\smart_data_provider.py"

    # 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # dict 시작과 끝을 매칭하여 수정
    i = 0
    while i < len(lines):
        line = lines[i]

        # metadata = { 로 시작하는 라인 찾기
        if ('metadata = {' in line or 'metadata={' in line) and line.strip().endswith('{'):
            # 해당 dict의 끝을 찾기
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == ')':
                    # ) 를 } 로 변경
                    lines[j] = lines[j].replace(')', '}')
                    break
                elif lines[j].strip() == '}':
                    # 이미 올바른 형태
                    break

        # record_access 함수 호출에서 잘못된 문법 수정
        if 'record_access(' in line and "'cache_hit'" in line:
            # 'cache_hit': True/False -> cache_hit=True/False
            if "'cache_hit': True" in line:
                lines[i] = line.replace("'cache_hit': True", "cache_hit=True")
            elif "'cache_hit': False" in line:
                lines[i] = line.replace("'cache_hit': False", "cache_hit=False")

        i += 1

    # 파일 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("Dict 문법 오류 안전 수정 완료")

if __name__ == "__main__":
    safe_dict_fix()

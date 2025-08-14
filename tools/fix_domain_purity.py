#!/usr/bin/env python3
"""
Domain Purity 수정 도구 (DDD 의존성 위반 해결)
Domain 계층에서 Infrastructure 의존성을 제거합니다.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple


def get_domain_files() -> List[Path]:
    """Domain 계층의 모든 Python 파일 목록 반환"""
    domain_path = Path("upbit_auto_trading/domain")
    return list(domain_path.rglob("*.py"))


def remove_infrastructure_imports(file_path: Path) -> bool:
    """파일에서 Infrastructure import 제거"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Infrastructure logging import 제거
        content = re.sub(
            r'^from upbit_auto_trading\.infrastructure\.logging import create_component_logger\n',
            '',
            content,
            flags=re.MULTILINE
        )

        # Infrastructure configuration import 제거
        content = re.sub(
            r'^from upbit_auto_trading\.infrastructure\.configuration import .*\n',
            '',
            content,
            flags=re.MULTILINE
        )

        # sqlite3 import 제거 (Domain에서는 사용하지 않아야 함)
        content = re.sub(
            r'^import sqlite3\n',
            '',
            content,
            flags=re.MULTILINE
        )

        # 중복된 빈 줄 정리
        content = re.sub(r'\n\n\n+', '\n\n', content)

        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

    except Exception as e:
        print(f"❌ {file_path} 처리 실패: {e}")
        return False

    return False


def remove_logger_usage(file_path: Path) -> bool:
    """파일에서 logger 사용 제거"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        original_lines = lines[:]
        filtered_lines = []

        for line in lines:
            # logger 초기화 라인 제거
            if 'self.logger = create_component_logger(' in line:
                continue

            # logger 사용 라인을 주석으로 변경
            if 'self.logger.' in line:
                indent = len(line) - len(line.lstrip())
                comment_line = ' ' * indent + f"# Domain Layer: 로깅 제거됨 - {line.strip()}\n"
                filtered_lines.append(comment_line)
                continue

            filtered_lines.append(line)

        if filtered_lines != original_lines:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(filtered_lines)
            return True

    except Exception as e:
        print(f"❌ {file_path} logger 제거 실패: {e}")
        return False

    return False


def remove_deprecated_files():
    """DEPRECATED 파일들 제거"""
    deprecated_files = [
        "upbit_auto_trading/domain/database_configuration/services/database_path_service_DEPRECATED.py",
        "upbit_auto_trading/infrastructure/configuration/__init___legacy.py",
        "upbit_auto_trading/ui/desktop/screens/settings/api_settings/api_key_manager_secure_legacy.py"
    ]

    removed_count = 0
    for file_path in deprecated_files:
        path = Path(file_path)
        if path.exists():
            try:
                # 백업 생성
                backup_path = path.with_suffix('.py.removed')
                path.rename(backup_path)
                print(f"✅ 제거됨: {file_path} -> {backup_path}")
                removed_count += 1
            except Exception as e:
                print(f"❌ 제거 실패 {file_path}: {e}")

    return removed_count


def main():
    """메인 실행 함수"""
    print("🔧 Domain Purity 수정 도구 시작")
    print("=" * 60)

    # 1. DEPRECATED 파일 제거
    print("\n📁 DEPRECATED 파일 제거 중...")
    removed_count = remove_deprecated_files()
    print(f"✅ {removed_count}개 DEPRECATED 파일 제거 완료")

    # 2. Domain 파일 정리
    print("\n🔍 Domain 계층 파일 검사 중...")
    domain_files = get_domain_files()
    print(f"📊 총 {len(domain_files)}개 파일 발견")

    import_fixed = 0
    logger_fixed = 0

    for file_path in domain_files:
        print(f"🔧 처리 중: {file_path}")

        # Infrastructure import 제거
        if remove_infrastructure_imports(file_path):
            import_fixed += 1
            print(f"  ✅ Infrastructure import 제거됨")

        # Logger 사용 제거
        if remove_logger_usage(file_path):
            logger_fixed += 1
            print(f"  ✅ Logger 사용 제거됨")

    print("\n" + "=" * 60)
    print("📊 Domain Purity 수정 완료")
    print(f"🔄 Infrastructure import 수정: {import_fixed}개 파일")
    print(f"🔇 Logger 사용 제거: {logger_fixed}개 파일")
    print(f"🗑️ DEPRECATED 파일 제거: {removed_count}개 파일")

    print("\n🔍 검증을 위해 super_legacy_detector를 다시 실행하세요:")
    print("python tools/super_legacy_detector.py")


if __name__ == "__main__":
    main()

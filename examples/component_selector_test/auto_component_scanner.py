"""
자동 컴포넌트 스캐너 - 실제 코드베이스에서 컴포넌트 자동 추출
=============================================================

Infrastructure 로깅 시스템에서 create_component_logger 사용 패턴을 스캔하여
실제 사용되는 컴포넌트 목록을 자동 생성합니다.
"""

import re
from pathlib import Path
from typing import Dict, Set


class ComponentScanner:
    """실제 코드베이스에서 컴포넌트를 자동 스캔"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.upbit_root = self.project_root / "upbit_auto_trading"

    def scan_all_components(self) -> Dict:
        """모든 컴포넌트를 DDD 계층별로 스캔"""
        components = {
            "🖥️ Presentation Layer": {},
            "🏗️ Application Layer": {},
            "🎯 Domain Layer": {},
            "🔌 Infrastructure Layer": {}
        }

        # 1. create_component_logger 사용 패턴 스캔
        used_components = self._scan_logger_usage()

        # 2. 파일 구조 기반 스캔
        structure_components = self._scan_file_structure()

        # 3. 두 결과 병합 및 DDD 계층별 분류
        all_components = used_components | structure_components

        for component in sorted(all_components):
            layer = self._classify_ddd_layer(component)
            category = self._get_component_category(component)

            if layer not in components:
                components[layer] = {}
            if category not in components[layer]:
                components[layer][category] = {}

            # 이모지 추가로 시각적 구분
            display_name = self._add_component_emoji(component)
            components[layer][category][display_name] = component

        return components

    def _scan_logger_usage(self) -> Set[str]:
        """create_component_logger 사용 패턴에서 컴포넌트명 추출"""
        components = set()
        pattern = r'create_component_logger\(["\']([^"\']+)["\']\)'

        for py_file in self.upbit_root.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # 파일 경로를 컴포넌트 경로로 변환
                        relative_path = py_file.relative_to(self.project_root)
                        component_path = str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
                        components.add(component_path)
                        components.add(match)  # 실제 사용된 이름도 추가
            except Exception:
                continue

        return components

    def _scan_file_structure(self) -> Set[str]:
        """파일 구조를 기반으로 컴포넌트 스캔"""
        components = set()

        for py_file in self.upbit_root.rglob("*.py"):
            if py_file.name.startswith('__') or py_file.name.startswith('test_'):
                continue

            try:
                relative_path = py_file.relative_to(self.project_root)
                component_path = str(relative_path).replace('/', '.').replace('\\', '.').replace('.py', '')
                components.add(component_path)
            except Exception:
                continue

        return components

    def _classify_ddd_layer(self, component: str) -> str:
        """컴포넌트를 DDD 계층으로 분류"""
        if '.ui.' in component or '.desktop.' in component:
            return "🖥️ Presentation Layer"
        elif '.application.' in component:
            return "🏗️ Application Layer"
        elif '.domain.' in component:
            return "🎯 Domain Layer"
        elif '.infrastructure.' in component:
            return "🔌 Infrastructure Layer"
        else:
            # 기본값: 경로 구조로 추정
            if component.startswith('upbit_auto_trading.ui'):
                return "🖥️ Presentation Layer"
            elif component.startswith('upbit_auto_trading.application'):
                return "🏗️ Application Layer"
            elif component.startswith('upbit_auto_trading.domain'):
                return "🎯 Domain Layer"
            elif component.startswith('upbit_auto_trading.infrastructure'):
                return "🔌 Infrastructure Layer"
            else:
                return "🔌 Infrastructure Layer"  # 기본값

    def _get_component_category(self, component: str) -> str:
        """컴포넌트 카테고리 분류"""
        if '.ui.desktop.screens.' in component:
            return "📱 Desktop Screens"
        elif '.ui.desktop.components.' in component:
            return "🧩 UI Components"
        elif '.ui.desktop.' in component:
            return "📱 Desktop UI"
        elif '.application.use_cases.' in component:
            return "📋 Use Cases"
        elif '.application.services.' in component:
            return "🔄 Services"
        elif '.domain.entities.' in component:
            return "🏪 Entities"
        elif '.domain.services.' in component:
            return "🔧 Services"
        elif '.infrastructure.repositories.' in component:
            return "🗄️ Repositories"
        elif '.infrastructure.logging.' in component:
            return "📝 Logging"
        elif '.infrastructure.' in component:
            return "🌐 External APIs"
        else:
            return "🔧 기타"

    def _add_component_emoji(self, component: str) -> str:
        """컴포넌트에 적절한 이모지 추가"""
        name = component.split('.')[-1]

        # 기능별 이모지 매핑
        emoji_map = {
            'main_window': '🏠',
            'settings': '⚙️',
            'dashboard': '📊',
            'chart': '📈',
            'trading': '💰',
            'strategy': '🎯',
            'engine': '🚀',
            'api': '🌐',
            'repository': '🗄️',
            'service': '🔧',
            'manager': '👨‍💼',
            'logger': '📝',
            'config': '⚙️',
            'handler': '🔧'
        }

        for key, emoji in emoji_map.items():
            if key in name.lower():
                return f"{emoji} {name.replace('_', ' ').title()}"

        return f"🔧 {name.replace('_', ' ').title()}"

    def generate_component_data_file(self, output_path: str = "auto_generated_component_data.py") -> str:
        """컴포넌트 데이터 파일 자동 생성"""
        components = self.scan_all_components()        # Python 코드 생성
        code = '''"""
자동 생성된 컴포넌트 데이터 - 실제 코드베이스 스캔 결과
=========================================================

create_component_logger 사용 패턴과 파일 구조를 기반으로
실제 존재하는 컴포넌트들을 자동 스캔하여 생성됨
"""

REAL_COMPONENT_TREE_DATA = '''

        code += self._dict_to_python_code(components, indent=0)

        code += '''

def get_real_components_flat():
    """실제 컴포넌트를 평면 리스트로 변환"""
    flat_list = []

    def _flatten(data, prefix=""):
        for key, value in data.items():
            if isinstance(value, dict):
                if any(isinstance(v, str) for v in value.values()):
                    # 말단 카테고리
                    for item_key, item_value in value.items():
                        if isinstance(item_value, str):
                            display_name = f"{prefix}{item_key}"
                            flat_list.append((display_name, item_value))
                else:
                    # 중간 카테고리
                    current_prefix = f"{prefix}{key} > "
                    _flatten(value, current_prefix)
            else:
                # 개별 컴포넌트
                display_name = f"{prefix}{key}"
                flat_list.append((display_name, value))

    _flatten(REAL_COMPONENT_TREE_DATA)
    return flat_list

def search_real_components(query):
    """실제 컴포넌트 검색"""
    query = query.lower()
    flat_list = get_real_components_flat()

    results = []
    for display_name, path in flat_list:
        if query in display_name.lower() or query in path.lower():
            results.append((display_name, path))

    return results
'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)

        return output_path

    def _dict_to_python_code(self, data, indent=0) -> str:
        """딕셔너리를 Python 코드 문자열로 변환"""
        if not isinstance(data, dict):
            return repr(data)

        spaces = "    " * indent
        lines = ["{"]

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f'{spaces}    "{key}": {self._dict_to_python_code(value, indent + 1)},')
            else:
                lines.append(f'{spaces}    "{key}": "{value}",')

        lines.append(f"{spaces}}}")
        return "\n".join(lines)


def test_scanner():
    """스캐너 테스트 실행"""
    project_root = Path(__file__).parent.parent.parent
    scanner = ComponentScanner(str(project_root))

    print("🔍 실제 컴포넌트 스캔 중...")
    components = scanner.scan_all_components()

    print("📊 발견된 컴포넌트 통계:")
    for layer, categories in components.items():
        if isinstance(categories, dict):
            count = sum(len(items) if isinstance(items, dict) else 1 for items in categories.values())
            print(f"  {layer}: {count}개")

    # 자동 생성 파일 생성
    output_file = scanner.generate_component_data_file()
    print(f"✅ 자동 생성 완료: {output_file}")

    return components


if __name__ == "__main__":
    test_scanner()

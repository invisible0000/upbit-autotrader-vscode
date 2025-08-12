"""
실제 컴포넌트 데이터 스캐너

프로젝트 내의 실제 컴포넌트들을 자동으로 스캔하여 데이터를 생성합니다.
create_component_logger 사용 패턴과 파일 구조를 기반으로 동작합니다.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union


class ComponentDataScanner:
    """실제 컴포넌트 데이터 스캐너"""

    def __init__(self, project_root: Optional[str] = None):
        if project_root is None:
            # 현재 파일 위치에서 프로젝트 루트 추정
            current_file = Path(__file__)
            self.project_root = current_file.parents[8]  # 프로젝트 루트까지 올라가기
        else:
            self.project_root = Path(project_root)

        self.upbit_auto_trading_path = self.project_root / "upbit_auto_trading"

    def scan_all_components(self) -> Dict[str, Dict[str, str]]:
        """모든 컴포넌트를 스캔하여 계층별로 분류"""
        components = {
            "🎨 Presentation Layer": {},
            "🚀 Application Layer": {},
            "🧠 Domain Layer": {},
            "🔧 Infrastructure Layer": {}
        }

        # 각 계층별로 스캔
        components["🎨 Presentation Layer"] = self._scan_presentation_layer()
        components["🚀 Application Layer"] = self._scan_application_layer()
        components["🧠 Domain Layer"] = self._scan_domain_layer()
        components["🔧 Infrastructure Layer"] = self._scan_infrastructure_layer()

        return components

    def scan_all_components_hierarchical(self) -> Dict[str, Any]:
        """모든 컴포넌트를 계층적 트리 구조로 스캔"""
        components = {
            "🎨 Presentation Layer": self._scan_presentation_layer_hierarchical(),
            "🚀 Application Layer": self._scan_application_layer_hierarchical(),
            "🧠 Domain Layer": self._scan_domain_layer_hierarchical(),
            "🔧 Infrastructure Layer": self._scan_infrastructure_layer_hierarchical()
        }
        return components

    def _scan_presentation_layer_hierarchical(self) -> Dict[str, Any]:
        """Presentation Layer를 계층적으로 스캔"""
        structure = {}

        # UI 디렉토리 스캔
        ui_path = self.upbit_auto_trading_path / "ui"
        if ui_path.exists():
            structure["📱 UI"] = self._scan_directory_hierarchical(ui_path, "upbit_auto_trading.ui")

        # Presentation 디렉토리 스캔
        presentation_path = self.upbit_auto_trading_path / "presentation"
        if presentation_path.exists():
            structure["🎯 Presentation"] = self._scan_directory_hierarchical(
                presentation_path, "upbit_auto_trading.presentation"
            )

        return structure

    def _scan_application_layer_hierarchical(self) -> Dict[str, Any]:
        """Application Layer를 계층적으로 스캔"""
        app_path = self.upbit_auto_trading_path / "application"
        if app_path.exists():
            return self._scan_directory_hierarchical(app_path, "upbit_auto_trading.application")
        return {}

    def _scan_domain_layer_hierarchical(self) -> Dict[str, Any]:
        """Domain Layer를 계층적으로 스캔"""
        domain_path = self.upbit_auto_trading_path / "domain"
        if domain_path.exists():
            return self._scan_directory_hierarchical(domain_path, "upbit_auto_trading.domain")
        return {}

    def _scan_infrastructure_layer_hierarchical(self) -> Dict[str, Any]:
        """Infrastructure Layer를 계층적으로 스캔"""
        infra_path = self.upbit_auto_trading_path / "infrastructure"
        if infra_path.exists():
            return self._scan_directory_hierarchical(infra_path, "upbit_auto_trading.infrastructure")
        return {}

    def _scan_directory_hierarchical(self, directory: Path, module_prefix: str, max_depth: int = 3) -> Dict[str, Any]:
        """디렉토리를 계층적으로 스캔"""
        structure = {}

        # 현재 디렉토리의 파이썬 파일들에서 컴포넌트 찾기
        for py_file in directory.glob("*.py"):
            if py_file.name == "__init__.py":
                continue

            component_names = self._extract_component_names_from_file(py_file)
            if component_names:
                relative_path = py_file.relative_to(self.upbit_auto_trading_path.parent)
                module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

                for comp_name in component_names:
                    display_name = self._clean_component_name(comp_name, py_file.name)
                    structure[display_name] = module_path

        # 서브디렉토리들을 재귀적으로 스캔 (깊이 제한)
        if max_depth > 0:
            for sub_dir in directory.iterdir():
                if sub_dir.is_dir() and sub_dir.name != "__pycache__":
                    sub_structure = self._scan_directory_hierarchical(
                        sub_dir,
                        f"{module_prefix}.{sub_dir.name}",
                        max_depth - 1
                    )
                    if sub_structure:  # 내용이 있는 경우만 추가
                        folder_icon = self._get_folder_icon(sub_dir.name)
                        structure[f"{folder_icon} {sub_dir.name.replace('_', ' ').title()}"] = sub_structure

        return structure

    def _get_folder_icon(self, folder_name: str) -> str:
        """폴더명에 따른 아이콘 반환"""
        icon_map = {
            "desktop": "🖥️",
            "widgets": "🧩",
            "screens": "📺",
            "settings": "⚙️",
            "logging": "📝",
            "dialogs": "💬",
            "common": "🔧",
            "components": "🧩",
            "services": "⚙️",
            "entities": "📦",
            "events": "⚡",
            "models": "📊",
            "database": "🗃️",
            "api": "🌐",
            "utils": "🛠️",
            "config": "⚙️",
            "exceptions": "⚠️"
        }
        return icon_map.get(folder_name, "📁")

    def _scan_presentation_layer(self) -> Dict[str, str]:
        """Presentation Layer 컴포넌트 스캔"""
        components = {}

        # UI 디렉토리 스캔
        ui_path = self.upbit_auto_trading_path / "ui"
        if ui_path.exists():
            components.update(self._scan_directory_for_components(
                ui_path, "upbit_auto_trading.ui"
            ))

        # Presentation 디렉토리 스캔
        presentation_path = self.upbit_auto_trading_path / "presentation"
        if presentation_path.exists():
            components.update(self._scan_directory_for_components(
                presentation_path, "upbit_auto_trading.presentation"
            ))

        return components

    def _scan_application_layer(self) -> Dict[str, str]:
        """Application Layer 컴포넌트 스캔"""
        app_path = self.upbit_auto_trading_path / "application"
        if app_path.exists():
            return self._scan_directory_for_components(
                app_path, "upbit_auto_trading.application"
            )
        return {}

    def _scan_domain_layer(self) -> Dict[str, str]:
        """Domain Layer 컴포넌트 스캔"""
        domain_path = self.upbit_auto_trading_path / "domain"
        if domain_path.exists():
            return self._scan_directory_for_components(
                domain_path, "upbit_auto_trading.domain"
            )
        return {}

    def _scan_infrastructure_layer(self) -> Dict[str, str]:
        """Infrastructure Layer 컴포넌트 스캔"""
        infra_path = self.upbit_auto_trading_path / "infrastructure"
        if infra_path.exists():
            return self._scan_directory_for_components(
                infra_path, "upbit_auto_trading.infrastructure"
            )
        return {}

    def _scan_directory_for_components(self, directory: Path, module_prefix: str) -> Dict[str, str]:
        """디렉토리를 스캔하여 컴포넌트들을 찾음"""
        components = {}

        for py_file in directory.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # 파일에서 create_component_logger 사용 패턴 찾기
            component_names = self._extract_component_names_from_file(py_file)

            if component_names:
                # 모듈 경로 생성
                relative_path = py_file.relative_to(self.upbit_auto_trading_path.parent)
                module_path = str(relative_path.with_suffix("")).replace(os.sep, ".")

                for comp_name in component_names:
                    # 컴포넌트 이름 정리
                    display_name = self._clean_component_name(comp_name, py_file.name)
                    components[display_name] = module_path

        return components

    def _extract_component_names_from_file(self, file_path: Path) -> List[str]:
        """파일에서 create_component_logger 호출을 찾아 컴포넌트 이름 추출"""
        component_names = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # create_component_logger("ComponentName") 패턴 찾기
            pattern = r'create_component_logger\s*\(\s*["\']([^"\']+)["\']\s*\)'
            matches = re.findall(pattern, content)

            if matches:
                component_names.extend(matches)
            else:
                # 클래스명도 추출 (fallback)
                class_pattern = r'class\s+([A-Z][a-zA-Z0-9_]*)\s*[\(:]'
                class_matches = re.findall(class_pattern, content)
                if class_matches:
                    # 주요 클래스만 필터링 (Widget, View, Service, Manager 등)
                    filtered_classes = [
                        cls for cls in class_matches
                        if any(keyword in cls for keyword in
                               ['Widget', 'View', 'Screen', 'Service', 'Manager',
                                'Dialog', 'Panel', 'Component', 'Controller'])
                    ]
                    component_names.extend(filtered_classes)

        except Exception:
            # 파일 읽기 실패시 무시
            pass

        return component_names

    def _clean_component_name(self, component_name: str, file_name: str) -> str:
        """컴포넌트 이름 정리 및 아이콘 추가"""
        # 파일명에서 추론한 카테고리별 아이콘
        if any(keyword in file_name.lower() for keyword in ['widget', 'ui', 'view', 'screen']):
            return f"🔧 {component_name}"
        elif any(keyword in file_name.lower() for keyword in ['service', 'manager']):
            return f"⚙️ {component_name}"
        elif any(keyword in file_name.lower() for keyword in ['dialog', 'popup']):
            return f"💬 {component_name}"
        elif any(keyword in file_name.lower() for keyword in ['chart', 'graph']):
            return f"📈 {component_name}"
        elif any(keyword in file_name.lower() for keyword in ['data', 'repository']):
            return f"📊 {component_name}"
        else:
            return f"🔧 {component_name}"

    def get_flat_component_list(self) -> List[Tuple[str, str]]:
        """플랫 형태의 컴포넌트 리스트 반환 (검색용)"""
        all_components = self.scan_all_components()
        flat_list = []

        for layer_name, components in all_components.items():
            for comp_name, comp_path in components.items():
                flat_list.append((comp_name, comp_path))

        return flat_list

    def search_components(self, query: str) -> List[Tuple[str, str]]:
        """컴포넌트 검색"""
        if not query:
            return self.get_flat_component_list()

        query_lower = query.lower()
        results = []

        for comp_name, comp_path in self.get_flat_component_list():
            if (query_lower in comp_name.lower() or
                query_lower in comp_path.lower()):
                results.append((comp_name, comp_path))

        return results


# 모듈 레벨에서 사용할 수 있는 기본 인스턴스
_scanner = ComponentDataScanner()


def get_real_component_data() -> Dict[str, Dict[str, str]]:
    """실제 컴포넌트 데이터 반환"""
    return _scanner.scan_all_components()


def get_real_component_data_hierarchical() -> Dict[str, Any]:
    """실제 컴포넌트 데이터를 계층적 구조로 반환"""
    return _scanner.scan_all_components_hierarchical()


def search_real_components(query: str) -> List[Tuple[str, str]]:
    """실제 컴포넌트 검색"""
    return _scanner.search_components(query)

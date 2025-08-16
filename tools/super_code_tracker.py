#!/usr/bin/env python3
"""
🔍 Super Code Tracker
개발 추적 및 기능 발견 도구 - DDD 계층별 기능 분석 및 중복 방지

🤖 LLM 사용 가이드:
===================
이 도구는 개발 중 기존 기능 발견과 코드 추적을 위한 전문 도구입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_code_tracker.py --feature-discovery <키워드>      # 기능 빠른 탐지 ⭐
2. python super_code_tracker.py --layer-analysis                  # DDD 계층별 기능 분포 ⭐
3. python super_code_tracker.py --duplicate-detection             # 중복 기능 탐지
4. python super_code_tracker.py --feature-map                     # 기능별 코드 위치 매핑
5. python super_code_tracker.py --quick-search <키워드>           # 키워드 기반 빠른 검색
6. python super_code_tracker.py --unused-cleanup                  # 미사용 코드 정리 제안

🎯 사용 시나리오:
- 🔍 새 기능 개발 전: --feature-discovery "trading strategy" (중복 개발 방지)
- 📊 아키텍처 점검: --layer-analysis (DDD 준수 확인)
- 🧹 코드 정리: --unused-cleanup (미사용 파일 제거)
- 🗺️ 코드 네비게이션: --feature-map (기능 위치 파악)

💡 기존 도구 통합:
- super_db_table_reference_code_analyzer.py → 테이블 참조 추적
- super_file_dependency_analyzer.py → 의존성 분석
- super_files_unused_detector.py → 미사용 코드 탐지
- super_import_tracker.py → import 관계 추적

작성일: 2025-08-16
작성자: Upbit Auto Trading Team
"""

import re
import ast
import time
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from collections import defaultdict
import argparse
import sys

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class FeatureInfo:
    """기능 정보"""
    name: str
    file_path: str
    layer: str  # Domain, Application, Infrastructure, Presentation
    function_count: int
    class_count: int
    line_count: int
    dependencies: List[str]
    description: str = ""


@dataclass
class DuplicatePattern:
    """중복 패턴 정보"""
    pattern_type: str  # 'function', 'class', 'logic'
    similarity_score: float
    locations: List[str]
    suggested_action: str


@dataclass
class LayerStats:
    """계층별 통계"""
    layer_name: str
    file_count: int
    function_count: int
    class_count: int
    total_lines: int
    main_features: List[str]


class SuperCodeTracker:
    """
    🔍 개발 추적 및 기능 발견 도구

    주요 기능:
    1. 기존 기능 빠른 탐지
    2. DDD 계층별 분석
    3. 중복 기능 탐지
    4. 코드 위치 매핑
    5. 미사용 코드 정리
    """

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.upbit_path = self.project_root / "upbit_auto_trading"
        self.start_time = time.time()

        # DDD 계층 정의
        self.layer_mapping = {
            'domain': 'upbit_auto_trading/domain',
            'application': 'upbit_auto_trading/application',
            'infrastructure': 'upbit_auto_trading/infrastructure',
            'presentation': 'upbit_auto_trading/ui'
        }

        # 캐시
        self._file_cache = {}
        self._ast_cache = {}

    def feature_discovery(self, keyword: str) -> None:
        """🔍 기능 빠른 탐지"""
        print(f"🔍 === 기능 탐지: '{keyword}' ===\n")

        if not keyword or len(keyword) < 2:
            print("❌ 키워드는 2글자 이상이어야 합니다.")
            return

        # 다양한 패턴으로 검색
        search_patterns = [
            keyword.lower(),
            keyword.replace(' ', '_').lower(),
            keyword.replace(' ', '').lower(),
            keyword.upper(),
            keyword.title().replace(' ', '')
        ]

        findings = []
        processed_files = set()

        # Python 파일 검색
        for py_file in self.upbit_path.rglob("*.py"):
            if py_file in processed_files:
                continue
            processed_files.add(py_file)

            try:
                content = self._get_file_content(py_file)
                layer = self._get_file_layer(py_file)

                # 파일명에서 검색
                filename_matches = any(pattern in py_file.stem.lower() for pattern in search_patterns)

                # 내용에서 검색
                content_matches = []
                for line_num, line in enumerate(content.split('\n'), 1):
                    for pattern in search_patterns:
                        if pattern in line.lower():
                            content_matches.append((line_num, line.strip()))

                if filename_matches or content_matches:
                    # AST 분석으로 상세 정보 수집
                    functions, classes = self._analyze_ast(py_file)

                    feature = FeatureInfo(
                        name=py_file.stem,
                        file_path=str(py_file.relative_to(self.project_root)),
                        layer=layer,
                        function_count=len(functions),
                        class_count=len(classes),
                        line_count=len(content.split('\n')),
                        dependencies=self._get_file_dependencies(py_file),
                        description=self._extract_description(content)
                    )

                    findings.append((feature, filename_matches, content_matches))

            except Exception:
                continue

        # 결과 출력
        if not findings:
            print(f"❌ '{keyword}' 관련 기능을 찾을 수 없습니다.")
            print("💡 다른 키워드로 시도해보세요.")
            return

        print(f"🎯 '{keyword}' 관련 기능 {len(findings)}개 발견:")

        # 계층별 그룹화
        by_layer = defaultdict(list)
        for feature, filename_match, content_matches in findings:
            by_layer[feature.layer].append((feature, filename_match, content_matches))

        for layer, layer_findings in by_layer.items():
            print(f"\n📁 {layer.upper()} 계층 ({len(layer_findings)}개):")

            for feature, filename_match, content_matches in layer_findings:
                match_type = "📁" if filename_match else "📝"
                print(f"   {match_type} {feature.name}")
                print(f"      📂 {feature.file_path}")
                print(f"      📊 함수: {feature.function_count}개, 클래스: {feature.class_count}개, 라인: {feature.line_count}개")

                if feature.description:
                    print(f"      📝 {feature.description[:100]}...")

                if content_matches:
                    print(f"      🔍 매칭 라인: {len(content_matches)}개")
                    for line_num, line in content_matches[:3]:  # 상위 3개만 표시
                        print(f"         L{line_num}: {line[:60]}...")
                    if len(content_matches) > 3:
                        print(f"         ... 외 {len(content_matches) - 3}개")
                print()

        # 중복 가능성 검사
        similar_features = self._find_similar_features([f[0] for f in findings])
        if similar_features:
            print("⚠️ 유사한 기능이 이미 존재할 가능성:")
            for feature1, feature2, similarity in similar_features:
                print(f"   • {feature1.name} ↔ {feature2.name} (유사도: {similarity:.0f}%)")

    def layer_analysis(self) -> None:
        """📊 DDD 계층별 기능 분포 분석"""
        print("📊 === DDD 계층별 기능 분포 분석 ===\n")

        layer_stats = {}

        for layer_name, layer_path in self.layer_mapping.items():
            full_path = self.project_root / layer_path

            if not full_path.exists():
                continue

            print(f"🔍 {layer_name.upper()} 계층 분석 중...")

            py_files = list(full_path.rglob("*.py"))
            total_functions = 0
            total_classes = 0
            total_lines = 0
            main_features = []

            for py_file in py_files:
                try:
                    content = self._get_file_content(py_file)
                    functions, classes = self._analyze_ast(py_file)

                    total_functions += len(functions)
                    total_classes += len(classes)
                    total_lines += len(content.split('\n'))

                    # 주요 기능 식별 (파일명 기준)
                    feature_name = py_file.stem
                    if not feature_name.startswith('__') and len(functions) + len(classes) > 2:
                        main_features.append(feature_name)

                except Exception:
                    continue

            layer_stats[layer_name] = LayerStats(
                layer_name=layer_name,
                file_count=len(py_files),
                function_count=total_functions,
                class_count=total_classes,
                total_lines=total_lines,
                main_features=main_features[:10]  # 상위 10개
            )

            stats = layer_stats[layer_name]
            print(f"   📁 파일: {stats.file_count}개")
            print(f"   🔧 함수: {stats.function_count}개")
            print(f"   🏗️ 클래스: {stats.class_count}개")
            print(f"   📝 총 라인: {stats.total_lines:,}개")
            print(f"   🎯 주요 기능: {len(stats.main_features)}개")
            print()

        # 계층별 비교 분석
        total_files = sum(stats.file_count for stats in layer_stats.values())
        total_functions = sum(stats.function_count for stats in layer_stats.values())

        print("📈 === 계층별 비교 ===")
        for layer_name, stats in layer_stats.items():
            file_ratio = (stats.file_count / total_files * 100) if total_files > 0 else 0
            func_ratio = (stats.function_count / total_functions * 100) if total_functions > 0 else 0

            print(f"🏗️ {layer_name.upper()}:")
            print(f"   📁 파일 비율: {file_ratio:.1f}%")
            print(f"   🔧 함수 비율: {func_ratio:.1f}%")
            print(f"   📊 파일당 평균 함수: {stats.function_count / max(stats.file_count, 1):.1f}개")

            # 주요 기능 나열
            if stats.main_features:
                features_text = ", ".join(stats.main_features[:5])
                if len(stats.main_features) > 5:
                    features_text += f" 외 {len(stats.main_features) - 5}개"
                print(f"   🎯 주요 기능: {features_text}")
            print()

        # DDD 원칙 준수 평가
        self._evaluate_ddd_compliance(layer_stats)

    def duplicate_detection(self) -> None:
        """🔄 중복 기능 탐지"""
        print("🔄 === 중복 기능 탐지 ===\n")

        # 함수명 기반 중복 검사
        function_names = defaultdict(list)
        class_names = defaultdict(list)

        for py_file in self.upbit_path.rglob("*.py"):
            try:
                functions, classes = self._analyze_ast(py_file)

                for func_name in functions:
                    function_names[func_name].append(str(py_file.relative_to(self.project_root)))

                for class_name in classes:
                    class_names[class_name].append(str(py_file.relative_to(self.project_root)))

            except Exception:
                continue

        # 중복 함수 찾기
        duplicate_functions = {name: files for name, files in function_names.items() if len(files) > 1}
        duplicate_classes = {name: files for name, files in class_names.items() if len(files) > 1}

        print(f"🔧 중복 함수: {len(duplicate_functions)}개")
        for func_name, files in list(duplicate_functions.items())[:10]:  # 상위 10개
            print(f"   • {func_name}:")
            for file_path in files:
                layer = self._get_file_layer(self.project_root / file_path)
                print(f"     📁 {layer}: {file_path}")
            print()

        print(f"🏗️ 중복 클래스: {len(duplicate_classes)}개")
        for class_name, files in list(duplicate_classes.items())[:10]:  # 상위 10개
            print(f"   • {class_name}:")
            for file_path in files:
                layer = self._get_file_layer(self.project_root / file_path)
                print(f"     📁 {layer}: {file_path}")
            print()

        # 로직 유사성 검사 (간단 버전)
        print("🧠 로직 유사성 검사:")
        similar_patterns = self._detect_similar_logic()

        if similar_patterns:
            for pattern in similar_patterns[:5]:  # 상위 5개
                print(f"   🔍 {pattern.pattern_type}: {pattern.similarity_score:.0f}% 유사")
                for location in pattern.locations:
                    print(f"     📍 {location}")
                print(f"   💡 제안: {pattern.suggested_action}")
                print()
        else:
            print("   ✅ 유사한 로직 패턴이 발견되지 않았습니다.")

    def feature_map(self) -> None:
        """🗺️ 기능별 코드 위치 매핑"""
        print("🗺️ === 기능별 코드 위치 매핑 ===\n")

        feature_map = defaultdict(lambda: defaultdict(list))

        # 기능 카테고리 정의
        feature_categories = {
            'trading': ['trade', 'order', 'buy', 'sell', 'strategy'],
            'indicator': ['rsi', 'sma', 'ema', 'bollinger', 'macd'],
            'data': ['market', 'price', 'candle', 'volume'],
            'ui': ['window', 'widget', 'view', 'presenter'],
            'config': ['config', 'setting', 'parameter'],
            'database': ['db', 'sqlite', 'repository', 'dao'],
            'api': ['upbit', 'request', 'response', 'client'],
            'validation': ['validate', 'check', 'verify'],
            'logging': ['log', 'logger', 'debug'],
            'util': ['util', 'helper', 'tool', 'common']
        }

        # 파일 분류
        for py_file in self.upbit_path.rglob("*.py"):
            try:
                content = self._get_file_content(py_file)
                file_path = str(py_file.relative_to(self.project_root))
                layer = self._get_file_layer(py_file)

                # 키워드 기반 분류
                for category, keywords in feature_categories.items():
                    for keyword in keywords:
                        if (keyword in py_file.stem.lower() or
                            keyword in content.lower()):

                            functions, classes = self._analyze_ast(py_file)

                            feature_map[category][layer].append({
                                'file': file_path,
                                'functions': len(functions),
                                'classes': len(classes),
                                'lines': len(content.split('\n'))
                            })
                            break  # 첫 번째 매칭으로 분류

            except Exception:
                continue

        # 결과 출력
        for category, layers in feature_map.items():
            total_files = sum(len(files) for files in layers.values())
            if total_files == 0:
                continue

            print(f"🎯 {category.upper()} 기능 ({total_files}개 파일):")

            for layer, files in layers.items():
                if not files:
                    continue

                total_functions = sum(f['functions'] for f in files)
                total_classes = sum(f['classes'] for f in files)

                print(f"   📁 {layer}: {len(files)}개 파일")
                print(f"      🔧 함수: {total_functions}개, 클래스: {total_classes}개")

                # 주요 파일 나열
                top_files = sorted(files, key=lambda x: x['functions'] + x['classes'], reverse=True)[:3]
                for file_info in top_files:
                    print(f"      📄 {Path(file_info['file']).name}: {file_info['functions']}함수, {file_info['classes']}클래스")
            print()

    def quick_search(self, keyword: str) -> None:
        """⚡ 키워드 기반 빠른 검색"""
        print(f"⚡ === 빠른 검색: '{keyword}' ===\n")

        if not keyword or len(keyword) < 2:
            print("❌ 키워드는 2글자 이상이어야 합니다.")
            return

        matches = []
        search_time = time.time()

        # 파일명, 함수명, 클래스명에서 검색
        for py_file in self.upbit_path.rglob("*.py"):
            try:
                # 파일명 검색
                if keyword.lower() in py_file.stem.lower():
                    matches.append(('file', str(py_file.relative_to(self.project_root)), py_file.stem))

                # 함수/클래스명 검색
                functions, classes = self._analyze_ast(py_file)

                for func_name in functions:
                    if keyword.lower() in func_name.lower():
                        matches.append(('function', str(py_file.relative_to(self.project_root)), func_name))

                for class_name in classes:
                    if keyword.lower() in class_name.lower():
                        matches.append(('class', str(py_file.relative_to(self.project_root)), class_name))

            except Exception:
                continue

        search_elapsed = time.time() - search_time

        if not matches:
            print(f"❌ '{keyword}' 관련 항목을 찾을 수 없습니다.")
            return

        print(f"🎯 {len(matches)}개 항목 발견 (검색 시간: {search_elapsed:.2f}초):")

        # 타입별 그룹화
        by_type = defaultdict(list)
        for match_type, file_path, name in matches:
            by_type[match_type].append((file_path, name))

        for match_type, items in by_type.items():
            type_emoji = {'file': '📁', 'function': '🔧', 'class': '🏗️'}
            print(f"\n{type_emoji[match_type]} {match_type.upper()} ({len(items)}개):")

            for file_path, name in items[:10]:  # 상위 10개
                layer = self._get_file_layer(self.project_root / file_path)
                print(f"   • {name} ({layer})")
                print(f"     📂 {file_path}")

            if len(items) > 10:
                print(f"   ... 외 {len(items) - 10}개")

    def unused_cleanup(self) -> None:
        """🧹 미사용 코드 정리 제안"""
        print("🧹 === 미사용 코드 정리 제안 ===\n")

        # 모든 Python 파일의 import 관계 분석
        all_imports = set()
        all_modules = set()

        for py_file in self.upbit_path.rglob("*.py"):
            try:
                content = self._get_file_content(py_file)

                # 모듈명 추가
                relative_path = py_file.relative_to(self.upbit_path)
                module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
                all_modules.add(module_name)

                # import 문 추출
                imports = self._extract_imports(content)
                all_imports.update(imports)

            except Exception:
                continue

        # 미사용 모듈 찾기
        unused_modules = []
        for module in all_modules:
            if module not in all_imports and not module.endswith('__init__'):
                module_path = self.upbit_path / f"{module.replace('.', '/')}.py"
                if module_path.exists():
                    unused_modules.append(str(module_path.relative_to(self.project_root)))

        print(f"📁 미사용 가능성이 있는 모듈: {len(unused_modules)}개")
        for module_path in unused_modules[:15]:  # 상위 15개
            print(f"   📄 {module_path}")
        if len(unused_modules) > 15:
            print(f"   ... 외 {len(unused_modules) - 15}개")

        # 빈 파일 찾기
        empty_files = []
        for py_file in self.upbit_path.rglob("*.py"):
            try:
                content = self._get_file_content(py_file)
                lines = [line.strip() for line in content.split('\n') if line.strip()]

                # 주석과 import만 있는 파일
                non_trivial_lines = [line for line in lines if not (
                    line.startswith('#') or
                    line.startswith('"""') or
                    line.startswith("'''") or
                    line.startswith('import ') or
                    line.startswith('from ')
                )]

                if len(non_trivial_lines) <= 2:  # 거의 빈 파일
                    empty_files.append(str(py_file.relative_to(self.project_root)))

            except Exception:
                continue

        print(f"\n📄 거의 빈 파일: {len(empty_files)}개")
        for file_path in empty_files[:10]:  # 상위 10개
            print(f"   📄 {file_path}")
        if len(empty_files) > 10:
            print(f"   ... 외 {len(empty_files) - 10}개")

        # 정리 제안
        print(f"\n💡 === 정리 제안 ===")
        if unused_modules or empty_files:
            print("🗂️ 안전한 정리 단계:")
            print("1. 📁 미사용 모듈을 legacy 폴더로 이동")
            print("2. 📄 빈 파일들을 통합 또는 제거")
            print("3. 🧪 테스트 실행으로 검증")
            print("4. 🔄 import 관계 재검토")
        else:
            print("✅ 정리가 필요한 파일이 발견되지 않았습니다.")

    def _get_file_content(self, file_path: Path) -> str:
        """파일 내용 조회 (캐시 사용)"""
        if file_path not in self._file_cache:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._file_cache[file_path] = f.read()
            except Exception:
                self._file_cache[file_path] = ""

        return self._file_cache[file_path]

    def _get_file_layer(self, file_path: Path) -> str:
        """파일의 DDD 계층 판단"""
        try:
            relative_path = file_path.relative_to(self.project_root)
            path_str = str(relative_path)

            if 'domain' in path_str:
                return 'domain'
            elif 'application' in path_str:
                return 'application'
            elif 'infrastructure' in path_str:
                return 'infrastructure'
            elif 'ui' in path_str or 'presentation' in path_str:
                return 'presentation'
            else:
                return 'other'
        except Exception:
            return 'unknown'

    def _analyze_ast(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """AST 분석으로 함수/클래스명 추출 (캐시 사용)"""
        if file_path not in self._ast_cache:
            functions = []
            classes = []

            try:
                content = self._get_file_content(file_path)
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)

                self._ast_cache[file_path] = (functions, classes)
            except Exception:
                self._ast_cache[file_path] = ([], [])

        return self._ast_cache[file_path]

    def _get_file_dependencies(self, file_path: Path) -> List[str]:
        """파일의 의존성 추출"""
        try:
            content = self._get_file_content(file_path)
            return self._extract_imports(content)
        except Exception:
            return []

    def _extract_imports(self, content: str) -> List[str]:
        """import 문 추출"""
        imports = []

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except Exception:
            # 정규식 fallback
            import_patterns = [
                r'import\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
                r'from\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+import'
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                imports.extend(matches)

        return imports

    def _extract_description(self, content: str) -> str:
        """파일 설명 추출"""
        lines = content.split('\n')

        # docstring 찾기
        for i, line in enumerate(lines[:20]):  # 상위 20줄만 검사
            if '"""' in line or "'''" in line:
                # 다음 줄들에서 설명 찾기
                for j in range(i + 1, min(i + 10, len(lines))):
                    desc_line = lines[j].strip()
                    if desc_line and not desc_line.startswith('"""') and not desc_line.startswith("'''"):
                        return desc_line

        # 주석에서 찾기
        for line in lines[:10]:
            if line.strip().startswith('#') and len(line.strip()) > 5:
                return line.strip()[1:].strip()

        return ""

    def _find_similar_features(self, features: List[FeatureInfo]) -> List[Tuple[FeatureInfo, FeatureInfo, float]]:
        """유사한 기능 찾기"""
        similar_pairs = []

        for i, feature1 in enumerate(features):
            for feature2 in features[i+1:]:
                # 이름 유사도
                name_similarity = self._calculate_string_similarity(feature1.name, feature2.name)

                # 구조 유사도
                func_diff = abs(feature1.function_count - feature2.function_count)
                class_diff = abs(feature1.class_count - feature2.class_count)
                structure_similarity = 100 - min(100, (func_diff + class_diff) * 10)

                # 전체 유사도
                overall_similarity = (name_similarity + structure_similarity) / 2

                if overall_similarity > 70:  # 70% 이상 유사
                    similar_pairs.append((feature1, feature2, overall_similarity))

        return sorted(similar_pairs, key=lambda x: x[2], reverse=True)

    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """문자열 유사도 계산 (간단한 버전)"""
        if not str1 or not str2:
            return 0

        # 공통 부분 문자열 비율
        common_chars = set(str1.lower()) & set(str2.lower())
        total_chars = set(str1.lower()) | set(str2.lower())

        if not total_chars:
            return 0

        return (len(common_chars) / len(total_chars)) * 100

    def _detect_similar_logic(self) -> List[DuplicatePattern]:
        """유사한 로직 패턴 탐지 (간단한 버전)"""
        patterns = []

        # 함수 길이 기반 유사성 검사
        function_lengths = defaultdict(list)

        for py_file in self.upbit_path.rglob("*.py"):
            try:
                content = self._get_file_content(py_file)
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 함수 길이 계산
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 10
                        function_lengths[func_lines].append(f"{py_file.stem}.{node.name}")

            except Exception:
                continue

        # 동일한 길이의 함수들 중 의심스러운 것들
        for length, functions in function_lengths.items():
            if length > 10 and len(functions) > 1:  # 10줄 이상, 2개 이상
                patterns.append(DuplicatePattern(
                    pattern_type=f"{length}줄 함수 패턴",
                    similarity_score=80.0,
                    locations=functions,
                    suggested_action="함수 내용을 비교하여 공통 로직 추출 검토"
                ))

        return patterns

    def _evaluate_ddd_compliance(self, layer_stats: Dict[str, LayerStats]) -> None:
        """DDD 원칙 준수 평가"""
        print("🏗️ === DDD 원칙 준수 평가 ===")

        total_files = sum(stats.file_count for stats in layer_stats.values())

        # 계층별 균형 검사
        domain_ratio = layer_stats.get('domain', LayerStats('domain', 0, 0, 0, 0, [])).file_count / max(total_files, 1) * 100
        infra_ratio = layer_stats.get('infrastructure', LayerStats('infrastructure', 0, 0, 0, 0, [])).file_count / max(total_files, 1) * 100

        print(f"📊 Domain 계층 비율: {domain_ratio:.1f}%", end="")
        if domain_ratio < 20:
            print(" ⚠️ 너무 적음 (20% 이상 권장)")
        elif domain_ratio > 50:
            print(" ⚠️ 너무 많음 (50% 이하 권장)")
        else:
            print(" ✅ 적절함")

        print(f"📊 Infrastructure 계층 비율: {infra_ratio:.1f}%", end="")
        if infra_ratio > 40:
            print(" ⚠️ 너무 많음 (40% 이하 권장)")
        else:
            print(" ✅ 적절함")

        # 전체 점수 계산
        balance_score = 100 - abs(domain_ratio - 30) - abs(infra_ratio - 25)  # 이상적: Domain 30%, Infra 25%
        complexity_score = min(100, 100 - (total_files / 10))  # 파일 수가 적을수록 좋음

        overall_score = (balance_score + complexity_score) / 2

        print(f"🎯 DDD 준수 점수: {overall_score:.1f}/100")
        if overall_score >= 80:
            print("   ✅ 훌륭한 아키텍처")
        elif overall_score >= 60:
            print("   🟡 개선 여지 있음")
        else:
            print("   🔴 구조 개선 필요")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Super Code Tracker - 개발 추적 및 기능 발견 도구')
    parser.add_argument('--feature-discovery', type=str, help='기능 빠른 탐지 (키워드)')
    parser.add_argument('--layer-analysis', action='store_true', help='DDD 계층별 기능 분포')
    parser.add_argument('--duplicate-detection', action='store_true', help='중복 기능 탐지')
    parser.add_argument('--feature-map', action='store_true', help='기능별 코드 위치 매핑')
    parser.add_argument('--quick-search', type=str, help='키워드 기반 빠른 검색')
    parser.add_argument('--unused-cleanup', action='store_true', help='미사용 코드 정리 제안')

    args = parser.parse_args()

    tracker = SuperCodeTracker()

    # 아무 옵션이 없으면 layer-analysis 실행
    if not any(vars(args).values()):
        tracker.layer_analysis()
        return

    if args.feature_discovery:
        tracker.feature_discovery(args.feature_discovery)

    if args.layer_analysis:
        tracker.layer_analysis()

    if args.duplicate_detection:
        tracker.duplicate_detection()

    if args.feature_map:
        tracker.feature_map()

    if args.quick_search:
        tracker.quick_search(args.quick_search)

    if args.unused_cleanup:
        tracker.unused_cleanup()


if __name__ == "__main__":
    main()

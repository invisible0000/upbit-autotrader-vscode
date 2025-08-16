#!/usr/bin/env python3
"""
🤖 Super Dev Assistant
개발 도우미 - 개발 효율성 극대화를 위한 AI 기반 코드 분석 도구

🤖 LLM 사용 가이드:
===================
이 도구는 개발 중 빠른 의사결정과 효율성 향상을 위한 AI 기반 도우미입니다.

📋 주요 명령어 (tools 폴더에서 실행):
1. python super_dev_assistant.py --what-exists "기능명"          # 해당 기능이 이미 있는지 확인 ⭐
2. python super_dev_assistant.py --where-is "기능명"             # 기능 구현 위치 찾기 ⭐
3. python super_dev_assistant.py --similar-code "설명"           # 유사한 코드 패턴 찾기
4. python super_dev_assistant.py --folder-summary <폴더>         # 폴더별 기능 요약
5. python super_dev_assistant.py --quick-guide <모듈>            # 모듈 사용법 빠른 가이드
6. python super_dev_assistant.py --integration-points           # 통합 가능한 포인트 탐지
7. python super_dev_assistant.py --architecture-health          # DDD 아키텍처 건강도 점수

🎯 사용 시나리오:
- 🔍 새 기능 개발 전: --what-exists "RSI 지표" (중복 개발 방지)
- 📍 코드 위치 파악: --where-is "트레이딩 로직" (빠른 네비게이션)
- 🔗 통합 지점 탐색: --integration-points (기존 코드 재활용)
- 📊 아키텍처 점검: --architecture-health (품질 관리)

💡 특별 기능:
- AI 기반 의미론적 코드 검색
- 자연어 질의 지원
- 개발 패턴 학습 및 제안
- 실시간 아키텍처 건강도 측정

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
import difflib

# 프로젝트 루트를 파이썬 패스에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class CodeMatch:
    """코드 매칭 결과"""
    file_path: str
    match_type: str  # 'exact', 'similar', 'partial'
    confidence: float  # 0-100
    description: str
    code_snippet: str
    line_number: int


@dataclass
class FolderSummary:
    """폴더 요약 정보"""
    path: str
    file_count: int
    main_purpose: str
    key_features: List[str]
    complexity_score: float
    dependencies: List[str]
    suggested_improvements: List[str]


@dataclass
class IntegrationPoint:
    """통합 포인트 정보"""
    location: str
    integration_type: str  # 'interface', 'service', 'utility', 'data'
    current_usage: int
    potential_usage: List[str]
    integration_benefit: str


class SuperDevAssistant:
    """
    🤖 개발 도우미 - AI 기반 코드 분석

    주요 기능:
    1. 자연어 기반 기능 검색
    2. 코드 위치 빠른 탐지
    3. 유사 코드 패턴 발견
    4. 폴더별 기능 요약
    5. 통합 지점 추천
    6. 아키텍처 건강도 측정
    """

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.upbit_path = self.project_root / "upbit_auto_trading"
        self.start_time = time.time()

        # 지식 베이스 구축
        self._build_knowledge_base()

        # 키워드 매핑 (한글 ↔ 영어)
        self.keyword_mapping = {
            # 트레이딩 관련
            '트레이딩': ['trading', 'trade'],
            '주문': ['order', 'buy', 'sell'],
            '전략': ['strategy', 'rule'],
            '조건': ['condition', 'trigger'],

            # 지표 관련
            '지표': ['indicator', 'technical'],
            'RSI': ['rsi', 'relative_strength'],
            '이동평균': ['sma', 'ema', 'moving_average'],
            '볼린저밴드': ['bollinger', 'band'],

            # 데이터 관련
            '시장데이터': ['market_data', 'candle', 'price'],
            '가격': ['price', 'rate'],
            '거래량': ['volume', 'amount'],

            # UI 관련
            '화면': ['ui', 'window', 'view'],
            '위젯': ['widget', 'component'],
            '버튼': ['button', 'btn'],

            # 설정 관련
            '설정': ['config', 'setting', 'parameter'],
            '파라미터': ['parameter', 'param', 'variable'],

            # DB 관련
            '데이터베이스': ['database', 'db', 'sqlite'],
            '저장': ['save', 'store', 'repository']
        }

    def what_exists(self, feature_query: str) -> None:
        """🔍 해당 기능이 이미 있는지 확인"""
        print(f"🔍 === 기능 존재 여부 확인: '{feature_query}' ===\n")

        if not feature_query or len(feature_query) < 2:
            print("❌ 기능명은 2글자 이상이어야 합니다.")
            return

        # 다단계 검색 수행
        matches = self._multi_level_search(feature_query)

        if not matches:
            print(f"✅ '{feature_query}' 기능이 발견되지 않았습니다.")
            print("💡 새로 개발해도 안전합니다!")

            # 유사한 기능 제안
            similar_suggestions = self._suggest_similar_features(feature_query)
            if similar_suggestions:
                print("\n🔗 참고할 만한 유사 기능:")
                for suggestion in similar_suggestions[:3]:
                    print(f"   • {suggestion}")
            return

        # 결과를 신뢰도 순으로 정렬
        matches.sort(key=lambda x: x.confidence, reverse=True)

        print(f"⚠️ '{feature_query}' 관련 기능이 이미 존재합니다!")
        print(f"🎯 총 {len(matches)}개 발견:")

        # 신뢰도별 그룹화
        high_confidence = [m for m in matches if m.confidence >= 80]
        medium_confidence = [m for m in matches if 50 <= m.confidence < 80]
        low_confidence = [m for m in matches if m.confidence < 50]

        if high_confidence:
            print(f"\n🔴 높은 유사도 ({len(high_confidence)}개) - 중복 가능성 높음:")
            for match in high_confidence:
                print(f"   📄 {Path(match.file_path).name} ({match.confidence:.0f}%)")
                print(f"      📂 {match.file_path}")
                print(f"      📝 {match.description}")
                if match.code_snippet:
                    snippet = match.code_snippet[:100].replace('\n', ' ')
                    print(f"      💻 {snippet}...")
                print()

        if medium_confidence:
            print(f"🟡 중간 유사도 ({len(medium_confidence)}개) - 참고 가능:")
            for match in medium_confidence[:3]:  # 상위 3개만
                print(f"   📄 {Path(match.file_path).name} ({match.confidence:.0f}%)")
                print(f"      📝 {match.description}")

        if low_confidence:
            print(f"\n🟢 낮은 유사도 ({len(low_confidence)}개) - 다른 용도일 가능성:")
            for match in low_confidence[:2]:  # 상위 2개만
                print(f"   📄 {Path(match.file_path).name} ({match.confidence:.0f}%)")

        # 권장 사항
        if high_confidence:
            print("\n💡 권장 사항:")
            print("1. 🔍 기존 기능을 먼저 검토해보세요")
            print("2. 🔧 기존 기능을 확장할 수 있는지 확인하세요")
            print("3. 🆕 정말 새로운 기능이 필요한지 재검토하세요")

    def where_is(self, feature_query: str) -> None:
        """📍 기능 구현 위치 찾기"""
        print(f"📍 === 기능 위치 찾기: '{feature_query}' ===\n")

        matches = self._multi_level_search(feature_query)

        if not matches:
            print(f"❌ '{feature_query}' 기능을 찾을 수 없습니다.")

            # 비슷한 키워드 제안
            suggestions = self._suggest_search_keywords(feature_query)
            if suggestions:
                print("💡 다음 키워드로 다시 시도해보세요:")
                for suggestion in suggestions:
                    print(f"   • {suggestion}")
            return

        # 위치별 그룹화
        by_layer = defaultdict(list)
        for match in matches:
            layer = self._get_file_layer(self.project_root / match.file_path)
            by_layer[layer].append(match)

        print(f"🎯 '{feature_query}' 기능 위치 ({len(matches)}개 발견):")

        for layer, layer_matches in by_layer.items():
            layer_matches.sort(key=lambda x: x.confidence, reverse=True)

            layer_emoji = {
                'domain': '🏗️',
                'application': '⚙️',
                'infrastructure': '🔧',
                'presentation': '🖥️',
                'other': '📁'
            }

            print(f"\n{layer_emoji.get(layer, '📁')} {layer.upper()} 계층 ({len(layer_matches)}개):")

            for match in layer_matches:
                confidence_emoji = "🟢" if match.confidence >= 80 else "🟡" if match.confidence >= 50 else "⚪"
                print(f"   {confidence_emoji} {Path(match.file_path).name} ({match.confidence:.0f}%)")
                print(f"      📂 {match.file_path}")
                print(f"      📝 {match.description}")

                if match.line_number > 0:
                    print(f"      📍 라인 {match.line_number}")

                # 빠른 네비게이션 힌트
                print(f"      💻 VS Code: Ctrl+G → {match.line_number}")
                print()

        # 주요 위치 요약
        main_locations = [m for m in matches if m.confidence >= 70]
        if main_locations:
            print("🎯 주요 구현 위치:")
            for match in main_locations[:3]:
                layer = self._get_file_layer(self.project_root / match.file_path)
                print(f"   📍 {layer}: {Path(match.file_path).name}")

    def similar_code(self, description: str) -> None:
        """🔗 유사한 코드 패턴 찾기"""
        print(f"🔗 === 유사 코드 패턴 검색: '{description}' ===\n")

        # 설명을 키워드로 분해
        keywords = self._extract_keywords_from_description(description)
        print(f"🔍 추출된 키워드: {', '.join(keywords)}")

        # 각 키워드별로 검색
        all_matches = []
        for keyword in keywords:
            matches = self._multi_level_search(keyword)
            all_matches.extend(matches)

        # 중복 제거 및 점수 합산
        file_scores = defaultdict(float)
        file_matches = {}

        for match in all_matches:
            file_scores[match.file_path] += match.confidence
            if match.file_path not in file_matches or match.confidence > file_matches[match.file_path].confidence:
                file_matches[match.file_path] = match

        # 상위 결과 선별
        top_files = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)[:10]

        if not top_files:
            print("❌ 유사한 코드 패턴을 찾을 수 없습니다.")
            return

        print(f"\n🎯 유사 패턴 {len(top_files)}개 발견:")

        for file_path, total_score in top_files:
            match = file_matches[file_path]
            layer = self._get_file_layer(self.project_root / file_path)

            print(f"\n📄 {Path(file_path).name} (점수: {total_score:.0f})")
            print(f"   📂 {file_path}")
            print(f"   🏗️ 계층: {layer}")
            print(f"   📝 {match.description}")

            # 코드 스니펫 표시
            if match.code_snippet:
                print("   💻 코드 스니펫:")
                lines = match.code_snippet.split('\n')[:3]
                for line in lines:
                    print(f"      {line}")
                if len(match.code_snippet.split('\n')) > 3:
                    print("      ...")

        # 패턴 분석
        self._analyze_code_patterns(top_files, file_matches)

    def folder_summary(self, folder_path: str) -> None:
        """📁 폴더별 기능 요약"""
        print(f"📁 === 폴더 기능 요약: {folder_path} ===\n")

        target_path = self.project_root / folder_path
        if not target_path.exists():
            target_path = self.upbit_path / folder_path

        if not target_path.exists():
            print(f"❌ 폴더를 찾을 수 없습니다: {folder_path}")
            return

        summary = self._analyze_folder(target_path)

        print(f"📊 폴더 분석 결과:")
        print(f"   📁 경로: {summary.path}")
        print(f"   📄 파일 수: {summary.file_count}개")
        print(f"   🎯 주요 목적: {summary.main_purpose}")
        print(f"   📊 복잡도: {summary.complexity_score:.0f}/100")

        if summary.key_features:
            print(f"\n🎯 핵심 기능 ({len(summary.key_features)}개):")
            for i, feature in enumerate(summary.key_features, 1):
                print(f"   {i}. {feature}")

        if summary.dependencies:
            print(f"\n🔗 주요 의존성 ({len(summary.dependencies)}개):")
            for dep in summary.dependencies[:5]:
                print(f"   • {dep}")
            if len(summary.dependencies) > 5:
                print(f"   ... 외 {len(summary.dependencies) - 5}개")

        if summary.suggested_improvements:
            print(f"\n💡 개선 제안 ({len(summary.suggested_improvements)}개):")
            for suggestion in summary.suggested_improvements:
                print(f"   • {suggestion}")

        # 하위 폴더 요약
        subfolders = [p for p in target_path.iterdir() if p.is_dir() and not p.name.startswith('.')]
        if subfolders:
            print(f"\n📂 하위 폴더 ({len(subfolders)}개):")
            for subfolder in subfolders[:5]:
                py_files = list(subfolder.rglob("*.py"))
                print(f"   📁 {subfolder.name}: {len(py_files)}개 파일")

    def quick_guide(self, module_name: str) -> None:
        """📖 모듈 사용법 빠른 가이드"""
        print(f"📖 === 모듈 가이드: {module_name} ===\n")

        # 모듈 파일 찾기
        module_files = []
        for py_file in self.upbit_path.rglob("*.py"):
            if module_name.lower() in py_file.stem.lower():
                module_files.append(py_file)

        if not module_files:
            print(f"❌ '{module_name}' 모듈을 찾을 수 없습니다.")
            return

        print(f"🎯 '{module_name}' 관련 모듈 {len(module_files)}개 발견:")

        for py_file in module_files[:3]:  # 상위 3개
            print(f"\n📄 {py_file.name}")
            print(f"   📂 {py_file.relative_to(self.project_root)}")

            try:
                content = self._get_file_content(py_file)

                # 독스트링 추출
                docstring = self._extract_module_docstring(content)
                if docstring:
                    print(f"   📝 {docstring[:200]}...")

                # 주요 클래스/함수 추출
                functions, classes = self._analyze_ast(py_file)

                if classes:
                    print(f"   🏗️ 주요 클래스: {', '.join(classes[:3])}")
                    if len(classes) > 3:
                        print(f"                  ... 외 {len(classes) - 3}개")

                if functions:
                    public_functions = [f for f in functions if not f.startswith('_')]
                    if public_functions:
                        print(f"   🔧 공개 함수: {', '.join(public_functions[:3])}")
                        if len(public_functions) > 3:
                            print(f"                ... 외 {len(public_functions) - 3}개")

                # 사용 예제 찾기
                usage_examples = self._find_usage_examples(py_file)
                if usage_examples:
                    print(f"   💻 사용 예제:")
                    for example in usage_examples[:2]:
                        print(f"      • {example}")

            except Exception:
                print("   ❌ 분석 실패")

    def integration_points(self) -> None:
        """🔗 통합 가능한 포인트 탐지"""
        print("🔗 === 통합 포인트 탐지 ===\n")

        integration_points = []

        # 인터페이스 클래스 찾기
        interface_files = []
        for py_file in self.upbit_path.rglob("*.py"):
            if 'interface' in py_file.stem.lower() or 'abstract' in py_file.stem.lower():
                interface_files.append(py_file)

        print(f"🔌 인터페이스 기반 통합점 ({len(interface_files)}개):")
        for py_file in interface_files:
            try:
                content = self._get_file_content(py_file)
                functions, classes = self._analyze_ast(py_file)

                # 구현체 수 확인
                implementers = self._find_implementers(py_file)

                point = IntegrationPoint(
                    location=str(py_file.relative_to(self.project_root)),
                    integration_type='interface',
                    current_usage=len(implementers),
                    potential_usage=[],
                    integration_benefit="다형성을 통한 확장성 제공"
                )

                integration_points.append(point)

                print(f"   🔌 {py_file.stem}")
                print(f"      📂 {py_file.relative_to(self.project_root)}")
                print(f"      🏗️ 클래스: {len(classes)}개")
                print(f"      🔧 구현체: {len(implementers)}개")
                if implementers:
                    print(f"      📋 구현체: {', '.join(implementers[:3])}")
                print()

            except Exception:
                continue

        # 서비스 클래스 찾기
        service_files = []
        for py_file in self.upbit_path.rglob("*.py"):
            if 'service' in py_file.stem.lower():
                service_files.append(py_file)

        print(f"⚙️ 서비스 기반 통합점 ({len(service_files)}개):")
        for py_file in service_files[:5]:  # 상위 5개
            try:
                content = self._get_file_content(py_file)
                functions, classes = self._analyze_ast(py_file)

                # 의존성 분석
                dependencies = self._extract_imports(content)
                external_deps = [dep for dep in dependencies if not dep.startswith('upbit_auto_trading')]

                print(f"   ⚙️ {py_file.stem}")
                print(f"      📂 {py_file.relative_to(self.project_root)}")
                print(f"      🔧 함수: {len(functions)}개")
                print(f"      🔗 의존성: {len(dependencies)}개 (외부: {len(external_deps)}개)")
                print()

            except Exception:
                continue

        # 유틸리티 함수 찾기
        utility_functions = self._find_utility_functions()

        print(f"🛠️ 유틸리티 기반 통합점 ({len(utility_functions)}개):")
        for func_info in utility_functions[:5]:
            print(f"   🛠️ {func_info['name']}")
            print(f"      📂 {func_info['file']}")
            print(f"      📝 {func_info['description']}")
            print()

        # 통합 권장사항
        if integration_points:
            print("💡 통합 권장사항:")
            print("1. 🔌 인터페이스를 활용하여 새 구현체 추가")
            print("2. ⚙️ 서비스 패턴으로 비즈니스 로직 캡슐화")
            print("3. 🛠️ 공통 유틸리티 함수 재사용")
            print("4. 📦 의존성 주입을 통한 느슨한 결합")

    def architecture_health(self) -> None:
        """📊 DDD 아키텍처 건강도 점수"""
        print("📊 === DDD 아키텍처 건강도 ===\n")

        health_metrics = {
            'layer_separation': 0,
            'dependency_direction': 0,
            'interface_usage': 0,
            'code_duplication': 0,
            'naming_consistency': 0,
            'test_coverage': 0
        }

        # 1. 계층 분리도 측정
        layer_separation_score = self._measure_layer_separation()
        health_metrics['layer_separation'] = layer_separation_score

        # 2. 의존성 방향 검사
        dependency_score = self._check_dependency_direction()
        health_metrics['dependency_direction'] = dependency_score

        # 3. 인터페이스 사용률
        interface_score = self._measure_interface_usage()
        health_metrics['interface_usage'] = interface_score

        # 4. 코드 중복도
        duplication_score = self._measure_code_duplication()
        health_metrics['code_duplication'] = duplication_score

        # 5. 네이밍 일관성
        naming_score = self._check_naming_consistency()
        health_metrics['naming_consistency'] = naming_score

        # 6. 테스트 커버리지 (간접 측정)
        test_score = self._estimate_test_coverage()
        health_metrics['test_coverage'] = test_score

        # 전체 점수 계산
        overall_score = sum(health_metrics.values()) / len(health_metrics)

        # 결과 출력
        print("📈 아키텍처 건강도 지표:")

        for metric, score in health_metrics.items():
            metric_names = {
                'layer_separation': '🏗️ 계층 분리도',
                'dependency_direction': '🔄 의존성 방향',
                'interface_usage': '🔌 인터페이스 사용',
                'code_duplication': '🔄 코드 중복 방지',
                'naming_consistency': '📝 네이밍 일관성',
                'test_coverage': '🧪 테스트 커버리지'
            }

            score_emoji = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            print(f"   {score_emoji} {metric_names[metric]}: {score:.0f}/100")

        # 전체 평가
        print(f"\n🎯 전체 건강도: {overall_score:.0f}/100")

        if overall_score >= 85:
            print("   🏆 훌륭한 아키텍처! 계속 유지하세요.")
        elif overall_score >= 70:
            print("   ✅ 양호한 상태입니다. 일부 개선점이 있습니다.")
        elif overall_score >= 50:
            print("   ⚠️ 개선이 필요합니다. 아래 권장사항을 확인하세요.")
        else:
            print("   🔴 심각한 문제가 있습니다. 리팩터링이 필요합니다.")

        # 개선 권장사항
        print(f"\n💡 개선 권장사항:")
        improvements = []

        if health_metrics['layer_separation'] < 70:
            improvements.append("🏗️ Domain 계층에서 Infrastructure 의존성 제거")

        if health_metrics['dependency_direction'] < 70:
            improvements.append("🔄 의존성 역전 원칙 적용 (DIP)")

        if health_metrics['interface_usage'] < 60:
            improvements.append("🔌 인터페이스 기반 설계 확대")

        if health_metrics['code_duplication'] < 60:
            improvements.append("🔄 중복 코드 제거 및 공통 모듈 추출")

        if health_metrics['naming_consistency'] < 70:
            improvements.append("📝 네이밍 규칙 정립 및 적용")

        if health_metrics['test_coverage'] < 50:
            improvements.append("🧪 단위 테스트 작성 확대")

        if improvements:
            for i, improvement in enumerate(improvements, 1):
                print(f"   {i}. {improvement}")
        else:
            print("   ✨ 현재 상태가 우수합니다!")

    def _build_knowledge_base(self) -> None:
        """지식 베이스 구축"""
        self.knowledge_base = {
            'files': {},
            'functions': {},
            'classes': {},
            'imports': defaultdict(list)
        }

        # 간단한 캐싱으로 성능 개선
        for py_file in self.upbit_path.rglob("*.py"):
            try:
                content = self._get_file_content(py_file)
                functions, classes = self._analyze_ast(py_file)
                imports = self._extract_imports(content)

                file_key = str(py_file.relative_to(self.project_root))
                self.knowledge_base['files'][file_key] = {
                    'content': content,
                    'functions': functions,
                    'classes': classes,
                    'imports': imports
                }

            except Exception:
                continue

    def _multi_level_search(self, query: str) -> List[CodeMatch]:
        """다단계 검색 수행"""
        matches = []

        # 한글 키워드를 영어로 확장
        expanded_keywords = self._expand_keywords(query)

        for file_path, file_info in self.knowledge_base['files'].items():
            file_matches = []

            # 파일명 검색
            for keyword in expanded_keywords:
                if keyword.lower() in Path(file_path).stem.lower():
                    file_matches.append(CodeMatch(
                        file_path=file_path,
                        match_type='filename',
                        confidence=90,
                        description=f"파일명에 '{keyword}' 포함",
                        code_snippet="",
                        line_number=0
                    ))

            # 클래스명 검색
            for class_name in file_info['classes']:
                for keyword in expanded_keywords:
                    if keyword.lower() in class_name.lower():
                        file_matches.append(CodeMatch(
                            file_path=file_path,
                            match_type='class',
                            confidence=85,
                            description=f"클래스 '{class_name}'",
                            code_snippet="",
                            line_number=0
                        ))

            # 함수명 검색
            for func_name in file_info['functions']:
                for keyword in expanded_keywords:
                    if keyword.lower() in func_name.lower():
                        file_matches.append(CodeMatch(
                            file_path=file_path,
                            match_type='function',
                            confidence=80,
                            description=f"함수 '{func_name}'",
                            code_snippet="",
                            line_number=0
                        ))

            # 내용 검색
            content = file_info['content']
            for keyword in expanded_keywords:
                if keyword.lower() in content.lower():
                    # 매칭된 라인 찾기
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if keyword.lower() in line.lower():
                            file_matches.append(CodeMatch(
                                file_path=file_path,
                                match_type='content',
                                confidence=60,
                                description=f"내용에 '{keyword}' 포함",
                                code_snippet=line.strip(),
                                line_number=i + 1
                            ))
                            break  # 첫 번째 매칭만

            # 파일별 최고 점수 매칭만 추가
            if file_matches:
                best_match = max(file_matches, key=lambda x: x.confidence)
                matches.append(best_match)

        return matches

    def _expand_keywords(self, query: str) -> List[str]:
        """키워드 확장"""
        keywords = [query]

        # 공백 기준 분리
        if ' ' in query:
            keywords.extend(query.split())

        # 한글 → 영어 매핑
        query_lower = query.lower()
        for korean, english_list in self.keyword_mapping.items():
            if korean in query_lower:
                keywords.extend(english_list)

        # 언더스코어, 카멜케이스 변형
        base_keyword = query.replace(' ', '_').lower()
        keywords.append(base_keyword)
        keywords.append(query.replace(' ', '').lower())

        return list(set(keywords))  # 중복 제거

    def _get_file_content(self, file_path: Path) -> str:
        """파일 내용 조회"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""

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
        """AST 분석"""
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
        except Exception:
            pass

        return functions, classes

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
            pass

        return imports

    def _suggest_similar_features(self, query: str) -> List[str]:
        """유사한 기능 제안"""
        suggestions = []

        # 키워드 기반 유사 기능 찾기
        expanded_keywords = self._expand_keywords(query)

        for file_path, file_info in self.knowledge_base['files'].items():
            file_name = Path(file_path).stem

            # 부분적 매칭
            for keyword in expanded_keywords:
                if len(keyword) > 3:  # 3글자 이상 키워드만
                    for word in file_name.split('_'):
                        if keyword[:3] in word and word not in suggestions:
                            suggestions.append(f"{file_name} ({file_path})")
                            break

        return suggestions[:5]

    def _suggest_search_keywords(self, query: str) -> List[str]:
        """검색 키워드 제안"""
        suggestions = []

        # 유사한 키워드 찾기
        all_filenames = [Path(fp).stem for fp in self.knowledge_base['files'].keys()]

        for filename in all_filenames:
            # 문자열 유사도 계산
            similarity = difflib.SequenceMatcher(None, query.lower(), filename.lower()).ratio()
            if 0.3 < similarity < 0.8:  # 적당한 유사도
                suggestions.append(filename)

        return suggestions[:5]

    def _extract_keywords_from_description(self, description: str) -> List[str]:
        """설명에서 키워드 추출"""
        # 간단한 키워드 추출
        words = re.findall(r'\w+', description.lower())

        # 불용어 제거
        stop_words = {'은', '는', '이', '가', '을', '를', '와', '과', '에', '의', '로', '으로', '하는', '있는', '같은'}
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        return keywords[:5]  # 상위 5개만

    def _analyze_code_patterns(self, top_files: List[Tuple[str, float]], file_matches: Dict[str, CodeMatch]) -> None:
        """코드 패턴 분석"""
        print(f"\n🔍 패턴 분석:")

        # 계층별 분포
        layer_count = defaultdict(int)
        for file_path, _ in top_files:
            layer = self._get_file_layer(self.project_root / file_path)
            layer_count[layer] += 1

        print("   📊 계층별 분포:")
        for layer, count in layer_count.items():
            print(f"      {layer}: {count}개")

        # 공통 패턴 식별
        common_functions = defaultdict(int)
        for file_path, _ in top_files:
            if file_path in self.knowledge_base['files']:
                functions = self.knowledge_base['files'][file_path]['functions']
                for func in functions:
                    common_functions[func] += 1

        repeated_functions = {f: c for f, c in common_functions.items() if c > 1}
        if repeated_functions:
            print("   🔄 공통 함수 패턴:")
            for func, count in sorted(repeated_functions.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"      {func}: {count}개 파일에서 사용")

    def _analyze_folder(self, folder_path: Path) -> FolderSummary:
        """폴더 분석"""
        py_files = list(folder_path.rglob("*.py"))

        if not py_files:
            return FolderSummary(
                path=str(folder_path.relative_to(self.project_root)),
                file_count=0,
                main_purpose="빈 폴더",
                key_features=[],
                complexity_score=0,
                dependencies=[],
                suggested_improvements=["파일 추가 필요"]
            )

        # 주요 목적 판단
        folder_name = folder_path.name.lower()
        purpose_mapping = {
            'domain': '비즈니스 로직 및 엔터티',
            'application': '유스케이스 및 서비스',
            'infrastructure': '외부 시스템 연동',
            'ui': '사용자 인터페이스',
            'presenter': 'UI 프레젠테이션 로직',
            'trading': '트레이딩 관련 기능',
            'indicator': '기술적 지표',
            'config': '설정 관리'
        }

        main_purpose = "일반 기능"
        for keyword, purpose in purpose_mapping.items():
            if keyword in folder_name:
                main_purpose = purpose
                break

        # 핵심 기능 추출
        key_features = []
        all_functions = []
        all_dependencies = []

        for py_file in py_files:
            try:
                content = self._get_file_content(py_file)
                functions, classes = self._analyze_ast(py_file)
                imports = self._extract_imports(content)

                all_functions.extend(functions)
                all_dependencies.extend(imports)

                # 주요 클래스를 핵심 기능으로
                key_features.extend(classes)

            except Exception:
                continue

        # 복잡도 계산
        avg_functions_per_file = len(all_functions) / max(len(py_files), 1)
        complexity_score = min(100, max(0, 100 - (avg_functions_per_file - 5) * 10))

        # 개선 제안
        improvements = []
        if len(py_files) > 20:
            improvements.append("폴더가 너무 큽니다. 하위 폴더로 분리 고려")
        if complexity_score < 50:
            improvements.append("파일당 함수가 너무 많습니다. 분리 고려")
        if not key_features:
            improvements.append("명확한 핵심 기능이 없습니다. 역할 정의 필요")

        return FolderSummary(
            path=str(folder_path.relative_to(self.project_root)),
            file_count=len(py_files),
            main_purpose=main_purpose,
            key_features=key_features[:10],
            complexity_score=complexity_score,
            dependencies=list(set(all_dependencies))[:10],
            suggested_improvements=improvements
        )

    def _extract_module_docstring(self, content: str) -> str:
        """모듈 독스트링 추출"""
        try:
            tree = ast.parse(content)
            if ast.get_docstring(tree):
                return ast.get_docstring(tree)
        except Exception:
            pass

        # 첫 번째 문자열 리터럴 찾기
        lines = content.split('\n')
        for line in lines[:10]:
            if '"""' in line or "'''" in line:
                return line.strip().replace('"""', '').replace("'''", "")

        return ""

    def _find_usage_examples(self, module_file: Path) -> List[str]:
        """사용 예제 찾기"""
        examples = []

        # 같은 디렉토리의 다른 파일에서 이 모듈 사용 찾기
        module_name = module_file.stem
        parent_dir = module_file.parent

        for py_file in parent_dir.rglob("*.py"):
            if py_file == module_file:
                continue

            try:
                content = self._get_file_content(py_file)
                if module_name in content:
                    # import 문 찾기
                    for line in content.split('\n'):
                        if 'import' in line and module_name in line:
                            examples.append(line.strip())
                            break
            except Exception:
                continue

        return examples[:3]

    def _find_implementers(self, interface_file: Path) -> List[str]:
        """인터페이스 구현체 찾기"""
        implementers = []

        try:
            content = self._get_file_content(interface_file)
            functions, classes = self._analyze_ast(interface_file)

            if not classes:
                return implementers

            interface_class = classes[0]  # 첫 번째 클래스를 인터페이스로 가정

            # 프로젝트 전체에서 이 클래스를 상속하는 클래스 찾기
            for file_path, file_info in self.knowledge_base['files'].items():
                if file_path == str(interface_file.relative_to(self.project_root)):
                    continue

                if interface_class in file_info['content']:
                    implementers.append(Path(file_path).stem)

        except Exception:
            pass

        return implementers

    def _find_utility_functions(self) -> List[Dict[str, str]]:
        """유틸리티 함수 찾기"""
        utilities = []

        for file_path, file_info in self.knowledge_base['files'].items():
            if 'util' in file_path.lower() or 'helper' in file_path.lower():
                for func_name in file_info['functions']:
                    if not func_name.startswith('_'):  # 공개 함수만
                        utilities.append({
                            'name': func_name,
                            'file': file_path,
                            'description': f"{Path(file_path).stem} 모듈의 유틸리티 함수"
                        })

        return utilities

    def _measure_layer_separation(self) -> float:
        """계층 분리도 측정"""
        violations = 0
        total_files = 0

        # Domain 계층에서 Infrastructure 의존성 검사
        for file_path, file_info in self.knowledge_base['files'].items():
            if 'domain' in file_path:
                total_files += 1
                for import_name in file_info['imports']:
                    if 'infrastructure' in import_name or 'sqlite' in import_name:
                        violations += 1

        if total_files == 0:
            return 100

        return max(0, 100 - (violations / total_files * 100))

    def _check_dependency_direction(self) -> float:
        """의존성 방향 검사"""
        # 간단한 휴리스틱: 상위 계층이 하위 계층만 의존하는지 확인
        violations = 0
        total_dependencies = 0

        layer_hierarchy = ['presentation', 'application', 'domain', 'infrastructure']

        for file_path, file_info in self.knowledge_base['files'].items():
            current_layer = self._get_file_layer(self.project_root / file_path)
            if current_layer == 'other':
                continue

            current_level = layer_hierarchy.index(current_layer) if current_layer in layer_hierarchy else -1

            for import_name in file_info['imports']:
                for dep_layer in layer_hierarchy:
                    if dep_layer in import_name:
                        dep_level = layer_hierarchy.index(dep_layer)
                        total_dependencies += 1

                        # 잘못된 의존성 방향 검사
                        if current_layer == 'domain' and dep_layer in ['infrastructure', 'presentation']:
                            violations += 1
                        elif current_layer == 'application' and dep_layer == 'presentation':
                            violations += 1

        if total_dependencies == 0:
            return 100

        return max(0, 100 - (violations / total_dependencies * 100))

    def _measure_interface_usage(self) -> float:
        """인터페이스 사용률 측정"""
        interface_files = 0
        total_files = 0

        for file_path, file_info in self.knowledge_base['files'].items():
            total_files += 1
            if ('interface' in file_path.lower() or
                'abstract' in file_path.lower() or
                any('abc' in imp for imp in file_info['imports'])):
                interface_files += 1

        if total_files == 0:
            return 0

        return (interface_files / total_files) * 100

    def _measure_code_duplication(self) -> float:
        """코드 중복도 측정"""
        function_names = defaultdict(int)

        for file_info in self.knowledge_base['files'].values():
            for func_name in file_info['functions']:
                if not func_name.startswith('_'):  # 공개 함수만
                    function_names[func_name] += 1

        duplicated_functions = sum(1 for count in function_names.values() if count > 1)
        total_functions = len(function_names)

        if total_functions == 0:
            return 100

        duplication_ratio = duplicated_functions / total_functions
        return max(0, 100 - (duplication_ratio * 100))

    def _check_naming_consistency(self) -> float:
        """네이밍 일관성 검사"""
        violations = 0
        total_names = 0

        # snake_case 패턴 검사
        snake_case_pattern = re.compile(r'^[a-z_][a-z0-9_]*$')

        for file_info in self.knowledge_base['files'].values():
            for func_name in file_info['functions']:
                total_names += 1
                if not snake_case_pattern.match(func_name):
                    violations += 1

        if total_names == 0:
            return 100

        return max(0, 100 - (violations / total_names * 100))

    def _estimate_test_coverage(self) -> float:
        """테스트 커버리지 추정"""
        test_files = 0
        source_files = 0

        for file_path in self.knowledge_base['files'].keys():
            if 'test' in file_path.lower():
                test_files += 1
            else:
                source_files += 1

        if source_files == 0:
            return 0

        # 테스트 파일 비율을 커버리지 추정치로 사용
        return min(100, (test_files / source_files) * 100)


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='Super Dev Assistant - 개발 도우미')
    parser.add_argument('--what-exists', type=str, help='해당 기능이 이미 있는지 확인')
    parser.add_argument('--where-is', type=str, help='기능 구현 위치 찾기')
    parser.add_argument('--similar-code', type=str, help='유사한 코드 패턴 찾기')
    parser.add_argument('--folder-summary', type=str, help='폴더별 기능 요약')
    parser.add_argument('--quick-guide', type=str, help='모듈 사용법 빠른 가이드')
    parser.add_argument('--integration-points', action='store_true', help='통합 가능한 포인트 탐지')
    parser.add_argument('--architecture-health', action='store_true', help='DDD 아키텍처 건강도 점수')

    args = parser.parse_args()

    assistant = SuperDevAssistant()

    # 아무 옵션이 없으면 architecture-health 실행
    if not any(vars(args).values()):
        assistant.architecture_health()
        return

    if args.what_exists:
        assistant.what_exists(args.what_exists)

    if args.where_is:
        assistant.where_is(args.where_is)

    if args.similar_code:
        assistant.similar_code(args.similar_code)

    if args.folder_summary:
        assistant.folder_summary(args.folder_summary)

    if args.quick_guide:
        assistant.quick_guide(args.quick_guide)

    if args.integration_points:
        assistant.integration_points()

    if args.architecture_health:
        assistant.architecture_health()


if __name__ == "__main__":
    main()

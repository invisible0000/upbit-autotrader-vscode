#!/usr/bin/env python3
"""
트레이딩 지표 변수 관리 CLI 도구

명령어:
  list                    - 모든 활성 지표 목록 출력
  compatible <ID>         - 특정 지표와 호환되는 지표들 조회
  check <ID1> <ID2>       - 두 지표의 호환성 검증
  add <ID> <name> [desc]  - 새 지표 추가 (자동 분류)
  activate <ID>           - 지표 활성화
  deactivate <ID>         - 지표 비활성화
  stats                   - 통계 정보 출력
  test                    - 호환성 테스트 실행
  batch-add               - 인기 지표 일괄 추가

사용 예시:
  python tools/trading_variables_cli.py list
  python tools/trading_variables_cli.py compatible SMA
  python tools/trading_variables_cli.py check SMA EMA
  python tools/trading_variables_cli.py add HULL_MA "헐 이동평균" "부드러운 이동평균"
"""

import argparse
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from upbit_auto_trading.utils.trading_variables.variable_manager import SimpleVariableManager
    from upbit_auto_trading.utils.trading_variables.indicator_classifier import SmartIndicatorClassifier
except ImportError as e:
    print(f"❌ 모듈 import 실패: {e}")
    print("프로젝트 루트에서 실행해주세요.")
    sys.exit(1)


class TradingVariablesCLI:
    """트레이딩 지표 변수 관리 CLI"""
    
    def __init__(self, db_path: str = 'trading_variables.db'):
        self.db_path = db_path
        self.vm = None
        self.classifier = SmartIndicatorClassifier()
    
    def _connect(self):
        """DB 연결"""
        if not self.vm:
            self.vm = SimpleVariableManager(self.db_path)
    
    def _close(self):
        """DB 연결 종료"""
        if self.vm:
            self.vm.close()
            self.vm = None
    
    def list_variables(self, args):
        """모든 활성 지표 목록 출력"""
        self._connect()
        
        all_vars = self.vm.get_all_variables(active_only=True)
        
        if not all_vars:
            print("📋 활성 지표가 없습니다.")
            return
        
        print(f"📋 활성 지표 목록 ({len(all_vars)}개)")
        print("=" * 80)
        
        # 카테고리별로 그룹화
        by_category = {}
        for var in all_vars:
            category = var['purpose_category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(var)
        
        # 카테고리 이름 매핑
        category_names = {
            'trend': '📈 추세 지표',
            'momentum': '⚡ 모멘텀 지표',
            'volatility': '🔥 변동성 지표',
            'volume': '📦 거래량 지표',
            'price': '💰 가격 데이터',
            'support_resistance': '🎯 지지/저항'
        }
        
        for category, vars_list in sorted(by_category.items()):
            category_name = category_names.get(category, category)
            print(f"\n{category_name} ({len(vars_list)}개):")
            
            for var in sorted(vars_list, key=lambda x: x['display_name_ko']):
                chart_icon = "🔗" if var['chart_category'] == 'overlay' else "📊"
                print(f"  {chart_icon} {var['variable_id']:20} {var['display_name_ko']}")
                if var.get('description'):
                    print(f"     💡 {var['description'][:60]}...")
    
    def show_compatible(self, args):
        """특정 지표와 호환되는 지표들 조회"""
        if not args.variable_id:
            print("❌ 지표 ID를 입력해주세요. 예: compatible SMA")
            return
        
        self._connect()
        
        base_id = args.variable_id.upper()
        compatible = self.vm.get_compatible_variables(base_id)
        
        if not compatible:
            print(f"❌ '{base_id}' 지표를 찾을 수 없거나 호환되는 지표가 없습니다.")
            return
        
        print(f"🔗 '{base_id}'와 호환되는 지표들 ({len(compatible)}개)")
        print("=" * 50)
        
        for var_id, name in compatible:
            print(f"  ✅ {var_id:15} {name}")
        
        # 호환성 정보도 출력
        if compatible:
            sample_id = compatible[0][0]
            result = self.vm.check_compatibility(base_id, sample_id)
            if result['compatible']:
                print(f"\n💡 호환 이유: {result['reason']}")
    
    def check_compatibility(self, args):
        """두 지표의 호환성 검증"""
        if not args.var1 or not args.var2:
            print("❌ 두 개의 지표 ID를 입력해주세요. 예: check SMA EMA")
            return
        
        self._connect()
        
        var1 = args.var1.upper()
        var2 = args.var2.upper()
        
        result = self.vm.check_compatibility(var1, var2)
        
        print(f"🔍 호환성 검증: {var1} ↔ {var2}")
        print("=" * 40)
        
        if result['compatible']:
            print(f"✅ 호환 가능")
            print(f"💡 이유: {result['reason']}")
        else:
            print(f"❌ 호환 불가")
            print(f"💡 이유: {result['reason']}")
        
        # 상세 정보 출력
        if result['var1_info'] and result['var2_info']:
            print(f"\n📊 {var1} 정보:")
            print(f"   이름: {result['var1_info']['name']}")
            print(f"   용도: {result['var1_info']['purpose']}")
            print(f"   비교: {result['var1_info']['comparison']}")
            
            print(f"\n📊 {var2} 정보:")
            print(f"   이름: {result['var2_info']['name']}")
            print(f"   용도: {result['var2_info']['purpose']}")
            print(f"   비교: {result['var2_info']['comparison']}")
    
    def add_variable(self, args):
        """새 지표 추가 (자동 분류)"""
        if not args.variable_id or not args.name:
            print("❌ 지표 ID와 이름을 입력해주세요. 예: add HULL_MA '헐 이동평균' '부드러운 이동평균'")
            return
        
        var_id = args.variable_id.upper()
        name = args.name
        description = args.description or ''
        
        print(f"🔍 새 지표 추가: {var_id} ({name})")
        print("=" * 50)
        
        # 자동 분류 실행
        success = self.classifier.add_new_indicator(var_id, name, description)
        
        if success:
            print(f"\n✅ 지표 추가 완료!")
            print(f"💡 활성화하려면: activate {var_id}")
        else:
            print(f"\n❌ 지표 추가 실패")
    
    def activate_variable(self, args):
        """지표 활성화"""
        if not args.variable_id:
            print("❌ 지표 ID를 입력해주세요. 예: activate HULL_MA")
            return
        
        self._connect()
        
        var_id = args.variable_id.upper()
        success = self.vm.activate_variable(var_id)
        
        if success:
            print(f"✅ '{var_id}' 지표가 활성화되었습니다.")
        else:
            print(f"❌ '{var_id}' 지표 활성화에 실패했습니다.")
    
    def deactivate_variable(self, args):
        """지표 비활성화"""
        if not args.variable_id:
            print("❌ 지표 ID를 입력해주세요. 예: deactivate HULL_MA")
            return
        
        self._connect()
        
        var_id = args.variable_id.upper()
        success = self.vm.deactivate_variable(var_id)
        
        if success:
            print(f"✅ '{var_id}' 지표가 비활성화되었습니다.")
        else:
            print(f"❌ '{var_id}' 지표 비활성화에 실패했습니다.")
    
    def show_stats(self, args):
        """통계 정보 출력"""
        self._connect()
        
        stats = self.vm.get_statistics()
        
        print("📊 트레이딩 지표 통계")
        print("=" * 40)
        print(f"총 지표 수: {stats.get('total_variables', 0)}개")
        print(f"활성 지표: {stats.get('active_variables', 0)}개")
        
        print("\n📈 카테고리별 분포:")
        category_names = {
            'trend': '추세',
            'momentum': '모멘텀',
            'volatility': '변동성',
            'volume': '거래량',
            'price': '가격',
            'support_resistance': '지지/저항'
        }
        
        for category, count in stats.get('by_category', {}).items():
            name = category_names.get(category, category)
            print(f"  {name:10}: {count:2}개")
        
        print("\n📊 차트 타입별 분포:")
        for chart_type, count in stats.get('by_chart_type', {}).items():
            type_name = '오버레이' if chart_type == 'overlay' else '서브플롯'
            print(f"  {type_name:10}: {count:2}개")
    
    def batch_add_indicators(self, args):
        """인기 지표 일괄 추가"""
        print("🚀 인기 지표 일괄 추가 시작...")
        print("=" * 50)
        
        success_count = self.classifier.batch_add_popular_indicators()
        
        print(f"\n🎯 {success_count}개 지표 추가 완료!")
        print("💡 추가된 지표들을 활성화하려면 개별적으로 activate 명령을 사용하세요.")
    
    def run_tests(self, args):
        """호환성 테스트 실행"""
        print("🧪 호환성 테스트 실행...")
        print("=" * 50)
        
        try:
            from tests.test_variable_compatibility import run_compatibility_tests
            success = run_compatibility_tests()
            
            if success:
                print("\n🎉 모든 테스트 통과!")
            else:
                print("\n⚠️ 일부 테스트 실패")
            
        except ImportError:
            print("❌ 테스트 모듈을 찾을 수 없습니다.")
        except Exception as e:
            print(f"❌ 테스트 실행 중 오류: {e}")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='트레이딩 지표 변수 관리 CLI 도구',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--db', default='trading_variables.db',
                       help='SQLite DB 파일 경로 (기본값: trading_variables.db)')
    
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # list 명령
    subparsers.add_parser('list', help='모든 활성 지표 목록 출력')
    
    # compatible 명령
    compatible_parser = subparsers.add_parser('compatible', help='호환되는 지표들 조회')
    compatible_parser.add_argument('variable_id', help='기준 지표 ID')
    
    # check 명령
    check_parser = subparsers.add_parser('check', help='두 지표의 호환성 검증')
    check_parser.add_argument('var1', help='첫 번째 지표 ID')
    check_parser.add_argument('var2', help='두 번째 지표 ID')
    
    # add 명령
    add_parser = subparsers.add_parser('add', help='새 지표 추가 (자동 분류)')
    add_parser.add_argument('variable_id', help='지표 ID')
    add_parser.add_argument('name', help='지표 이름')
    add_parser.add_argument('description', nargs='?', default='', help='지표 설명 (선택사항)')
    
    # activate 명령
    activate_parser = subparsers.add_parser('activate', help='지표 활성화')
    activate_parser.add_argument('variable_id', help='지표 ID')
    
    # deactivate 명령
    deactivate_parser = subparsers.add_parser('deactivate', help='지표 비활성화')
    deactivate_parser.add_argument('variable_id', help='지표 ID')
    
    # stats 명령
    subparsers.add_parser('stats', help='통계 정보 출력')
    
    # batch-add 명령
    subparsers.add_parser('batch-add', help='인기 지표 일괄 추가')
    
    # test 명령
    subparsers.add_parser('test', help='호환성 테스트 실행')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # CLI 인스턴스 생성
    cli = TradingVariablesCLI(args.db)
    
    try:
        # 명령 실행
        command_map = {
            'list': cli.list_variables,
            'compatible': cli.show_compatible,
            'check': cli.check_compatibility,
            'add': cli.add_variable,
            'activate': cli.activate_variable,
            'deactivate': cli.deactivate_variable,
            'stats': cli.show_stats,
            'batch-add': cli.batch_add_indicators,
            'test': cli.run_tests
        }
        
        if args.command in command_map:
            command_map[args.command](args)
        else:
            print(f"❌ 알 수 없는 명령: {args.command}")
            parser.print_help()
    
    finally:
        cli._close()


if __name__ == "__main__":
    main()

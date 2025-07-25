"""
데이터 소스 가용성 간단 체크
"""

def check_data_sources():
    """데이터 소스 상태 확인"""
    print("📊 데이터 소스 상태 확인")
    print("-" * 30)
    
    try:
        # 데이터 소스 매니저 확인
        from upbit_auto_trading.ui.desktop.screens.strategy_management.data_source_manager import get_data_source_manager
        
        manager = get_data_source_manager()
        print("✅ 데이터 소스 매니저 로드 성공")
        
        # 사용 가능한 소스들 확인
        sources = manager.get_available_sources()
        print(f"📋 사용 가능한 데이터 소스: {len(sources)}개")
        
        if sources:
            for key, info in sources.items():
                print(f"  🔹 {key}: {info['name']}")
        else:
            print("⚠️ 현재 사용 가능한 데이터 소스가 없습니다")
            print("   이는 다음과 같은 이유일 수 있습니다:")
            print("   - 데이터베이스 파일이 없음")
            print("   - 내장 시뮬레이션 엔진 초기화 문제")
            print("   - 모듈 import 경로 문제")
            print("   현재 개발 단계에서는 UI 레이아웃 확인이 우선입니다.")
        
    except Exception as e:
        print(f"❌ 데이터 소스 확인 실패: {e}")
        print("💡 현재는 UI 구조 확인에 집중하고, 데이터 소스는 나중에 연결합니다.")

def check_embedded_engine():
    """내장 시뮬레이션 엔진 확인"""
    print("\n🔧 내장 시뮬레이션 엔진 확인")
    print("-" * 30)
    
    try:
        from upbit_auto_trading.ui.desktop.screens.strategy_management.embedded_simulation_engine import EmbeddedSimulationDataEngine
        
        engine = EmbeddedSimulationDataEngine()
        print("✅ 내장 시뮬레이션 엔진 생성 성공")
        
        # 시나리오 개수 확인
        scenarios = ["상승 추세", "하락 추세", "급등", "급락", "횡보", "이동평균 교차"]
        working_scenarios = 0
        
        for scenario in scenarios:
            try:
                result = engine.search_scenario_data(scenario, "RSI", ">", 70, 500)
                if result['success']:
                    working_scenarios += 1
            except:
                pass
        
        print(f"📊 작동하는 시나리오: {working_scenarios}/{len(scenarios)}개")
        
    except Exception as e:
        print(f"❌ 내장 엔진 확인 실패: {e}")

if __name__ == "__main__":
    print("🚀 데이터 소스 상태 간단 체크")
    print("=" * 50)
    
    check_data_sources()
    check_embedded_engine()
    
    print("\n📝 결론:")
    print("- 현재는 UI 레이아웃과 버튼 크기 조정이 우선")
    print("- 데이터 소스 연결은 UI 완성 후 진행")
    print("- 버튼들이 화면에 잘 맞는지 확인하는 것이 중요")

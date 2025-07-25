"""
Data Generators Component
시뮬레이션 데이터 생성을 담당하는 컴포넌트
"""

import numpy as np
import random


class DataGenerators:
    """시뮬레이션 데이터 생성을 담당하는 컴포넌트"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def generate_price_data_for_chart(self, scenario, length=50):
        """가격용 시뮬레이션 데이터 생성 (원화 기준)"""
        try:
            # 기본 가격 설정 (5백만원 기준)
            base_price = 5000000
            
            # 시나리오별 가격 패턴
            if scenario in ["상승 추세", "Uptrend"]:
                # 상승 추세: 점진적 상승
                trend = np.linspace(0, 800000, length)
                noise = np.random.randn(length) * 50000
                price_data = base_price + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                # 하락 추세: 점진적 하락
                trend = np.linspace(0, -800000, length)
                noise = np.random.randn(length) * 50000
                price_data = base_price + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 급등: 빠른 상승 후 안정화
                trend = np.concatenate([
                    np.linspace(0, 200000, length // 3),
                    np.linspace(200000, 1000000, length // 3),
                    np.linspace(1000000, 900000, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 70000
                price_data = base_price + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 급락: 빠른 하락 후 반등
                trend = np.concatenate([
                    np.linspace(0, -100000, length // 3),
                    np.linspace(-100000, -800000, length // 3),
                    np.linspace(-800000, -600000, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 80000
                price_data = base_price + trend + noise
            elif scenario in ["횡보", "Sideways"]:
                # 횡보 패턴 - 5백만원 근처에서 변동
                noise = np.random.randn(length) * 30000  # 3만원 변동
                price_data = base_price + noise
            elif scenario in ["이동평균 교차", "MA Cross"]:
                # 이동평균 교차 패턴
                noise = np.random.randn(length) * 40000
                price_data = base_price + np.cumsum(noise * 0.01)
            else:
                # 기본 랜덤 패턴 - 5백만원 기준
                noise = np.random.randn(length) * 60000
                price_data = base_price + np.cumsum(noise * 0.02)
            
            # 가격이 음수가 되지 않도록 보정
            price_data = np.maximum(price_data, 100000)  # 최소 10만원
            
            return price_data.tolist()
            
        except Exception as e:
            print(f"❌ 가격 데이터 생성 실패: {e}")
            # 기본 5백만원 근처 랜덤 데이터
            return [5000000 + random.randint(-200000, 200000) for _ in range(length)]
    
    def generate_rsi_data_for_chart(self, scenario, length=50):
        """RSI용 시뮬레이션 데이터 생성 (0-100 범위)"""
        try:
            # RSI 기본값 설정
            base_rsi = 50  # 중립값
            
            # 시나리오별 RSI 패턴
            if scenario in ["상승 추세", "Uptrend"]:
                # 상승 추세: RSI가 50에서 70으로 증가
                trend = np.linspace(0, 20, length)
                noise = np.random.randn(length) * 5
                rsi_data = base_rsi + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                # 하락 추세: RSI가 50에서 30으로 감소
                trend = np.linspace(0, -20, length)
                noise = np.random.randn(length) * 5
                rsi_data = base_rsi + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 급등: RSI가 빠르게 과매수 구간(70+)으로
                trend = np.concatenate([
                    np.linspace(0, 10, length // 3),
                    np.linspace(10, 35, length // 3),
                    np.linspace(35, 30, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 3
                rsi_data = base_rsi + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 급락: RSI가 빠르게 과매도 구간(30-)으로
                trend = np.concatenate([
                    np.linspace(0, 5, length // 3),
                    np.linspace(5, -35, length // 3),
                    np.linspace(-35, -30, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 3
                rsi_data = base_rsi + trend + noise
            elif scenario in ["횡보", "Sideways"]:
                # 횡보: RSI 50 근처에서 변동
                noise = np.random.randn(length) * 8
                rsi_data = base_rsi + noise
            else:
                # 기본: RSI 랜덤 변동
                noise = np.random.randn(length) * 10
                rsi_data = base_rsi + np.cumsum(noise * 0.1)
            
            # RSI 범위 제한 (0-100)
            rsi_data = np.clip(rsi_data, 0, 100)
            
            print(f"📊 RSI 데이터 생성: {scenario}, 범위 {rsi_data.min():.1f}-{rsi_data.max():.1f}")
            return rsi_data.tolist()
            
        except Exception as e:
            print(f"❌ RSI 데이터 생성 실패: {e}")
            # 기본 RSI 데이터
            return [random.uniform(20, 80) for _ in range(length)]
    
    def generate_macd_data_for_chart(self, scenario, length=50):
        """MACD용 시뮬레이션 데이터 생성 (-2 ~ 2 범위)"""
        try:
            # MACD 기본값 설정
            base_macd = 0  # 중립값
            
            # 시나리오별 MACD 패턴
            if scenario in ["상승 추세", "Uptrend"]:
                # 상승 추세: MACD가 양수로 증가
                trend = np.linspace(0, 1.5, length)
                noise = np.random.randn(length) * 0.1
                macd_data = base_macd + trend + noise
            elif scenario in ["하락 추세", "Downtrend"]:
                # 하락 추세: MACD가 음수로 감소
                trend = np.linspace(0, -1.5, length)
                noise = np.random.randn(length) * 0.1
                macd_data = base_macd + trend + noise
            elif scenario in ["급등", "Surge"]:
                # 급등: MACD가 빠르게 큰 양수로
                trend = np.concatenate([
                    np.linspace(0, 0.5, length // 3),
                    np.linspace(0.5, 2.0, length // 3),
                    np.linspace(2.0, 1.5, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 0.05
                macd_data = base_macd + trend + noise
            elif scenario in ["급락", "Crash"]:
                # 급락: MACD가 빠르게 큰 음수로
                trend = np.concatenate([
                    np.linspace(0, -0.3, length // 3),
                    np.linspace(-0.3, -2.0, length // 3),
                    np.linspace(-2.0, -1.5, length - 2 * (length // 3))
                ])
                noise = np.random.randn(length) * 0.05
                macd_data = base_macd + trend + noise
            elif scenario in ["이동평균 교차", "MA Cross"]:
                # 이동평균 교차: MACD가 0 근처에서 교차
                noise = np.random.randn(length) * 0.2
                macd_data = np.sin(np.linspace(0, 4*np.pi, length)) * 0.5 + noise
            else:
                # 기본: MACD 랜덤 변동
                noise = np.random.randn(length) * 0.3
                macd_data = base_macd + np.cumsum(noise * 0.05)
            
            # MACD 범위 제한 (-2 ~ 2)
            macd_data = np.clip(macd_data, -2, 2)
            
            print(f"📊 MACD 데이터 생성: {scenario}, 범위 {macd_data.min():.2f}-{macd_data.max():.2f}")
            return macd_data.tolist()
            
        except Exception as e:
            print(f"❌ MACD 데이터 생성 실패: {e}")
            # 기본 MACD 데이터
            return [random.uniform(-1, 1) for _ in range(length)]
    
    def generate_simulation_data(self, scenario, variable_name):
        """시나리오별 실제 데이터 기반 시뮬레이션 - 업그레이드 버전"""
        try:
            # 실제 데이터 시뮬레이션 엔진 사용 시도
            try:
                from ..real_data_simulation import get_simulation_engine
                
                engine = get_simulation_engine()
                real_data = engine.get_scenario_data(scenario, length=50)
                
                if real_data and real_data.get('data_source') == 'real_market_data':
                    # 실제 시장 데이터 사용 성공
                    print(f"✅ 실제 시장 데이터 사용: {scenario} ({real_data.get('period', 'Unknown')})")
                    
                    # 변수 타입에 따른 값 조정
                    current_value = real_data['current_value']
                    
                    if 'rsi' in variable_name.lower():
                        # RSI 시뮬레이션을 위한 값 조정 (0-100 범위)
                        current_value = min(max(current_value % 100, 0), 100)
                    elif 'ma' in variable_name.lower() or '이동평균' in variable_name.lower():
                        # 이동평균 관련은 그대로 사용
                        pass
                    elif 'macd' in variable_name.lower():
                        # MACD는 -1 ~ 1 범위로 조정
                        current_value = (current_value / 50000) - 1
                    
                    return {
                        'current_value': current_value,
                        'base_value': real_data['base_value'],
                        'change_percent': real_data['change_percent'],
                        'scenario': scenario,
                        'data_source': 'real_market_data',
                        'period': real_data.get('period', 'Unknown')
                    }
                else:
                    # 실제 데이터 로드 실패 시 폴백
                    print(f"⚠️ 실제 데이터 로드 실패, 시뮬레이션 데이터 사용: {scenario}")
            
            except ImportError:
                print(f"⚠️ 실제 데이터 엔진 없음, 시뮬레이션 데이터 사용: {scenario}")
        
        except Exception as e:
            print(f"❌ 실제 데이터 엔진 오류: {e}")
        
        # 폴백: 변수 타입별 시뮬레이션 데이터 생성 (개선된 버전)
        
        # 변수 타입에 따른 시나리오별 값 생성
        if 'rsi' in variable_name.lower():
            # RSI 시뮬레이션 (0-100 범위)
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = random.uniform(55, 75)  # 상승 시 RSI 높음
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = random.uniform(25, 45)  # 하락 시 RSI 낮음
            elif scenario in ["Surge", "급등"]:
                base_value = random.uniform(70, 85)  # 급등 시 과매수
            elif scenario in ["Crash", "급락"]:
                base_value = random.uniform(15, 35)  # 급락 시 과매도
            else:
                base_value = random.uniform(40, 60)  # 중립
                
        elif 'macd' in variable_name.lower():
            # MACD 시뮬레이션 (-2 ~ 2 범위)
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = random.uniform(0.2, 1.5)  # 상승 시 양수
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = random.uniform(-1.5, -0.2)  # 하락 시 음수
            elif scenario in ["Surge", "급등"]:
                base_value = random.uniform(1.0, 2.0)  # 급등 시 큰 양수
            elif scenario in ["Crash", "급락"]:
                base_value = random.uniform(-2.0, -1.0)  # 급락 시 큰 음수
            elif scenario in ["MA Cross", "이동평균 교차"]:
                base_value = random.uniform(-0.3, 0.3)  # 교차점 근처
            else:
                base_value = random.uniform(-0.5, 0.5)  # 중립
                
        elif 'price' in variable_name.lower() or '가격' in variable_name.lower():
            # 가격 시뮬레이션 (5백만원 기준)
            base_price = 5000000
            if scenario in ["Uptrend", "상승 추세"]:
                base_value = base_price * random.uniform(1.05, 1.15)
            elif scenario in ["Downtrend", "하락 추세"]:
                base_value = base_price * random.uniform(0.85, 0.95)
            elif scenario in ["Surge", "급등"]:
                base_value = base_price * random.uniform(1.2, 1.5)
            elif scenario in ["Crash", "급락"]:
                base_value = base_price * random.uniform(0.6, 0.8)
            else:
                base_value = base_price * random.uniform(0.98, 1.02)
                
        elif 'volume' in variable_name.lower() or '거래량' in variable_name.lower():
            # 거래량 시뮬레이션
            if scenario in ["Surge", "급등", "Crash", "급락"]:
                base_value = random.uniform(5000000, 20000000)  # 높은 거래량
            else:
                base_value = random.uniform(1000000, 5000000)  # 일반 거래량
        else:
            # 기타 지표들
            base_value = random.uniform(30, 70)
        
        # 최종 값 반환
        current_value = base_value
        
        return {
            'current_value': current_value,
            'base_value': base_value,
            'change_percent': 0,  # 변경율은 시나리오별 값에 이미 반영됨
            'scenario': scenario,
            'data_source': 'fallback_simulation'
        }

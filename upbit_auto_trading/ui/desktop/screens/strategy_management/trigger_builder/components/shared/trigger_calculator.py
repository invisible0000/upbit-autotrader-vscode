"""
Trigger Calculator Component
트리거 계산 로직을 담당하는 컴포넌트
"""


class TriggerCalculator:
    """트리거 계산 로직을 담당하는 컴포넌트"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_trigger_points(self, price_data, operator, target_value):
        """실제 가격 데이터를 기반으로 트리거 포인트 계산 - 개선된 버전"""
        trigger_points = []
        
        try:
            if not price_data or len(price_data) == 0:
                print("❌ 가격 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # 연산자별 조건 확인
            for i, price in enumerate(price_data):
                triggered = False
                
                if operator == '>' and price > target_float:
                    triggered = True
                elif operator == '>=' and price >= target_float:
                    triggered = True
                elif operator == '<' and price < target_float:
                    triggered = True
                elif operator == '<=' and price <= target_float:
                    triggered = True
                elif operator == '~=' and target_float != 0:
                    # 근사값 (±1%)
                    diff_percent = abs(price - target_float) / abs(target_float) * 100
                    if diff_percent <= 1.0:
                        triggered = True
                elif operator == '!=' and price != target_float:
                    triggered = True
                
                if triggered:
                    trigger_points.append(i)
            
            # 연속된 트리거 포인트 필터링 조건 완화
            # 가격 기반 조건(>, >=, <, <=)의 경우 필터링 최소화
            if len(trigger_points) > 1 and operator in ['~=', '!=']:
                # 근사값이나 부등호 조건에서만 필터링 적용
                filtered_points = [trigger_points[0]]
                for point in trigger_points[1:]:
                    if point - filtered_points[-1] > 1:  # 간격을 1로 줄임
                        filtered_points.append(point)
                trigger_points = filtered_points
            # >, >=, <, <= 조건에서는 연속된 신호를 모두 유지
            
            print("🎯 트리거 포인트 계산:")
            print(f"   연산자: {operator}, 대상값: {target_float}")
            print(f"   가격 범위: {min(price_data):.0f} ~ {max(price_data):.0f}")
            print(f"   조건 충족 포인트: {len([p for i, p in enumerate(price_data) if self._check_condition(p, operator, target_float)])}개")
            print(f"   필터링 후 신호: {len(trigger_points)}개")
            print(f"   포인트 위치: {trigger_points[:10]}{'...' if len(trigger_points) > 10 else ''}")
            
            return trigger_points
            
        except Exception as e:
            print(f"❌ 트리거 포인트 계산 오류: {e}")
            return []
    
    def _check_condition(self, value, operator, target):
        """조건 체크 헬퍼 메서드"""
        if operator == '>':
            return value > target
        elif operator == '>=':
            return value >= target
        elif operator == '<':
            return value < target
        elif operator == '<=':
            return value <= target
        elif operator == '~=' and target != 0:
            diff_percent = abs(value - target) / abs(target) * 100
            return diff_percent <= 1.0
        elif operator == '!=':
            return value != target
        return False
    
    def calculate_rsi_trigger_points(self, rsi_data, operator, target_value):
        """RSI 데이터를 기반으로 트리거 포인트 계산"""
        trigger_points = []
        
        try:
            if not rsi_data or len(rsi_data) == 0:
                print("❌ RSI 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # RSI 범위 체크 (0-100)
            if not (0 <= target_float <= 100):
                print(f"⚠️ RSI 목표값이 범위를 벗어남: {target_float} (0-100 범위여야 함)")
                return []
            
            # 연산자별 조건 확인
            for i, rsi in enumerate(rsi_data):
                if self._check_condition(rsi, operator, target_float):
                    trigger_points.append(i)
            
            # RSI는 연속된 값이 같을 수 있으므로 필터링 적용
            if len(trigger_points) > 1:
                filtered_points = [trigger_points[0]]
                for point in trigger_points[1:]:
                    if point - filtered_points[-1] > 2:  # RSI는 간격을 2로 설정
                        filtered_points.append(point)
                trigger_points = filtered_points
            
            print(f"🎯 RSI 트리거 포인트 계산: {operator} {target_float}")
            print(f"   RSI 범위: {min(rsi_data):.1f} ~ {max(rsi_data):.1f}")
            print(f"   신호 개수: {len(trigger_points)}개")
            
            return trigger_points
            
        except Exception as e:
            print(f"❌ RSI 트리거 포인트 계산 오류: {e}")
            return []
    
    def calculate_macd_trigger_points(self, macd_data, operator, target_value):
        """MACD 데이터를 기반으로 트리거 포인트 계산"""
        trigger_points = []
        
        try:
            if not macd_data or len(macd_data) == 0:
                print("❌ MACD 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # 연산자별 조건 확인
            for i, macd in enumerate(macd_data):
                if self._check_condition(macd, operator, target_float):
                    trigger_points.append(i)
            
            # MACD는 0 교차 등이 중요하므로 필터링 최소화
            if len(trigger_points) > 1 and operator in ['~=']:
                filtered_points = [trigger_points[0]]
                for point in trigger_points[1:]:
                    if point - filtered_points[-1] > 1:
                        filtered_points.append(point)
                trigger_points = filtered_points
            
            print(f"🎯 MACD 트리거 포인트 계산: {operator} {target_float}")
            print(f"   MACD 범위: {min(macd_data):.2f} ~ {max(macd_data):.2f}")
            print(f"   신호 개수: {len(trigger_points)}개")
            
            return trigger_points
            
        except Exception as e:
            print(f"❌ MACD 트리거 포인트 계산 오류: {e}")
            return []
    
    def calculate_generic_trigger_points(self, data, operator, target_value, data_type="generic"):
        """범용 트리거 포인트 계산"""
        trigger_points = []
        
        try:
            if not data or len(data) == 0:
                print(f"❌ {data_type} 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # 연산자별 조건 확인
            for i, value in enumerate(data):
                if self._check_condition(value, operator, target_float):
                    trigger_points.append(i)
            
            # 기본 필터링 적용
            if len(trigger_points) > 1:
                filtered_points = [trigger_points[0]]
                for point in trigger_points[1:]:
                    if point - filtered_points[-1] > 1:
                        filtered_points.append(point)
                trigger_points = filtered_points
            
            print(f"🎯 {data_type} 트리거 포인트 계산: {operator} {target_float}")
            print(f"   데이터 범위: {min(data):.2f} ~ {max(data):.2f}")
            print(f"   신호 개수: {len(trigger_points)}개")
            
            return trigger_points
            
        except Exception as e:
            print(f"❌ {data_type} 트리거 포인트 계산 오류: {e}")
            return []

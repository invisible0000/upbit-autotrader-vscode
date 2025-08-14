"""
Trigger Calculator Component
트리거 계산 로직을 담당하는 컴포넌트
"""

class TriggerCalculator:
    """트리거 계산 로직을 담당하는 컴포넌트"""
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_trigger_points(self, variable_data, operator, target_value):
        """변수 데이터(가격, RSI, SMA 등)를 기반으로 트리거 포인트 계산 - 개선된 버전"""
        trigger_points = []
        
        try:
            if not variable_data or len(variable_data) == 0:
                print("❌ 변수 데이터가 없습니다")
                return []
            
            target_float = float(target_value)
            
            # 데이터 범위 로깅 (디버깅용)
            data_min = min(variable_data)
            data_max = max(variable_data)
            print(f"🎯 트리거 포인트 계산:")
            print(f"   연산자: {operator}, 대상값: {target_float}")
            print(f"   가격 범위: {data_min:.0f} ~ {data_max:.0f}")
            
            # 연산자별 조건 확인
            for i, value in enumerate(variable_data):
                triggered = False
                
                if operator == '>' and value > target_float:
                    triggered = True
                elif operator == '>=' and value >= target_float:
                    triggered = True
                elif operator == '<' and value < target_float:
                    triggered = True
                elif operator == '<=' and value <= target_float:
                    triggered = True
                elif operator == '~=' and target_float != 0:
                    # 근사값 (±1%)
                    diff_percent = abs(value - target_float) / abs(target_float) * 100
                    if diff_percent <= 1.0:
                        triggered = True
                elif operator == '!=' and value != target_float:
                    triggered = True
                
                if triggered:
                    trigger_points.append(i)
            
            print(f"   조건 충족 포인트: {len(trigger_points)}개")
            
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
    
    def calculate_sma(self, prices, period):
        """단순이동평균 계산"""
        if len(prices) < period:
            return [prices[0]] * len(prices)  # 데이터 부족시 첫 번째 값으로 채움
        
        sma_values = []
        for i in range(len(prices)):
            if i < period - 1:
                # 초기값: 지금까지의 평균
                sma_values.append(sum(prices[:i + 1]) / (i + 1))
            else:
                # 정상 SMA 계산
                sma_values.append(sum(prices[i - period + 1:i + 1]) / period)
        
        return sma_values
    
    def calculate_ema(self, prices, period):
        """지수이동평균 계산"""
        if not prices:
            return []
        
        alpha = 2 / (period + 1)
        ema_values = [prices[0]]  # 첫 번째 값은 그대로
        
        for i in range(1, len(prices)):
            ema = alpha * prices[i] + (1 - alpha) * ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        if len(prices) < period + 1:
            return [50] * len(prices)  # 데이터 부족시 중간값 반환
        
        # 가격 변화 계산
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        
        # 상승과 하락 분리
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        # 초기 평균
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = [50]  # 첫 번째 값
        
        # RSI 계산
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        # 부족한 초기값들 채움
        while len(rsi_values) < len(prices):
            rsi_values.insert(0, 50)
        
        return rsi_values
    
    def calculate_macd(self, prices):
        """MACD 계산 (12일 EMA - 26일 EMA)"""
        ema12 = self.calculate_ema(prices, 12)
        ema26 = self.calculate_ema(prices, 26)
        
        macd = [ema12[i] - ema26[i] for i in range(len(prices))]
        return macd
    
    def calculate_cross_trigger_points(self, base_data, external_data, operator):
        """두 변수간 크로스 트리거 포인트 계산"""
        if not base_data or not external_data:
            return []
        
        trigger_points = []
        min_length = min(len(base_data), len(external_data))
        
        for i in range(1, min_length):  # 이전값과 비교하므로 1부터 시작
            prev_base = base_data[i - 1]
            curr_base = base_data[i]
            prev_external = external_data[i - 1]
            curr_external = external_data[i]
            
            # 크로스 감지
            if operator == '>':
                # 골든 크로스: 기본 변수가 외부 변수를 위로 돌파
                if prev_base <= prev_external and curr_base > curr_external:
                    trigger_points.append(i)
            elif operator == '<':
                # 데드 크로스: 기본 변수가 외부 변수를 아래로 돌파
                if prev_base >= prev_external and curr_base < curr_external:
                    trigger_points.append(i)
            elif operator == '>=':
                if prev_base < prev_external and curr_base >= curr_external:
                    trigger_points.append(i)
            elif operator == '<=':
                if prev_base > prev_external and curr_base <= curr_external:
                    trigger_points.append(i)
        
        print(f"🎯 크로스 트리거 포인트 계산: {operator}")
        print(f"   기본 변수 범위: {min(base_data):.2f} ~ {max(base_data):.2f}")
        print(f"   외부 변수 범위: {min(external_data):.2f} ~ {max(external_data):.2f}")
        print(f"   크로스 신호: {len(trigger_points)}개")
        
        return trigger_points

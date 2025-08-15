"""
누락된 usage 카테고리 추가 스크립트
"""

import sqlite3
from datetime import datetime

def add_missing_usage_categories():
    """누락된 usage 카테고리 추가"""

    with sqlite3.connect("data/settings.sqlite3") as conn:
        cursor = conn.cursor()

        # usage 카테고리 누락 변수들 찾기
        cursor.execute("""
            SELECT DISTINCT variable_id
            FROM tv_variable_help_documents
            WHERE variable_id NOT IN (
                SELECT variable_id FROM tv_variable_help_documents WHERE help_category = 'usage'
            )
            ORDER BY variable_id
        """)
        missing_vars = [row[0] for row in cursor.fetchall()]

        print(f"📊 usage 카테고리 누락 변수: {len(missing_vars)}개")

        for variable_id in missing_vars:
            # concept 문서의 내용을 복사해서 usage 문서 생성
            cursor.execute("""
                SELECT title_ko, content_ko
                FROM tv_variable_help_documents
                WHERE variable_id = ? AND help_category = 'concept'
                LIMIT 1
            """, (variable_id,))

            concept_data = cursor.fetchone()
            if not concept_data:
                print(f"⚠️  concept 문서 없음: {variable_id}")
                continue

            concept_title, concept_content = concept_data

            # usage용 제목과 내용 생성
            usage_title = f"{variable_id} 활용 전략"
            usage_content = f"""## 🎯 전략 구성 방법

### 1. 조건 설정 예시
```
{variable_id} > 기준값 일 때 매수
{variable_id} < 기준값 일 때 매도
```

### 2. 다른 지표와 조합
- **추세 확인**: SMA, EMA와 함께 사용
- **모멘텀 확인**: RSI, MACD와 조합
- **변동성 체크**: ATR, 볼린저밴드 참고

### 3. 리스크 관리
- 단일 지표만으로 판단 금지
- 시장 상황 고려 필수
- 손절 조건 반드시 설정

⚠️ **주의**: 과거 데이터 기반이므로 미래를 보장하지 않습니다."""

            # usage 문서 삽입
            cursor.execute("""
                INSERT INTO tv_variable_help_documents
                (variable_id, help_category, content_type, title_ko, content_ko, display_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                variable_id, 'usage', 'markdown', usage_title, usage_content,
                2, datetime.now(), datetime.now()
            ))

            print(f"✅ usage 문서 추가: {variable_id}")

        conn.commit()
        print(f"🎉 완료: {len(missing_vars)}개 변수에 usage 카테고리 추가")

if __name__ == "__main__":
    add_missing_usage_categories()

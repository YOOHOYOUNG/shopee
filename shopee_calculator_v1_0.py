import pandas as pd
import math
import streamlit as st
import requests

# 국가별 요율 정보
countries_data = {
    'Country': ['Singapore', 'Malaysia', 'Thailand', 'Vietnam',
                'Philippines', 'Indonesia', 'Taiwan', 'Brazil'],
    'Currency': ['SGD', 'MYR', 'THB', 'VND',
                 'PHP', 'IDR', 'TWD', 'BRL'],
    'Shopee Commission': [0.04, 0.0432, 0.0642, 0.09,
                          0.0448, 0.054, 0.045, 0.16],
    # VAT 제거: Shopee KRSC에서 자동으로 세금이 추가되므로 별도로 계산하지 않습니다.
    'PG Fee': [0.02] * 8
}

countries_df = pd.DataFrame(countries_data)

# 업데이트된 무게별 배송비 구조
updated_shipping_fee_structure = {
    'Singapore': [
        (500, 5000), (1000, 7000), (1500, 9000),
        (2000, 11000), (2500, 13000), (3000, 15000),
        ('above', 2000)
    ],
    'Malaysia': [
        (500, 5500), (1000, 7500), (1500, 9500),
        (2000, 11500), (2500, 13500), (3000, 15500),
        ('above', 2000)
    ],
    'Philippines': [
        (500, 7000), (1000, 9000), (1500, 11000),
        (2000, 13000), (2500, 15000), (3000, 17000),
        ('above', 2000)
    ],
    'Thailand': [
        (500, 6000), (1000, 8000), (1500, 10000),
        (2000, 12000), (2500, 14000), (3000, 16000),
        ('above', 2000)
    ],
    'Vietnam': [
        (500, 6500), (1000, 8500), (1500, 10500),
        (2000, 12500), (2500, 14500), (3000, 16500),
        ('above', 2000)
    ],
    'Indonesia': [
        (500, 7500), (1000, 9500), (1500, 11500),
        (2000, 13500), (2500, 15500), (3000, 17500),
        ('above', 2000)
    ],
    'Taiwan': [
        (500, 5500), (1000, 7500), (1500, 9500),
        (2000, 11500), (2500, 13500), (3000, 15500),
        ('above', 2000)
    ],
    'Brazil': [
        (500, 15000), (1000, 20000), (1500, 25000),
        (2000, 30000), (2500, 35000), (3000, 40000),
        ('above', 5000)
    ]
}

def calculate_updated_shipping_fee(country, weight):
    """업데이트된 국가와 무게에 따른 배송비 계산."""
    fees = updated_shipping_fee_structure[country]
    for limit, fee in fees:
        if limit == 'above':
            additional_weight = max(0, weight - 3000)
            additional_fee = ((additional_weight // 500) + 1) * fee
            return fees[-2][1] + additional_fee
        if weight <= limit:
            return fee
    return fees[-1][1]

def calculate_required_price_for_margin(total_cost, target_margin=30, discount_rate=30):
    """할인 후에도 지정된 마진을 유지하기 위한 최소 판매가 계산."""
    M = target_margin / 100  # 목표 마진율
    D = discount_rate / 100  # 할인율
    required_price = total_cost / ((1 - M) * (1 - D))
    return required_price

def round_up_to_nearest(value, unit):
    """지정된 단위로 올림."""
    return int(math.ceil(value / unit)) * unit

def calculate_full_price_info_debug(row, country_data, exchange_rates,
                                    target_margin=30, discount_rate=30):
    """개별 상품의 모든 가격 정보를 포함한 데이터 생성."""
    country = country_data['Country']
    currency = country_data['Currency']
    exchange_rate = exchange_rates.get(currency)
    if not exchange_rate:
        exchange_rate = 1  # 환율 정보가 없을 경우 기본값 설정
    weight = row['Weight (g)']
    shipping_fee_krw = calculate_updated_shipping_fee(country, weight)

    # 원가, 한국 배송비 및 국제 배송비 포함한 총 원가 계산
    total_cost = (row['Cost (KRW)'] +
                  row['Korean Shipping Fee (KRW)'] +
                  shipping_fee_krw)

    # 추가 비용: 수수료, PG Fee (VAT 제외)
    commission = country_data['Shopee Commission'] * total_cost
    pg_fee = country_data['PG Fee'] * total_cost

    # 최종 총 비용 (VAT 제외)
    final_total_cost = total_cost + commission + pg_fee

    # 가격 반올림 (10원 단위)
    final_total_cost = round_up_to_nearest(final_total_cost, 10)

    # 순익을 위한 최소 판매가 계산 (할인율 적용)
    required_price = calculate_required_price_for_margin(
        final_total_cost, target_margin, discount_rate)

    # 가격 반올림 (10원 단위)
    required_price = round_up_to_nearest(required_price, 10)

    # 현지 통화로 가격 변환 (KRW -> 현지 통화)
    price_in_local_currency = required_price * exchange_rate

    # 현지 통화 가격 올림 (정수 단위)
    price_in_local_currency = math.ceil(price_in_local_currency)

    # 반환 데이터 재구성
    return {
        '상품명': row['Product Name'],
        '국가': country,
        '현지 통화': currency,
        '원가 (KRW)': int(row['Cost (KRW)']),
        '한국 배송비 (KRW)': int(row['Korean Shipping Fee (KRW)']),
        '무게 (g)': int(weight),
        '국제 배송비 (KRW)': int(shipping_fee_krw),
        '총 원가 (KRW)': int(total_cost),
        'Shopee 수수료 (KRW)': int(commission),
        'PG 수수료 (KRW)': int(pg_fee),
        '최종 원가 (KRW)': int(final_total_cost),
        '목표 마진 최소 판매가 (KRW)': int(required_price),
        '현지 통화 최소 판매가': int(price_in_local_currency)
    }

# 환율 정보 가져오기
def get_exchange_rates():
    """실시간 환율 정보를 API로부터 가져옵니다."""
    url = "https://open.er-api.com/v6/latest/KRW"  # 무료로 사용할 수 있는 환율 API
    try:
        response = requests.get(url)
        data = response.json()
        if data['result'] == 'success':
            rates = data['rates']
            return rates
        else:
            st.error("환율 정보를 가져오는 데 실패했습니다.")
            return {}
    except Exception as e:
        st.error("환율 정보를 가져오는 도중 오류가 발생했습니다.")
        return {}
def main():

    # Streamlit을 활용한 UI 구성
    st.title("Shopee 판매 가격 계산기")

    # 환율 정보 가져오기
    st.header("실시간 환율 정보 가져오는 중...")
    exchange_rates = get_exchange_rates()
    if exchange_rates:
        st.success("환율 정보를 성공적으로 가져왔습니다.")

        # 상품 정보 입력
        st.header("상품 정보 입력")
        product_name = st.text_input("상품명", value="과일나라 딸기")
        cost_krw = st.number_input("원가 (KRW)", min_value=0, value=9900, step=100)
        korean_shipping_fee_krw = st.number_input(
            "한국 배송비 (KRW)", min_value=0, value=2500, step=100)
        weight_g = st.number_input("무게 (g)", min_value=0, value=1000, step=100)
        target_margin_percent = st.number_input(
            "목표 마진 (%)", min_value=0, value=30, step=1)
        discount_rate = st.number_input("할인율 (%)", min_value=0, value=30, step=1)

        if st.button("계산하기"):
            if product_name and cost_krw and weight_g:
                product_data = {
                    'Product Name': [product_name],
                    'Cost (KRW)': [cost_krw],
                    'Korean Shipping Fee (KRW)': [korean_shipping_fee_krw],
                    'Weight (g)': [weight_g],
                }
                product_df = pd.DataFrame(product_data)

                # 계산 결과 저장
                rounded_debug_results = []
                for _, country_row in countries_df.iterrows():
                    for _, product_row in product_df.iterrows():
                        rounded_info_debug = calculate_full_price_info_debug(
                            product_row, country_row, exchange_rates,
                            target_margin=target_margin_percent,
                            discount_rate=discount_rate)
                        rounded_debug_results.append(rounded_info_debug)

                # 결과 데이터프레임 생성
                rounded_debug_results_df = pd.DataFrame(rounded_debug_results)

                # 금액 형식 설정
                pd.options.display.float_format = '{:,.0f}'.format

                # 상세 결과 표시
                st.header("상세 계산 결과")
                st.write(rounded_debug_results_df)

                # 요약 결과 생성
                summary_data = {
                    '상품명': [],
                    '목표 마진 최소 판매가 (KRW)': []
                }

                # 각 국가의 현지 통화 최소 판매가를 저장할 딕셔너리 초기화
                for currency in countries_df['Currency']:
                    summary_data[currency] = []

                # 상품별로 요약 데이터 생성
                for product in product_df['Product Name'].unique():
                    temp_df = rounded_debug_results_df[
                        rounded_debug_results_df['상품명'] == product]
                    summary_data['상품명'].append(product)
                    summary_data['목표 마진 최소 판매가 (KRW)'].append(
                        temp_df['목표 마진 최소 판매가 (KRW)'].iloc[0])

                    for currency in countries_df['Currency']:
                        price = temp_df[temp_df['현지 통화'] == currency][
                            '현지 통화 최소 판매가'].values[0]
                        summary_data[currency].append(price)

                summary_df = pd.DataFrame(summary_data)

                # 요약 결과 표시
                st.header("요약 결과")
                st.write(summary_df)
            else:
                st.error("모든 필드를 입력해주세요.")
    else:
        st.error("환율 정보를 가져오지 못해 계산을 진행할 수 없습니다.")


if __name__ == "__main__":
    main()
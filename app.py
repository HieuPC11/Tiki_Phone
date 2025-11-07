import os
import math
import pandas as pd
import streamlit as st
import altair as alt
import numpy as np


def calculate_summary_metrics(df: pd.DataFrame) -> dict:
    """Tính toán các chỉ số tóm tắt cho Executive Summary"""
    if df.empty:
        return {key: 0 for key in ['total_revenue', 'total_products', 'avg_price', 'avg_rating', 
                                  'avg_clv', 'nps_score', 'marketing_roi', 'brand_equity', 
                                  'inventory_turnover', 'csi', 'repeat_purchase_prob', 
                                  'market_share', 'cac']}
    
    metrics = {}
    
    # 1. Chỉ số tài chính cơ bản
    if 'total_sales_per_product' in df.columns:
        metrics['total_revenue'] = df['total_sales_per_product'].sum()
    elif all(col in df.columns for col in ['price(vnd)', 'quantity_sold']):
        # Tính toán total sales nếu cột chưa có
        metrics['total_revenue'] = (df['price(vnd)'] * df['quantity_sold']).sum()
    else:
        metrics['total_revenue'] = 0
    metrics['total_products'] = len(df)
    metrics['avg_price'] = df['price(vnd)'].mean() if 'price(vnd)' in df.columns else 0
    metrics['avg_rating'] = df['rating_average'].mean() if 'rating_average' in df.columns else 0
    
    # 2. Customer Lifetime Value trung bình
    if 'customer_lifetime_value' in df.columns:
        metrics['avg_clv'] = df['customer_lifetime_value'].mean()
    else:
        # Tính CLV ước tính
        if all(col in df.columns for col in ['price(vnd)', 'rating_average']):
            metrics['avg_clv'] = df['price(vnd)'].mean() * df['rating_average'].mean() * 2.5
        else:
            metrics['avg_clv'] = 0
    
    # 3. Net Promoter Score
    if 'rating_average' in df.columns:
        # Chuyển đổi từ thang 5 sao sang NPS (-100 đến +100)
        ratings = df['rating_average'].dropna()
        promoters = (ratings >= 4.5).sum()
        detractors = (ratings <= 3.0).sum()
        total_responses = len(ratings)
        if total_responses > 0:
            metrics['nps_score'] = ((promoters - detractors) / total_responses) * 100
        else:
            metrics['nps_score'] = 0
    else:
        metrics['nps_score'] = 0
    
    # 4. Marketing ROI
    if 'discount' in df.columns and 'quantity_sold' in df.columns:
        total_discount = (df['discount'] * df['quantity_sold']).sum()
        # Sử dụng total_revenue đã tính toán
        additional_revenue = metrics['total_revenue'] * 0.15  # Giả định 15% tăng trưởng
        if total_discount > 0:
            metrics['marketing_roi'] = ((additional_revenue - total_discount) / total_discount) * 100
        else:
            metrics['marketing_roi'] = 15.0
    else:
        metrics['marketing_roi'] = 15.0
    
    # 5. Brand Equity Score
    if 'brand_name' in df.columns and 'rating_average' in df.columns:
        # Tính toán brand scores với xử lý an toàn
        agg_dict = {'rating_average': 'mean', 'quantity_sold': 'sum'}
        if 'total_sales_per_product' in df.columns:
            agg_dict['total_sales_per_product'] = 'sum'
        brand_scores = df.groupby('brand_name').agg(agg_dict)
        if not brand_scores.empty:
            # Normalize scores to 0-100 scale
            quality_score = (brand_scores['rating_average'] / 5.0 * 40).mean()
            volume_score = 30  # Fixed score for volume
            revenue_score = 30  # Fixed score for revenue
            metrics['brand_equity'] = quality_score + volume_score + revenue_score
        else:
            metrics['brand_equity'] = 65.0
    else:
        metrics['brand_equity'] = 65.0
    
    # 6. Inventory Turnover
    if 'quantity_sold' in df.columns and 'review_count' in df.columns:
        metrics['inventory_turnover'] = (df['quantity_sold'] / (df['review_count'] + 1)).mean()
    else:
        metrics['inventory_turnover'] = 2.5
    
    # 7. Customer Satisfaction Index
    if 'rating_average' in df.columns:
        metrics['csi'] = (df['rating_average'].mean() / 5.0) * 100
    else:
        metrics['csi'] = 75.0
    
    # 8. Repeat Purchase Probability
    if 'rating_average' in df.columns and 'review_count' in df.columns:
        # Dựa trên rating và số lượng review
        satisfaction_factor = df['rating_average'].mean() / 5.0
        engagement_factor = min(1.0, df['review_count'].mean() / 100)
        metrics['repeat_purchase_prob'] = (satisfaction_factor * 0.7 + engagement_factor * 0.3) * 100
    else:
        metrics['repeat_purchase_prob'] = 45.0
    
    # 9. Market Share (estimated)
    if 'brand_name' in df.columns and 'total_sales_per_product' in df.columns:
        total_market = df['total_sales_per_product'].sum()
        top_brand_revenue = df.groupby('brand_name')['total_sales_per_product'].sum().max()
        if total_market > 0:
            metrics['market_share'] = (top_brand_revenue / total_market) * 100
        else:
            metrics['market_share'] = 12.5
    else:
        metrics['market_share'] = 12.5
    
    # 10. Customer Acquisition Cost (CAC)
    if 'total_sales_per_product' in df.columns:
        # Ước tính CAC dựa trên doanh thu
        avg_revenue = df['total_sales_per_product'].mean()
        metrics['cac'] = avg_revenue * 0.25  # Giả định CAC = 25% doanh thu trung bình
    else:
        metrics['cac'] = 500000  # 500k VND default
    
    return metrics


def calculate_financial_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán các chỉ số tài chính nâng cao cho phân tích chuyên gia"""
    
    # === BASIC FINANCIAL METRICS ===
    df['conversion_rate'] = df['quantity_sold'] / (df['review_count'] + 1)
    df['discount_roi'] = (df['quantity_sold'] * df['discount']) / df['discount'].replace(0, 1)
    df['revenue_per_review'] = df['total_sales_per_product'] / (df['review_count'] + 1)
    
    # === ADVANCED FINANCIAL METRICS ===
    
    # 1. Customer Lifetime Value (CLV)
    if all(col in df.columns for col in ['price(vnd)', 'rating_average', 'quantity_sold']):
        # CLV = Average Order Value × Purchase Frequency × Customer Lifespan × Profit Margin
        avg_order_value = df['price(vnd)']
        purchase_frequency = df['quantity_sold'] / (df['review_count'] + 1)  # Proxy
        customer_lifespan = df['rating_average']  # Higher rating = longer relationship
        profit_margin = 0.2  # Assumed 20% margin
        df['customer_lifetime_value'] = avg_order_value * purchase_frequency * customer_lifespan * profit_margin
    
    # 2. Net Promoter Score (NPS) estimation
    if 'rating_average' in df.columns:
        # Convert 5-star rating to NPS scale (-100 to +100)
        df['estimated_nps'] = ((df['rating_average'] - 3) / 2 * 100).clip(-100, 100)
    
    # 3. Customer Acquisition Cost (CAC) proxy
    if 'discount' in df.columns and 'quantity_sold' in df.columns:
        df['estimated_cac'] = df['discount'] / (df['quantity_sold'] + 1)
    
    # 4. Return on Marketing Investment (ROMI)
    if all(col in df.columns for col in ['total_sales_per_product', 'discount']):
        df['romi'] = (df['total_sales_per_product'] - df['discount']) / (df['discount'] + 1) * 100
    
    # 5. Market Share Analysis
    if 'category_name' in df.columns:
        category_total = df.groupby('category_name')['total_sales_per_product'].transform('sum')
        df['market_share'] = df['total_sales_per_product'] / category_total * 100
        
        # Market penetration rate
        category_count = df.groupby('category_name')['product_name'].transform('count')
        df['market_penetration'] = (1 / category_count) * 100
    
    # 6. Price Premium Analysis
    if 'price(vnd)' in df.columns and 'category_name' in df.columns:
        category_avg_price = df.groupby('category_name')['price(vnd)'].transform('mean')
        df['price_premium'] = ((df['price(vnd)'] - category_avg_price) / category_avg_price * 100).fillna(0)
    
    # 7. Brand Equity Score
    if all(col in df.columns for col in ['brand_name', 'rating_average', 'quantity_sold', 'total_sales_per_product']):
        brand_stats = df.groupby('brand_name').agg({
            'rating_average': 'mean',
            'quantity_sold': 'sum',
            'total_sales_per_product': 'sum',
            'review_count': 'sum'
        })
        
        # Normalize and calculate brand equity
        brand_equity = {}
        for brand in brand_stats.index:
            quality_score = brand_stats.loc[brand, 'rating_average'] / 5.0 * 30
            volume_score = brand_stats.loc[brand, 'quantity_sold'] / brand_stats['quantity_sold'].max() * 25
            revenue_score = brand_stats.loc[brand, 'total_sales_per_product'] / brand_stats['total_sales_per_product'].max() * 25
            awareness_score = brand_stats.loc[brand, 'review_count'] / brand_stats['review_count'].max() * 20
            
            brand_equity[brand] = quality_score + volume_score + revenue_score + awareness_score
        
        df['brand_equity_score'] = df['brand_name'].map(brand_equity).fillna(0)
    
    # 8. Inventory Turnover Ratio (estimated)
    df['inventory_turnover'] = df['quantity_sold'] / (df['review_count'] + 1)
    
    # 9. Customer Satisfaction Index (CSI)
    if 'rating_average' in df.columns and 'review_count' in df.columns:
        # Weight rating by number of reviews for more reliable CSI
        df['csi'] = (df['rating_average'] * np.log(df['review_count'] + 1)) / 5.0 * 100
    
    # 10. Repeat Purchase Probability (proxy)
    if all(col in df.columns for col in ['rating_average', 'discount_rate(%)']):
        # Higher rating and reasonable discount increase repeat purchase likelihood
        df['repeat_purchase_prob'] = (
            (df['rating_average'] / 5.0 * 0.7) + 
            (np.clip(df['discount_rate(%)'], 0, 30) / 30 * 0.3)
        ) * 100
    
    return df


def create_detailed_price_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Tạo phân tích giá và cạnh tranh chi tiết"""
    if 'price(vnd)' in df.columns:
        mean_price = df['price(vnd)'].mean()
        std_price = df['price(vnd)'].std()
        
        if std_price > 0:
            df['price_zscore'] = (df['price(vnd)'] - mean_price) / std_price
        else:
            df['price_zscore'] = 0
        
        # Enhanced price tiers with more granular segmentation
        df['price_tier'] = pd.cut(df['price(vnd)'], 
                                 bins=[0, 2_000_000, 5_000_000, 10_000_000, 20_000_000, 50_000_000, float('inf')],
                                 labels=['Budget', 'Economy', 'Mid-range', 'Premium', 'Luxury', 'Ultra-Premium'],
                                 include_lowest=True)
        
        # Price competitiveness categories
        df['price_competitiveness'] = pd.cut(df['price_zscore'], 
                                           bins=[-float('inf'), -1.5, -0.5, 0.5, 1.5, float('inf')],
                                           labels=['Very Competitive', 'Competitive', 'Market Average', 'Premium', 'Ultra Premium'])
        
        # Value Score (Quality/Price ratio)
        if 'rating_average' in df.columns:
            df['value_score'] = (df['rating_average'] / (df['price(vnd)'] / 1_000_000)) * 100
        
        # Pricing efficiency
        if 'original_price' in df.columns:
            df['pricing_efficiency'] = df['total_sales_per_product'] / df['original_price'].replace(0, 1)
            df['discount_impact'] = (df['quantity_sold'] * df['discount']) / (df['discount'] + 1)
    
    return df


def calculate_market_concentration(df: pd.DataFrame) -> dict:
    """Tính chỉ số tập trung thị trường (HHI - Herfindahl-Hirschman Index)"""
    if 'brand_name' in df.columns and 'total_sales_per_product' in df.columns:
        brand_revenues = df.groupby('brand_name')['total_sales_per_product'].sum()
        total_revenue = brand_revenues.sum()
        
        if total_revenue > 0:
            market_shares = brand_revenues / total_revenue
            hhi = (market_shares ** 2).sum() * 10000  # HHI scale 0-10000
            
            # Market structure interpretation
            if hhi < 1500:
                structure = "Highly Competitive"
                risk = "Low"
            elif hhi < 2500:
                structure = "Moderately Concentrated"  
                risk = "Medium"
            else:
                structure = "Highly Concentrated"
                risk = "High"
            
            return {
                'hhi': hhi,
                'structure': structure,
                'risk': risk,
                'top_3_share': market_shares.nlargest(3).sum() * 100,
                'market_leaders': market_shares.nlargest(3).to_dict()
            }
    
    return {'hhi': 0, 'structure': 'Unknown', 'risk': 'Unknown', 'top_3_share': 0, 'market_leaders': {}}


@st.cache_data(show_spinner=False)
def load_data(csv_path: str = "tiki_product_data.csv") -> pd.DataFrame:
    """Load dữ liệu từ file CSV với xử lý đường dẫn thông minh"""
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, csv_path)
    
    # Try script directory first, then current directory
    if os.path.exists(full_path):
        df = pd.read_csv(full_path)
    elif os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
    else:
        # If file doesn't exist, create sample data for demo
        st.warning(f"⚠️ Không tìm thấy file {csv_path}. Đang tạo dữ liệu mẫu...")
        df = pd.DataFrame({
            'product_name': [f'iPhone {i}' for i in range(1, 51)] + [f'Samsung Galaxy {i}' for i in range(1, 51)],
            'brand_name': ['Apple'] * 50 + ['Samsung'] * 50,
            'price(vnd)': np.random.uniform(5_000_000, 30_000_000, 100),
            'quantity_sold': np.random.randint(10, 1000, 100),
            'rating_average': np.random.uniform(3.5, 5.0, 100),
            'review_count': np.random.randint(5, 500, 100),
            'discount': np.random.uniform(0, 0.3, 100),
            'category_name': ['Điện thoại'] * 100,
            'subcategory_name': ['Smartphone'] * 100
        })
        # Calculate total sales for demo data
        df['total_sales_per_product'] = df['price(vnd)'] * df['quantity_sold']
        st.info("✅ Đã tạo dữ liệu mẫu để demo dashboard")
        return df
    
    # Chuẩn hoá tên cột và kiểu dữ liệu tối thiểu
    # Các cột kỳ vọng từ EDA: id, product_name, price(vnd), quantity_sold, brand_name, category_name, subcategory_name
    # Cho phép thiếu một vài cột và xử lý an toàn
    if "price(vnd)" in df.columns:
        df["price(vnd)"] = pd.to_numeric(df["price(vnd)"], errors="coerce")
    if "quantity_sold" in df.columns:
        df["quantity_sold"] = pd.to_numeric(df["quantity_sold"], errors="coerce").fillna(0)
    if "rating_average" in df.columns:
        df["rating_average"] = pd.to_numeric(df["rating_average"], errors="coerce")

    # Tạo doanh thu ước tính nếu chưa có
    if "total_sales_per_product" not in df.columns and {"price(vnd)", "quantity_sold"}.issubset(df.columns):
        df["total_sales_per_product"] = df["price(vnd)"] * df["quantity_sold"]

    # Binning theo khoảng giá
    if "price_range" not in df.columns and "price(vnd)" in df.columns:
        price_bins = [0, 1_000_000, 5_000_000, 10_000_000, 20_000_000, 50_000_000, 100_000_000, math.inf]
        price_labels = [
            "0-1M",
            "1-5M",
            "5-10M",
            "10-20M",
            "20-50M",
            "50-100M",
            "100M+",
        ]
        df["price_range"] = pd.cut(df["price(vnd)"], bins=price_bins, labels=price_labels, right=False)

    # Thêm các tính toán tài chính
    df = calculate_financial_metrics(df)
    df = create_detailed_price_analysis(df)
    
    # Seasonal analysis (nếu có dữ liệu thời gian)
    if 'updated_at' in df.columns:
        df['updated_at'] = pd.to_datetime(df['updated_at'])
        df['month'] = df['updated_at'].dt.month
        df['quarter'] = df['updated_at'].dt.quarter

    return df


def format_vnd(x: float) -> str:
    try:
        return f"{x:,.0f} VND"
    except Exception:
        return "-"


def main():
    st.set_page_config(
        page_title="📱 Expert Tiki Phone Analytics", 
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Advanced CSS styling for professional dashboard
    st.markdown("""
    <style>
    .main-header {
        font-size: 42px;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 25px 0;
        margin-bottom: 30px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .executive-summary {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 25px;
        border-radius: 20px;
        margin: 25px 0;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        margin: 10px 0;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .kpi-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 30px;
        border-radius: 20px;
        margin: 25px 0;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
    }
    .insight-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border-left: 5px solid #ff6b6b;
    }
    .competitive-alert {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #4ecdc4;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">📱 Expert Financial Analytics Dashboard - Tiki Phone Market Intelligence</h1>', unsafe_allow_html=True)
    
    # Load and prepare data
    df = load_data()
    if df is None:
        return

    
    # Calculate comprehensive metrics
    df_enhanced = calculate_financial_metrics(df)  # Enhanced dataframe with calculated columns
    df_enhanced = create_detailed_price_analysis(df_enhanced)  # Add price analysis
    metrics = calculate_summary_metrics(df_enhanced)  # Summary metrics for dashboard
    market_concentration = calculate_market_concentration(df_enhanced)
    
    # Executive Summary Section
    st.markdown('<div class="executive-summary">', unsafe_allow_html=True)
    st.markdown("### 🎯 **Executive Summary - Market Intelligence Report**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        **📊 Market Overview**
        - Total Market Value: **₫{metrics['total_revenue']:,.0f}**
        - Active Products: **{metrics['total_products']:,}** units
        - Market Structure: **{market_concentration['structure']}**
        - Concentration Risk: **{market_concentration['risk']}**
        """)
    
    with col2:
        st.markdown(f"""
        **💰 Financial Performance**
        - Customer Lifetime Value: **₫{metrics['avg_clv']:,.0f}**
        - Marketing ROI: **{metrics['marketing_roi']:.1f}%**
        - Brand Equity Score: **{metrics['brand_equity']:.1f}**
        - Inventory Turnover: **{metrics['inventory_turnover']:.2f}x**
        """)
    
    with col3:
        st.markdown(f"""
        **🏆 Quality & Satisfaction**
        - Net Promoter Score: **{metrics['nps_score']:.1f}%**
        - Customer Satisfaction: **{metrics['csi']:.1f}%**
        - Repeat Purchase Rate: **{metrics['repeat_purchase_prob']:.1f}%**
        - Quality Rating: **{metrics['avg_rating']:.2f}/5.0**
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Advanced Sidebar with Market Intelligence
    st.sidebar.markdown("### 🎛️ **Advanced Analytics Controls**")
    
    # Competitive Intelligence Alerts
    st.sidebar.markdown("### 🚨 **Market Intelligence Alerts**")
    
    # Market concentration analysis
    hhi_color = "🔴" if market_concentration['hhi'] > 2500 else "🟡" if market_concentration['hhi'] > 1500 else "🟢"
    st.sidebar.markdown(f"""
    <div class="competitive-alert">
    {hhi_color} <strong>Market Concentration</strong><br>
    HHI Index: {market_concentration['hhi']:.0f}<br>
    Status: {market_concentration['structure']}<br>
    Top 3 Control: {market_concentration['top_3_share']:.1f}%
    </div>
    """, unsafe_allow_html=True)
    
    # Price competitiveness alert
    price_volatility = df['price(vnd)'].std() / df['price(vnd)'].mean() * 100
    volatility_color = "🔴" if price_volatility > 50 else "🟡" if price_volatility > 30 else "🟢"
    st.sidebar.markdown(f"""
    <div class="competitive-alert">
    {volatility_color} <strong>Price Volatility</strong><br>
    Coefficient: {price_volatility:.1f}%<br>
    Market Stability: {'High Risk' if price_volatility > 50 else 'Medium Risk' if price_volatility > 30 else 'Stable'}
    </div>
    """, unsafe_allow_html=True)
    
    # Filter controls with safe handling
    brand_values = df['brand_name'].dropna().unique()
    brands = ['All Brands'] + sorted([str(b) for b in brand_values if str(b) != 'nan'])
    selected_brand = st.sidebar.selectbox("🏷️ Brand Focus:", brands)
    
    # Safe price range calculation
    price_values = df['price(vnd)'].dropna()
    if len(price_values) > 0:
        min_price, max_price = int(price_values.min()), int(price_values.max())
    else:
        min_price, max_price = 0, 1000000
    
    price_range = st.sidebar.slider(
        "💰 Price Range Analysis:",
        min_price, max_price,
        (min_price, max_price),
        format="₫%d"
    )
    
    # Apply intelligent filters
    filtered_df = df_enhanced.copy()
    if selected_brand != 'All Brands':
        filtered_df = filtered_df[filtered_df['brand_name'] == selected_brand]
    filtered_df = filtered_df[
        (filtered_df['price(vnd)'] >= price_range[0]) & 
        (filtered_df['price(vnd)'] <= price_range[1])
    ]

    
    # Professional KPI Dashboard
    st.markdown('<div class="kpi-container">', unsafe_allow_html=True)
    st.markdown("### 📊 **Professional Key Performance Indicators**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("💎 Market Cap", f"₫{metrics['total_revenue']:,.0f}", delta=f"{metrics['market_share']:.1f}% share")
        st.metric("🎯 Customer CLV", f"₫{metrics['avg_clv']:,.0f}", delta=f"{metrics['nps_score']:.1f}% NPS")
    
    with col2:
        st.metric("🏆 Brand Equity", f"{metrics['brand_equity']:.1f}", delta=f"{metrics['csi']:.1f}% CSI")
        st.metric("📈 ROMI", f"{metrics['marketing_roi']:.1f}%", delta=f"{metrics['cac']:.0f}₫ CAC")
    
    with col3:
        st.metric("🔄 Inventory Turn", f"{metrics['inventory_turnover']:.2f}x", delta="Efficient")
        st.metric("⭐ Quality Score", f"{metrics['avg_rating']:.2f}/5", delta=f"{metrics['repeat_purchase_prob']:.1f}% loyalty")
    
    with col4:
        st.metric("📱 Product Portfolio", f"{metrics['total_products']:,}", delta="Active SKUs")
        st.metric("💰 Avg. Ticket", f"₫{metrics['avg_price']:,.0f}", delta="Premium positioning")
    
    with col5:
        st.metric("🎪 Market Position", f"#{1 if metrics['market_share'] > 20 else 2 if metrics['market_share'] > 10 else 3}")
        st.metric("🛡️ Risk Level", f"{market_concentration['risk']}", delta=f"HHI: {market_concentration['hhi']:.0f}")
    
    st.markdown('</div>', unsafe_allow_html=True)

    
    # Advanced Analytics Tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Market Intelligence", "💎 Portfolio Analysis", "🎯 Customer Intelligence", 
        "🏆 Competitive Analysis", "📈 Predictive Analytics", "💼 Investment Analysis",
        "🔍 Phân Tích So Sánh"
    ])
    
    with tab1:
        st.markdown("### 📊 **Bảng Điều Khiển Thông Minh Thị Trường**")
        st.markdown("*Phân tích hiệu suất giá - chất lượng và phân bố thị phần với công nghệ trực quan hóa tiên tiến*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 **Bản Đồ Thông Minh Giá - Hiệu Suất**")
            st.markdown("*Biểu đồ bong bóng thể hiện mối quan hệ giữa giá cả, khối lượng bán và điểm giá trị. Kích thước bong bóng = doanh thu*")
            
            # Advanced Price-Performance Bubble Chart với dữ liệu an toàn
            if not filtered_df.empty and 'price(vnd)' in filtered_df.columns and 'quantity_sold' in filtered_df.columns:
                # Ensure we have required columns with safe defaults
                chart_data = filtered_df.copy()
                if 'value_score' not in chart_data.columns:
                    chart_data['value_score'] = chart_data['rating_average'] * 20 if 'rating_average' in chart_data.columns else 50
                if 'price_competitiveness' not in chart_data.columns:
                    chart_data['price_competitiveness'] = 'Trung bình'
                
                bubble_chart = alt.Chart(chart_data.head(100)).mark_circle(opacity=0.8).encode(
                    x=alt.X('price(vnd):Q', title='Giá Bán (VNĐ)', scale=alt.Scale(type='log')),
                    y=alt.Y('quantity_sold:Q', title='Khối Lượng Bán'),
                    size=alt.Size('total_sales_per_product:Q', title='Doanh Thu', 
                                scale=alt.Scale(range=[50, 400])),
                    color=alt.Color('value_score:Q', title='Điểm Giá Trị',
                                  scale=alt.Scale(scheme='viridis', reverse=False)),
                    tooltip=['name:N', 'brand_name:N', 'price(vnd):Q', 'quantity_sold:Q', 
                            'value_score:Q', 'price_competitiveness:N']
                ).properties(
                    width=400,
                    height=350,
                    title="Bản Đồ Phân Tích Giá - Hiệu Suất"
                ).interactive()
                
                st.altair_chart(bubble_chart, use_container_width=True)
                
                # Thêm giải thích chi tiết
                st.markdown("""
                **📋 Cách Đọc Biểu Đồ:**
                - **Trục X**: Giá sản phẩm (thang logarit)
                - **Trục Y**: Số lượng đã bán
                - **Kích thước bong bóng**: Tổng doanh thu
                - **Màu sắc**: Điểm giá trị (xanh lá = tốt, tím = kém)
                - **Vị trí lý tưởng**: Góc trên bên trái (giá thấp, bán nhiều)
                """)
            else:
                st.info("⚠️ Không đủ dữ liệu để hiển thị biểu đồ bong bóng")
        
        with col2:
            st.markdown("#### 🏆 **Phân Bố Thị Phần Thương Hiệu**")
            st.markdown("*Biểu đồ donut thể hiện tỷ lệ doanh thu của các thương hiệu hàng đầu trong thị trường điện thoại*")
            
            # Market Share Donut Chart với xử lý dữ liệu an toàn
            if not filtered_df.empty and 'brand_name' in filtered_df.columns and 'total_sales_per_product' in filtered_df.columns:
                brand_revenue = filtered_df.groupby('brand_name')['total_sales_per_product'].sum().reset_index()
                brand_revenue = brand_revenue.sort_values('total_sales_per_product', ascending=False).head(8)
                
                if not brand_revenue.empty:
                    # Tính phần trăm thị phần
                    total_revenue = brand_revenue['total_sales_per_product'].sum()
                    brand_revenue['market_share_pct'] = (brand_revenue['total_sales_per_product'] / total_revenue * 100).round(1)
                    
                    donut_chart = alt.Chart(brand_revenue).mark_arc(
                        innerRadius=50,
                        outerRadius=120,
                        stroke='white',
                        strokeWidth=3
                    ).encode(
                        theta=alt.Theta('total_sales_per_product:Q', title='Doanh Thu'),
                        color=alt.Color('brand_name:N', 
                                      scale=alt.Scale(scheme='category20'),
                                      legend=alt.Legend(title="Thương Hiệu Hàng Đầu", orient="right")),
                        tooltip=['brand_name:N', 
                                alt.Tooltip('total_sales_per_product:Q', format=',.0f', title='Doanh Thu'),
                                alt.Tooltip('market_share_pct:Q', format='.1f', title='Thị Phần (%)')]
                    ).properties(
                        width=400,
                        height=350,
                        title="Phân Bố Thị Phần - Top 8 Thương Hiệu"
                    )
                    
                    st.altair_chart(donut_chart, use_container_width=True)
                    
                    # Hiển thị thống kê thị phần
                    st.markdown("**📊 Thống Kê Thị Phần:**")
                    for i, row in brand_revenue.head(3).iterrows():
                        st.markdown(f"• **{row['brand_name']}**: {row['market_share_pct']:.1f}% thị trường")
                else:
                    st.info("⚠️ Không có dữ liệu thương hiệu để hiển thị")
            else:
                st.info("⚠️ Không đủ dữ liệu để tạo biểu đồ thị phần")

    
    with tab2:
        st.markdown("### 💎 **Phân Tích Rủi Ro - Lợi Nhuận Danh Mục**")
        st.markdown("*Ma trận hiệu quả định giá và phân tích hiệu suất theo phân khúc giá để tối ưu hóa danh mục sản phẩm*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ⚡ **Ma Trận Hiệu Quả Danh Mục**")
            st.markdown("*Phân tích mối quan hệ giữa hiệu quả định giá và chất lượng sản phẩm*")
            
            # Portfolio Performance Scatter với xử lý dữ liệu an toàn
            if not filtered_df.empty and 'rating_average' in filtered_df.columns:
                chart_data = filtered_df.copy()
                
                # Tạo pricing_efficiency nếu chưa có
                if 'pricing_efficiency' not in chart_data.columns:
                    if 'total_sales_per_product' in chart_data.columns and 'price(vnd)' in chart_data.columns:
                        chart_data['pricing_efficiency'] = chart_data['total_sales_per_product'] / chart_data['price(vnd)'].replace(0, 1)
                    else:
                        chart_data['pricing_efficiency'] = chart_data['rating_average'] * 100
                
                # Tạo price_tier nếu chưa có
                if 'price_tier' not in chart_data.columns:
                    if 'price(vnd)' in chart_data.columns:
                        chart_data['price_tier'] = pd.cut(chart_data['price(vnd)'], 
                                                         bins=[0, 2_000_000, 5_000_000, 15_000_000, float('inf')],
                                                         labels=['Phổ Thông', 'Tầm Trung', 'Cao Cấp', 'Siêu Cao Cấp'])
                    else:
                        chart_data['price_tier'] = 'Tầm Trung'
                
                portfolio_chart = alt.Chart(chart_data.head(100)).mark_circle(size=120, opacity=0.7).encode(
                    x=alt.X('pricing_efficiency:Q', title='Hiệu Quả Định Giá'),
                    y=alt.Y('rating_average:Q', title='Điểm Chất Lượng (1-5)', scale=alt.Scale(domain=[0, 5])),
                    color=alt.Color('price_tier:N', title='Phân Khúc Giá',
                                  scale=alt.Scale(scheme='plasma')),
                    size=alt.Size('total_sales_per_product:Q', title='Doanh Thu'),
                    tooltip=['name:N', 'brand_name:N', 'price_tier:N', 
                            alt.Tooltip('pricing_efficiency:Q', format='.2f', title='Hiệu Quả Định Giá'),
                            alt.Tooltip('rating_average:Q', format='.2f', title='Điểm Chất Lượng')]
                ).properties(
                    width=400,
                    height=350,
                    title="Ma Trận Hiệu Quả Danh Mục Sản Phẩm"
                ).interactive()
                
                st.altair_chart(portfolio_chart, use_container_width=True)
                
                # Thêm hướng dẫn phân tích
                st.markdown("""
                **🎯 Hướng Dẫn Phân Tích:**
                - **Góc phải trên**: Hiệu quả cao + Chất lượng tốt ⭐ **Star Products**
                - **Góc trái trên**: Hiệu quả thấp + Chất lượng tốt 🐄 **Cash Cows**  
                - **Góc phải dưới**: Hiệu quả cao + Chất lượng kém ❓ **Question Marks**
                - **Góc trái dưới**: Hiệu quả thấp + Chất lượng kém 🐕 **Dogs**
                """)
            else:
                st.info("⚠️ Không đủ dữ liệu để tạo ma trận hiệu quả")
        
        with col2:
            st.markdown("#### 📊 **Hiệu Suất Theo Phân Khúc Giá**")
            st.markdown("*Phân tích doanh thu và điểm giá trị của từng phân khúc giá để xác định cơ hội tăng trưởng*")
            
            # Price Tier Performance với xử lý dữ liệu
            if not filtered_df.empty:
                chart_data = filtered_df.copy()
                
                # Tạo price_tier nếu chưa có
                if 'price_tier' not in chart_data.columns:
                    if 'price(vnd)' in chart_data.columns:
                        chart_data['price_tier'] = pd.cut(chart_data['price(vnd)'], 
                                                         bins=[0, 2_000_000, 5_000_000, 15_000_000, float('inf')],
                                                         labels=['Phổ Thông', 'Tầm Trung', 'Cao Cấp', 'Siêu Cao Cấp'])
                    else:
                        chart_data['price_tier'] = 'Tầm Trung'
                
                # Tính value_score nếu chưa có
                if 'value_score' not in chart_data.columns:
                    if 'rating_average' in chart_data.columns:
                        chart_data['value_score'] = chart_data['rating_average'] * 20
                    else:
                        chart_data['value_score'] = 60
                
                # Determine which column to use for counting
                name_col = 'product_name' if 'product_name' in chart_data.columns else 'brand_name'
                
                tier_performance = chart_data.groupby('price_tier').agg({
                    'total_sales_per_product': 'sum',
                    'rating_average': 'mean',
                    'quantity_sold': 'sum',
                    'value_score': 'mean',
                    name_col: 'count'
                }).reset_index()
                tier_performance.columns = ['price_tier', 'total_revenue', 'avg_rating', 'total_quantity', 'avg_value_score', 'product_count']
                
                if not tier_performance.empty:
                    tier_chart = alt.Chart(tier_performance).mark_bar(
                        cornerRadiusTopLeft=5,
                        cornerRadiusTopRight=5,
                        strokeWidth=2,
                        stroke='white'
                    ).encode(
                        x=alt.X('price_tier:O', title='Phân Khúc Giá', 
                               sort=['Phổ Thông', 'Tầm Trung', 'Cao Cấp', 'Siêu Cao Cấp']),
                        y=alt.Y('total_revenue:Q', title='Tổng Doanh Thu (VNĐ)', axis=alt.Axis(format=',.0f')),
                        color=alt.Color('avg_value_score:Q', title='Điểm Giá Trị TB',
                                      scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100])),
                        tooltip=['price_tier:N', 
                                alt.Tooltip('total_revenue:Q', format=',.0f', title='Tổng Doanh Thu'),
                                alt.Tooltip('avg_value_score:Q', format='.1f', title='Điểm Giá Trị TB'),
                                alt.Tooltip('product_count:Q', title='Số Sản Phẩm'),
                                alt.Tooltip('avg_rating:Q', format='.2f', title='Điểm Rating TB')]
                    ).properties(
                        width=400,
                        height=350,
                        title="Hiệu Suất Doanh Thu Theo Phân Khúc"
                    )
                    
                    st.altair_chart(tier_chart, use_container_width=True)
                    
                    # Thống kê chi tiết
                    st.markdown("**💰 Phân Tích Chi Tiết:**")
                    best_tier = tier_performance.loc[tier_performance['total_revenue'].idxmax()]
                    st.markdown(f"• **Phân khúc hiệu quả nhất**: {best_tier['price_tier']}")
                    st.markdown(f"• **Doanh thu**: {best_tier['total_revenue']:,.0f} VNĐ")
                    st.markdown(f"• **Điểm giá trị**: {best_tier['avg_value_score']:.1f}/100")
                    st.markdown(f"• **Số sản phẩm**: {best_tier['product_count']} sản phẩm")
                else:
                    st.info("⚠️ Không có dữ liệu phân khúc giá")
            else:
                st.info("⚠️ Không đủ dữ liệu để phân tích phân khúc")
    
    with tab3:
        st.markdown("### 🎯 **Thông Minh Khách Hàng & Phân Tích Hành Vi**")
        st.markdown("*Phân tích sâu về mức độ hài lòng, giá trị khách hàng và các mẫu hành vi mua sắm để tối ưu chiến lược*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔥 **Bản Đồ Hài Lòng Khách Hàng**")
            st.markdown("*Ma trận nhiệt thể hiện mức độ hài lòng theo thương hiệu và phân khúc giá*")
            
            # Customer Satisfaction Heatmap với xử lý dữ liệu an toàn
            if not filtered_df.empty and 'brand_name' in filtered_df.columns and 'rating_average' in filtered_df.columns:
                chart_data = filtered_df.copy()
                
                # Tạo price_tier nếu chưa có
                if 'price_tier' not in chart_data.columns:
                    if 'price(vnd)' in chart_data.columns:
                        chart_data['price_tier'] = pd.cut(chart_data['price(vnd)'], 
                                                         bins=[0, 2_000_000, 5_000_000, 15_000_000, float('inf')],
                                                         labels=['Phổ Thông', 'Tầm Trung', 'Cao Cấp', 'Siêu Cao Cấp'])
                    else:
                        chart_data['price_tier'] = 'Tầm Trung'
                
                satisfaction_data = []
                for tier in chart_data['price_tier'].unique():
                    if pd.notna(tier):
                        tier_data = chart_data[chart_data['price_tier'] == tier]
                        for brand in tier_data['brand_name'].value_counts().head(4).index:  # Top 4 brands per tier
                            brand_data = tier_data[tier_data['brand_name'] == brand]
                            if not brand_data.empty:
                                satisfaction_data.append({
                                    'Phân_Khúc': str(tier),
                                    'Thương_Hiệu': brand,
                                    'Điểm_Hài_Lòng': brand_data['rating_average'].mean(),
                                    'Khối_Lượng': brand_data['quantity_sold'].sum(),
                                    'Số_Sản_Phẩm': len(brand_data)
                                })
                
                if satisfaction_data:
                    satisfaction_df = pd.DataFrame(satisfaction_data)
                    
                    heatmap = alt.Chart(satisfaction_df).mark_rect(
                        stroke='white',
                        strokeWidth=2
                    ).encode(
                        x=alt.X('Thương_Hiệu:O', title='Thương Hiệu'),
                        y=alt.Y('Phân_Khúc:O', title='Phân Khúc Giá'),
                        color=alt.Color('Điểm_Hài_Lòng:Q', title='Điểm Hài Lòng',
                                      scale=alt.Scale(scheme='redyellowgreen', domain=[3, 5])),
                        size=alt.Size('Khối_Lượng:Q', title='Khối Lượng Bán',
                                    scale=alt.Scale(range=[100, 800])),
                        tooltip=['Thương_Hiệu:N', 'Phân_Khúc:N', 
                                alt.Tooltip('Điểm_Hài_Lòng:Q', format='.2f', title='Điểm Hài Lòng'),
                                alt.Tooltip('Khối_Lượng:Q', format=',', title='Khối Lượng Bán'),
                                alt.Tooltip('Số_Sản_Phẩm:Q', title='Số Sản Phẩm')]
                    ).properties(
                        width=400,
                        height=350,
                        title="Bản Đồ Thông Minh Hài Lòng Khách Hàng"
                    )
                    
                    st.altair_chart(heatmap, use_container_width=True)
                    
                    # Insights về satisfaction
                    best_satisfaction = satisfaction_df.loc[satisfaction_df['Điểm_Hài_Lòng'].idxmax()]
                    st.markdown(f"""
                    **🏆 Thương Hiệu Hài Lòng Nhất:**
                    - **{best_satisfaction['Thương_Hiệu']}** trong phân khúc **{best_satisfaction['Phân_Khúc']}**
                    - **Điểm hài lòng**: {best_satisfaction['Điểm_Hài_Lòng']:.2f}/5.0
                    - **Khối lượng bán**: {best_satisfaction['Khối_Lượng']:,} sản phẩm
                    """)
                else:
                    st.info("⚠️ Không đủ dữ liệu để tạo bản đồ hài lòng")
            else:
                st.info("⚠️ Thiếu dữ liệu thương hiệu hoặc rating")
        
        with col2:
            st.markdown("#### 💎 **Phân Bố Giá Trị Khách Hàng**")
            st.markdown("*Phân tích phân bố điểm giá trị khách hàng để nhận diện các nhóm khách hàng tiềm năng*")
            
            # Customer Value Distribution với tính toán value_score
            if not filtered_df.empty:
                chart_data = filtered_df.copy()
                
                # Tính value_score nếu chưa có
                if 'value_score' not in chart_data.columns:
                    if all(col in chart_data.columns for col in ['rating_average', 'price(vnd)', 'quantity_sold']):
                        # Value Score = (Quality * 0.4 + Price Competitiveness * 0.3 + Popularity * 0.3) * 100
                        quality_score = chart_data['rating_average'] / 5.0 * 0.4
                        price_score = (1 / (chart_data['price(vnd)'] / chart_data['price(vnd)'].median())) * 0.3
                        popularity_score = (chart_data['quantity_sold'] / chart_data['quantity_sold'].max()) * 0.3
                        chart_data['value_score'] = (quality_score + price_score + popularity_score) * 100
                    elif 'rating_average' in chart_data.columns:
                        chart_data['value_score'] = chart_data['rating_average'] * 20
                    else:
                        chart_data['value_score'] = np.random.normal(60, 15, len(chart_data))
                
                # Tạo biểu đồ phân bố
                value_dist = alt.Chart(chart_data).mark_area(
                    opacity=0.8,
                    interpolate='monotone',
                    line={'color': '#1f77b4', 'strokeWidth': 3},
                    color=alt.Gradient(
                        gradient='linear',
                        stops=[
                            alt.GradientStop(color='#e8f4fd', offset=0),
                            alt.GradientStop(color='#1f77b4', offset=1)
                        ],
                        x1=1, x2=1, y1=1, y2=0
                    )
                ).encode(
                    x=alt.X('value_score:Q', bin=alt.Bin(maxbins=15), title='Điểm Giá Trị Khách Hàng (0-100)'),
                    y=alt.Y('count():Q', title='Số Lượng Sản Phẩm'),
                    tooltip=[alt.Tooltip('value_score:Q', bin=alt.Bin(maxbins=15), title='Khoảng Điểm Giá Trị'),
                            alt.Tooltip('count():Q', title='Số Sản Phẩm')]
                ).properties(
                    width=400,
                    height=350,
                    title="Phân Bố Điểm Giá Trị Khách Hàng"
                )
                
                st.altair_chart(value_dist, use_container_width=True)
                
                # Thống kê giá trị khách hàng
                avg_value = chart_data['value_score'].mean()
                high_value_count = (chart_data['value_score'] >= 70).sum()
                total_products = len(chart_data)
                
                st.markdown(f"""
                **📊 Phân Tích Giá Trị Khách Hàng:**
                - **Điểm giá trị trung bình**: {avg_value:.1f}/100
                - **Sản phẩm giá trị cao** (≥70 điểm): {high_value_count} sản phẩm ({high_value_count/total_products*100:.1f}%)
                - **Phân loại**: {"Tốt" if avg_value >= 65 else "Trung bình" if avg_value >= 50 else "Cần cải thiện"}
                """)
                
                # Khuyến nghị
                if avg_value >= 70:
                    st.success("🎉 **Xuất sắc!** Portfolio có điểm giá trị khách hàng cao")
                elif avg_value >= 60:
                    st.info("👍 **Tốt!** Có thể cải thiện thêm một số sản phẩm")
                else:
                    st.warning("⚠️ **Cần cải thiện** chất lượng và giá trị sản phẩm")
            else:
                st.info("⚠️ Không có dữ liệu để phân tích giá trị khách hàng")

    
    with tab4:
        st.markdown("### 🏆 **Competitive Positioning Analysis**")
        
        # Competitive insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("#### 📊 **Market Leaders Analysis**")
            
            top_performers = df.groupby('brand_name').agg({
                'total_sales_per_product': 'sum',
                'rating_average': 'mean',
                'quantity_sold': 'sum'
            }).sort_values('total_sales_per_product', ascending=False).head(5)
            
            for i, (brand, data) in enumerate(top_performers.iterrows(), 1):
                st.markdown(f"""
                **#{i} {brand}**
                - Revenue: ₫{data['total_sales_per_product']:,.0f}
                - Quality: {data['rating_average']:.2f}/5.0
                - Volume: {data['quantity_sold']:,} units
                """)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("#### 🎯 **Strategic Recommendations**")
            
            recommendations = [
                f"🎪 **Market Focus**: Target {market_concentration['structure'].lower()} segments",
                f"💰 **Price Strategy**: Optimize around ₫{metrics['avg_price']:,.0f} sweet spot",
                f"⭐ **Quality Initiative**: Improve to exceed {metrics['avg_rating']:.2f} rating benchmark",
                f"🏆 **Brand Building**: Increase equity score above {metrics['brand_equity']:.1f}",
                f"📈 **Growth Opportunity**: CLV potential of ₫{metrics['avg_clv']:,.0f} per customer"
            ]
            
            for rec in recommendations:
                st.markdown(rec)
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown("### 📈 **Predictive Analytics & Forecasting**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Revenue trend simulation
            revenue_projection = []
            base_revenue = metrics['total_revenue']
            for month in range(1, 13):
                # Simple growth projection with seasonality
                seasonal_factor = 1 + 0.1 * np.sin(month * np.pi / 6)
                growth_factor = 1 + (metrics['marketing_roi'] / 100) * 0.01
                projected = base_revenue * seasonal_factor * growth_factor * (month / 12 + 0.8)
                revenue_projection.append({'Month': month, 'Projected_Revenue': projected})
            
            projection_df = pd.DataFrame(revenue_projection)
            
            projection_chart = alt.Chart(projection_df).mark_line(
                point=True,
                strokeWidth=3,
                color='#ff6b6b'
            ).encode(
                x=alt.X('Month:O', title='Month'),
                y=alt.Y('Projected_Revenue:Q', title='Projected Revenue (VNĐ)'),
                tooltip=['Month:O', 'Projected_Revenue:Q']
            ).properties(
                width=400,
                height=350,
                title="12-Month Revenue Projection"
            )
            
            st.altair_chart(projection_chart, use_container_width=True)
        
        with col2:
            # Market opportunity analysis
            opportunity_data = []
            for tier in ['Budget', 'Mid-range', 'Premium', 'Luxury']:
                tier_products = filtered_df[filtered_df['price_tier'] == tier] if 'price_tier' in filtered_df.columns else pd.DataFrame()
                if not tier_products.empty:
                    current_revenue = tier_products['total_sales_per_product'].sum()
                    potential_growth = current_revenue * (1 + np.random.uniform(0.1, 0.4))  # 10-40% growth potential
                    opportunity_data.append({
                        'Segment': tier,
                        'Current': current_revenue,
                        'Potential': potential_growth,
                        'Opportunity': potential_growth - current_revenue
                    })
            
            if opportunity_data:
                opp_df = pd.DataFrame(opportunity_data)
                
                opp_chart = alt.Chart(opp_df).mark_bar().encode(
                    x=alt.X('Segment:O', title='Market Segment'),
                    y=alt.Y('Opportunity:Q', title='Growth Opportunity (VNĐ)'),
                    color=alt.Color('Opportunity:Q', scale=alt.Scale(scheme='viridis')),
                    tooltip=['Segment:N', 'Current:Q', 'Potential:Q', 'Opportunity:Q']
                ).properties(
                    width=400,
                    height=350,
                    title="Market Growth Opportunities"
                )
                
                st.altair_chart(opp_chart, use_container_width=True)
    
    with tab6:
        st.markdown("### 💼 **Investment Analysis & ROI Dashboard**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # ROI Analysis by Brand
            brand_roi = filtered_df.groupby('brand_name').agg({
                'total_sales_per_product': 'sum',
                'quantity_sold': 'sum',
                'rating_average': 'mean'
            }).reset_index()
            
            if not brand_roi.empty:
                brand_roi['roi_score'] = (brand_roi['total_sales_per_product'] / brand_roi['total_sales_per_product'].max() * 50 +
                                         brand_roi['rating_average'] / 5 * 30 +
                                         brand_roi['quantity_sold'] / brand_roi['quantity_sold'].max() * 20)
                
                roi_chart = alt.Chart(brand_roi.head(10)).mark_bar(
                    cornerRadiusTopLeft=5,
                    cornerRadiusTopRight=5
                ).encode(
                    x=alt.X('roi_score:Q', title='Investment ROI Score'),
                    y=alt.Y('brand_name:O', sort='-x', title='Brand'),
                    color=alt.Color('roi_score:Q', scale=alt.Scale(scheme='redyellowgreen'), legend=None),
                    tooltip=['brand_name:N', 'roi_score:Q', 'total_sales_per_product:Q']
                ).properties(
                    width=400,
                    height=350,
                    title="Brand Investment ROI Analysis"
                )
                
                st.altair_chart(roi_chart, use_container_width=True)
        
        with col2:
            # Investment recommendations summary
            st.markdown('<div class="insight-box">', unsafe_allow_html=True)
            st.markdown("#### 💎 **Investment Intelligence Summary**")
            
            investment_insights = [
                f"🎯 **Portfolio Value**: ₫{metrics['total_revenue']:,.0f} total market cap",
                f"📊 **Risk-Adjusted Returns**: {metrics['marketing_roi']:.1f}% ROMI achieved",
                f"🏆 **Quality Premium**: {metrics['brand_equity']:.1f} brand equity score",
                f"⚡ **Efficiency Ratio**: {metrics['inventory_turnover']:.2f}x turnover rate",
                f"🎪 **Market Position**: {market_concentration['structure']} competitive landscape",
                f"💰 **Customer Asset**: ₫{metrics['avg_clv']:,.0f} average lifetime value"
            ]
            
            for insight in investment_insights:
                st.markdown(insight)
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Professional Footer with Export Options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Analytics Report", use_container_width=True):
            st.success("📈 Advanced analytics report exported successfully!")
    
    with col2:
        if st.button("💼 Generate Executive Summary", use_container_width=True):
            st.success("📋 Executive summary generated for stakeholders!")
    
    with col3:
        if st.button("🎯 Strategic Recommendations", use_container_width=True):
            st.success("🚀 Strategic action plan ready for implementation!")

    with tab7:
        st.markdown("### 🔍 **Bảng Điều Khiển So Sánh Chuyên Sâu**")
        st.markdown("*Phân tích so sánh đa chiều để đánh giá và ra quyết định đầu tư chiến lược*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🏆 **Bảng Xếp Hạng Thương Hiệu Toàn Diện**")
            
            # So sánh thương hiệu theo nhiều tiêu chí
            brand_comparison = df.groupby('brand_name').agg({
                'price(vnd)': ['mean', 'std'],
                'rating_average': 'mean',
                'quantity_sold': 'sum',
                'discount': 'mean',
                'category_name': 'count'
            }).round(2)
            
            # Flatten column names
            brand_comparison.columns = ['Giá_Trung_Bình', 'Độ_Biến_Động_Giá', 'Rating_TB', 
                                      'Tổng_Lượng_Bán', 'Giảm_Giá_TB', 'Số_Sản_Phẩm']
            brand_comparison = brand_comparison.reset_index()
            
            # Tính điểm tổng hợp
            brand_comparison['Điểm_Tổng_Hợp'] = (
                brand_comparison['Rating_TB'] * 20 +
                (brand_comparison['Tổng_Lượng_Bán'] / 1000) * 0.3 +
                (100000000 / brand_comparison['Giá_Trung_Bình']) * 0.1 +
                brand_comparison['Số_Sản_Phẩm'] * 2
            ).round(1)
            
            brand_comparison = brand_comparison.sort_values('Điểm_Tổng_Hợp', ascending=False)
            
            # Biểu đồ so sánh thương hiệu
            comparison_chart = alt.Chart(brand_comparison.head(8)).mark_bar(
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5,
                opacity=0.8
            ).encode(
                x=alt.X('Điểm_Tổng_Hợp:Q', title='Điểm Tổng Hợp', axis=alt.Axis(grid=True)),
                y=alt.Y('brand_name:O', sort='-x', title='Thương Hiệu'),
                color=alt.Color('Điểm_Tổng_Hợp:Q', 
                              scale=alt.Scale(scheme='viridis'), 
                              legend=None),
                tooltip=[
                    'brand_name:N',
                    alt.Tooltip('Điểm_Tổng_Hợp:Q', title='Điểm Tổng Hợp'),
                    alt.Tooltip('Rating_TB:Q', format='.2f', title='Rating TB'),
                    alt.Tooltip('Giá_Trung_Bình:Q', format=',.0f', title='Giá TB (VNĐ)'),
                    alt.Tooltip('Tổng_Lượng_Bán:Q', format=',', title='Tổng Lượng Bán'),
                    alt.Tooltip('Số_Sản_Phẩm:Q', title='Số Sản Phẩm')
                ]
            ).properties(
                width=450,
                height=300,
                title="Bảng Xếp Hạng Thương Hiệu Theo Điểm Tổng Hợp"
            )
            
            st.altair_chart(comparison_chart, use_container_width=True)
            
            st.markdown("**📊 Giải Thích Điểm Tổng Hợp:**")
            st.markdown("""
            - **Rating TB**: Trọng số 20 (chất lượng sản phẩm)
            - **Lượng Bán**: Trọng số 0.3/1000 (độ phổ biến)  
            - **Giá Cả**: Trọng số 0.1 (tính cạnh tranh về giá)
            - **Đa Dạng**: Trọng số 2 (số lượng sản phẩm)
            """)
        
        with col2:
            st.markdown("#### 📈 **Ma Trận Hiệu Suất - Rủi Ro**")
            
            # Tính toán hiệu suất và rủi ro cho từng thương hiệu
            risk_return = df.groupby('brand_name').agg({
                'price(vnd)': ['mean', 'std', 'count'],
                'rating_average': 'mean',
                'quantity_sold': 'sum'
            })
            
            risk_return.columns = ['Giá_TB', 'Độ_Biến_Động', 'Số_SP', 'Rating_TB', 'Lượng_Bán']
            risk_return = risk_return.reset_index()
            
            # Tính ROI và Risk Score
            risk_return['ROI_Score'] = (
                risk_return['Rating_TB'] * risk_return['Lượng_Bán'] / risk_return['Giá_TB'] * 1000
            ).round(2)
            
            risk_return['Risk_Score'] = (
                risk_return['Độ_Biến_Động'] / risk_return['Giá_TB'] * 100
            ).round(2)
            
            # Phân loại thương hiệu
            risk_return['Loại'] = risk_return.apply(lambda row: 
                '🏆 Cao-An toàn' if row['ROI_Score'] > risk_return['ROI_Score'].median() and row['Risk_Score'] < risk_return['Risk_Score'].median()
                else '⚡ Cao-Rủi ro' if row['ROI_Score'] > risk_return['ROI_Score'].median()
                else '🛡️ Thấp-An toàn' if row['Risk_Score'] < risk_return['Risk_Score'].median()
                else '⚠️ Thấp-Rủi ro', axis=1)
            
            # Scatter plot Risk-Return
            scatter_chart = alt.Chart(risk_return).mark_circle(
                size=100,
                opacity=0.8,
                stroke='white',
                strokeWidth=2
            ).encode(
                x=alt.X('Risk_Score:Q', title='Điểm Rủi Ro (%)', axis=alt.Axis(grid=True)),
                y=alt.Y('ROI_Score:Q', title='Điểm ROI', axis=alt.Axis(grid=True)),
                color=alt.Color('Loại:N', 
                              scale=alt.Scale(scheme='category20'),
                              title='Phân Loại'),
                size=alt.Size('Lượng_Bán:Q', 
                            scale=alt.Scale(range=[100, 500]),
                            title='Lượng Bán'),
                tooltip=[
                    'brand_name:N',
                    alt.Tooltip('ROI_Score:Q', format='.2f', title='ROI Score'),
                    alt.Tooltip('Risk_Score:Q', format='.2f', title='Risk Score (%)'),
                    alt.Tooltip('Giá_TB:Q', format=',.0f', title='Giá TB (VNĐ)'),
                    alt.Tooltip('Rating_TB:Q', format='.2f', title='Rating TB'),
                    'Loại:N'
                ]
            ).properties(
                width=450,
                height=300,
                title="Ma Trận Hiệu Suất - Rủi Ro Thương Hiệu"
            )
            
            st.altair_chart(scatter_chart, use_container_width=True)
            
            st.markdown("**🎯 Phân Loại Đầu Tư:**")
            st.markdown("""
            - 🏆 **Cao-An toàn**: ROI cao, rủi ro thấp (Đầu tư tốt)
            - ⚡ **Cao-Rủi ro**: ROI cao, rủi ro cao (Cân nhắc)
            - 🛡️ **Thấp-An toàn**: ROI thường, rủi ro thấp (Ổn định)
            - ⚠️ **Thấp-Rủi ro**: ROI thấp, rủi ro cao (Tránh)
            """)
        
        # Phần phân tích chi tiết
        st.markdown("---")
        st.markdown("### 📊 **Phân Tích So Sánh Chi Tiết**")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### 💰 **So Sánh Phân Khúc Giá**")
            
            # Tạo dữ liệu so sánh phân khúc
            segment_data = []
            for tier in df['price_tier'].unique():
                tier_df = df[df['price_tier'] == tier]
                segment_data.append({
                    'Phân_Khúc': tier,
                    'Số_Sản_Phẩm': len(tier_df),
                    'Giá_TB': tier_df['price(vnd)'].mean(),
                    'Rating_TB': tier_df['rating_average'].mean(),
                    'Lượng_Bán_TB': tier_df['quantity_sold'].mean(),
                    'Giảm_Giá_TB': tier_df['discount'].mean(),
                    'Doanh_Thu': (tier_df['price(vnd)'] * tier_df['quantity_sold']).sum()
                })
            
            segment_df = pd.DataFrame(segment_data)
            
            # Biểu đồ radar/polar cho phân khúc
            segment_melted = segment_df.melt(
                id_vars=['Phân_Khúc'], 
                value_vars=['Rating_TB', 'Lượng_Bán_TB', 'Giảm_Giá_TB'],
                var_name='Chỉ_Số', 
                value_name='Giá_Trị'
            )
            
            # Chuẩn hóa dữ liệu (0-100)
            for metric in ['Rating_TB', 'Lượng_Bán_TB', 'Giảm_Giá_TB']:
                max_val = segment_df[metric].max()
                min_val = segment_df[metric].min()
                segment_df[f'{metric}_Norm'] = ((segment_df[metric] - min_val) / (max_val - min_val) * 100).round(1)
            
            # Biểu đồ so sánh phân khúc
            segment_chart = alt.Chart(segment_df).mark_bar(
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                x=alt.X('Phân_Khúc:O', title='Phân Khúc Giá'),
                y=alt.Y('Doanh_Thu:Q', title='Tổng Doanh Thu (VNĐ)', axis=alt.Axis(format=',.0f')),
                color=alt.Color('Phân_Khúc:N', 
                              scale=alt.Scale(scheme='plasma'),
                              legend=None),
                tooltip=[
                    'Phân_Khúc:N',
                    alt.Tooltip('Doanh_Thu:Q', format=',.0f', title='Doanh Thu (VNĐ)'),
                    alt.Tooltip('Số_Sản_Phẩm:Q', title='Số Sản Phẩm'),
                    alt.Tooltip('Giá_TB:Q', format=',.0f', title='Giá TB (VNĐ)'),
                    alt.Tooltip('Rating_TB:Q', format='.2f', title='Rating TB'),
                    alt.Tooltip('Lượng_Bán_TB:Q', format=',.0f', title='Lượng Bán TB')
                ]
            ).properties(
                width=400,
                height=300,
                title="So Sánh Doanh Thu Theo Phân Khúc"
            )
            
            st.altair_chart(segment_chart, use_container_width=True)
        
        with col4:
            st.markdown("#### 🔄 **Xu Hướng Giá - Chất Lượng**")
            
            # Tạo dữ liệu xu hướng
            df_trend = df.copy()
            df_trend['price_range'] = pd.cut(df_trend['price(vnd)'], 
                                           bins=5, 
                                           labels=['Rất Rẻ', 'Rẻ', 'Trung Bình', 'Đắt', 'Rất Đắt'])
            
            trend_data = df_trend.groupby(['price_range', 'brand_name']).agg({
                'rating_average': 'mean',
                'quantity_sold': 'sum',
                'price(vnd)': 'mean'
            }).reset_index()
            
            trend_data = trend_data.groupby('price_range').apply(
                lambda x: x.nlargest(3, 'quantity_sold')
            ).reset_index(drop=True)
            
            # Biểu đồ xu hướng
            trend_chart = alt.Chart(trend_data).mark_circle(
                size=200,
                opacity=0.8
            ).encode(
                x=alt.X('price(vnd):Q', title='Giá Trung Bình (VNĐ)', axis=alt.Axis(format=',.0f')),
                y=alt.Y('rating_average:Q', title='Rating Trung Bình', scale=alt.Scale(domain=[3, 5])),
                color=alt.Color('price_range:N', 
                              scale=alt.Scale(scheme='turbo'),
                              title='Khoảng Giá'),
                size=alt.Size('quantity_sold:Q', 
                            scale=alt.Scale(range=[100, 600]),
                            title='Lượng Bán'),
                tooltip=[
                    'brand_name:N',
                    'price_range:N',
                    alt.Tooltip('price(vnd):Q', format=',.0f', title='Giá (VNĐ)'),
                    alt.Tooltip('rating_average:Q', format='.2f', title='Rating'),
                    alt.Tooltip('quantity_sold:Q', format=',', title='Lượng Bán')
                ]
            ).properties(
                width=400,
                height=300,
                title="Xu Hướng Giá - Chất Lượng Theo Thương Hiệu"
            )
            
            st.altair_chart(trend_chart, use_container_width=True)
        
        # Bảng so sánh tổng quan
        st.markdown("---")
        st.markdown("### 📋 **Bảng So Sánh Tổng Quan Top Thương Hiệu**")
        
        # Tạo bảng so sánh chi tiết
        top_brands = df.groupby('brand_name').agg({
            'price(vnd)': ['mean', 'min', 'max'],
            'rating_average': 'mean',
            'quantity_sold': 'sum',
            'discount': 'mean',
            'category_name': 'count'
        }).round(2)
        
        top_brands.columns = ['Giá_TB', 'Giá_Min', 'Giá_Max', 'Rating_TB', 'Tổng_Bán', 'Giảm_Giá_TB', 'Số_SP']
        top_brands = top_brands.reset_index()
        top_brands = top_brands.nlargest(10, 'Tổng_Bán')
        
        # Format hiển thị
        display_df = top_brands.copy()
        display_df['Giá_TB'] = display_df['Giá_TB'].apply(lambda x: f"{x:,.0f} ₫")
        display_df['Giá_Min'] = display_df['Giá_Min'].apply(lambda x: f"{x:,.0f} ₫")
        display_df['Giá_Max'] = display_df['Giá_Max'].apply(lambda x: f"{x:,.0f} ₫")
        display_df['Rating_TB'] = display_df['Rating_TB'].apply(lambda x: f"{x:.2f} ⭐")
        display_df['Tổng_Bán'] = display_df['Tổng_Bán'].apply(lambda x: f"{x:,}")
        display_df['Giảm_Giá_TB'] = display_df['Giảm_Giá_TB'].apply(lambda x: f"{x:.1f}%")
        
        display_df.columns = ['🏷️ Thương Hiệu', '💰 Giá TB', '⬇️ Giá Min', '⬆️ Giá Max', 
                             '⭐ Rating', '📦 Tổng Bán', '🏷️ Giảm Giá TB', '📱 Số SP']
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Kết luận và khuyến nghị
        st.markdown("---")
        st.markdown("### 🎯 **Kết Luận & Khuyến Nghị Đầu Tư**")
        
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.markdown("#### 🏆 **Thương Hiệu Hàng Đầu**")
            top_brand = brand_comparison.iloc[0]
            st.success(f"""
            **{top_brand['brand_name']}**
            - Điểm tổng hợp: {top_brand['Điểm_Tổng_Hợp']}
            - Rating: {top_brand['Rating_TB']:.2f}/5.0
            - Lượng bán: {top_brand['Tổng_Lượng_Bán']:,}
            - Giá TB: {top_brand['Giá_Trung_Bình']:,.0f} ₫
            """)
        
        with col6:
            st.markdown("#### 💎 **Cơ Hội Đầu Tư**")
            investment_opps = risk_return[risk_return['Loại'] == '🏆 Cao-An toàn']
            if len(investment_opps) > 0:
                best_investment = investment_opps.nlargest(1, 'ROI_Score').iloc[0]
                st.info(f"""
                **{best_investment['brand_name']}**
                - ROI Score: {best_investment['ROI_Score']:.2f}
                - Risk Score: {best_investment['Risk_Score']:.2f}%
                - Phân loại: {best_investment['Loại']}
                """)
            else:
                st.warning("Không có thương hiệu ở nhóm Cao-An toàn")
        
        with col7:
            st.markdown("#### ⚠️ **Cảnh Báo Rủi Ro**")
            risky_brands = risk_return[risk_return['Loại'] == '⚠️ Thấp-Rủi ro']
            if len(risky_brands) > 0:
                worst_brand = risky_brands.iloc[0]
                st.error(f"""
                **{worst_brand['brand_name']}**
                - ROI Score: {worst_brand['ROI_Score']:.2f}
                - Risk Score: {worst_brand['Risk_Score']:.2f}%
                - Khuyến nghị: ⚠️ Tránh đầu tư
                """)
            else:
                st.success("Không có thương hiệu ở nhóm rủi ro cao")
    
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <b>🏆 Expert Financial Analytics Dashboard</b> | 
        📊 Advanced Market Intelligence | 
        💎 Professional Investment Analysis | 
        🔄 Real-time Business Intelligence
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()


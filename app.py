import os
import math
import pandas as pd
import streamlit as st
import altair as alt


@st.cache_data(show_spinner=False)
def load_data(csv_path: str = "tiki_product_data.csv") -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {csv_path}")

    df = pd.read_csv(csv_path)

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

    return df


def format_vnd(x: float) -> str:
    try:
        return f"{x:,.0f} VND"
    except Exception:
        return "-"


def main():
    st.set_page_config(page_title="Tiki Product Monitor", layout="wide")
    st.title("Tiki Product Monitor (Snapshot)")
    st.caption(
        "Dashboard theo dõi sản phẩm (bản chụp 1 thời điểm). "
        "Khuyến nghị thêm dữ liệu theo ngày để phân tích thời gian và chiến lược giá."
    )

    # Sidebar: chọn dữ liệu và filter
    csv_path = st.sidebar.text_input("Đường dẫn CSV", value="tiki_product_data.csv")

    try:
        df = load_data(csv_path)
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()

    # Các cột hay dùng
    col_price = "price(vnd)" if "price(vnd)" in df.columns else None
    col_qty = "quantity_sold" if "quantity_sold" in df.columns else None
    col_rev = "total_sales_per_product" if "total_sales_per_product" in df.columns else None
    col_brand = "brand_name" if "brand_name" in df.columns else None
    col_cat = "category_name" if "category_name" in df.columns else None
    col_subcat = "subcategory_name" if "subcategory_name" in df.columns else None
    col_rating = "rating_average" if "rating_average" in df.columns else None

    # Sidebar filters
    if col_cat and df[col_cat].notna().any():
        categories = ["(All)"] + sorted(df[col_cat].dropna().astype(str).unique().tolist())
        sel_cat = st.sidebar.selectbox("Category", categories)
    else:
        sel_cat = "(All)"

    filtered = df.copy()
    if sel_cat != "(All)" and col_cat:
        filtered = filtered[filtered[col_cat] == sel_cat]

    if col_subcat and filtered[col_subcat].notna().any():
        subcats_all = sorted(filtered[col_subcat].dropna().astype(str).unique().tolist())
        sel_subcats = st.sidebar.multiselect("Subcategory", subcats_all)
        if sel_subcats:
            filtered = filtered[filtered[col_subcat].isin(sel_subcats)]

    if col_brand and filtered[col_brand].notna().any():
        brands_all = sorted(filtered[col_brand].dropna().astype(str).unique().tolist())
        sel_brands = st.sidebar.multiselect("Brand", brands_all)
        if sel_brands:
            filtered = filtered[filtered[col_brand].isin(sel_brands)]

    # KPIs
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("Sản phẩm", f"{len(filtered):,}")
    with kpi_cols[1]:
        if col_qty:
            st.metric("Số lượng bán (ước)", f"{filtered[col_qty].sum():,.0f}")
        else:
            st.metric("Số lượng bán (ước)", "-")
    with kpi_cols[2]:
        if col_rev:
            st.metric("Doanh thu (ước)", format_vnd(filtered[col_rev].sum()))
        else:
            st.metric("Doanh thu (ước)", "-")
    with kpi_cols[3]:
        if col_price:
            st.metric("Giá trung bình", format_vnd(filtered[col_price].mean()))
        else:
            st.metric("Giá trung bình", "-")
    with kpi_cols[4]:
        if col_rating and filtered[col_rating].notna().any():
            st.metric("Rating TB", f"{filtered[col_rating].mean():.2f}")
        else:
            st.metric("Rating TB", "-")

    st.divider()

    # Layout 2 cột cho các biểu đồ tổng quan
    col_left, col_right = st.columns(2)

    with col_left:
        # Biểu đồ phân bổ theo subcategory (Pie chart)
        st.subheader("Phân bổ sản phẩm theo subcategory")
        if col_subcat and filtered[col_subcat].notna().any():
            subcat_dist = (
                filtered[col_subcat]
                .value_counts()
                .reset_index(name="count")
                .head(15)  # Top 15 subcategories
            )
            subcat_dist.columns = ["subcategory", "count"]
            pie = alt.Chart(subcat_dist).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("count:Q"),
                color=alt.Color(
                    "subcategory:N", 
                    legend=alt.Legend(title="Subcategory", orient="right"),
                    scale=alt.Scale(scheme="tableau20")
                ),
                tooltip=[
                    alt.Tooltip("subcategory:N", title="Subcategory"), 
                    alt.Tooltip("count:Q", format=",", title="Số sản phẩm")
                ],
            )
            st.altair_chart(pie.properties(height=300), use_container_width=True)
            st.caption("⚠️ Hiển thị Top 15 subcategories")
        else:
            st.info("Không có dữ liệu subcategory.")

    with col_right:
        # Biểu đồ phân phối rating
        st.subheader("Phân phối Rating")
        if col_rating and filtered[col_rating].notna().any():
            rating_data = filtered[filtered[col_rating] > 0][col_rating]
            if len(rating_data) > 0:
                hist_df = pd.DataFrame({col_rating: rating_data})
                hist = alt.Chart(hist_df).mark_bar(color="#ff7f0e").encode(
                    x=alt.X(f"{col_rating}:Q", bin=alt.Bin(maxbins=20), title="Rating"),
                    y=alt.Y("count()", title="Số sản phẩm"),
                    tooltip=[alt.Tooltip(f"{col_rating}:Q", bin=alt.Bin(maxbins=20)), alt.Tooltip("count()")],
                )
                st.altair_chart(hist.properties(height=300), use_container_width=True)
            else:
                st.info("Không có dữ liệu rating hợp lệ.")
        else:
            st.info("Không có dữ liệu rating.")

    st.divider()

    # Biểu đồ Top thương hiệu theo doanh thu
    st.subheader("Top thương hiệu theo doanh thu")
    if col_brand and col_rev and (filtered[[col_brand, col_rev]].dropna().shape[0] > 0):
        group_cols = [col_brand]
        color_enc = alt.value("#1f77b4")
        if col_cat and sel_cat == "(All)":
            group_cols = [col_cat, col_brand]
        by_brand = (
            filtered.groupby(group_cols)[col_rev]
            .sum()
            .reset_index(name="total_sales_vnd")
            .sort_values("total_sales_vnd", ascending=False)
            .head(10)
        )

        base = alt.Chart(by_brand).mark_bar().encode(
            x=alt.X("total_sales_vnd:Q", title="Doanh thu (VND)", axis=alt.Axis(format=",")),
            y=alt.Y(f"{col_brand}:N", sort='-x', title="Brand"),
        )
        if col_cat and sel_cat == "(All)":
            chart = base.encode(color=alt.Color(f"{col_cat}:N", title="Category"))
        else:
            chart = base.encode(color=color_enc)
        st.altair_chart(chart.properties(height=380), use_container_width=True)
    else:
        st.info("Thiếu cột brand/doanh thu để vẽ biểu đồ.")

    st.divider()

    # Layout 2 cột cho biểu đồ phân tích
    analysis_left, analysis_right = st.columns(2)

    with analysis_left:
        # Phân phối giá (Histogram)
        st.subheader("Phân phối giá sản phẩm")
        if col_price and filtered[col_price].notna().any():
            price_data = filtered[filtered[col_price] > 0][col_price]
            if len(price_data) > 0:
                price_df = pd.DataFrame({col_price: price_data})
                price_hist = alt.Chart(price_df).mark_bar(color="#d62728").encode(
                    x=alt.X(f"{col_price}:Q", bin=alt.Bin(maxbins=30), title="Giá (VND)"),
                    y=alt.Y("count()", title="Số sản phẩm"),
                    tooltip=[alt.Tooltip(f"{col_price}:Q", bin=alt.Bin(maxbins=30), format=","), alt.Tooltip("count()")],
                )
                st.altair_chart(price_hist.properties(height=320), use_container_width=True)
            else:
                st.info("Không có dữ liệu giá hợp lệ.")
        else:
            st.info("Không có dữ liệu giá.")

    with analysis_right:
        # Phân bổ số lượng bán theo khoảng giá
        st.subheader("Số lượng bán theo khoảng giá")
        if "price_range" in filtered.columns and col_qty:
            pr = (
                filtered.groupby("price_range")[col_qty]
                .sum()
                .reset_index(name="total_qty")
                .sort_values("price_range")
            )
            line = alt.Chart(pr).mark_line(point=True, strokeWidth=3).encode(
                x=alt.X("price_range:N", title="Khoảng giá"),
                y=alt.Y("total_qty:Q", title="Số lượng bán", axis=alt.Axis(format=",")),
                tooltip=["price_range", alt.Tooltip("total_qty:Q", format=",")],
                color=alt.value("#2ca02c"),
            )
            st.altair_chart(line.properties(height=320), use_container_width=True)
        else:
            st.info("Chưa có cột price_range hoặc quantity_sold.")

    st.divider()

    # Top subcategories theo doanh thu
    if col_subcat and col_rev and filtered[col_subcat].notna().any():
        st.subheader("Top Subcategories theo doanh thu")
        by_subcat = (
            filtered.groupby(col_subcat)[col_rev]
            .sum()
            .reset_index(name="total_sales_vnd")
            .sort_values("total_sales_vnd", ascending=False)
            .head(15)
        )
        subcat_chart = alt.Chart(by_subcat).mark_bar(color="#9467bd").encode(
            x=alt.X("total_sales_vnd:Q", title="Doanh thu (VND)", axis=alt.Axis(format=",")),
            y=alt.Y(f"{col_subcat}:N", sort='-x', title="Subcategory"),
            tooltip=[alt.Tooltip(f"{col_subcat}:N"), alt.Tooltip("total_sales_vnd:Q", format=",", title="Doanh thu")],
        )
        st.altair_chart(subcat_chart.properties(height=400), use_container_width=True)

    st.divider()

    # Biểu đồ tương quan (Scatter plots)
    scatter_left, scatter_right = st.columns(2)

    with scatter_left:
        # Tương quan Giá vs Số lượng bán
        st.subheader("Giá vs Số lượng bán")
        if col_price and col_qty:
            scatter_data = filtered[[col_price, col_qty]].dropna()
            scatter_data = scatter_data[(scatter_data[col_price] > 0) & (scatter_data[col_qty] > 0)]
            if len(scatter_data) > 0:
                scatter = alt.Chart(scatter_data.head(500)).mark_circle(size=60, opacity=0.6).encode(
                    x=alt.X(f"{col_price}:Q", title="Giá (VND)", scale=alt.Scale(type="log")),
                    y=alt.Y(f"{col_qty}:Q", title="Số lượng bán", scale=alt.Scale(type="log")),
                    tooltip=[alt.Tooltip(f"{col_price}:Q", format=","), alt.Tooltip(f"{col_qty}:Q", format=",")],
                    color=alt.value("#17becf"),
                )
                st.altair_chart(scatter.properties(height=320), use_container_width=True)
                st.caption("⚠️ Chỉ hiển thị 500 sản phẩm đầu (sau khi lọc). Trục log scale.")
            else:
                st.info("Không đủ dữ liệu để vẽ scatter plot.")
        else:
            st.info("Thiếu cột giá hoặc số lượng bán.")

    with scatter_right:
        # Tương quan Discount Rate vs Số lượng bán
        st.subheader("Discount Rate vs Số lượng bán")
        col_discount = "discount_rate(%)" if "discount_rate(%)" in filtered.columns else None
        if col_discount and col_qty:
            scatter_disc = filtered[[col_discount, col_qty]].dropna()
            scatter_disc = scatter_disc[scatter_disc[col_qty] > 0]
            if len(scatter_disc) > 0:
                scatter_d = alt.Chart(scatter_disc.head(500)).mark_circle(size=60, opacity=0.6).encode(
                    x=alt.X(f"{col_discount}:Q", title="Discount Rate (%)"),
                    y=alt.Y(f"{col_qty}:Q", title="Số lượng bán", scale=alt.Scale(type="log")),
                    tooltip=[alt.Tooltip(f"{col_discount}:Q", format=".1f"), alt.Tooltip(f"{col_qty}:Q", format=",")],
                    color=alt.value("#e377c2"),
                )
                st.altair_chart(scatter_d.properties(height=320), use_container_width=True)
                st.caption("⚠️ Chỉ hiển thị 500 sản phẩm đầu. Trục Y: log scale.")
            else:
                st.info("Không đủ dữ liệu để vẽ scatter plot.")
        else:
            st.info("Thiếu cột discount rate hoặc số lượng bán.")

    st.divider()

    # Top sản phẩm theo doanh thu / số lượng
    st.subheader("Top sản phẩm")
    left, right = st.columns(2)
    cols_display = []
    for c in ["id", "product_name", col_brand, col_cat, col_subcat, col_price, col_qty, col_rev]:
        if isinstance(c, str) and c in filtered.columns:
            cols_display.append(c)

    with left:
        st.caption("Theo doanh thu")
        if col_rev:
            top_rev = (
                filtered.sort_values(col_rev, ascending=False)
                .loc[:, cols_display]
                .head(20)
            )
            st.dataframe(top_rev, use_container_width=True)
        else:
            st.info("Không có cột doanh thu để xếp hạng.")

    with right:
        st.caption("Theo số lượng bán")
        if col_qty:
            top_qty = (
                filtered.sort_values(col_qty, ascending=False)
                .loc[:, cols_display]
                .head(20)
            )
            st.dataframe(top_qty, use_container_width=True)
        else:
            st.info("Không có cột số lượng để xếp hạng.")

    # Tải dữ liệu đã lọc
    st.download_button(
        label="Tải CSV đã lọc",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="tiki_products_filtered.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()


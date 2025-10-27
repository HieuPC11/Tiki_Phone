s

# Tiki Product Data Crawler & Dashboard

## 🎯 Mục tiêu dự án
Thu thập, phân tích và trực quan hóa dữ liệu sản phẩm từ website tiki.vn, tập trung vào các danh mục điện thoại, laptop, thiết bị điện tử.

## 📦 Cấu trúc dự án

```
tiki-crawler/
├── src/                          # Source code chính
│   ├── crawler/                  # Module crawl dữ liệu
│   ├── utils/                    # Các hàm tiện ích
│   └── __init__.py
│
├── data/                         # Dữ liệu
│   ├── raw/                      # Dữ liệu thô từ crawler
│   ├── processed/                # Dữ liệu đã xử lý
│   └── README.md
│
├── notebooks/                    # Jupyter notebooks
│   ├── tiki_crawl_product_data.ipynb    # Crawl dữ liệu
│   ├── eda_product_data.ipynb           # EDA & phân tích
│   └── data_analysis.ipynb              # Phân tích nâng cao
│
├── dashboard/                    # Streamlit dashboard
│   ├── app.py                    # Main dashboard app
│   ├── components/               # Dashboard components
│   └── assets/                   # Static files (images, css)
│
├── config/                       # Configuration files
│   ├── settings.py               # App settings
│   └── categories.json           # Danh mục sản phẩm
│
├── docs/                         # Tài liệu dự án
│   ├── API.md                    # API documentation
│   └── CHANGELOG.md              # Lịch sử thay đổi
│
├── tests/                        # Unit tests
│
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore file
└── README.md                     # Tài liệu chính
```

## 🚀 Hướng dẫn sử dụng

### Bước 1: Cài đặt môi trường
```bash
# Clone repository
git clone https://github.com/autuanh/tiki-crawler.git
cd tiki-crawler

# Tạo virtual environment (khuyến nghị)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 2: Crawl dữ liệu
```bash
# Mở và chạy notebook
jupyter notebook notebooks/tiki_crawl_product_data.ipynb
```
- Dữ liệu sẽ được lưu vào thư mục `data/raw/`
- File output: `data/raw/tiki_product_data.csv`

### Bước 3: Phân tích dữ liệu (EDA)
```bash
# Mở notebook phân tích
jupyter notebook notebooks/eda_product_data.ipynb
```
- Khám phá và trực quan hóa dữ liệu
- Tạo insights về giá, số lượng bán, thương hiệu, v.v.

### Bước 4: Chạy Dashboard
```bash
# Chạy Streamlit dashboard
streamlit run dashboard/app.py
```
- Mở trình duyệt tại: `http://localhost:8501`
- Dashboard tự động load dữ liệu từ `data/raw/tiki_product_data.csv`

## ⚡ Tính năng dashboard
- Lọc dữ liệu theo category, subcategory, brand
- KPI: số sản phẩm, số lượng bán, doanh thu ước tính, giá trung bình, rating trung bình
- Biểu đồ:
  - Phân bổ sản phẩm theo subcategory (màu sắc đa dạng, dễ so sánh)
  - Phân phối rating
  - Phân phối giá sản phẩm
  - Top thương hiệu theo doanh thu
  - Top subcategory theo doanh thu
  - Scatter plot: Giá vs Số lượng bán, Discount Rate vs Số lượng bán
- Bảng xếp hạng top sản phẩm theo doanh thu và số lượng bán
- Tải về dữ liệu đã lọc dưới dạng CSV

## 🛠️ Yêu cầu môi trường
- **Python**: >= 3.8
- **Thư viện chính**:
  - `requests`: HTTP requests cho crawler
  - `pandas`: Xử lý và phân tích dữ liệu
  - `tqdm`: Progress bar
  - `seaborn`, `matplotlib`: Visualization trong notebooks
  - `numpy`: Tính toán số học
  - `streamlit`: Web dashboard framework
  - `altair`: Interactive charts trong dashboard

## � Dataset
Dữ liệu thu thập bao gồm các trường:
- `id`: ID sản phẩm trên Tiki
- `product_name`: Tên sản phẩm
- `price(vnd)`: Giá hiện tại (VND)
- `original_price`: Giá gốc
- `discount`: Số tiền giảm giá
- `discount_rate(%)`: Tỷ lệ giảm giá
- `review_count`: Số lượng đánh giá
- `rating_average`: Điểm rating trung bình
- `quantity_sold`: Số lượng đã bán
- `brand_name`: Tên thương hiệu
- `category_name`: Danh mục chính
- `subcategory_name`: Danh mục con
- `updated_at`: Thời gian cập nhật

## 🔄 Roadmap
- [ ] Tự động hóa crawl dữ liệu định kỳ
- [ ] Thêm database để lưu trữ lịch sử giá
- [ ] Phân tích xu hướng giá theo thời gian
- [ ] Hệ thống cảnh báo giá tốt
- [ ] API để truy vấn dữ liệu
- [ ] Deploy dashboard lên cloud

## 📝 Ghi chú
- Dự án chỉ phục vụ mục đích học tập và nghiên cứu
- Tuân thủ `robots.txt` và chính sách của Tiki
- Không sử dụng cho mục đích thương mại

## 📬 Liên hệ & đóng góp
- **Tác giả**: autuanh
- **Repository**: [github.com/autuanh/tiki-crawler](https://github.com/autuanh/tiki-crawler)
- **Đóng góp**: Tạo issue hoặc pull request trên Github
- **License**: MIT

---
⭐ Nếu thấy hữu ích, hãy star repo này!

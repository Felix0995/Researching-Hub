# ResearchHub MBA V1.0

Hệ thống Quản lý Tri thức & Nghiên cứu Học thuật Cá nhân (Local-first Personal Academic Knowledge Library).

## 1. Giới thiệu tổng quan

**ResearchHub MBA** là ứng dụng web cá nhân chạy cục bộ (local-first) trên máy Mac, được thiết kế chuyên biệt để lưu trữ, bảo toàn, phân loại, tìm kiếm, đọc, trích dẫn số trang và lập ma trận tổng quan tài liệu học thuật cho học viên MBA và nhà nghiên cứu độc lập.

### Nguyên tắc cốt lõi:
- **Cục bộ & Bảo mật (100% Offline):** Toàn bộ dữ liệu, tệp nghiên cứu và ghi chú cá nhân được lưu trữ trực tiếp trên máy Mac (`127.0.0.1`), không truyền tải qua cloud, không sử dụng OpenAI API hay chatbot trong V1.0.
- **Bảo toàn tệp gốc:** Tệp PDF/DOCX được sao chép vào kho lưu trữ có quản lý theo mã băm SHA-256, không bao giờ sửa đổi tệp gốc tại chỗ.
- **Đa ngôn ngữ:** Giao diện tiếng Việt; hỗ trợ tìm kiếm tài liệu Tiếng Việt, Tiếng Anh và Tiếng Trung Phồn thể (繁體中文).
- **Công nghệ nền tảng:** Python, Streamlit, SQLite (FTS5), PyMuPDF, python-docx, openpyxl.

---

## 2. Yêu cầu hệ thống

- **Hệ điều hành:** macOS (hỗ trợ cả Apple Silicon arm64 và Intel x86_64).
- **Python:** Python 3.9 trở lên.
- **Git:** Git 2.30+.

---

## 3. Hướng dẫn cài đặt & Khởi chạy cục bộ

### Bước 1: Khởi tạo môi trường ảo (Virtual Environment)
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 2: Cài đặt các gói phụ thuộc
```bash
pip install --upgrade pip
pip install -r requirements-dev.txt
```

### Bước 3: Cấu hình môi trường (tùy chọn)
Sao chép tệp mẫu cấu hình nếu cần tùy chỉnh cổng hoặc thư mục lưu trữ:
```bash
cp .env.example .env
```

### Bước 4: Khởi chạy ứng dụng Streamlit
```bash
streamlit run app.py
```
Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ mặc định: [http://127.0.0.1:8501](http://127.0.0.1:8501).

---

## 4. Kiểm thử & Kiểm tra chất lượng mã (QA & Linting)

Chạy bộ kiểm thử tự động:
```bash
pytest
```

Chạy kiểm tra quy chuẩn mã nguồn (linter):
```bash
ruff check .
```

---

## 5. Cấu trúc thư mục dự án

```
researchhub-mba/
├── AGENTS.md                 # Quy chế thực thi cho AI Agent
├── agent.md                  # Hợp đồng kỹ thuật & tiêu chuẩn kỹ thuật phần mềm
├── gdd.md                    # Tài liệu Thiết kế & Mục tiêu Sản phẩm (GDD)
├── README.md                 # Hướng dẫn dự án & cài đặt
├── pyproject.toml            # Cấu hình dự án Python, ruff và pytest
├── requirements.txt          # Gói phụ thuộc chính thức (runtime)
├── requirements-dev.txt      # Gói phụ thuộc cho dev và test
├── .env.example              # Mẫu cấu hình môi trường
├── .gitignore                # Quy tắc loại trừ dữ liệu, DB và tệp nhạy cảm
├── app.py                    # Điểm khởi nhập ứng dụng Streamlit
├── researchhub/              # Gói mã nguồn chính
│   ├── __init__.py
│   ├── config.py             # Quản lý đường dẫn và tham số cấu hình
│   ├── ui/                   # Giao diện người dùng & màn hình
│   ├── services/             # Nghiệp vụ logic
│   ├── repositories/         # Tầng truy xuất dữ liệu
│   ├── parsers/              # Trích xuất PDF / DOCX
│   ├── storage/              # Lưu trữ tệp & kiểm tra SHA-256
│   ├── db/                   # Quản lý kết nối & lược đồ SQLite
│   └── models/               # Định nghĩa thực thể dữ liệu
├── tests/                    # Bộ kiểm thử đơn vị và tích hợp
│   ├── __init__.py
│   └── test_basic.py
└── data/                     # [Gitignored] Thư mục chứa SQLite và tệp tài liệu
```

---

## 6. Trạng thái dự án & Lộ trình thực hiện

Dự án tuân thủ quy trình kiểm soát thay đổi nghiêm ngặt theo từng giai đoạn (Phase-gated PR review):

- [x] **Phase 0:** Kiểm toán môi trường, thiết lập quy chế an toàn & khởi tạo khung dự án tối thiểu.
- [ ] **Phase 1:** Thiết lập hạ tầng lưu trữ tệp và lược đồ SQLite 14 bảng.
- [ ] **Phase 2:** Nhập liệu tệp (PDF/DOCX), giải mã nội dung và màn hình chi tiết tài liệu.
- [ ] **Phase 3:** Phân loại đa chiều (Lĩnh vực, Dự án nghiên cứu, Nhãn, Tác giả).
- [ ] **Phase 4:** Công cụ tìm kiếm toàn văn FTS5 và trích xuất ngữ cảnh đa ngữ.
- [ ] **Phase 5:** Sổ tay nghiên cứu (Notebook) và trích đoạn học thuật.
- [ ] **Phase 6:** Ma trận tài liệu tổng quan (Literature Matrix) & Xuất Word/Excel.
- [ ] **Phase 7:** Bảng điều khiển (Dashboard), Sao lưu/Phục hồi toàn vẹn & Nghiệm thu phát hành.

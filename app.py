"""ResearchHub MBA V1.0 — Ứng dụng Quản lý Tri thức & Nghiên cứu Học thuật Cá nhân.

Điểm khởi nhập tối thiểu cho Giai đoạn 0 (Phase 0 Foundation).
"""

from __future__ import annotations

import streamlit as st

from researchhub import __app_name__, __version__
from researchhub.config import config


def main() -> None:
    """Điểm khởi chạy giao diện chào mừng ResearchHub MBA V1.0."""
    st.set_page_config(
        page_title=f"{__app_name__} v{__version__}",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("📚 ResearchHub MBA V1.0")
    st.caption("Hệ thống Quản lý Tri thức & Nghiên cứu Học thuật Cá nhân (Local-first)")

    st.divider()

    st.success("✅ **Khởi tạo hệ thống thành công — Giai đoạn 0 (Phase 0: Project Foundation)**")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Giới thiệu hệ thống")
        st.markdown(
            "**ResearchHub MBA** là hệ thống thư viện nghiên cứu cá nhân cục bộ (local-first):\n\n"
            "- 🔒 **Bảo mật & Cục bộ:** 100% dữ liệu trên máy cá nhân, không AI bên thứ ba.\n"
            "- 📑 **Hỗ trợ định dạng:** PDF và DOCX (bảo toàn tệp gốc trong kho lưu trữ).\n"
            "- 🌐 **Hỗ trợ đa ngôn ngữ:** Tiếng Việt, Tiếng Anh, Tiếng Trung Phồn thể.\n"
            "- 🔍 **Tìm kiếm chính xác:** Toàn văn FTS5, trích dẫn số trang thực tế.\n"
            "- 📊 **Ma trận tổng quan:** Hỗ trợ tổng hợp tài liệu, xuất Word / Excel."
        )

        st.info(
            "ℹ️ **Lưu ý:** Ứng dụng hiện đang ở **Giai đoạn 0 (Khởi tạo an toàn & Kiểm toán)**. "
            "Các tính năng quản lý tệp, cơ sở dữ liệu SQLite, tìm kiếm và ma trận tài liệu "
            "sẽ được kích hoạt tuần tự theo từng giai đoạn được phê duyệt."
        )

    with col2:
        st.subheader("Thông tin môi trường cục bộ")
        st.write(f"- **Phiên bản:** `v{__version__}`")
        st.write(f"- **Địa chỉ phục vụ:** `{config.host}:{config.port}`")
        st.write(f"- **Gốc dự án:** `{config.project_root.name}`")
        st.write(f"- **Thư mục dữ liệu:** `{config.data_dir.name}`")
        st.write("- **Trạng thái:** Sẵn sàng cho Giai đoạn 1 (Phase 1)")

    st.divider()
    st.caption("ResearchHub MBA V1.0 — Bản quyền người dùng cá nhân. Không chia sẻ công cộng.")


if __name__ == "__main__":
    main()

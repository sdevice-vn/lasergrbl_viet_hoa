1. Tạo repo mới trên GitHub (private cũng được).
2. Giải nén zip này và đẩy toàn bộ nội dung (kể cả thư mục .github) lên nhánh chính.
3. Vào tab Actions > "Build LaserGRBL Tieng Viet (Windows)" (tự chạy khi push, hoặc bấm Run workflow).
4. Khi xong, mở lần chạy đó, tải mục Artifacts > LaserGRBL_Windows_TiengViet.
5. Giải nén (giữ nguyên thư mục con `vi`), chạy LaserGRBL.exe (ngôn ngữ mặc định là Tiếng Việt; có thể đổi trong menu Ngôn ngữ).

Ghi chú:
- Bản build yêu cầu .NET Framework 4.8 (có sẵn trên Windows 10 1903 trở lên và Windows 11).
- Muốn sửa/bổ sung bản dịch: chỉnh `vi_translations.json` (chuỗi tiếng Anh gốc -> tiếng Việt) rồi push lại, workflow tự build.
- Chuỗi nào chưa có trong `vi_translations.json` sẽ hiển thị tiếng Anh; danh sách chúng được in ở bước "Ap dung ban dich tieng Viet" trong log.

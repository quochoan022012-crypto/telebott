# Telegram Shop Bot - Demo Cửa Hàng Bán Key/Acc Tự Động

Mã nguồn Telegram Bot bằng Python mô phỏng hệ thống bán hàng tự động với menu bàn phím, danh mục sản phẩm đa tầng, xem chi tiết giá tiền, tồn kho và hướng dẫn thanh toán.

## Giao diện & Chức năng hỗ trợ

1. **Lệnh `/start`**: Lời chào chào mừng theo tên người dùng, mở menu chính (Reply Keyboard).
2. **Menu bàn phím chính**:
   - `🛍️ Mua Key/Acc`: Hiển thị danh mục sản phẩm (Inline Keyboard).
   - `💳 Nạp Tiền`: Hướng dẫn chuyển khoản ngân hàng & Momo tự động (QR + cú pháp nạp).
   - `💎 Cá Nhân`: Xem số dư tài khoản (demo), ID Telegram, Username, ngày tham gia.
   - `🏆 Top Nạp`: Xếp hạng những người dùng nạp tiền nhiều nhất.
   - `📄 Lịch Sử Nạp`: Nhật ký các giao dịch nạp tiền.
   - `🤵 Hỗ Trợ`: Thông tin liên hệ Admin CSKH.
3. **Luồng chọn sản phẩm đa tầng**:
   - Bấm `🛍️ Mua Key/Acc` -> Chọn danh mục (ví dụ: `Fluorite`, `Migul Lite`...).
   - Chọn sản phẩm (ví dụ: `Fluorite 1 Ngày - 65,000đ (Kho: 3)`) -> Có nút `Quay Lại` danh mục.
   - Chọn số lượng cần mua (`Mua 1`, `Mua 5`, `Mua 10`, `Mua 50`) -> Có nút `Quay Lại Danh Mục`.
   - Nếu sản phẩm hết hàng (Kho: 0), hệ thống sẽ hiển thị thông báo cảnh báo hết hàng dạng Alert.
   - Nếu còn hàng, hiển thị hóa đơn thanh toán kèm hướng dẫn chuyển khoản (Demo).

---

## Hướng dẫn cài đặt và chạy thử

### Bước 1: Chuẩn bị môi trường
Máy tính của bạn cần được cài đặt sẵn **Python** (Phiên bản >= 3.8).

### Bước 2: Tạo Bot và Lấy Token
1. Truy cập Telegram, tìm kiếm bot [@BotFather](https://t.me/BotFather).
2. Gửi lệnh `/newbot` và đặt tên cho bot của bạn.
3. Nhập username cho bot (phải kết thúc bằng chữ `bot`, ví dụ: `my_shop_test_bot`).
4. Sao chép đoạn **API Token** được cung cấp.

### Bước 3: Cấu hình mã nguồn
1. Mở tệp `.env` trong thư mục code.
2. Thay thế `YOUR_TELEGRAM_BOT_TOKEN_HERE` bằng đoạn API Token bạn vừa lấy ở Bước 2.
   ```env
   BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   ```

### Bước 4: Cài đặt thư viện và chạy Bot
1. Mở Command Prompt (cmd) hoặc PowerShell trên Windows.
2. Di chuyển vào thư mục chứa code:
   ```cmd
   cd C:\Users\jcchu\.gemini\antigravity\scratch\telegram_shop_bot
   ```
3. Cài đặt các thư viện cần thiết:
   ```cmd
   pip install -r requirements.txt
   ```
4. Khởi động bot:
   ```cmd
   python bot.py
   ```

Bây giờ bạn có thể mở Telegram, tìm kiếm tên bot của mình và bấm `/start` để thử nghiệm các chức năng!

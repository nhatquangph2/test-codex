# test-codex

Khung mẫu bằng GPT để thử nghiệm tự động đăng bài.

## Cách sử dụng

1. Tạo file cấu hình JSON (xem `example_posts.json`).
2. Xem nhanh toàn bộ cấu hình và nội dung sẽ gửi bằng chế độ preview:

   ```bash
   python -m social_agent.main --config example_posts.json --preview
   ```

3. Chạy công cụ ở chế độ mô phỏng để kiểm tra lịch đăng:

   ```bash
   python -m social_agent.main --config example_posts.json --simulate
   ```

4. Khi đã sẵn sàng gửi ra ngoài (ví dụ dùng webhook), bỏ `--simulate` và
   thêm cấu hình nền tảng phù hợp. Webhook client có xử lý lỗi cơ bản
   (log thông báo khi endpoint không phản hồi).

## Cấu trúc cấu hình

- `platform_settings`: danh sách client, mỗi client có một `name` (ví dụ
  `facebook`, `instagram`, `tiktok`, `youtube`) và khai báo `type` để tái sử
  dụng client nền tảng:
  - `type: console`: chỉ log ra console (an toàn để demo).
  - `type: webhook`: gửi POST JSON tới endpoint chỉ định (`url`, `headers`,
    `timeout`).
- `posts`: mảng bài đăng với các trường `platform`, `content`, `scheduled_for`
  (ISO 8601, tùy chọn) và `metadata` (tùy chọn).

Các client hiện tại:

- `console`: in nội dung ra log, an toàn cho thử nghiệm. Có thể khai báo nhiều
  client với nhãn khác nhau (ví dụ `facebook`, `instagram`).
- `webhook`: gửi POST JSON tới một endpoint tùy chọn. Hỗ trợ khai báo nhiều
  client với `type: webhook` để gắn token/URL riêng cho từng mạng xã hội.

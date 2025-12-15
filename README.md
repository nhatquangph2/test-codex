# Social agent demo

Ví dụ đơn giản để gửi bài viết lên Facebook, Instagram, TikTok và YouTube bằng Python.

## Cách cấu hình OAuth/token
- **Facebook Page / Instagram Graph API**
  - App dashboard: tạo Page access token hoặc Instagram business token với scope `pages_manage_posts`, `pages_show_list`, `instagram_basic`, `instagram_content_publish`.
  - Endpoint mẫu: `https://graph.facebook.com/v18.0/{page_id}/feed` (Facebook) hoặc `https://graph.facebook.com/v18.0/{business_account_id}/media` (Instagram).
  - Token ngắn hạn cần đổi sang long-live qua `GET /oauth/access_token?grant_type=fb_exchange_token` và gia hạn trước khi hết hạn.
- **TikTok Business API**
  - OAuth theo tài liệu TikTok: lấy `access_token` với scope `video.upload`, `video.publish`.
  - Endpoint mẫu: `https://open.tiktokapis.com/v2/post/publish/` dùng `Authorization: Bearer <access_token>` và webhook nhận trạng thái tải lên.
  - Khi nhận thông báo token sắp hết hạn, gọi refresh token endpoint để đổi sang token mới.
- **YouTube Data API**
  - Đăng ký OAuth client, trao quyền `https://www.googleapis.com/auth/youtube.upload`.
  - Gửi POST tới `https://www.googleapis.com/youtube/v3/videos?part=snippet,status` với header `Authorization: Bearer <token>`.
  - Token hết hạn phải được làm mới qua refresh token của OAuth 2.0.

## Ví dụ cấu hình và payload
Xem file [`example_posts.json`](./example_posts.json) để có đầy đủ mẫu cho từng mạng xã hội. Mỗi mục chứa:
- `type`: `facebook` | `instagram` | `tiktok` | `youtube`.
- Thông tin OAuth/token và định danh trang/kênh.
- Payload cần gửi (message/caption/video_url...).

Sử dụng nhanh:
```python
from social_agent.platform_clients import create_client
import json

with open("example_posts.json") as f:
    posts = json.load(f)

facebook_cfg = posts["facebook"]
client = create_client(facebook_cfg)
client.publish(facebook_cfg["post"])
```

## Kiểm thử
Các kiểm thử dùng pytest và mock HTTP để chắc chắn payload, header và log lỗi đúng khi API trả lỗi hoặc token hết hạn.
Chạy toàn bộ bằng lệnh:

```bash
pytest
```

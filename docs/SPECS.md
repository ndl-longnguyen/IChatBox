# IChatBox Specs (Multi-Website)

## Mục tiêu
IChatBox là hệ thống chatbox bán tích hợp cho nhiều website. Mỗi website tương ứng với 1 `CustomerKey` (license key) dùng để:
- Nhúng widget vào website (client).
- Kết nối WebSocket để chat realtime.
- Gắn dữ liệu chat vào đúng "tenant" (một user/admin) và không trộn lẫn giữa các website.

## Khái niệm chính
- **Super admin**: dùng Django Admin ở `/supper-admin/` để quản lý tất cả user và dữ liệu.
- **User (admin/tenant)**: một khách hàng của bạn. Mỗi user có 1 key để nhúng widget lên website.
- **CustomerKey**: license key public để nhúng. Key có thể bật/tắt (disable), rotate, và có thông số gói (plan).
- **Participant**: một visitor trên website của tenant, định danh theo `device` (lưu trong localStorage).
- **ChatRoom**: phòng chat giữa tenant và một participant.
- **ChatMessage**: tin nhắn trong phòng chat.
- **AISettings**: cấu hình AI auto-reply riêng của từng tenant.
- **KnowledgeDocument / KnowledgeChunk**: dữ liệu training cá nhân và phần chunk tối ưu để truy vấn context.

## Tenant isolation (multi-website)
Tất cả dữ liệu chat gắn với `CustomerKey.user` và `Participant.user`. Widget chỉ truy cập qua `token=<CustomerKey.key>`, do đó:
- Tenant A không thể đọc được lịch sử của tenant B.
- Mỗi user chỉ thấy chat của mình trong UI `/admin/chat/`.

## API HTTP cho widget
Các endpoint trả JSON và set CORS `Access-Control-Allow-Origin: *` để widget chạy trên domain khác.

### `GET /admin/widget-config/?token=<key>`
Trả về cấu hình widget cho key.
- `allow_anonymous`: `true` cho phép vào chat ngay (Guest); `false` yêu cầu nhập name + (email hoặc phone).
- `plan`: tên gói (string).
- `history_limit`: số message tối đa widget được load lại khi reload (server-side source of truth).

Nếu key invalid hoặc bị khóa `is_active=false`: generic `404` để không leak trạng thái key.

### `GET /admin/widget-history/?token=<key>&device=<device>&limit=<n>`
Trả về lịch sử chat của visitor theo `token + device`.
- `device`: visitor id lưu trong localStorage (`ichatbox_visitor_id`).
- `limit`: widget có thể gửi nhưng server luôn clamp theo `CustomerKey.history_limit` và giới hạn tối đa 200.

Nếu chưa có chat: trả `messages: []`.
Nếu key invalid hoặc bị khóa: generic `404`.

## WebSocket realtime
### Visitor: `/ws/user/chat/?token=<key>&username=<name>&device=<device>&phone=<p>|&email=<e>`
Server sẽ:
1. Resolve `CustomerKey` theo token.
2. Nếu key bị khóa: đóng socket.
3. Nếu `allow_anonymous=false`: yêu cầu `username` và có `phone` hoặc `email`, thiếu sẽ đóng socket.
4. `Participant` được tạo/lookup theo `(tenant_user, device)`.
5. `ChatRoom` được tạo/lookup theo `(tenant_user, participant)`.
6. Tin nhắn visitor lưu với `sender_type=PARTICIPANT`.
7. Nếu admin bật AI auto-reply và có training data phù hợp, hệ thống tạo tin nhắn phản hồi với `sender_type=USER`.

### Admin UI: `/ws/admin/chat/`
Admin đăng nhập `/admin/login/` và xem chat tại `/admin/chat/`.
Admin chỉ join các room của chính mình.

## Lưu log chat khi reload
- Widget lưu `visitorId` trong localStorage: `ichatbox_visitor_id`.
- Widget lưu thông tin visitor theo key: `ichatbox_visitor_info_<token>`.
- Khi load widget, nếu có thể vào chat thì widget gọi `widget-history` trước khi connect WebSocket để render lại log cũ.
- Khi user clear cache/localStorage, device id mất, widget sẽ coi như visitor mới và không còn map được log cũ.

## Quản trị key (Super admin)
Trong `/supper-admin/`:
- Disable/Enable key: chặn HTTP config/history và WebSocket connect.
- Rotate key: generate UUID mới (các website nhúng key cũ sẽ bị vô hiệu).
- Set `plan` và `history_limit`: kiểm soát tính năng theo gói.

## AI local auto-reply
- AI chạy qua local Ollama-compatible API, cấu hình bằng `AI_LOCAL_BASE_URL` và `AI_LOCAL_MODEL`.
- Admin bật/tắt auto-reply tại `/admin/ai/`.
- Admin training dữ liệu bằng nhập form hoặc upload file text/markdown/csv/json.
- Database lưu bản gốc ở `KnowledgeDocument`, sau đó tách thành `KnowledgeChunk` theo từng tenant để truy vấn context khi visitor gửi tin nhắn.
- Nếu local AI lỗi, timeout hoặc chưa có dữ liệu phù hợp, hệ thống không tự trả lời và chat realtime vẫn hoạt động bình thường.

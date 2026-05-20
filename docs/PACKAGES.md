# Gói Dịch Vụ (Đề xuất)

Tất cả gói đều áp dụng theo từng website (từng `CustomerKey`).

## FREE
- `plan`: `FREE`
- `history_limit`: 20
- `allow_anonymous`: tùy chọn
- Key rotate/disable: có (super admin)

## STARTER
- `plan`: `STARTER`
- `history_limit`: 50
- Hỗ trợ cơ bản

## PRO
- `plan`: `PRO`
- `history_limit`: 200
- Ưu tiên hỗ trợ

## ENTERPRISE (custom)
- `plan`: `ENTERPRISE`
- `history_limit`: >= 200 (tuỳ)
- Tính năng bổ sung (gợi ý):
  - Whitelist domain được phép gọi widget API
  - SLA, analytics, exports
  - Multi-agent trong cùng tenant

## Mapping kỹ thuật
- `history_limit` được enforce ở server (`/admin/widget-history/`), widget chỉ gửi `limit` như hint.
- Khi `is_active=false`:
  - `widget-config` và `widget-history` trả `403`
  - WebSocket visitor bị đóng ngay khi connect

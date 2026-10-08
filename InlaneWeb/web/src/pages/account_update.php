<?php
/**
 * account_update.php — Cap nhat ho so (UPDATE).
 *
 * !!! DIEM INJECT: UPDATE injection !!!
 * Input 'email' noi thang vao SET -> co the sua record khac / dump qua error.
 * Payload mau (email):
 *   x@x.com' WHERE username='admin'-- -           (doi email cua admin)
 *   x@x.com', role='admin' WHERE username='jsmith'-- -   (tu nang quyen)
 *   x@x.com' WHERE id=1 AND extractvalue(1,concat(0x7e,version()))-- -  (error-based)
 */
$u = current_user();
if (!$u) { header('Location: /login'); exit; }

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { header('Location: /account'); exit; }

$email = $_POST['email'] ?? '';

// !!! NOI CHUOI email vao SET — khong sanitize -> UPDATE injection !!!
$sql = "UPDATE users SET email = '$email' WHERE id = " . intval($u['id']);

render_header('Cập nhật hồ sơ');
echo '<div class="card"><h1>Cập nhật hồ sơ</h1>';
echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

if (exec_write($sql)) {
    $affected = mysqli_affected_rows(db());
    flash('Đã cập nhật hồ sơ. Số bản ghi bị ảnh hưởng: <strong>' . $affected . '</strong>.', 'success');
}
echo '<p class="muted"><a href="/account">← Về hồ sơ</a></p></div>';
render_footer();

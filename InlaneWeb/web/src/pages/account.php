<?php
/**
 * account.php — Ho so user + danh sach van don + form cap nhat.
 *
 * !!! DIEM INJECT (phu): Error-based qua tham so ?order= khi sap xep van don !!!
 * Payload mau:
 *   /account?order=(extractvalue(1,concat(0x7e,(SELECT api_key FROM users WHERE username='admin'))))
 */
$u = current_user();
if (!$u) { header('Location: /login'); exit; }

render_header('Hồ sơ');
?>
<div class="card">
    <h1>Xin chào, <?= htmlspecialchars($u['username']) ?></h1>
    <table class="data">
        <tr><th>Tên đăng nhập</th><td><?= htmlspecialchars($u['username']) ?></td></tr>
        <tr><th>Email</th><td><?= htmlspecialchars($u['email']) ?></td></tr>
        <tr><th>Vai trò</th><td><?= htmlspecialchars($u['role']) ?></td></tr>
        <tr><th>API Key</th><td><code><?= htmlspecialchars($u['api_key']) ?></code></td></tr>
    </table>
</div>

<div class="card">
    <h2>Cập nhật hồ sơ</h2>
    <form action="/account/update" method="post">
        <div class="form-row">
            <label>Email</label>
            <input type="text" name="email" value="<?= htmlspecialchars($u['email']) ?>">
        </div>
        <button class="btn" type="submit">Lưu thay đổi</button>
    </form>
</div>

<div class="card">
    <h2>Vận đơn của tôi</h2>
    <?php
    // Sap xep theo tham so ?order= (mac dinh 'id') -> Error-based qua ORDER BY expr
    $order = $_GET['order'] ?? 'id';
    // !!! NOI CHUOI vao ORDER BY — khong sanitize !!!
    $sql = "SELECT tracking_no, port_code, status FROM shipments WHERE customer_id = "
         . intval($u['id']) . " ORDER BY $order";
    echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

    $res = query($sql);
    if ($res && mysqli_num_rows($res) > 0) {
        echo '<table class="data"><tr><th>Mã vận đơn</th><th>Cảng</th><th>Trạng thái</th></tr>';
        while ($row = mysqli_fetch_assoc($res)) {
            echo '<tr><td>' . htmlspecialchars($row['tracking_no']) . '</td>'
               . '<td>' . htmlspecialchars($row['port_code']) . '</td>'
               . '<td>' . htmlspecialchars($row['status']) . '</td></tr>';
        }
        echo '</table>';
    } elseif ($res) {
        flash('Bạn chưa có vận đơn nào.', 'info');
    }
    ?>
</div>
<?php
render_footer();

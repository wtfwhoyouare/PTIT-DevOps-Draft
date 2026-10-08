<?php
/**
 * admin_dashboard.php — Dashboard quan tri (staff/admin).
 * Co o tim khach hang (?customer=) -> Boolean/Error, va cac lien ket toi
 * cong cu export (CREATE) va console (stacked).
 */
$u = current_user();
if (!$u || !in_array($u['role'], ['admin', 'staff'])) {
    render_header('Truy cập bị từ chối');
    echo '<div class="card"><h1>403 — Cần quyền quản trị</h1>'
       . '<p class="muted">Gợi ý: có thể đăng nhập bằng SQLi với vai trò admin.</p></div>';
    render_footer();
    exit;
}

render_header('Quản trị');
?>
<div class="card">
    <h1>Bảng điều khiển quản trị</h1>
    <p class="muted">Xin chào <?= htmlspecialchars($u['username']) ?> (<?= htmlspecialchars($u['role']) ?>)</p>
</div>

<div class="card">
    <h2>Tìm khách hàng</h2>
    <form class="searchbar" action="/admin" method="get">
        <input type="text" name="customer" value="<?= htmlspecialchars($_GET['customer'] ?? '') ?>" placeholder="Tên khách hàng...">
        <button class="btn" type="submit">Tìm</button>
    </form>
    <?php
    if (!empty($_GET['customer'])) {
        $c = $_GET['customer'];
        // !!! NOI CHUOI -> UNION/Error/Boolean !!!
        $sql = "SELECT username, email, role FROM users WHERE username LIKE '%$c%'";
        echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';
        $res = query($sql);
        if ($res && mysqli_num_rows($res) > 0) {
            echo '<table class="data"><tr><th>Username</th><th>Email</th><th>Role</th></tr>';
            while ($row = mysqli_fetch_row($res)) {
                echo '<tr><td>' . htmlspecialchars((string)$row[0]) . '</td>'
                   . '<td>' . htmlspecialchars((string)$row[1]) . '</td>'
                   . '<td>' . htmlspecialchars((string)$row[2]) . '</td></tr>';
            }
            echo '</table>';
        }
    }
    ?>
</div>

<div class="card">
    <h2>Công cụ quản trị</h2>
    <p><a href="/admin/reports/export">→ Xuất báo cáo (tạo bảng tạm)</a> — tạo bảng snapshot theo tên tuỳ chọn.</p>
    <p><a href="/admin/console?filter=status">→ Console lọc nâng cao</a> — bộ lọc dữ liệu vận đơn.</p>
</div>
<?php
render_footer();

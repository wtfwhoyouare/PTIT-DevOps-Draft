<?php
/**
 * admin_report_export.php — Tao bang bao cao tam (CREATE): /admin/reports/export
 *
 * !!! DIEM INJECT: CREATE injection (inject dinh danh bang) !!!
 * Ten bang do user dat, noi thang vao CREATE TABLE ... AS SELECT.
 * Payload mau (report_name):
 *   snap1 AS SELECT * FROM dev.credentials-- -        (tao bang chua credentials)
 *   snap2(x) AS SELECT LOAD_FILE('/etc/passwd')-- -   (nhet noi dung file vao bang)
 * Sau do co the doc lai bang vua tao qua endpoint SELECT khac.
 */
$u = current_user();
if (!$u || !in_array($u['role'], ['admin', 'staff'])) {
    render_header('Truy cập bị từ chối');
    echo '<div class="card"><h1>403 — Cần quyền quản trị</h1></div>';
    render_footer();
    exit;
}

render_header('Xuất báo cáo');
echo '<div class="card"><h1>Xuất báo cáo (snapshot)</h1>';
echo '<p class="muted">Tạo một bảng snapshot tạm từ dữ liệu vận đơn hiện tại.</p>';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = $_POST['report_name'] ?? '';
    // !!! NOI CHUOI ten bang vao CREATE TABLE — khong sanitize -> CREATE injection !!!
    $sql = "CREATE TABLE report_$name AS SELECT tracking_no, status FROM shipments";
    echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';
    if (exec_write($sql)) {
        flash('Đã tạo bảng báo cáo <code>report_' . htmlspecialchars($name) . '</code>.', 'success');
    }
}
?>
    <form action="/admin/reports/export" method="post">
        <div class="form-row">
            <label>Tên báo cáo</label>
            <input type="text" name="report_name" placeholder="vd: q1_2024">
        </div>
        <button class="btn" type="submit">Tạo báo cáo</button>
    </form>
    <p class="muted"><a href="/admin">← Về dashboard</a></p>
</div>
<?php
render_footer();

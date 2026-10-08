<?php
/**
 * admin_console.php — Console loc nang cao: /admin/console?filter=
 *
 * !!! DIEM INJECT: STACKED QUERY (mysqli_multi_query) !!!
 * Vi dung API multi_query, MOT injection co the chay CHONG nhieu cau lenh
 * ngan bang ';' -> INSERT / UPDATE / DELETE / CREATE / DROP tuy y.
 * (Khac voi mysqli_query() thong thuong — MySQL khong cho stacked.)
 * Payload mau (filter):
 *   status; INSERT INTO users(username,password,role) VALUES('h4x','h4x','admin')-- -
 *   status; UPDATE users SET role='admin' WHERE username='jsmith'-- -
 *   status; DELETE FROM comments-- -
 *   status; CREATE TABLE pwned AS SELECT * FROM dev.credentials-- -
 *   status; DROP TABLE report_x-- -
 */
$u = current_user();
if (!$u || !in_array($u['role'], ['admin', 'staff'])) {
    render_header('Truy cập bị từ chối');
    echo '<div class="card"><h1>403 — Cần quyền quản trị</h1></div>';
    render_footer();
    exit;
}

$filter = $_GET['filter'] ?? 'status';

render_header('Console lọc nâng cao');
echo '<div class="card"><h1>Console lọc vận đơn</h1>';
echo '<form class="searchbar" action="/admin/console" method="get">'
   . '<input type="text" name="filter" value="' . htmlspecialchars($filter) . '" placeholder="Cột lọc...">'
   . '<button class="btn" type="submit">Lọc</button></form>';

// !!! NOI CHUOI filter — chay bang multi_query -> STACKED injection !!!
$sql = "SELECT tracking_no, $filter FROM shipments";
echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

$rows = exec_multi($sql);
if ($rows) {
    echo '<table class="data"><tr>';
    foreach (array_keys($rows[0]) as $col) {
        echo '<th>' . htmlspecialchars($col) . '</th>';
    }
    echo '</tr>';
    foreach ($rows as $r) {
        echo '<tr>';
        foreach ($r as $cell) {
            echo '<td>' . htmlspecialchars((string)$cell) . '</td>';
        }
        echo '</tr>';
    }
    echo '</table>';
} else {
    flash('Không có dữ liệu trả về (query stacked có thể đã chạy các lệnh ghi).', 'info');
}
echo '<p class="muted"><a href="/admin">← Về dashboard</a></p></div>';
render_footer();

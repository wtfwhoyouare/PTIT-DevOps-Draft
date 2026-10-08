<?php
/**
 * shipment_detail.php — Chi tiet don hang + binh luan.
 * /shipments/{id}   (id la so; input van vao query -> SELECT injectable)
 * Trang nay hien form them binh luan (INSERT) va nut xoa (DELETE).
 */
$u = current_user();
if (!$u) { header('Location: /login'); exit; }

$id = $_GET['id'] ?? '';

render_header('Chi tiết đơn hàng');

// SELECT don hang (id noi chuoi -> injectable, kieu so)
$sql = "SELECT id, tracking_no, port_code, status FROM shipments WHERE id = $id";
echo '<div class="card"><h1>Đơn hàng #' . htmlspecialchars($id) . '</h1>';
echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';
$sh = query_one($sql);
if ($sh) {
    echo '<table class="data">'
       . '<tr><th>Mã vận đơn</th><td>' . htmlspecialchars($sh['tracking_no']) . '</td></tr>'
       . '<tr><th>Cảng</th><td>' . htmlspecialchars($sh['port_code']) . '</td></tr>'
       . '<tr><th>Trạng thái</th><td>' . htmlspecialchars($sh['status']) . '</td></tr>'
       . '</table>';
}
echo '</div>';

// Danh sach binh luan
echo '<div class="card"><h2>Bình luận</h2>';
$cres = query("SELECT c.id, c.content, c.created_at, u.username
               FROM comments c JOIN users u ON u.id = c.user_id
               WHERE c.shipment_id = " . intval($id) . " ORDER BY c.created_at");
if ($cres) {
    while ($c = mysqli_fetch_assoc($cres)) {
        echo '<div class="comment"><div>' . htmlspecialchars($c['content']) . '</div>'
           . '<div class="meta">' . htmlspecialchars($c['username']) . ' · '
           . htmlspecialchars($c['created_at'])
           . ' · <a href="/comments/' . $c['id'] . '/delete" '
           . 'onclick="return confirm(\'Xoá bình luận?\')">Xoá</a></div></div>';
    }
}

// Form them binh luan -> POST /shipments/{id}/comments  (INSERT inject)
?>
    <h2 style="margin-top:20px">Thêm bình luận</h2>
    <form action="/shipments/<?= intval($id) ?>/comments" method="post">
        <div class="form-row">
            <textarea name="content" rows="3" placeholder="Nhập bình luận..."></textarea>
        </div>
        <button class="btn" type="submit">Gửi bình luận</button>
    </form>
</div>
<?php
render_footer();

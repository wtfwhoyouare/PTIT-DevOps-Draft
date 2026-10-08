<?php
/**
 * news.php — Tin tuc. Xem chi tiet 1 tin qua ?id=
 *
 * !!! DIEM INJECT (phu): UNION/Error qua ?id= !!!
 * Payload mau:  /news?id=1 UNION SELECT 1,username,password FROM users-- -
 */
render_header('Tin tức');

$id = $_GET['id'] ?? '';
?>
<div class="card">
    <h1>Tin tức &amp; Thông báo</h1>
    <?php
    if ($id !== '') {
        // !!! NOI CHUOI id (kieu so, khong bao quote) -> UNION-based (3 cot) !!!
        $sql = "SELECT id, title, body FROM news WHERE id = $id";
        echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';
        $res = query($sql);
        if ($res) {
            while ($row = mysqli_fetch_row($res)) {
                echo '<h2>' . htmlspecialchars((string)$row[1]) . '</h2>';
                echo '<p>' . htmlspecialchars((string)$row[2]) . '</p>';
            }
        }
        echo '<p class="muted"><a href="/news">← Tất cả tin tức</a></p>';
    } else {
        $res = query("SELECT id, title, published_at FROM news ORDER BY published_at DESC");
        echo '<table class="data"><tr><th>#</th><th>Tiêu đề</th><th>Ngày đăng</th></tr>';
        while ($row = mysqli_fetch_assoc($res)) {
            echo '<tr><td>' . $row['id'] . '</td>'
               . '<td><a href="/news?id=' . $row['id'] . '">' . htmlspecialchars($row['title']) . '</a></td>'
               . '<td>' . htmlspecialchars($row['published_at']) . '</td></tr>';
        }
        echo '</table>';
    }
    ?>
</div>
<?php
render_footer();

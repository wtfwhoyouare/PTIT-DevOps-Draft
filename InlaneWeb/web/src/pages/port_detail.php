<?php
/**
 * port_detail.php — Chi tiet mot cang: /ports/{code}
 *
 * !!! DIEM INJECT: In-band ERROR-based !!!
 * display_errors=On + in mysqli_error() -> ep ham loi de lo du lieu.
 * Payload mau (dat vao {code} tren URL, da urldecode):
 *   CN SHA' AND extractvalue(1,concat(0x7e,(SELECT database())))-- -
 *   CN SHA' AND updatexml(1,concat(0x7e,(SELECT version())),1)-- -
 */
render_header('Chi tiết cảng');

$code = $_GET['code'] ?? '';
?>
<div class="card">
    <h1>Chi tiết cảng: <code><?= htmlspecialchars($code) ?></code></h1>
    <?php
    // !!! NOI CHUOI — khong sanitize -> Error-based SQLi !!!
    $sql = "SELECT code, city, country, volume FROM ports WHERE code = '$code'";
    echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

    $row = query_one($sql);
    if ($row) {
        echo '<table class="data">';
        echo '<tr><th>Mã cảng</th><td>' . htmlspecialchars($row['code']) . '</td></tr>';
        echo '<tr><th>Thành phố</th><td>' . htmlspecialchars($row['city']) . '</td></tr>';
        echo '<tr><th>Quốc gia</th><td>' . htmlspecialchars($row['country']) . '</td></tr>';
        echo '<tr><th>Sản lượng</th><td>' . htmlspecialchars($row['volume']) . ' M TEU</td></tr>';
        echo '</table>';
    } else {
        flash('Không có dữ liệu cho cảng này.', 'info');
    }
    ?>
    <p class="muted"><a href="/ports">← Quay lại tra cứu</a></p>
</div>
<?php
render_footer();

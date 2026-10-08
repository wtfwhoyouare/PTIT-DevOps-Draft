<?php
/**
 * ports.php — Tra cuu cang (?q=).  Query SELECT, ket qua hien bang.
 *
 * !!! DIEM INJECT: In-band UNION-based !!!
 * Bang ket qua co 4 cot hien thi (code, city, country, volume) -> UNION 4 cot.
 * Payload mau:  ' UNION SELECT 1,@@version,3,4-- -
 *               ' UNION SELECT 1,schema_name,3,4 FROM information_schema.schemata-- -
 */
render_header('Tra cứu cảng');

$q = $_GET['q'] ?? '';
?>
<div class="card">
    <h1>Tra cứu cảng biển</h1>
    <form class="searchbar" action="/ports" method="get">
        <input type="text" name="q" value="<?= htmlspecialchars($q) ?>" placeholder="Mã cảng...">
        <button class="btn" type="submit">Tra cứu</button>
    </form>

    <?php if ($q !== ''): ?>
        <?php
        // !!! NOI CHUOI TRUC TIEP — khong sanitize -> SQLi (UNION-based) !!!
        $sql = "SELECT code, city, country, volume FROM ports WHERE code LIKE '%$q%'";
        echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

        $res = query($sql);
        if ($res && mysqli_num_rows($res) > 0) {
            echo '<table class="data"><tr><th>Mã cảng</th><th>Thành phố</th><th>Quốc gia</th><th>Sản lượng (M TEU)</th></tr>';
            while ($row = mysqli_fetch_row($res)) {
                echo '<tr>';
                foreach ($row as $cell) {
                    echo '<td>' . htmlspecialchars((string)$cell) . '</td>';
                }
                echo '</tr>';
            }
            echo '</table>';
        } elseif ($res) {
            flash('Không tìm thấy cảng nào khớp với "<code>' . htmlspecialchars($q) . '</code>".', 'info');
        }
        ?>
    <?php else: ?>
        <p class="muted">Nhập mã cảng để tra cứu (vd: <code>CN</code>, <code>SG</code>, <code>DXB</code>).</p>
    <?php endif; ?>
</div>
<?php
render_footer();

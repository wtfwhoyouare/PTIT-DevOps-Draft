<?php
/**
 * login.php — Dang nhap.
 *
 * !!! DIEM INJECT: Boolean-based + Authentication Bypass !!!
 * Trang chi phan hoi "thanh cong / that bai" (khong lo du lieu) -> Boolean.
 * Payload mau (username):
 *   admin'-- -                         (auth bypass bang comment)
 *   ' OR '1'='1                        (auth bypass bang OR)
 *   admin' AND SUBSTRING(database(),1,1)='i'-- -   (Boolean char-by-char)
 */
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    // !!! NOI CHUOI CA username LAN password — khong sanitize !!!
    $sql = "SELECT id, username, role FROM users WHERE username = '$username' AND password = '$password'";
    $row = query_one($sql);

    if ($row) {
        // Dang nhap thanh cong -> chi bao thanh cong (Boolean TRUE)
        $_SESSION['uid'] = $row['id'];
        header('Location: /account');
        exit;
    } else {
        $error = 'Sai tên đăng nhập hoặc mật khẩu.'; // Boolean FALSE (khong lo chi tiet)
    }
}

render_header('Đăng nhập');
?>
<div class="card" style="max-width:440px;margin:0 auto;">
    <h1>Đăng nhập</h1>
    <?php if ($error) flash($error, 'error'); ?>
    <form action="/login" method="post">
        <div class="form-row">
            <label>Tên đăng nhập</label>
            <input type="text" name="username" autofocus>
        </div>
        <div class="form-row">
            <label>Mật khẩu</label>
            <input type="password" name="password">
        </div>
        <button class="btn" type="submit" style="width:100%">Đăng nhập</button>
    </form>
    <p class="muted" style="margin-top:16px">Tài khoản demo: <code>jsmith / Spring2024!</code></p>
</div>
<?php
render_footer();

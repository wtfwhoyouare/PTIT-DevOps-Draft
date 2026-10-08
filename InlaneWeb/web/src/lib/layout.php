<?php
/** layout.php — Header / nav / footer dung chung (UI giong app that). */

function current_user(): ?array
{
    if (!empty($_SESSION['uid'])) {
        // NOTE: doc lai user tu DB moi request (khong sanitize uid tu session)
        return query_one("SELECT * FROM users WHERE id = " . intval($_SESSION['uid']));
    }
    return null;
}

function render_header(string $title = 'IlFreight Logistics'): void
{
    $u = current_user();
    ?><!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= htmlspecialchars($title) ?> — IlFreight Logistics</title>
    <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<div class="lab-banner">⚠ INTENTIONALLY VULNERABLE — TRAINING ONLY · Lab SQL Injection</div>
<header class="topbar">
    <a class="brand" href="/">
        <span class="brand-mark">◆</span> IlFreight <span class="brand-sub">Logistics</span>
    </a>
    <nav class="mainnav">
        <a href="/">Trang chủ</a>
        <a href="/ports">Cảng biển</a>
        <a href="/track">Tra cứu vận đơn</a>
        <a href="/news">Tin tức</a>
        <?php if ($u): ?>
            <a href="/account">Hồ sơ</a>
            <?php if (in_array($u['role'], ['admin', 'staff'])): ?>
                <a href="/admin" class="nav-admin">Quản trị</a>
            <?php endif; ?>
            <a href="/logout" class="nav-cta">Đăng xuất (<?= htmlspecialchars($u['username']) ?>)</a>
        <?php else: ?>
            <a href="/login" class="nav-cta">Đăng nhập</a>
        <?php endif; ?>
    </nav>
</header>
<main class="container">
<?php
}

function render_footer(): void
{
    ?>
</main>
<footer class="footer">
    <div>© 2024 IlFreight Logistics Co. — Global Freight Forwarding &amp; Port Services</div>
    <div class="footer-warn">Môi trường huấn luyện nội bộ</div>
</footer>
</body>
</html>
<?php
}

/** flash() — thong bao ngan (success/error/info). */
function flash(string $msg, string $type = 'info'): void
{
    echo '<div class="flash flash-' . $type . '">' . $msg . '</div>';
}

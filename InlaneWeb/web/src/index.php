<?php
/**
 * index.php — Front controller / router.
 * Map cac route "giong that" (URL sach) toi handler tuong ung.
 */
session_start();

require __DIR__ . '/lib/db.php';
require __DIR__ . '/lib/layout.php';

// Lay path (bo query string), bo dau '/' cuoi
$uri  = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = rtrim($uri, '/');
if ($path === '') { $path = '/'; }
$method = $_SERVER['REQUEST_METHOD'];

// Helper: dispatch toi file handler trong /pages
function page(string $file): void
{
    require __DIR__ . '/pages/' . $file;
    exit;
}

// ---------------------------------------------------------------------------
//  ROUTING
// ---------------------------------------------------------------------------

// Auth
if ($path === '/login')  { page('login.php'); }
if ($path === '/logout') { page('logout.php'); }

// Trang chu & noi dung
if ($path === '/')     { page('home.php'); }
if ($path === '/news') { page('news.php'); }

// Cang bien
if ($path === '/ports') { page('ports.php'); }                       // ?q=  -> UNION
if (preg_match('#^/ports/(.+)$#', $path, $m)) {                      // /ports/{code} -> Error
    $_GET['code'] = urldecode($m[1]);
    page('port_detail.php');
}

// Tra cuu van don (JSON API) -> Time-based
if ($path === '/track')     { page('track.php'); }
if ($path === '/api/track') { page('track_api.php'); }

// Tai khoan
if ($path === '/account')        { page('account.php'); }            // Error-based
if ($path === '/account/update') { page('account_update.php'); }     // UPDATE inject

// Binh luan don hang
if (preg_match('#^/shipments/(\d+)/comments$#', $path, $m)) {        // INSERT inject
    $_GET['shipment_id'] = $m[1];
    page('comment_add.php');
}
if (preg_match('#^/shipments/([^/]+)$#', $path, $m)) {               // chi tiet don hang
    $_GET['id'] = urldecode($m[1]);
    page('shipment_detail.php');
}
if (preg_match('#^/comments/(.+)/delete$#', $path, $m)) {            // DELETE inject
    $_GET['comment_id'] = urldecode($m[1]);
    page('comment_delete.php');
}

// Khu quan tri
if ($path === '/admin')                 { page('admin_dashboard.php'); }
if ($path === '/admin/reports/export')  { page('admin_report_export.php'); } // CREATE inject
if ($path === '/admin/console')         { page('admin_console.php'); }       // Stacked

// Tai bao cao -> OOB
if ($path === '/reports/download') { page('report_download.php'); }

// ---------------------------------------------------------------------------
//  404
// ---------------------------------------------------------------------------
http_response_code(404);
render_header('Không tìm thấy');
echo '<div class="card"><h1>404</h1><p>Không tìm thấy trang: <code>'
    . htmlspecialchars($path) . '</code></p><p><a href="/">Về trang chủ</a></p></div>';
render_footer();

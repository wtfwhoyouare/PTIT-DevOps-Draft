<?php
/** home.php — Trang chu: hero + o tra cuu cang + tin tuc moi. */
render_header('Trang chủ');
?>
<div class="hero">
    <h1>Vận tải &amp; Logistics toàn cầu</h1>
    <p>Tra cứu cảng biển, theo dõi vận đơn và quản lý lô hàng của bạn với IlFreight Logistics.</p>
    <form class="searchbar" action="/ports" method="get">
        <input type="text" name="q" placeholder="Nhập mã cảng, ví dụ: CN, SG, DXB..." autofocus>
        <button class="btn" type="submit">Tra cứu cảng</button>
    </form>
</div>

<div class="card">
    <h2>Tin tức mới nhất</h2>
    <?php
    // SELECT don gian (khong co diem inject o day — chi hien thi)
    $res = query("SELECT title, body, published_at FROM news ORDER BY published_at DESC LIMIT 5");
    if ($res) {
        while ($row = mysqli_fetch_assoc($res)) {
            echo '<div class="comment"><strong>' . htmlspecialchars($row['title']) . '</strong>'
               . '<div class="meta">' . htmlspecialchars($row['published_at']) . '</div>'
               . '<div>' . htmlspecialchars($row['body']) . '</div></div>';
        }
    }
    ?>
</div>

<div class="card">
    <h2>Dịch vụ</h2>
    <p class="muted">Freight forwarding · Port handling · Customs clearance · Warehousing · Last-mile delivery</p>
</div>
<?php
render_footer();

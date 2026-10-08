<?php
/** track.php — Trang tra cuu van don (goi /api/track qua fetch). */
render_header('Tra cứu vận đơn');
?>
<div class="card">
    <h1>Tra cứu vận đơn</h1>
    <p class="muted">Nhập mã vận đơn (tracking number) để xem trạng thái lô hàng.</p>
    <form class="searchbar" onsubmit="return doTrack(event)">
        <input type="text" id="tracking" placeholder="Ví dụ: ILF1042CN">
        <button class="btn" type="submit">Theo dõi</button>
    </form>
    <div id="result" style="margin-top:16px"></div>
</div>

<script>
async function doTrack(e) {
    e.preventDefault();
    const t = document.getElementById('tracking').value;
    const box = document.getElementById('result');
    box.innerHTML = '<p class="muted">Đang tra cứu...</p>';
    const started = performance.now();
    // Goi API JSON — endpoint nay dinh Time-based SQLi
    const res = await fetch('/api/track?tracking=' + encodeURIComponent(t));
    const took = Math.round(performance.now() - started);
    const data = await res.json();
    if (data.found) {
        box.innerHTML = '<table class="data">'
            + '<tr><th>Mã vận đơn</th><td>' + data.tracking_no + '</td></tr>'
            + '<tr><th>Cảng</th><td>' + data.port_code + '</td></tr>'
            + '<tr><th>Trạng thái</th><td>' + data.status + '</td></tr>'
            + '</table><p class="muted">Phản hồi trong ' + took + ' ms.</p>';
    } else {
        box.innerHTML = '<div class="flash flash-info">Không tìm thấy vận đơn. '
            + '(Phản hồi trong ' + took + ' ms.)</div>';
    }
}
</script>
<?php
render_footer();

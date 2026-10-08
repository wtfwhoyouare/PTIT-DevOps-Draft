<?php
/**
 * db.php — Ket noi database va helper query.
 *
 * !!! CO Y DE LO !!!
 * - Ket noi bang user 'root' (FILE privilege) -> phuc vu doc/ghi file & OOB.
 * - Helper query() KHONG sanitize -> moi noi noi chuoi input deu dinh SQLi.
 * - db_error() in nguyen mysqli_error() ra front-end -> Error-based SQLi.
 */

function db(): mysqli
{
    static $conn = null;
    if ($conn === null) {
        $host = getenv('DB_HOST') ?: 'db';
        $user = getenv('DB_USER') ?: 'root';
        $pass = getenv('DB_PASS') ?: 'password';
        $name = getenv('DB_NAME') ?: 'ilfreight';

        // Tat che do nem exception cua mysqli de tu tay in loi ra front-end
        // (giong code cu, phuc vu Error-based injection).
        mysqli_report(MYSQLI_REPORT_OFF);

        $conn = mysqli_connect($host, $user, $pass, $name);
        if (!$conn) {
            die('DB connection failed: ' . mysqli_connect_error());
        }
    }
    return $conn;
}

/**
 * query() — chay SELECT, tra ve mysqli_result hoac FALSE.
 * In loi SQL ra front-end neu that bai (Error-based).
 */
function query(string $sql)
{
    $conn = db();
    $res = mysqli_query($conn, $sql);
    if ($res === false) {
        // Loi SQL hien nguyen van ra trang -> Error-based SQLi
        echo '<div class="sql-error"><strong>SQL Error:</strong> '
            . mysqli_error($conn) . '</div>';
    }
    return $res;
}

/** exec_write() — chay INSERT/UPDATE/DELETE/CREATE (khong tra row). */
function exec_write(string $sql): bool
{
    $conn = db();
    $ok = mysqli_query($conn, $sql);
    if ($ok === false) {
        echo '<div class="sql-error"><strong>SQL Error:</strong> '
            . mysqli_error($conn) . '</div>';
        return false;
    }
    return true;
}

/**
 * exec_multi() — chay STACKED query bang mysqli_multi_query().
 * !!! Day la API CHO PHEP nhieu cau lenh ngan bang ';' trong MOT loi goi.
 *     Chinh vi vay endpoint dung ham nay bi STACKED-query injection,
 *     du MySQL mac dinh khong cho stacked qua mysqli_query() thong thuong.
 */
function exec_multi(string $sql): array
{
    $conn = db();
    $out = [];
    if (mysqli_multi_query($conn, $sql)) {
        do {
            if ($res = mysqli_store_result($conn)) {
                while ($row = mysqli_fetch_assoc($res)) {
                    $out[] = $row;
                }
                mysqli_free_result($res);
            }
        } while (mysqli_more_results($conn) && mysqli_next_result($conn));
    }
    if ($err = mysqli_error($conn)) {
        echo '<div class="sql-error"><strong>SQL Error:</strong> ' . $err . '</div>';
    }
    return $out;
}

/** Lay 1 row tien loi. */
function query_one(string $sql): ?array
{
    $res = query($sql);
    if ($res && mysqli_num_rows($res) > 0) {
        return mysqli_fetch_assoc($res);
    }
    return null;
}

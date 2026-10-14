# 📋 BẢNG PHÂN CÔNG NHIỆM VỤ DỰ ÁN & BÀI TẬP LỚN DEVSECOPS

> **Học phần:** Thực hành DevOps / DevSecOps  
> **Ứng dụng mục tiêu:** InlaneWeb Logistics Portal (PHP 8.2 & MariaDB)  
> **Repository nộp bài:** `wtfwhoyouare/PTIT-DevOps-SonarQube`  
> **Tổng số file source code:** 33 files (Được chia đầy đủ 100%, không thiếu file nào)  
> **Chỉ tiêu lỗi mỗi thành viên:** Tối thiểu 4 lỗi (2 Code Quality + 2 Security)

---

## 👥 TỔNG QUAN PHÂN CHIA NHIỆM VỤ

| STT | Thành viên | Vai trò phụ trách | Số lượng file | Đóng góp Code Quality | Đóng góp Security |
| :-: | :--- | :--- | :-: | :--- | :--- |
| 1 | **Nam** | DevOps & Database Lead | 7 files | 2 lỗi (`lib/db.php`) | 2 lỗi (Config & DB Query) |
| 2 | **Hải** | Core Web, Routing & Layout | 7 files | 2 lỗi (`index.php`, `layout.php`) | 2 lỗi (Server & Header Config) |
| 3 | **Mạnh** | User Auth, Profile & Community | 7 files | 2 lỗi (`login.php`, `account.php`) | 2 lỗi (SQLi Login & Account) |
| 4 | **Đức Anh** | Admin Portal & Reporting | 6 files | 2 lỗi (`admin_dashboard`, `admin_export`) | 2 lỗi (SQLi Admin Dashboard & Console) |
| 5 | **Mai** | Logistics Tracking & Ports Catalog | 6 files | 2 lỗi (`home.php`, `track.php`) | 2 lỗi (SQLi Track & Shipment) |
| **TỔNG** | **5 Thành viên** | **Toàn bộ hệ thống InlaneWeb** | **33/33 files** | **10 lỗi Code Quality** | **10 lỗi Security SAST** |

---

## 📁 CHI TIẾT PHÂN CÔNG TỪNG THÀNH VIÊN

### 1. 🧑‍💻 Thành viên: NAM (DevOps & Database Lead)
*Phụ trách hạ tầng Docker container, cấu hình MariaDB, schema khởi tạo dữ liệu và thư viện kết nối trung tâm.*

#### 📄 Danh sách file phân công commit & push (7 files):
1. `InlaneWeb/docker-compose.yml` *(Cấu hình multi-container chạy app web và db)*
2. `InlaneWeb/db/Dockerfile` *(Dockerfile đóng gói MariaDB)*
3. `InlaneWeb/db/init.sql` *(Script SQL tạo bảng và nạp dữ liệu mẫu ban đầu)*
4. `InlaneWeb/db/lab.cnf` *(Cấu hình tinh chỉnh dịch vụ MariaDB)*
5. `InlaneWeb/db/fix-perms-entrypoint.sh` *(Shell script phân quyền entrypoint volume CSDL)*
6. `InlaneWeb/web/src/lib/db.php` *(Thư viện kết nối CSDL và các hàm truy vấn cốt lõi)*
7. `InlaneWeb/README.md` *(Tài liệu hướng dẫn khởi chạy môi trường)*

#### 🔍 4 lỗi phụ trách trong Báo cáo Bài tập lớn:
- **Code Quality 1 (SonarQube `php:S100` - Minor):** Hàm `exec_write` tại `lib/db.php:49` không tuân thủ quy ước đặt tên chuẩn camelCase `^[a-z][a-zA-Z0-9]*$`.
- **Code Quality 2 (SonarQube `php:S100` - Minor):** Hàm `query_one` tại `lib/db.php:88` vi phạm chuẩn đặt tên của dự án.
- **Security 1 (Code Audit / OWASP A05 - Medium):** Hardcode thông tin xác thực CSDL (`DB_USER`, `DB_PASS`) trong `lib/db.php:10-15` thay vì đọc từ biến môi trường bí mật.
- **Security 2 (Semgrep / CWE-89 - Critical):** Hàm `query($sql)` tại `lib/db.php:41` cho phép thực thi câu lệnh SQL trực tiếp mà không bắt buộc dùng Prepared Statements.

---

### 2. 🧑‍💻 Thành viên: HẢI (Core Web, Routing & Layout)
*Phụ trách cấu hình Web Server Apache, PHP runtime, URL rewriting, router trung tâm và master layout.*

#### 📄 Danh sách file phân công commit & push (7 files):
1. `InlaneWeb/web/Dockerfile` *(Dockerfile đóng gói môi trường PHP 8.2 Apache)*
2. `InlaneWeb/web/php.ini` *(File cấu hình runtime của PHP)*
3. `InlaneWeb/web/apache/000-default.conf` *(Cấu hình VirtualHost Apache)*
4. `InlaneWeb/web/src/.htaccess` *(Quy tắc rewrite URL toàn bộ request về index.php)*
5. `InlaneWeb/web/src/index.php` *(Router chính điều hướng các trang nghiệp vụ)*
6. `InlaneWeb/web/src/assets/style.css` *(Toàn bộ stylesheet giao diện ứng dụng)*
7. `InlaneWeb/web/src/lib/layout.php` *(Thư viện render Header, Navigation bar và Footer)*

#### 🔍 4 lỗi phụ trách trong Báo cáo Bài tập lớn:
- **Code Quality 1 (SonarQube `php:S2003` - Minor):** Dùng lệnh `require` thay vì `require_once` tại `index.php:8-9, 20` gây nguy cơ nạp tệp lặp lại.
- **Code Quality 2 (SonarQube `php:S100` - Minor):** Các hàm `render_header` và `render_footer` tại `lib/layout.php:13, 50` vi phạm quy ước đặt tên camelCase.
- **Security 1 (Security Header Audit / OWASP A05 - Medium):** Cấu hình Apache `000-default.conf` thiếu các HTTP Security Headers thiết yếu (`X-Frame-Options`, `Content-Security-Policy`).
- **Security 2 (Configuration Audit / CWE-200 - Low/Medium):** Cấu hình `web/php.ini` để lộ thông tin phiên bản PHP (`expose_php = On`) và thiếu giới hạn bộ nhớ chặt chẽ.

---

### 3. 🧑‍💻 Thành viên: MẠNH (User Auth, Profile & Community)
*Phụ trách phân hệ xác thực (Đăng nhập, Đăng xuất), hồ sơ cá nhân và khu vực tin tức, thảo luận của người dùng.*

#### 📄 Danh sách file phân công commit & push (7 files):
1. `InlaneWeb/web/src/pages/login.php` *(Giao diện và xử lý đăng nhập hệ thống)*
2. `InlaneWeb/web/src/pages/logout.php` *(Xử lý huỷ session đăng xuất)*
3. `InlaneWeb/web/src/pages/account.php` *(Trang thông tin tài khoản và danh sách đơn cá nhân)*
4. `InlaneWeb/web/src/pages/account_update.php` *(Xử lý cập nhật email cá nhân)*
5. `InlaneWeb/web/src/pages/news.php` *(Trang hiển thị bài viết tin tức logistics)*
6. `InlaneWeb/web/src/pages/comment_add.php` *(Xử lý thêm bình luận bài viết)*
7. `InlaneWeb/web/src/pages/comment_delete.php` *(Xử lý xoá bình luận)*

#### 🔍 4 lỗi phụ trách trong Báo cáo Bài tập lớn:
- **Code Quality 1 (SonarQube `php:S121` - Critical):** Thiếu cặp dấu ngoặc nhọn `{}` cho khối lệnh lồng nhau tại `pages/login.php:36`.
- **Code Quality 2 (SonarQube `Web:InputWithoutLabelCheck` - Major):** Thẻ `<input>` tại `pages/login.php:40` và `pages/account.php:29` thiếu thuộc tính `id` để liên kết với `<label>`.
- **Security 1 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection tại chức năng đăng nhập `pages/login.php:22` cho phép bypass login bằng `' OR '1'='1`.
- **Security 2 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection tại chức năng cập nhật email `pages/account_update.php:20` khi nối trực tiếp biến `$email`.

---

### 4. 🧑‍💻 Thành viên: ĐỨC ANH (Admin Portal & Reporting)
*Phụ trách phân hệ Quản trị viên: dashboard tổng quan, console nội bộ, xuất dữ liệu báo cáo và tài liệu kỹ thuật.*

#### 📄 Danh sách file phân công commit & push (6 files):
1. `InlaneWeb/web/src/pages/admin_dashboard.php` *(Dashboard quản trị user và trạng thái vận chuyển)*
2. `InlaneWeb/web/src/pages/admin_console.php` *(Giao diện console thực thi truy vấn nghiệp vụ)*
3. `InlaneWeb/web/src/pages/admin_report_export.php` *(Chức năng xuất báo cáo quản trị)*
4. `InlaneWeb/web/src/pages/report_download.php` *(Xử lý tải file báo cáo đã xuất)*
5. `InlaneWeb/writeup.md` *(Tài liệu phân tích kiến trúc an toàn của cổng thông tin)*
6. `InlaneWeb/web/src/files/.gitkeep` *(Thư mục lưu trữ các tệp tin kết xuất)*

#### 🔍 4 lỗi phụ trách trong Báo cáo Bài tập lớn:
- **Code Quality 1 (SonarQube `Web:InputWithoutLabelCheck` - Major):** Input tìm kiếm khách hàng tại `pages/admin_dashboard.php:26` thiếu liên kết nhãn `<label>`.
- **Code Quality 2 (SonarQube `Web:S6853` - Major):** Label tại `pages/admin_report_export.php:36` không liên kết hợp lệ với control nhập liệu.
- **Security 1 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection trong chức năng tìm kiếm người dùng tại `pages/admin_dashboard.php:33` qua biến `$_GET['customer']`.
- **Security 2 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection tại console nội bộ `pages/admin_console.php:33` qua biến `$_GET['filter']`.

---

### 5. 🧑‍💻 Thành viên: MAI (Logistics Tracking & Ports Catalog)
*Phụ trách cổng tra cứu vận đơn logistics, API tra cứu hành trình lô hàng và danh mục cảng biển đối tác.*

#### 📄 Danh sách file phân công commit & push (6 files):
1. `InlaneWeb/web/src/pages/home.php` *(Trang chủ tìm kiếm nhanh lô hàng)*
2. `InlaneWeb/web/src/pages/track.php` *(Trang giao diện tra cứu chi tiết hành trình vận đơn)*
3. `InlaneWeb/web/src/pages/track_api.php` *(Endpoint API trả dữ liệu hành trình dạng JSON)*
4. `InlaneWeb/web/src/pages/shipment_detail.php` *(Trang xem thông tin chi tiết một lô hàng)*
5. `InlaneWeb/web/src/pages/ports.php` *(Danh bạ hệ thống cảng biển đối tác)*
6. `InlaneWeb/web/src/pages/port_detail.php` *(Trang xem chi tiết cơ sở hạ tầng từng cảng)*

#### 🔍 4 lỗi phụ trách trong Báo cáo Bài tập lớn:
- **Code Quality 1 (SonarQube `Web:InputWithoutLabelCheck` - Major):** Thẻ `<input>` tìm kiếm trên trang chủ `pages/home.php:9` thiếu nhãn accessibility.
- **Code Quality 2 (SonarQube `Web:InputWithoutLabelCheck` - Major):** Thẻ `<input>` tìm kiếm cảng biển tại `pages/ports.php:17` và tra cứu tại `pages/track.php:9` thiếu nhãn hợp lệ.
- **Security 1 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection khi tra cứu mã vận đơn `pages/track.php:12` qua biến `$_GET['tracking_no']`.
- **Security 2 (Semgrep `tainted-sql-string` / CWE-89 - High/Critical):** SQL Injection xem chi tiết lô hàng tại `pages/shipment_detail.php:12` cho phép khai thác UNION-based SQLi.

---

## 🚀 QUY TRÌNH COMMIT & PUSH ĐỂ TẠO LỊCH SỬ GIT ĐẸP MẮT

Để repo `wtfwhoyouare/PTIT-DevOps-SonarQube` có đồ thị Git chuẩn chỉnh, không bị xung đột code:

### Bước 1: Khởi tạo và đẩy nền tảng (Thành viên: NAM)
1. Nam clone repo mới về máy:
   ```bash
   git clone https://github.com/wtfwhoyouare/PTIT-DevOps-SonarQube.git
   cd PTIT-DevOps-SonarQube
   ```
2. Nam copy **7 file được phân công** vào thư mục `InlaneWeb/`.
3. Commit và push lên nhánh chính:
   ```bash
   git add InlaneWeb/
   git commit -m "feat(infra): setup Docker environment, MariaDB schema and db connector"
   git push origin main
   ```

### Bước 2: Bổ sung cấu hình Web & Layout (Thành viên: HẢI)
1. Hải pull code mới nhất:
   ```bash
   git pull origin main
   ```
2. Hải thêm **7 file của Hải** vào `InlaneWeb/`.
3. Commit và push:
   ```bash
   git add InlaneWeb/
   git commit -m "feat(core): configure Apache, PHP runtime, router and master layout"
   git push origin main
   ```

### Bước 3: Tạo nhánh riêng cho các module tính năng (MẠNH, ĐỨC ANH, MAI)
Các bạn tạo branch tương ứng với module của mình:
- **Mạnh:**
  ```bash
  git checkout -b feature/user-auth-profile
  # Thêm 7 file của Mạnh
  git add InlaneWeb/
  git commit -m "feat(auth): implement user authentication, profile and discussion board"
  git push origin feature/user-auth-profile
  ```
- **Đức Anh:**
  ```bash
  git checkout -b feature/admin-reports
  # Thêm 6 file của Đức Anh
  git add InlaneWeb/
  git commit -m "feat(admin): build admin dashboard, query console and report export"
  git push origin feature/admin-reports
  ```
- **Mai:**
  ```bash
  git checkout -b feature/logistics-tracking
  # Thêm 6 file của Mai
  git add InlaneWeb/
  git commit -m "feat(logistics): add tracking portal, tracking API and ports directory"
  git push origin feature/logistics-tracking
  ```

### Bước 4: Tạo Pull Request (PR) và Merge vào `main`
- Lần lượt tạo PR trên GitHub từ các nhánh vào `main` và merge lại.
- Thầy cô khi xem tab **Insights $\rightarrow$ Network** và **Contributors** sẽ thấy mô hình phân nhánh và đóng góp của cả 5 bạn vô cùng đồng đều, bài bản và chuyên nghiệp!

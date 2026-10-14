# PTIT-DevOps-Draft

Dự án PHP 8.2 / Docker phục vụ đào tạo SQL Injection. Mã nguồn ứng dụng nằm trong
[`InlaneWeb/`](InlaneWeb/README.md); ứng dụng cố ý chứa lỗ hổng.

## Quy trình phát triển nhóm & DevSecOps Pipeline

- Các thành viên làm việc trên các nhánh tính năng (`dev`, `feature/*`).
- Khi hoàn thành, tạo Pull Request và **merge vào `main`**: Pipeline GitHub Actions sẽ **tự động kích hoạt** song song:
  1. **SonarQube Community Build:** Đánh giá chất lượng mã nguồn (Code Quality, Bugs, Độ tin cậy).
  2. **Semgrep SAST:** Quét chuyên sâu các lỗ hổng an toàn thông tin (SQL Injection, XSS, Cấu hình an toàn).

## SonarQube & Semgrep trên GitHub Actions

Workflow [SonarQube](.github/workflows/sonarqube.yml) chạy khi push lên `main`,
hoặc chạy thủ công trong **Actions → SonarQube → Run workflow** (chọn `main`).

```text
Checkout → kiểm thử công cụ báo cáo → PHP 8.2 lint
  → chạy SonarQube Community Build + H2 mới
  → đợi server → đổi mật khẩu admin → tạo project/gate/token tạm
  → SonarScanner → đợi server xử lý analysis
  → xuất HTML/JSON/Summary → upload artifact
  → trả trạng thái lint/scan/Quality Gate → xóa container và dữ liệu tạm
```

Không dùng snapshot, PostgreSQL, self-hosted runner hay SonarQube Cloud. Mỗi job
chạy độc lập trên GitHub-hosted Ubuntu. Không cần cấu hình GitHub Secret hoặc
SonarQube token trước: token được tạo trong job, mask khỏi log và mất hiệu lực
khi instance bị xóa. Cổng SonarQube chỉ bind loopback của runner.

### Kế hoạch triển khai và kiểm chứng

1. Ghim SonarQube image theo phiên bản/digest và GitHub Actions theo commit SHA.
2. Bootstrap instance mới, dùng token scan giới hạn theo project; mật khẩu admin
   ngẫu nhiên chỉ dùng trong job để quản trị và xuất dữ liệu có quyền Browse.
3. Quét `InlaneWeb/web/src`, gồm PHP/CSS; không chạy ứng dụng/database của lab.
4. Chờ Compute Engine xử lý đúng task ID; kiểm tra thực sự có PHP được phân tích.
5. Xuất toàn bộ trang issues/hotspots, metrics và Quality Gate; upload trước khi
   quyết định fail pipeline. Chạy thử trên GitHub Actions để kiểm chứng toàn bộ flow.

Các phiên bản được ghim trong workflow. Khi nâng cấp SonarQube, cập nhật cả tag
và digest rồi chạy kiểm chứng API/bootstrap/export trước khi dùng phiên bản mới.
PHP lint dùng dòng image `php:8.2-cli` để nhận bản vá PHP 8.2.

### Xem report

Vào **Actions → SonarQube → lần chạy của commit**:

- **Summary**: trạng thái gate, lint/scanner, số PHP files, thống kê issues và
  điều kiện gate. Gate thất bại vẫn có report nếu analysis hoàn tất.
- **Artifacts → sonarqube-report-…**: tải ZIP, giải nén và mở `report.html`.
  Báo cáo có severity, loại issue, file/dòng, rule và message; link source trỏ
  tới đúng commit trên GitHub. Hotspots nằm ở bảng riêng.

```text
reports/sonarqube/
├── report.html
├── summary.md
├── issues.json
├── hotspots.json
├── metrics.json
├── quality-gate.json
├── files.json
├── analysis-task.json
├── bootstrap.json
├── metadata.json
├── status.json
├── php-lint.log
├── server.log
└── container-state.json
```

Artifact giữ **30 ngày**, chịu giới hạn lưu trữ/chính sách repository của GitHub.
Report không commit vào Git. HTML là bản tĩnh tự tạo từ Web API; dashboard và
lịch sử SonarQube không còn sau job. Khi server/scanner lỗi, report ghi
`UNAVAILABLE` và kèm chẩn đoán; các JSON chưa lấy được sẽ không tồn tại.
Job bị hủy hoặc runner mất kết nối có thể chưa kịp upload report.

### Quality Gate và trạng thái pipeline

Gate được định nghĩa tại [`ci/sonarqube-quality-gate.json`](ci/sonarqube-quality-gate.json),
dùng **Standard Experience** và đánh giá **overall code**. Không dùng gate chỉ xét
new code vì database mới mỗi job không giữ baseline lịch sử.

| Điều kiện để đạt | Phạm vi |
| --- | --- |
| Security rating = A | Toàn bộ mã |
| Reliability rating = A | Toàn bộ mã |
| Maintainability rating = A | Toàn bộ mã |
| Hotspots đã review = 100%, khi metric áp dụng | Toàn bộ mã |
| Duplicated lines ≤ 10% | Toàn bộ mã |

Không áp dụng coverage gate: dự án chưa có PHPUnit/coverage report. Metric
không xuất hiện không đồng nghĩa giá trị bằng 0. Hotspots của lab chưa được
review có thể làm gate fail; không tự đánh dấu reviewed/false positive.

Push lên `main` mặc định **enforce gate**: Quality Gate không đạt sẽ làm job đỏ
**sau khi upload report**. Vì ứng dụng cố ý có lỗ hổng, gate đỏ có thể là kết quả
đúng, không phải lỗi cài đặt.

Để thử nghiệm ở chế độ report-only, chạy **Run workflow**, bỏ chọn
`enforce_quality_gate`. Chế độ này chỉ bỏ chặn vì gate; lỗi lint, bootstrap,
scanner, xử lý analysis hoặc xuất report vẫn làm pipeline thất bại.

### Giới hạn bảo mật và vận hành

- Community Build hỗ trợ PHP nhưng không có đầy đủ taint analysis SQLi qua
  nhiều hàm/tệp như Developer Edition trở lên. Gate xanh/zero vulnerabilities
  không chứng minh lab an toàn. Dùng bản phù hợp nếu mục tiêu là đánh giá SAST SQLi.
- Không hỗ trợ branch/PR analysis trong cấu hình này; workflow chỉ chạy `main`.
- Mỗi job phải tải/chạy server và analyzer; đây là lựa chọn phục vụ lab, không
  phải dịch vụ SonarQube lưu lịch sử lâu dài. Runner cần đủ RAM; server giới hạn 4 GB.
- Workflow không tự triển khai lab và không sửa các điểm cố ý vulnerable.
- Push mới có thể hủy scan cũ đang chạy vì các lần scan không chia sẻ trạng thái.

### Kiểm thử công cụ báo cáo tại máy

Chỉ cần Python 3.10+, không cần thư viện Python bên ngoài:

```powershell
python -m unittest discover -s tests -v
```

Các test kiểm tra pagination, HTML escaping, link đúng commit, gate fail vẫn
xuất report, report-only không che lỗi thực thi, timeout/missing metadata,
zero PHP files và không ghi credential vào báo cáo. Không dùng kết quả mock
này để kết luận container/scanner tích hợp đã chạy thành công.

### Khi GitHub không cho chạy workflow

GitHub Actions phải hoạt động cho tài khoản sở hữu repository. Nếu chạy thủ công
báo `HTTP 422: Actions has been disabled for this user`, đây là blocker cấp tài
khoản dù API quyền repository có thể vẫn trả `enabled: true`. Kiểm tra thông báo
trong trang Actions; nếu tài khoản đang bị GitHub vô hiệu hóa Actions, liên hệ
[GitHub Support](https://support.github.com/) để được xem xét. Đổi quyền repository
không tự khắc phục trạng thái vô hiệu hóa riêng này.

Sau khi GitHub mở lại Actions, chạy kiểm chứng đầu tiên ở chế độ report-only:

```powershell
gh workflow run sonarqube.yml --ref main -f enforce_quality_gate=false
gh run list --workflow sonarqube.yml --limit 5
```

Xác nhận job hoàn tất phần scan/export và tải được `report.html`. Sau đó chạy
lại với `enforce_quality_gate=true` để xác nhận job đỏ đúng khi gate không đạt.
Xem [hướng dẫn trạng thái Actions bị vô hiệu hóa](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository).

### Tài liệu

- [SonarQube Docker evaluation](https://docs.sonarsource.com/sonarqube-community-build/try-out-sonarqube)
- [GitHub Actions integration](https://docs.sonarsource.com/sonarqube-community-build/devops-platform-integration/github-integration/adding-analysis-to-github-actions-workflow)
- [SonarQube Web API](https://docs.sonarsource.com/sonarqube-community-build/extension-guide/web-api)
- [SonarQube Server edition comparison](https://www.sonarsource.com/plans-and-pricing/sonarqube/)
- [GitHub artifact downloads](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts)

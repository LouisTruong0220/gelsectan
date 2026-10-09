# -*- coding: utf-8 -*-
"""Dựng trang hướng dẫn GỬI KHÁCH: nối Google Sheets của khách với robot.

    python google-sheet/dung-huong-dan.py
    → google-sheet/huong-dan-ket-noi-google-sheets.html   (một tệp tự chứa, gửi thẳng cho khách)

Đoạn mã Apps Script lấy NGUYÊN từ Code.gs bên cạnh — chỉ có MỘT bản mã, sửa Code.gs rồi chạy lại.
Trang này đi ra ngoài công ty: KHÔNG nhắc đường dẫn máy Roboworld, không đòi khách cài gì.
"""
import html, io, os, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ma = io.open(os.path.join(HERE, "Code.gs"), encoding="utf-8").read()

TRANG = u"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Nối Google Sheets với robot — hướng dẫn 10 phút</title>
<style>
:root{--do:#C13F28;--do-dam:#5E0F18;--dao:#FDE9E1;--chu:#1b1b1b;--nhat:#5b5b5b;--vien:#e6dcd8}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI",Roboto,Arial,sans-serif;color:var(--chu);background:#faf7f6;line-height:1.6;font-size:17px}
.khung{max-width:880px;margin:0 auto;padding:28px 20px 60px}
header{border-bottom:4px solid var(--do);padding-bottom:16px;margin-bottom:24px}
header small{color:var(--do);font-weight:700;letter-spacing:.08em;text-transform:uppercase}
h1{font-size:30px;line-height:1.25;margin:6px 0 8px;color:var(--do-dam)}
h2{font-size:21px;margin:34px 0 10px;color:var(--do)}
p{margin:8px 0}
.tom{background:var(--dao);border-left:5px solid var(--do);padding:14px 18px;border-radius:0 10px 10px 0}
ol.buoc{counter-reset:b;list-style:none;padding:0;margin:0}
ol.buoc > li{counter-increment:b;position:relative;background:#fff;border:1px solid var(--vien);border-radius:12px;
  padding:16px 18px 16px 66px;margin:12px 0}
ol.buoc > li::before{content:counter(b);position:absolute;left:16px;top:16px;width:36px;height:36px;border-radius:50%;
  background:var(--do);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center}
ol.buoc b.t{display:block;font-size:18px;margin-bottom:4px}
kbd{background:#fff;border:1px solid #cfc4c0;border-bottom-width:2px;border-radius:6px;padding:1px 7px;font:inherit;font-size:15px;white-space:nowrap}
code{background:#f1e9e6;border-radius:5px;padding:1px 6px;font-family:Consolas,monospace;font-size:15px}
.ma{position:relative;margin:12px 0}
pre{background:#1e1a19;color:#f4ece9;border-radius:12px;padding:16px;overflow:auto;font-family:Consolas,monospace;font-size:13.5px;
  line-height:1.5;max-height:420px;margin:0}
.nut{position:absolute;right:12px;top:12px;background:var(--do);color:#fff;border:0;border-radius:8px;padding:8px 16px;
  font:inherit;font-weight:700;cursor:pointer}
.luu-y{background:#fff;border:1px dashed var(--do);border-radius:12px;padding:14px 18px;margin:14px 0}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;border:1px solid var(--vien)}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid var(--vien);vertical-align:top}
th{background:var(--do);color:#fff}
footer{margin-top:40px;padding-top:16px;border-top:1px solid var(--vien);color:var(--nhat);font-size:15px}
@media print{.nut{display:none}pre{max-height:none}}
</style>
</head>
<body>
<div class="khung">
<header>
  <small>Roboworld · Hướng dẫn cho khách hàng</small>
  <h1>Nối Google Sheets của anh chị với robot</h1>
  <p>Mỗi khách tham dự để lại thông tin trên robot sẽ tự thành <b>một dòng mới</b> trong trang tính của anh chị,
     sau vài giây. Làm một lần, khoảng 10 phút, không cần cài phần mềm.</p>
</header>

<div class="tom">
  <b>Anh chị cần:</b> một tài khoản Google và một trang tính Google Sheets (tạo mới hoặc dùng trang có sẵn).<br>
  <b>Xong việc, anh chị gửi lại cho Roboworld hai thứ:</b> ① địa chỉ ứng dụng web (kết thúc bằng <code>/exec</code>)
  và ② mã bí mật anh chị tự đặt ở bước 3.
</div>

<h2>Các bước</h2>
<ol class="buoc">
  <li><b class="t">Mở trang tính</b>
      Vào <code>sheets.google.com</code>, tạo một trang tính mới (ví dụ đặt tên “Khách sự kiện — robot”), hoặc mở trang anh chị muốn dùng.
      Robot sẽ tự tạo một tab tên <b>“Khách để lại thông tin”</b> — các tab khác không bị đụng tới.</li>
  <li><b class="t">Mở Apps Script</b>
      Trên thanh bảng chọn: <kbd>Tiện ích mở rộng</kbd> → <kbd>Apps Script</kbd>. Một thẻ mới mở ra với vài dòng mã có sẵn —
      <b>xoá hết</b> rồi dán đoạn mã ở cuối trang này vào.</li>
  <li><b class="t">Đặt mã bí mật</b>
      Ở gần đầu đoạn mã có dòng <code>var MA_BI_MAT = 'doi-ma-nay-truoc-khi-dung';</code>.
      Đổi phần trong dấu nháy thành một chuỗi riêng của anh chị, chỉ dùng chữ không dấu và số, ví dụ <code>chibach-2026-k7m2</code>.
      Bấm biểu tượng đĩa mềm để lưu.</li>
  <li><b class="t">Triển khai thành ứng dụng web</b>
      Góc trên bên phải: <kbd>Triển khai</kbd> → <kbd>Tùy chọn triển khai mới</kbd> → bấm bánh răng chọn loại <kbd>Ứng dụng web</kbd>.<br>
      · <b>Thực thi dưới tên:</b> Tôi<br>
      · <b>Người có quyền truy cập:</b> Bất kỳ ai<br>
      Bấm <kbd>Triển khai</kbd>. Google hỏi cấp quyền → chọn tài khoản của anh chị → <kbd>Nâng cao</kbd> →
      <kbd>Đi tới … (không an toàn)</kbd> → <kbd>Cho phép</kbd>. Màn cảnh báo này hiện ra vì đoạn mã do chính anh chị
      dán vào, chưa qua Google thẩm định — nó chỉ có quyền ghi vào trang tính này.</li>
  <li><b class="t">Sao chép địa chỉ</b>
      Google hiện “URL ứng dụng web”, dạng <code>https://script.google.com/macros/s/…/exec</code>. Bấm <kbd>Sao chép</kbd>.</li>
  <li><b class="t">Thử nhanh</b>
      Dán địa chỉ đó vào một thẻ trình duyệt mới. Thấy dòng chữ <code>{"ok":true, …}</code> là ứng dụng đang chạy.</li>
  <li><b class="t">Gửi cho Roboworld</b>
      Gửi <b>địa chỉ ở bước 5</b> và <b>mã bí mật ở bước 3</b> cho kỹ thuật viên Roboworld. Bên em nạp vào robot và gửi thử một dòng
      — anh chị sẽ thấy dòng “DÒNG THỬ KẾT NỐI” hiện trong trang tính (xoá đi được).</li>
</ol>

<h2>Trang tính sẽ có những cột nào</h2>
<table>
  <tr><th>Cột</th><th>Nội dung</th></tr>
  <tr><td>Thời gian</td><td>Giờ và ngày khách bấm gửi trên robot</td></tr>
  <tr><td>Họ và tên · Số điện thoại</td><td>Hai ô bắt buộc. Số điện thoại lưu dạng chữ để giữ số 0 ở đầu</td></tr>
  <tr><td>Chức vụ · Doanh nghiệp / đơn vị</td><td>Không bắt buộc — khách có thể bỏ trống</td></tr>
  <tr><td>Nguồn</td><td>Khách để lại thông tin từ chế độ nào: Tra cứu, Giao tiếp AI hay màn chính</td></tr>
  <tr><td>Câu hỏi đang xem</td><td>Câu hỏi khách xem gần nhất trước khi để lại thông tin — gợi ý cho cuộc gọi tư vấn</td></tr>
  <tr><td>Robot · Mã dòng</td><td>Dùng để đối chiếu; mã dòng giúp tránh ghi trùng khi mạng chập chờn</td></tr>
</table>

<div class="luu-y">
  <b>Ba điều nên biết</b><br>
  · <b>Mất mạng không mất khách.</b> Robot luôn lưu vào bộ nhớ của nó trước, rồi mới gửi lên trang tính; chưa gửi được thì
    cứ 30 giây thử lại. Cuối sự kiện Roboworld cũng gửi anh chị một tệp Excel đối chiếu.<br>
  · <b>Giữ kín địa chỉ và mã bí mật.</b> Ai có cả hai là ghi được dòng vào trang tính (không đọc, không xoá được).
    Muốn khoá lại sau sự kiện: <kbd>Triển khai</kbd> → <kbd>Quản lý các tùy chọn triển khai</kbd> → <kbd>Lưu trữ</kbd>.<br>
  · <b>Đây là dữ liệu cá nhân của khách tham dự.</b> Anh chị chỉ chia sẻ trang tính cho người cần dùng.
</div>

<h2>Đoạn mã để dán ở bước 2</h2>
<div class="ma">
  <button class="nut" onclick="chep(this)">Sao chép mã</button>
  <pre id="ma">__MA__</pre>
</div>

<footer>Cần hỗ trợ: Roboworld · hotline 0866 153 946</footer>
</div>
<script>
function chep(nut){
  var t = document.getElementById('ma').textContent;
  function xong(){ nut.textContent = 'Đã sao chép'; setTimeout(function(){ nut.textContent = 'Sao chép mã'; }, 2000); }
  if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(t).then(xong, tay); } else tay();
  function tay(){
    var r = document.createRange(); r.selectNodeContents(document.getElementById('ma'));
    var s = getSelection(); s.removeAllRanges(); s.addRange(r);
    try{ document.execCommand('copy'); xong(); }catch(e){ nut.textContent = 'Bôi đen sẵn — bấm Ctrl+C'; }
  }
}
</script>
</body>
</html>
"""

ra = os.path.join(HERE, "huong-dan-ket-noi-google-sheets.html")
io.open(ra, "w", encoding="utf-8").write(TRANG.replace("__MA__", html.escape(ma)))
print("✔ " + ra)

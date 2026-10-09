# -*- coding: utf-8 -*-
"""Ghép khung-app.html + du-lieu/app-data.json → demo/index.html tự chứa, rồi rải sang
android/app/src/main/assets/ để build APK.  (Robot Gelsectan — Chi Bách Pharma — Minibot)

    python dung-du-lieu.py     # chạy trước nếu đổi DOCX hoặc bảng viết tay
    python dung-app.py

Vì sao nhúng dữ liệu vào thẳng HTML: Chromium chặn fetch() qua file://, nháy đúp mở tệp là
trang trắng. Vì sao script tự rải sang assets/: chép tay thì LẦN NÀO CŨNG QUÊN — build ra APK
vẫn là giao diện cũ.

CỔNG WEBVIEW 66 — MINIBOT CHẠY CHROME 66 (2018), ROM KHOÁ KHÔNG NÂNG ĐƯỢC. CSS đời mới bị bỏ
qua LẶNG LẼ, JS đời mới GIẾT CẢ KHỐI SCRIPT (app ra trang chết, không một dòng lỗi).
Thấy mẫu cấm là DỪNG, không sinh tệp.
"""
import base64, io, json, os, re, shutil, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
KHUNG = os.path.join(HERE, "khung-app.html")
DULIEU = os.path.join(HERE, "du-lieu", "app-data.json")
DEMO = os.path.join(HERE, "demo")
ASSETS = os.path.join(HERE, "android", "app", "src", "main", "assets")
os.makedirs(DEMO, exist_ok=True)

khung = io.open(KHUNG, encoding="utf-8").read()
data = io.open(DULIEU, encoding="utf-8").read()

CAM = [
    (r"(?<![-\w])gap\s*:",     "flexbox gap chỉ có từ Chrome 84 — lưới dùng grid-gap, flex dùng margin"),
    (r"(?<![-\w])inset\s*:",   "inset chỉ có từ Chrome 87 — viết đủ top/right/bottom/left"),
    (r"\?\.[\w\[(]",           "optional chaining ?. chỉ có từ Chrome 80 — giết cả khối script"),
    (r"\?\?",                  "toán tử ?? chỉ có từ Chrome 80 — giết cả khối script"),
    (r"\.flat\(|\.flatMap\(",  "Array.flat chỉ có từ Chrome 69"),
    (r"\.matchAll\(",          "String.matchAll chỉ có từ Chrome 73"),
    (r"Object\.fromEntries",   "Object.fromEntries chỉ có từ Chrome 73"),
    (r"\.replaceAll\(",        "String.replaceAll chỉ có từ Chrome 85"),
    (r"backdrop-filter",       "backdrop-filter chỉ có từ Chrome 76"),
    (r"aspect-ratio\s*:",      "aspect-ratio chỉ có từ Chrome 88"),
    (r":is\(|:where\(",        ":is() / :where() chỉ có từ Chrome 88"),
    (r"\.at\(-",               "Array.at chỉ có từ Chrome 92"),
    (r"globalThis",            "globalThis chỉ có từ Chrome 71"),
    (r"catch\s*\{",            "catch không tham số (catch {) — viết catch(e) cho chắc"),
    (r"\bclamp\(|\bmin\(.*rem|\bmax\(.*rem", "CSS clamp()/min()/max() chỉ có từ Chrome 79"),
    (r"\(\?<[=!]",             "lookbehind trong biểu thức chính quy — sai là giết cả khối script trên Chrome cũ"),
    (r"place-items|place-content", "place-items/place-content — dùng align-items + justify-content cho chắc"),
    (r"margin\s*:\s*0\s+auto", "margin:0 auto XOÁ margin-top đang thay cho khoảng cách hàng — viết margin-left/right riêng"),
]
loi = []
for mau, vi_sao in CAM:
    for so, dong in enumerate(khung.splitlines(), 1):
        # Chú thích nói về mẫu cấm thì không tính
        if re.search(mau, dong) and not re.match(r"\s*(/\*|\*|//|<!--|⚠)", dong):
            loi.append("khung-app.html dòng %d: %s\n       %s" % (so, vi_sao, dong.strip()[:100]))
            break

# Mọi onclick="ham(" phải có hàm cùng tên — gõ sai tên là nút chết câm.
for ten in sorted(set(re.findall(r'onclick="(?:if\([^)]*\)\s*)?([a-zA-Z_]\w*)\(', khung))):
    if not re.search(r"function\s+%s\s*\(" % ten, khung):
        loi.append("onclick gọi hàm '%s' mà không có function nào tên đó" % ten)

# ⚠ Biến tên CAU ở lớp web ĐÈ MẤT cây cầu addJavascriptInterface (dính ở app giao hàng Bella).
if re.search(r"\b(var|let|const)\s+CAU\b", khung):
    loi.append("khung-app.html khai biến tên CAU — đè mất cầu nối window.CAU, robot sẽ đứng im")

MOC = "/*__DU_LIEU__*/"
if MOC not in khung:
    loi.append("khung-app.html thiếu mốc " + MOC)
for moc in ("/*__BAT_DAU_BO_TIM__*/", "/*__HET_BO_TIM__*/"):
    if moc not in khung:
        loi.append("khung-app.html thiếu mốc %s — bộ thử tools/thu-tim-kiem.mjs bóc mã giữa hai mốc này" % moc)

d = json.loads(data)
for thu_muc, mau in (("bieu-cam", r"bieu-cam/([\w\-]+\.mp4)"), ("hinh", r"hinh/([\w\-]+\.png)")):
    co = set(os.listdir(os.path.join(HERE, thu_muc)))
    for tep in sorted(set(re.findall(mau, khung))):
        if tep not in co:
            loi.append("khung-app.html gọi %s/%s nhưng thư mục không có tệp đó" % (thu_muc, tep))

# Lời app đọc mà dữ liệu không có → robot IM LẶNG, không lỗi. Mọi L.<khoá> phải có trong D.loi.
for khoa in sorted(set(re.findall(r"\bL\.([a-z_]+)\b", khung))):
    if khoa not in d.get("loi", {}):
        loi.append("khung-app.html dùng lời L.%s mà dung-du-lieu.py (bảng LOI) không có" % khoa)
for khoa in sorted(set(re.findall(r"ra\('[\w-]+', '([a-z_]+)'", khung))):
    if khoa not in d.get("loi", {}):
        loi.append("phanXu dùng lời '%s' mà bảng LOI không có" % khoa)

if not os.path.isfile(os.path.join(HERE, "nhac", "mua.mp3")):
    loi.append("thiếu nhac/mua.mp3 — nút Nhảy múa sẽ câm")

if loi:
    print("✘ DỪNG — chưa đạt:")
    for x in loi:
        print("   · " + x)
    raise SystemExit(1)

# ── Ghép ────────────────────────────────────────────────────────────────
nhung = data.replace("</", "<\\/")
html = khung.replace(MOC, "window.DU_LIEU=" + nhung + ";")


# Bản demo/index.html: logo nhúng base64 (quy tắc 4 của workspace — HTML tự chứa); chỉ clip
# biểu cảm để rời cạnh tệp (nhúng 3 MB video vào HTML là quá nặng).
def nhung_anh(m):
    p = os.path.join(HERE, "hinh", m.group(1))
    return "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode("ascii")


html_demo = re.sub(r"hinh/([\w\-]+\.png)", nhung_anh, html)
io.open(os.path.join(DEMO, "index.html"), "w", encoding="utf-8").write(html_demo)


def rai(nguon, dich):
    """Chép đè từng tệp — không xoá hàng loạt (quy tắc 2 của workspace)."""
    os.makedirs(dich, exist_ok=True)
    n = 0
    for f in os.listdir(nguon):
        p = os.path.join(nguon, f)
        if os.path.isfile(p) and not f.endswith(".md"):
            shutil.copy2(p, os.path.join(dich, f))
            n += 1
    return n


# APK: khung + dữ liệu RỜI NHAU (MainActivity ghép lúc chạy, đọc thẻ nhớ trước) + bản ghép sẵn
# index.html làm lưới đỡ khi thẻ nhớ hỏng.
os.makedirs(ASSETS, exist_ok=True)
shutil.copy2(KHUNG, os.path.join(ASSETS, "khung-app.html"))
shutil.copy2(DULIEU, os.path.join(ASSETS, "app-data.json"))
io.open(os.path.join(ASSETS, "index.html"), "w", encoding="utf-8").write(html)
n1 = rai(os.path.join(HERE, "bieu-cam"), os.path.join(ASSETS, "bieu-cam"))
n2 = rai(os.path.join(HERE, "hinh"), os.path.join(ASSETS, "hinh"))
rai(os.path.join(HERE, "nhac"), os.path.join(ASSETS, "nhac"))
rai(os.path.join(HERE, "nhac"), os.path.join(DEMO, "nhac"))
# Giọng Yuna — chỉ chép tệp .mp3 (bỏ _da-sinh.json, _bang-tra.json)
os.makedirs(os.path.join(ASSETS, "giong"), exist_ok=True)
n3 = 0
for f in os.listdir(os.path.join(HERE, "giong", "mp3")) if os.path.isdir(os.path.join(HERE, "giong", "mp3")) else []:
    if f.endswith(".mp3"):
        shutil.copy2(os.path.join(HERE, "giong", "mp3", f), os.path.join(ASSETS, "giong", f)); n3 += 1
rai(os.path.join(HERE, "bieu-cam"), os.path.join(DEMO, "bieu-cam"))

print("✔ demo/index.html  %.0f KB · %d câu hỏi · %d nhóm" % (
    os.path.getsize(os.path.join(DEMO, "index.html")) / 1e3, len(d["cau"]), len(d["nhom"])))
print("✔ android assets: khung-app.html + app-data.json + index.html · %d clip biểu cảm · %d logo · %d MP3 giọng Yuna" % (n1, n2, n3))

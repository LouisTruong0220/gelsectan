# -*- coding: utf-8 -*-
"""Sinh KHO KIẾN THỨC để nạp lên Robot Portal (OrionStar) — cho AgentOS trả lời câu NGOÀI bộ tìm.

    python dung-kho-tri-thuc.py
    → kho-tri-thuc/gelsectan-hoi-dap.txt      nạp lên Portal (cổng nhận .txt · .pdf · .docx)
    → kho-tri-thuc/persona-robot.md           chữ chép–dán vào ô persona / mục tiêu trên Portal (KHÔNG nạp)

Sinh từ CHÍNH du-lieu/app-data.json — màn hình, lời robot đọc và kho Portal không bao giờ lệch nhau.
Persona lấy NGUYÊN từ MainApplication.kt (hằng PERSONA, MUC_TIEU) — một bản duy nhất.

⚠ Kho Portal cấu hình THEO DOANH NGHIỆP (hãng trả lời, mục A9): dùng CHUNG cho mọi robot trong tài
  khoản Roboworld. Tài liệu hành chính công Tây Hòa, Cao Xanh… đang nằm trên đó thì robot này cũng
  đọc được — và ngược lại. Vì vậy mỗi đoạn trong kho đều ghi rõ "Gelsectan — Chi Bách Pharma".
  Sự kiện xong nên GỠ tệp này khỏi Portal.
"""
import io, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(io.open(os.path.join(HERE, "du-lieu", "app-data.json"), encoding="utf-8"))
kt = io.open(os.path.join(HERE, "android", "app", "src", "main", "java", "vn", "roboworld", "chibach",
                          "MainApplication.kt"), encoding="utf-8").read()
RA = os.path.join(HERE, "kho-tri-thuc")
os.makedirs(RA, exist_ok=True)


def hang_kotlin(ten):
    m = re.search(r"const val %s =\s*((?:\"[^\"]*\"\s*\+?\s*)+)" % ten, kt)
    if not m:
        print("✘ Không bóc được hằng %s trong MainApplication.kt" % ten)
        raise SystemExit(1)
    return "".join(re.findall(r"\"([^\"]*)\"", m.group(1)))


persona, muc_tieu = hang_kotlin("PERSONA"), hang_kotlin("MUC_TIEU")

dong = []
dong.append("BỘ HỎI ĐÁP VỀ GELSECTAN — CHI BÁCH PHARMA")
dong.append("Nguồn: %s. Cập nhật %s." % (d["nguon"], d["cap_nhat"]))
dong.append("Tài liệu này là nguồn DUY NHẤT để trả lời câu hỏi về Gelsectan. Gelsectan là thiết bị y tế, "
            "không phải thuốc, không phải thực phẩm chức năng.")
dong.append("Người hỏi có thể đọc tên sản phẩm thành: Gen séc tan, Giơ séc tan, Ghen sếch tăng, Dên xéc tan, "
            "Séc tan, Gensectan. Tất cả đều là Gelsectan.")
dong.append("")
dong.append("NGUYÊN TẮC KHI TRẢ LỜI VỀ GELSECTAN")
for c in d["compliance"]:
    dong.append("- " + c)
dong.append("- Nội dung không có trong tài liệu này (giá bán, điểm bán, bệnh lý khác, trường hợp bệnh nhân cụ thể): "
            "nói rõ là chưa có dữ liệu và mời trao đổi với chuyên viên Medical tại quầy Chi Bách Pharma.")
dong.append("")
ten_nhom = {n["ma"]: n["ten"] for n in d["nhom"]}
for n in d["nhom"]:
    dong.append("=" * 60)
    dong.append("GELSECTAN — %s" % n["ten"].upper())
    dong.append("=" * 60)
    for c in d["cau"]:
        if c["nhom"] != n["ma"]:
            continue
        dong.append("")
        dong.append("Câu hỏi về Gelsectan (Chi Bách Pharma): " + c["hoi"])
        dong.append("Cách hỏi khác: " + "; ".join(c["bien_the"]))
        dong.append("Trả lời: " + c["dap"])
    dong.append("")

tep = os.path.join(RA, "gelsectan-hoi-dap.txt")
io.open(tep, "w", encoding="utf-8").write("\n".join(dong) + "\n")

md = u"""# Persona cho Robot Portal — robot Gelsectan (Chi Bách Pharma)

> Chép–dán vào ô tương ứng trên Robot Portal nếu cổng có ô persona / mục tiêu cho appId của app này.
> App cũng tự đặt hai đoạn này lúc khởi động (`setPersona` / `setObjective` trong MainApplication.kt) —
> tệp này sinh từ chính mã đó, đừng sửa tay; sửa ở MainApplication.kt rồi chạy lại `dung-kho-tri-thuc.py`.

## Persona

%s

## Mục tiêu

%s

## Nạp kho kiến thức

Nạp tệp `gelsectan-hoi-dap.txt` (cùng thư mục) lên kho kiến thức của Portal. **Không nạp tệp .md này.**

⚠ Kho Portal dùng chung cho mọi robot của tài khoản Roboworld. Sau sự kiện nên gỡ tệp Gelsectan khỏi kho,
không thì robot hành chính công cũng có thể trả lời câu hỏi bằng nội dung Gelsectan.
""" % (persona, muc_tieu)
io.open(os.path.join(RA, "persona-robot.md"), "w", encoding="utf-8").write(md)

# ── Cổng kiểm: persona phải mang đủ bốn nguyên tắc compliance của khách ──
thieu = [x for x in ("chữa khỏi", "thiết bị y tế", "tờ hướng dẫn sử dụng", "Medical") if x not in muc_tieu + persona]
if thieu:
    print("✘ Persona / mục tiêu trong MainApplication.kt thiếu ý compliance: %s" % ", ".join(thieu))
    raise SystemExit(1)

print("✔ kho-tri-thuc/gelsectan-hoi-dap.txt  %.1f KB · %d câu hỏi · %d cách hỏi khác" % (
    os.path.getsize(tep) / 1e3, len(d["cau"]), sum(len(c["bien_the"]) for c in d["cau"])))
print("✔ kho-tri-thuc/persona-robot.md")

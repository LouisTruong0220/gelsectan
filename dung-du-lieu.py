# -*- coding: utf-8 -*-
"""DOCX bộ câu hỏi của Chi Bách Pharma → du-lieu/app-data.json  (app Gelsectan — Minibot)

    python dung-du-lieu.py

NGUYÊN TẮC SỐ MỘT — ĐÂY LÀ NỘI DUNG Y TẾ, KHÁCH ĐÃ DUYỆT TỪNG CÂU:
  · Câu hỏi và câu trả lời BÓC NGUYÊN VĂN từ du-lieu/nguon/cau-hoi-co-ban-gelsectan.docx.
    Script này không sửa một chữ nào của phần hiển thị (trường `dap`).
  · Trường `doc` là bản để ROBOT ĐỌC: cùng nội dung, chỉ đổi CÁCH VIẾT cho máy đọc được —
    số viết thành chữ, tên riêng tiếng nước ngoài phiên âm (bảng PHAT_AM). Không thêm bớt ý.
  · Mọi câu do APP tự soạn (lời chào, lời mời, câu từ chối) gom ở LOI / DU_HANH / LE_TAN bên
    dưới — MỘT chỗ, để gửi Chi Bách Pharma duyệt trước sự kiện. Các câu giới thiệu chỉ dùng ý
    đã có trong bộ câu trả lời và tuân bốn nguyên tắc compliance ở cuối tài liệu của khách.

Khách gửi bản DOCX mới: chép đè vào du-lieu/nguon/ (giữ tên tệp) rồi chạy lại script.
Số câu, thứ tự đổi → xem lại ba bảng viết tay: NHOM_CUA · BIEN_THE · PHAT_AM.

CỔNG CHẤT LƯỢNG — sai một điều là DỪNG, không sinh tệp:
  · câu hỏi không có câu trả lời · id trong bảng viết tay không có trong DOCX (và ngược lại)
  · bản đọc còn chữ số / ký hiệu máy không đọc được
  · câu trả lời vi phạm compliance: có "chữa khỏi", hoặc gọi Gelsectan là "thuốc"
  · câu trả lời dài quá 30 giây đọc (khách yêu cầu ≤ 30 giây)
"""
import io, json, os, re, sys, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import docx

HERE = os.path.dirname(os.path.abspath(__file__))
NGUON = os.path.join(HERE, "du-lieu", "nguon", "cau-hoi-co-ban-gelsectan.docx")
RA = os.path.join(HERE, "du-lieu", "app-data.json")

# ═════════════════════════ BẢNG VIẾT TAY ═════════════════════════

# Sáu nhóm trên màn Tra cứu — chia theo việc người hỏi đang muốn biết.
NHOM = [
    ("co-che",     "Cơ chế tác động",             "Màng bảo vệ niêm mạc ruột, hấp thu, khác men vi sinh"),
    ("tong-quan",  "Tổng quan sản phẩm",          "Gelsectan là gì, thành phần, chỉ định, xuất xứ"),
    ("lieu-dung",  "Liều dùng và cách dùng",      "Liều, thời điểm uống, thời gian điều trị, bảo quản"),
    ("doi-tuong",  "Đối tượng đặc biệt",          "Trẻ em, thai kỳ, cho con bú, tương tác"),
    ("an-toan",    "An toàn",                     "Tác dụng phụ, dùng lâu dài, táo bón"),
    ("bang-chung", "Bằng chứng và lựa chọn",      "Nghiên cứu lâm sàng, so với loperamide, thể bệnh"),
]
NHOM_CUA = {
    "0.1": "tong-quan", "0.2": "tong-quan", "0.3": "tong-quan", "0.4": "tong-quan", "0.5": "tong-quan", "0.25": "tong-quan",
    "0.6": "co-che", "0.7": "co-che", "0.8": "co-che", "0.9": "co-che",
    "0.10": "lieu-dung", "0.11": "lieu-dung", "0.12": "lieu-dung", "0.13": "lieu-dung", "0.14": "lieu-dung", "0.18": "lieu-dung",
    "0.15": "doi-tuong", "0.16": "doi-tuong", "0.17": "doi-tuong",
    "0.19": "an-toan", "0.20": "an-toan", "0.21": "an-toan",
    "0.22": "bang-chung", "0.23": "bang-chung", "0.24": "bang-chung",
}

# CÁCH HỎI KHÁC của cùng một câu — nguyên liệu cho bộ tìm (khung-app.html, khối BO_TIM).
# Khách yêu cầu: "hỏi cùng một vấn đề nhưng diễn đạt khác nhau vẫn phải trả lời đúng".
# Viết bằng lời người thật sẽ nói ở quầy. KHÔNG chép các câu này sang bộ thử
# (tools/thu-tim-kiem.mjs) — bộ thử phải dùng cách nói KHÁC, không thì nó tự chấm bài mình.
# Sau mỗi buổi chạy máy thật: kéo nhật ký về, câu nào robot không nhận ra thì thêm vào đây.
BIEN_THE = {
    "0.1": ["Gelsectan là gì", "Gelsectan thuộc loại sản phẩm gì", "Gelsectan có phải là thuốc không",
            "đây là thuốc hay thiết bị y tế", "Gelsectan có phải thực phẩm chức năng không",
            "sản phẩm này được phân loại là gì", "giới thiệu về Gelsectan"],
    "0.2": ["thành phần của Gelsectan là gì", "Gelsectan gồm những chất gì", "trong Gelsectan có gì",
            "hoạt chất của Gelsectan", "công thức của Gelsectan gồm gì", "Gelsectan có xyloglucan không",
            "một viên có chứa những gì"],
    "0.3": ["chỉ định của Gelsectan", "Gelsectan chỉ định cho bệnh gì", "Gelsectan dùng trong trường hợp nào",
            "Gelsectan có tác dụng gì", "Gelsectan dùng để làm gì", "công dụng của Gelsectan",
            "Gelsectan điều trị bệnh gì", "bệnh nhân nào nên dùng Gelsectan",
            "Gelsectan dùng làm gì"],
    "0.4": ["Gelsectan sản xuất ở đâu", "xuất xứ của Gelsectan", "Gelsectan của nước nào", "Gelsectan của hãng nào",
            "nhà sản xuất Gelsectan là ai", "công ty nào phân phối Gelsectan", "Gelsectan nhập khẩu từ đâu"],
    "0.5": ["Gelsectan dạng gì", "Gelsectan là viên hay gói", "một hộp Gelsectan có bao nhiêu viên",
            "quy cách đóng gói của Gelsectan", "Gelsectan dạng viên nang phải không", "hộp mấy viên"],
    "0.6": ["cơ chế tác dụng của Gelsectan", "cơ chế của Gelsectan là gì", "Gelsectan tác động như thế nào",
            "Gelsectan hoạt động ra sao", "Gelsectan tạo màng bảo vệ như thế nào", "nguyên lý hoạt động của Gelsectan"],
    "0.7": ["hàng rào niêm mạc ruột là gì", "bảo vệ hàng rào niêm mạc nghĩa là sao", "tăng tính thấm ruột là gì",
            "tại sao phải bảo vệ niêm mạc ruột", "hàng rào ruột lỏng lẻo thì sao", "giải thích về hàng rào niêm mạc ruột"],
    "0.8": ["Gelsectan có hấp thu không", "Gelsectan có vào máu không", "Gelsectan có hấp thu toàn thân không",
            "Gelsectan có ngấm vào cơ thể không", "sản phẩm có tác dụng toàn thân không",
            "Gelsectan chỉ tác dụng tại chỗ phải không"],
    "0.9": ["Gelsectan khác probiotic thế nào", "so sánh Gelsectan với men vi sinh", "Gelsectan có phải men vi sinh không",
            "Gelsectan và men tiêu hóa khác nhau thế nào", "dùng chung với men vi sinh được không",
            "Gelsectan có lợi khuẩn không"],
    "0.10": ["liều dùng Gelsectan", "Gelsectan uống mấy viên một ngày", "mỗi ngày uống bao nhiêu viên",
             "cách dùng Gelsectan", "Gelsectan uống thế nào", "liều tấn công và liều duy trì là bao nhiêu",
             "ngày uống mấy lần", "một lần uống mấy viên"],
    "0.11": ["Gelsectan uống trước hay sau ăn", "uống lúc đói hay lúc no", "uống Gelsectan vào lúc nào",
             "thời điểm uống Gelsectan", "uống trước bữa ăn hay sau bữa ăn", "nên uống buổi sáng hay buổi tối"],
    "0.12": ["dùng Gelsectan trong bao lâu", "một liệu trình Gelsectan bao lâu", "uống Gelsectan mấy tuần",
             "thời gian điều trị là bao lâu", "liệu trình kéo dài mấy tuần", "phải uống bao nhiêu ngày"],
    "0.13": ["bao lâu thì Gelsectan có tác dụng", "sau bao lâu thấy hiệu quả", "uống bao lâu thì đỡ",
             "khi nào thấy cải thiện triệu chứng", "Gelsectan có hiệu quả nhanh không", "mất bao lâu để có kết quả"],
    "0.14": ["hết triệu chứng có cần uống tiếp không", "có cần dùng duy trì không", "khi đỡ rồi có ngưng được không",
             "ngưng Gelsectan có tái phát không", "có phải uống duy trì lâu dài không", "hết triệu chứng thì dừng được chưa"],
    "0.15": ["trẻ em dùng Gelsectan được không", "Gelsectan cho trẻ nhỏ được không", "bé mấy tuổi thì dùng được",
             "dùng cho bệnh nhi được không", "Gelsectan có dùng cho trẻ con không", "trẻ dưới mười hai tuổi uống được không"],
    "0.16": ["bà bầu dùng Gelsectan được không", "phụ nữ mang thai uống được không", "đang cho con bú có dùng được không",
             "có thai dùng Gelsectan có sao không", "mẹ bầu uống được không", "thai phụ dùng được không"],
    "0.17": ["Gelsectan có tương tác thuốc không", "uống chung với thuốc khác được không", "dùng cùng thuốc khác có sao không",
             "Gelsectan có ảnh hưởng thuốc khác không", "dùng đồng thời với kháng sinh được không",
             "có cần uống cách xa thuốc khác không"],
    "0.18": ["bảo quản Gelsectan như thế nào", "Gelsectan bảo quản ở nhiệt độ nào", "cách bảo quản sản phẩm",
             "có cần để tủ lạnh không", "hạn dùng của Gelsectan", "hạn sử dụng bao lâu", "điều kiện bảo quản của Gelsectan"],
    "0.19": ["tác dụng phụ của Gelsectan", "Gelsectan có tác dụng không mong muốn gì", "uống Gelsectan có bị gì không",
             "Gelsectan có an toàn không", "tác dụng ngoại ý của Gelsectan", "có phản ứng phụ không",
             "có tác dụng phát sinh nào không"],   # nhật ký robot 01/10: ASR nghe "phụ" thành "phát sinh"
    "0.20": ["dùng Gelsectan lâu dài có sao không", "uống lâu dài có an toàn không", "dùng kéo dài có hại không",
             "uống nhiều tháng có ảnh hưởng gì không", "dùng dài hạn được không", "sử dụng sáu tháng có an toàn không",
             "sử dụng lâu dài có an toàn không"],
    "0.21": ["Gelsectan có gây táo bón không", "uống Gelsectan có bị táo bón không", "cầm tiêu chảy xong có bị táo không",
             "có bị chuyển sang táo bón không", "Gelsectan có làm chậm nhu động ruột không"],
    "0.22": ["Gelsectan có nghiên cứu lâm sàng không", "bằng chứng lâm sàng của Gelsectan",
             "có thử nghiệm lâm sàng nào chứng minh", "Gelsectan có bằng chứng khoa học không",
             "có dữ liệu nghiên cứu nào", "nghiên cứu nào chứng minh hiệu quả", "có trong hướng dẫn điều trị không"],
    "0.23": ["Gelsectan khác gì loperamide", "so sánh Gelsectan với loperamide",
             "tại sao dùng Gelsectan mà không dùng loperamide", "Gelsectan có gì hơn thuốc cầm tiêu chảy",
             "ưu điểm so với loperamide", "dùng chung với loperamide được không", "Gelsectan hơn loperamide ở điểm nào"],
    "0.24": ["Gelsectan dùng cho thể tiêu chảy phải không", "hội chứng ruột kích thích sau nhiễm trùng dùng được không",
             "Gelsectan dùng cho thể nào của hội chứng ruột kích thích", "ruột kích thích thể tiêu chảy có dùng được không",
             "thể sau nhiễm trùng dùng Gelsectan được không"],
    "0.25": ["Gelsectan có ở Việt Nam chưa", "ở Việt Nam đã có Gelsectan chưa", "Gelsectan đã về Việt Nam chưa",
             "bệnh viện nào có Gelsectan", "Gelsectan đã trúng thầu chưa", "sản phẩm có trong bệnh viện chưa"],
}

# CÁCH VIẾT CHO MÁY ĐỌC — thay theo thứ tự. Chỉ đổi chữ viết, KHÔNG đổi nội dung.
# ⚠ CHƯA NGHE TRÊN MÁY THẬT. Giọng máy của Minibot đọc phiên âm ra sao phải nghe rồi chỉnh
#   ở đây (màn kỹ thuật có nút "Đọc thử tên riêng").
PHAT_AM = [
    (" (medical device)", ""),
    ("(Trifan 2019)", "của tác giả Tri-phan, năm hai nghìn không trăm mười chín"),
    ("(de los Rios 2021)", "của tác giả Đê lốt Ri-ốt, năm hai nghìn không trăm hai mươi mốt"),
    ("(Viazis 2025)", "của tác giả Vi-a-dít, năm hai nghìn không trăm hai mươi lăm"),
    ("liều tấn công 2 viên × 2 lần mỗi ngày", "liều tấn công hai viên, hai lần mỗi ngày"),
    ("duy trì 1 viên × 2 lần mỗi ngày", "duy trì một viên, hai lần mỗi ngày"),
    ("xylo-oligosaccharides", "xy-lô ô-li-gô-sác-ca-rít"),
    ("Xyloglucan", "Xy-lô-glu-can"), ("xyloglucan", "xy-lô-glu-can"),
    ("Gelsectan", "Gen-séc-tan"),
    ("Biofarma", "Bi-ô-phác-ma"), ("Devintec", "Đê-vin-téc"),
    ("Chi Bách Pharma", "Chi Bách Phác-ma"),
    ("Loperamide", "Lô-pê-ra-mít"), ("loperamide", "lô-pê-ra-mít"),
    ("(probiotic)", ""), ("probiotic", "men vi sinh"), ("prebiotic", "pờ-ri-bai-ô-tíc"),
    ("tannin", "ta-nanh"), ("protein", "prô-tê-in"),
    ("Medical", "Mê-đi-cồ"),
    (" – ", ", "), ("–", ", "), ("“", ""), ("”", ""),
]

CHU_SO = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def doc_so(n):
    """Số 0..9999 thành chữ — đủ cho liều dùng, số tuần, số viên."""
    n = int(n)
    if n < 10:
        return CHU_SO[n]
    if n < 100:
        ch, dv = divmod(n, 10)
        s = "mười" if ch == 1 else CHU_SO[ch] + " mươi"
        if dv == 0:
            return s
        if dv == 5:
            return s + " lăm"
        if dv == 1 and ch > 1:
            return s + " mốt"
        return s + " " + CHU_SO[dv]
    if n < 1000:
        tr, con = divmod(n, 100)
        s = CHU_SO[tr] + " trăm"
        if con == 0:
            return s
        if con < 10:
            return s + " linh " + CHU_SO[con]
        return s + " " + doc_so(con)
    ng, con = divmod(n, 1000)
    s = CHU_SO[ng] + " nghìn"
    if con == 0:
        return s
    if con < 100:
        return s + " không trăm " + (("linh " + CHU_SO[con]) if con < 10 else doc_so(con))
    return s + " " + doc_so(con)


def ban_doc(chu):
    s = chu
    for cu, moi in PHAT_AM:
        s = s.replace(cu, moi)
    s = re.sub(r"\d+", lambda m: doc_so(m.group(0)), s)
    return re.sub(r"\s+", " ", s).replace(" ,", ",").strip()


# ═════════════════════════ LỜI DO APP SOẠN — GỬI KHÁCH DUYỆT ═════════════════════════
# hien = chữ trên màn hình · doc = bản robot đọc (bỏ trống thì tự sinh từ hien qua PHAT_AM).
LOI_MOI_DE_LAI = ("Nếu anh chị muốn tìm hiểu thêm về sản phẩm, vui lòng để lại thông tin "
                  "để bên em tư vấn chi tiết hơn.")      # nguyên văn yêu cầu của khách

LOI = {
    "chao":          "Xin chào anh chị! Em là robot của Chi Bách Pharma. Anh chị muốn tìm hiểu về Gelsectan, "
                     "mời chạm vào một mục trên màn hình ạ.",
    "chao_tra_cuu":  "Mời anh chị chạm vào câu hỏi mình quan tâm, em sẽ đọc phần giải đáp ạ.",
    "chao_ai_mic":   "Anh chị muốn hỏi gì về Gelsectan, bấm nút micro bên dưới rồi nói với em ạ.",
    "chao_ai_cham":  "Anh chị chạm vào một câu hỏi bên dưới để hỏi em ạ.",
    "moi_de_lai":    LOI_MOI_DE_LAI,
    "form_mo":       LOI_MOI_DE_LAI,
    "form_loi":      "Anh chị kiểm tra lại giúp em ô được đánh dấu ạ.",
    "cam_on":        "Em cảm ơn anh chị. Chi Bách Pharma sẽ liên hệ để tư vấn chi tiết hơn ạ.",
    "chua_luu":      "Em chưa lưu được thông tin. Nhờ anh chị báo nhân viên tại quầy giúp em ạ.",
    # ── các lớp chặn bằng mã ──
    "khan_cap":      "Có người cần giúp gấp. Nhờ mọi người hỗ trợ ngay. Nếu cần cấp cứu, xin gọi số một một năm. "
                     "Em là robot, em không sơ cứu được.",
    "ca_nhan":       "Em là robot giới thiệu thông tin sản phẩm nên không tư vấn điều trị cho trường hợp cụ thể được ạ. "
                     "Anh chị vui lòng hỏi ý kiến bác sĩ điều trị, hoặc trao đổi với chuyên viên Medical tại quầy "
                     "Chi Bách Pharma ạ.",
    "gia":           "Em chưa có thông tin về giá và điểm bán ạ. Kính mời anh chị ghé quầy Chi Bách Pharma, "
                     "hoặc để lại thông tin để được tư vấn chi tiết hơn.",
    "chua_khoi":     "Gelsectan là thiết bị y tế, hỗ trợ kiểm soát triệu chứng của hội chứng ruột kích thích. "
                     "Chi tiết xin mời anh chị tham khảo tờ hướng dẫn sử dụng, hoặc trao đổi với chuyên viên Medical ạ.",
    "chinh_tri":     "Câu này nằm ngoài phạm vi của em ạ. Em chỉ giới thiệu thông tin về Gelsectan thôi.",
    "chua_co":       "Nội dung này em chưa có trong dữ liệu nên không dám trả lời ạ. Kính mời anh chị trao đổi với "
                     "chuyên viên Medical tại quầy Chi Bách Pharma, hoặc để lại thông tin để được tư vấn chi tiết hơn.",
    "goi_y":         "Em chưa chắc mình hiểu đúng câu hỏi. Anh chị chạm vào câu gần nhất với ý mình trên màn hình giúp em ạ.",
    # ── xã giao ──
    "xg_chao":       "Em chào anh chị ạ! Em là robot của Chi Bách Pharma. Anh chị muốn biết gì về Gelsectan cứ hỏi em nhé.",
    "xg_ten":        "Em là robot của Chi Bách Pharma, em giới thiệu thông tin về Gelsectan ạ.",
    "xg_cam_on":     "Dạ không có gì ạ. Anh chị cần hỏi thêm gì về Gelsectan cứ hỏi em nhé.",
    "xg_tam_biet":   "Em chào anh chị. Chúc anh chị một ngày tốt lành ạ.",
    # ── du hành / lễ tân ──
    "dh_bat_dau":    "Em bắt đầu đi một vòng ạ. Anh chị cần xem thông tin, cứ chạm vào màn hình của em nhé.",
    "lt_bat_dau":    "Em về vị trí lễ tân ạ.",
    "khong_di_duoc": "Em chưa tự di chuyển được. Nhờ nhân viên kỹ thuật kiểm tra giúp em ạ.",
    "cam_on_nhay":   "Em cảm ơn anh chị đã xem em nhảy ạ! Anh chị muốn tìm hiểu về Gelsectan, cứ chạm vào màn hình nhé.",
}

# Câu robot nói KHI ĐANG ĐI (du hành) và KHI ĐỨNG LỄ TÂN — xoay vòng.
# Mỗi câu = một ý giới thiệu lấy từ bộ câu trả lời + lời mời chạm màn hình.
DU_HANH = {
    "diem": ["Diem 1", "Diem 2", "Diem 3", "Diem 4", "Diem 5"],
    "nghi_giay": 22,          # khoảng cách giữa hai câu giới thiệu lúc đang đi
    "cau": [
        "Xin chào quý vị! Em là robot của Chi Bách Pharma. Mời quý vị chạm vào màn hình để tìm hiểu về Gelsectan ạ.",
        "Gelsectan là thiết bị y tế, tạo lớp màng bảo vệ trên niêm mạc ruột. Mời anh chị chạm vào màn hình để xem thông tin ạ.",
        "Gelsectan hỗ trợ kiểm soát triệu chứng của hội chứng ruột kích thích. Anh chị muốn biết thêm, cứ chạm vào màn hình của em nhé.",
        "Gelsectan được sản xuất tại Ý, do Chi Bách Pharma phân phối độc quyền tại Việt Nam. Mời anh chị chạm vào màn hình để tìm hiểu ạ.",
        "Anh chị có câu hỏi về Gelsectan? Chạm vào màn hình, em sẽ giải đáp ngay ạ.",
        "Kính mời quý vị ghé quầy Chi Bách Pharma để biết thêm thông tin chi tiết về Gelsectan ạ.",
    ],
}
LE_TAN = {
    "diem": "Le tan",
    "nghi_giay": 25,          # nghỉ giữa hai câu mời — ngắn hơn là ồn cả sảnh
    "cau": [
        "Xin chào quý vị! Em là robot của Chi Bách Pharma. Mời quý vị chạm vào màn hình để tìm hiểu về Gelsectan ạ.",
        "Anh chị có câu hỏi về Gelsectan? Mời chạm vào màn hình, em sẽ giải đáp ạ.",
        "Gelsectan là thiết bị y tế, tạo lớp màng bảo vệ trên niêm mạc ruột. Mời anh chị chạm vào màn hình để xem thông tin ạ.",
        "Mời anh chị chạm vào màn hình để trò chuyện với em về Gelsectan ạ.",
    ],
}

# CÁCH BỘ NHẬN DẠNG GIỌNG NÓI NGHE NHẦM TÊN "GELSECTAN" — lấy từ NHẬT KÝ ROBOT THẬT.
# Google ASR tiếng Việt trên Minibot hay nghe ra CHỮ TIẾNG ANH, không phải âm Việt (đo 01/10/2026:
# "gentle là gì", "Translate đang làm gì", "gen Z là gì", "sex tư hoạt động…", "your second time tư…",
# "danh sách an có tác dụng phụ không"). Viết KHÔNG DẤU, chữ thường. App thay cụm này bằng "Gelsectan".
#   "dau": True  = chỉ thay khi cụm đứng ĐẦU câu (sau lời dẫn "cho hỏi", "em ơi"…) — dùng cho cụm vốn là
#                  tiếng Việt / tiếng Anh có nghĩa ("danh sách an toàn", "gen Z") để không sửa nhầm giữa câu.
# Sau MỖI buổi chạy máy thật: python tools/day-web.py --lay-ve, đọc cột câu khách nói, thêm cách nghe mới vào đây.
BI_DANH_TEN = [
    {"cum": "your second time tu", "dau": False}, {"cum": "your second time", "dau": False},
    {"cum": "second time tu", "dau": False}, {"cum": "your second", "dau": True},
    {"cum": "gentlemen", "dau": True}, {"cum": "gentle", "dau": True}, {"cum": "gentel", "dau": True},
    {"cum": "translate", "dau": True}, {"cum": "translation", "dau": True},
    {"cum": "gen z", "dau": True}, {"cum": "gen zet", "dau": True},
    {"cum": "sex tu", "dau": False}, {"cum": "sex tan", "dau": False}, {"cum": "sec tu", "dau": False},
    {"cum": "danh sach an", "dau": True}, {"cum": "danh sach ta", "dau": True}, {"cum": "danh sach", "dau": True},
    {"cum": "settle", "dau": True},
    {"cum": "jessica tan", "dau": False}, {"cum": "gel sec tan", "dau": False},
]

# Khách hỏi trống không "Gelsectan là gì", "giới thiệu về sản phẩm" → đọc câu mở đầu này.
CAU_LA_GI = "0.1"
# "Gelsectan làm gì" (ASR hay nghe "dùng" thành "đang") → câu chỉ định.
CAU_CONG_DUNG = "0.3"

# Câu hỏi mẫu trên màn Giao tiếp AI — id trỏ vào bộ câu hỏi.
CAU_MAU = ["0.1", "0.3", "0.6", "0.10", "0.19", "0.22", "0.9", "0.13", "0.25"]

# Ô trong bảng để lại thông tin — đúng bốn mục khách yêu cầu. Cột Google Sheets lấy theo `ma`.
# hoa: True = viết hoa chữ đầu MỖI từ (họ tên) · "dau" = chỉ chữ đầu ô · False = để nguyên.
# Khách gõ tên riêng thì bấm phím "Chữ hoa" trên bàn phím.
FORM = [
    {"ma": "ten",     "nhan": "Họ và tên",                "bat": True,  "kieu": "chu", "hoa": True,  "goi": "Ví dụ: Nguyễn Văn An"},
    {"ma": "sdt",     "nhan": "Số điện thoại",            "bat": True,  "kieu": "so",  "hoa": False, "goi": "Ví dụ: 0912 345 678"},
    {"ma": "chuc_vu", "nhan": "Chức vụ",                  "bat": False, "kieu": "chu", "hoa": "dau", "goi": "Ví dụ: Bác sĩ, Dược sĩ, Trưởng khoa"},
    {"ma": "don_vi",  "nhan": "Tên doanh nghiệp / đơn vị", "bat": False, "kieu": "chu", "hoa": "dau", "goi": "Ví dụ: Bệnh viện, nhà thuốc, công ty"},
]

# ═════════════════════════ BÓC DOCX ═════════════════════════
tai = docx.Document(NGUON)
doan = [p.text.strip() for p in tai.paragraphs if p.text.strip()]

cau, dang, compliance, luu_y, vao_compliance = [], None, [], "", False
for d in doan:
    if d.lower().startswith("nguyên tắc compliance"):
        vao_compliance, dang = True, None
        continue
    if vao_compliance:
        compliance.append(d.lstrip("• ").strip())
        continue
    m = re.match(r"^(\d+\.\d+)\.\s+(.*\?)\s*$", d)
    if m:
        dang = {"id": m.group(1), "hoi": m.group(2).strip(), "dap": ""}
        cau.append(dang)
        continue
    if d.startswith("⚠"):
        luu_y = d.lstrip("⚠ ").strip()
        continue
    if dang is not None:
        dang["dap"] = (dang["dap"] + " " + d).strip()

# ═════════════════════════ GHÉP + CỔNG CHẤT LƯỢNG ═════════════════════════
loi = []
ids = [c["id"] for c in cau]
if len(cau) < 5:
    loi.append("Chỉ bóc được %d câu hỏi — DOCX đổi khuôn rồi? (khuôn: '0.N. Câu hỏi?' rồi tới đoạn trả lời)" % len(cau))
for c in cau:
    if not c["dap"]:
        loi.append("Câu %s không có câu trả lời" % c["id"])
for bang, ten in ((NHOM_CUA, "NHOM_CUA"), (BIEN_THE, "BIEN_THE")):
    for k in bang:
        if k not in ids:
            loi.append("%s có id %s mà DOCX không có" % (ten, k))
    for i in ids:
        if i not in bang:
            loi.append("Câu %s chưa có trong bảng %s" % (i, ten))
for i in CAU_MAU:
    if i not in ids:
        loi.append("CAU_MAU trỏ id %s không có" % i)

TOC_DO_DOC = 15.0        # ký tự / giây — ước lượng giọng máy tiếng Việt, CHƯA đo trên Minibot
canh_bao = []
for c in cau:
    c["nhom"] = NHOM_CUA.get(c["id"], "")
    c["bien_the"] = BIEN_THE.get(c["id"], [])
    c["doc"] = ban_doc(c["dap"])
    c["hoi_doc"] = ban_doc(c["hoi"])
    if re.search(r"[\d×%]", c["doc"]):
        loi.append("Câu %s: bản đọc còn chữ số/ký hiệu — bổ sung PHAT_AM: %s" % (c["id"], c["doc"]))
    # compliance của khách: không "chữa khỏi"; gọi "thiết bị y tế", không gọi "thuốc"
    if re.search(r"chữa khỏi|khỏi hẳn|trị dứt", c["dap"], re.I):
        loi.append("Câu %s: câu trả lời có chữ 'chữa khỏi' — trái nguyên tắc compliance" % c["id"])
    if re.search(r"(thuốc Gelsectan|Gelsectan là thuốc|loại thuốc này)", c["dap"], re.I):
        loi.append("Câu %s: câu trả lời gọi Gelsectan là 'thuốc' — trái nguyên tắc compliance" % c["id"])
    giay = len(c["doc"]) / TOC_DO_DOC
    c["giay"] = round(giay, 1)
    if giay > 30:
        canh_bao.append("Câu %s ước %.0f giây đọc (> 30 giây khách yêu cầu) — %d ký tự" % (c["id"], giay, len(c["doc"])))
    if "trúng thầu" in c["dap"]:
        canh_bao.append("Câu %s có claim 'trúng thầu' — compliance của khách: chỉ nêu khi có danh sách/quyết định cập nhật. "
                        "Hỏi lại Chi Bách Pharma trước sự kiện." % c["id"])


def loi_hai_ban(chu):
    return {"hien": chu, "doc": ban_doc(chu)}


loi_app = {k: loi_hai_ban(v) for k, v in LOI.items()}
for ten, khoi in (("DU_HANH", DU_HANH), ("LE_TAN", LE_TAN)):
    khoi["cau"] = [loi_hai_ban(x) for x in khoi["cau"]]
for k, v in list(loi_app.items()) + [("dh", x) for x in DU_HANH["cau"]] + [("lt", x) for x in LE_TAN["cau"]]:
    if re.search(r"[\d×%]", v["doc"]):
        loi.append("Lời app '%s': bản đọc còn chữ số/ký hiệu" % k)
    if re.search(r"chữa khỏi|khỏi hẳn|trị dứt|thuốc Gelsectan|Gelsectan là thuốc", v["hien"], re.I):
        loi.append("Lời app '%s' trái compliance" % k)

if loi:
    print("✘ DỪNG — chưa đạt:")
    for x in loi:
        print("   · " + x)
    raise SystemExit(1)

nhom = [{"ma": m, "ten": t, "phu": p, "so": sum(1 for c in cau if c["nhom"] == m)} for m, t, p in NHOM]
data = {
    "san_pham": "Gelsectan",
    "don_vi": "Chi Bách Pharma",
    "cap_nhat": datetime.date.today().strftime("%d/%m/%Y"),
    "nguon": "Bộ câu hỏi cơ bản về Gelsectan — Chi Bách Pharma gửi 30/09/2026",
    "luu_y_khach": luu_y,
    "compliance": compliance,
    "nhom": nhom,
    "cau": cau,
    "cau_mau": CAU_MAU,
    "loi": loi_app,
    "du_hanh": DU_HANH,
    "le_tan": LE_TAN,
    "form": FORM,
    "cho_ve_giay": 60,            # vắng thao tác bấy nhiêu giây thì về màn biểu cảm / đi tiếp
    "cho_ve_form_giay": 150,      # riêng bảng điền thông tin — người ta đang gõ
    "ten_doc": ban_doc("Gelsectan"),
    "cau_la_gi": CAU_LA_GI,
    "cau_cong_dung": CAU_CONG_DUNG,
    "bi_danh_ten": BI_DANH_TEN,
}
os.makedirs(os.path.dirname(RA), exist_ok=True)
io.open(RA, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=1))

print("✔ %s" % os.path.relpath(RA, HERE))
print("  %d câu hỏi · %d nhóm · %d cách hỏi khác · %d lời do app soạn · câu dài nhất ước %.0f giây" % (
    len(cau), len(nhom), sum(len(c["bien_the"]) for c in cau),
    len(loi_app) + len(DU_HANH["cau"]) + len(LE_TAN["cau"]), max(c["giay"] for c in cau)))
for x in canh_bao:
    print("  ⚠ " + x)

# ── Bảng lời robot do APP soạn — một tệp để gửi Chi Bách Pharma duyệt ──
NHAN_LOI = {
    "chao": "Khách chạm màn hình", "chao_tra_cuu": "Vào Tra cứu", "chao_ai_mic": "Vào Giao tiếp AI (có micro)",
    "chao_ai_cham": "Vào Giao tiếp AI (máy không micro)", "moi_de_lai": "Khách nói muốn để lại thông tin",
    "form_mo": "Mở bảng để lại thông tin (nguyên văn yêu cầu của khách)", "form_loi": "Bảng điền thiếu ô",
    "cam_on": "Gửi thông tin xong", "chua_luu": "Không lưu được thông tin", "khan_cap": "Có người kêu cấp cứu",
    "ca_nhan": "Xin tư vấn cho một người bệnh cụ thể", "gia": "Hỏi giá / chỗ mua", "chua_khoi": "Câu hỏi có chữ 'chữa khỏi'",
    "chinh_tri": "Hỏi chuyện chính trị", "chua_co": "Câu ngoài bộ câu hỏi, không có AI trả lời",
    "goi_y": "Robot chưa chắc hiểu đúng câu", "xg_chao": "Khách chào", "xg_ten": "Hỏi robot là ai",
    "xg_cam_on": "Khách cảm ơn", "xg_tam_biet": "Khách tạm biệt", "dh_bat_dau": "Bắt đầu du hành",
    "lt_bat_dau": "Bắt đầu lễ tân", "khong_di_duoc": "Robot không tự đi được", "cam_on_nhay": "Nhảy xong bài",
}
md = ["# Lời robot do app soạn — gửi Chi Bách Pharma duyệt", "",
      "Sinh tự động bởi `dung-du-lieu.py` ngày %s. **Đừng sửa tệp này** — sửa bảng `LOI` / `DU_HANH` / `LE_TAN` "
      "trong `dung-du-lieu.py` rồi chạy lại." % data["cap_nhat"], "",
      "25 câu trả lời về Gelsectan KHÔNG nằm ở đây: robot đọc nguyên văn bộ câu hỏi khách đã gửi.", "",
      "| Khi nào robot nói | Câu robot nói |", "|---|---|"]
for k, v in LOI.items():
    md.append("| %s | %s |" % (NHAN_LOI.get(k, k), v))
md += ["", "## Khi đang du hành (xoay vòng, cách nhau khoảng %d giây)" % DU_HANH["nghi_giay"], ""]
md += ["%d. %s" % (i + 1, x["hien"]) for i, x in enumerate(DU_HANH["cau"])]
md += ["", "## Khi đứng lễ tân (xoay vòng, cách nhau khoảng %d giây)" % LE_TAN["nghi_giay"], ""]
md += ["%d. %s" % (i + 1, x["hien"]) for i, x in enumerate(LE_TAN["cau"])]
io.open(os.path.join(HERE, "du-lieu", "loi-robot-can-duyet.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
print("✔ du-lieu/loi-robot-can-duyet.md — gửi khách duyệt")

# Robot Gelsectan — Minibot · Chi Bách Pharma

Robot **Minibot (GreetingBot Mini)** đứng tại quầy Chi Bách Pharma trong sự kiện y khoa: trả lời câu
hỏi về **Gelsectan** bằng chạm và bằng giọng nói, mời khách để lại thông tin, đồng bộ lên
**Google Sheets của khách**.

| | |
|---|---|
| Trạng thái | **v1.2 — đã cài trên Minibot SN MC1BHW0C170230407107 ngày 01/10/2026.** Giọng Yuna (58 MP3) · sửa tên Gelsectan sau nhận giọng nói · nhảy múa. Chưa đo nhảy múa và xoay theo người trên máy |
| Hồ sơ dự án | [`10-project/Chi-Bach-Pharma/`](../../10-project/Chi-Bach-Pharma/HO-SO.md) |
| Package | `vn.roboworld.chibach` |
| appId OrionStar | ⚠ **đang mượn** `app_cf616a2925464745b14bc4e3b2275e6d` (appId dùng chung các app sự kiện). Có appId riêng thì thay ở **hai** chỗ: `Cai.APP_ID` và `assets/actionRegistry.json` |
| APK | [`apk/gelsectan-chi-bach-minibot-v1.2.apk`](apk/) |
| Làm mẫu theo | [`hcc-cao-xanh-minibot`](../hcc-cao-xanh-minibot/README.md) (vỏ Minibot + AgentOS/Portal kiểu Tây Hòa) · [`su-kien-cong-nghiep-2026-minibot`](../su-kien-cong-nghiep-2026-minibot/README.md) (du hành + bảng điền Telex) |

> **Xem ngay trên máy tính:** nháy đúp [`demo/index.html`](demo/index.html). Ở màn Giao tiếp AI, bấm
> nút micro để **gõ thử câu hỏi** và xem app phân xử thế nào. Ảnh 22 màn chụp sẵn ở `demo/anh-soi/`.

## Luồng (anh Trường yêu cầu 30/09/2026)

**Màn chờ** chiếu biểu cảm robot → khách **chạm** → robot **chào** + **xoay theo người** (focus) → **màn chính** bốn chế độ:

| Chế độ | Làm gì |
|---|---|
| **Tra cứu** | CHỈ CHẠM. Trái: 25 câu hỏi chia 6 nhóm. Phải: phần giải đáp chữ to, robot **đọc nguyên văn**. Chọn câu khác / bấm nút nào cũng **cắt tiếng ngay**. Có nút *Để lại thông tin liên hệ* |
| **Giao tiếp AI** | Mặt biểu cảm + một lời thoại + nút mic bấm-mới-nghe (lối app Tây Hòa). Câu trong bộ câu hỏi → app đọc **nguyên văn**; câu ngoài bộ → **AgentOS + kho Robot Portal**. Có nút *Để lại thông tin liên hệ*; khách nói "tôi muốn để lại thông tin" cũng mở bảng |
| **Du hành** | Hỏi xác nhận → đi liên tục `Diem 1 → … → Diem 5` không dừng, vừa đi vừa giới thiệu, màn hình chiếu biểu cảm + lời mời chạm. Chạm là **dừng ngay** |
| **Lễ tân** | Hỏi xác nhận → về điểm `Le tan`, đứng đó chiếu biểu cảm, cứ ~25 giây phát một câu mời khách chạm màn hình |
| **Nhảy múa** | Thêm 01/10/2026, chép nguyên app Cao Xanh: nhạc `nhac/mua.mp3` (chưa rõ bản quyền — xem `nhac/NGUON.md`), phách đo sẵn (VU_DAO), lắc thân + gật đầu đúng phách, chạm là dừng. Đang nhảy thì không bị kéo về màn chờ |

- **Rời Tra cứu / Giao tiếp AI về màn chính** → bật **bảng mời để lại thông tin** (robot đọc đúng lời mời của
  khách), có nút **Bỏ qua**. Khách đã điền hoặc đã bỏ qua thì không hỏi lại trong lượt đó.
- **Vắng thao tác 60 giây** → tự về màn biểu cảm và **làm tiếp chế độ nền** (đi tiếp / mời tiếp). Đang đọc
  thì cộng thêm thời lượng câu đang đọc; đang ở bảng điền thì 150 giây.
- Bấm **giữ logo Gelsectan** ở màn chính 1,2 giây → **màn kỹ thuật**: AgentOS có không, AI thông chưa,
  micro, mạng, bản đồ có đủ 6 điểm không, Google Sheets gửi được chưa (có nút gửi thử).

---

## ⚠⚠ Độ chính xác — vì sao app KHÔNG để AI trả lời mọi câu

Khách nói rõ: từng dùng giải pháp khác, *hỏi đúng nội dung trong bộ câu hỏi mà robot trả lời không đúng
trọng tâm*. Và đây là nội dung y tế đã được khách duyệt từng câu, kèm bốn nguyên tắc compliance.

Nên mỗi câu khách nói đi qua **bộ điều phối** (`TraLoi.kt` → hàm `phanXu` trong `khung-app.html`):

| Thứ tự | Lớp | Robot làm gì |
|---|---|---|
| 1 | **Chặn bằng mã**: khẩn cấp · chính trị · hỏi giá/chỗ mua · xin tư vấn cho một người cụ thể · chữ "chữa khỏi" | đọc câu cố định (bảng `LOI`); AI không được mở miệng |
| 2 | **Bộ tìm câu hỏi** nhận ra CHẮC (kể cả diễn đạt khác — bảng `BIEN_THE`, 159 cách hỏi) | đọc **nguyên văn** câu trả lời của khách; AgentOS bị cắt ở lượt này |
| 3 | Bộ tìm **chưa chắc** | hiện 2–3 câu gần nhất cho khách chạm; máy có AgentOS thì AgentOS vẫn trả lời |
| 4 | **Ngoài bộ câu hỏi** | máy có AgentOS: **AgentOS + Portal** (quá 15 giây im thì app nói "em chưa có"). Máy chưa có: "em chưa có" + nút để lại thông tin |

Thêm một chốt ở **đầu ra**: chữ AgentOS nói ra mà có "chữa khỏi", "thuốc Gelsectan"… → cắt tiếng, app đọc
thay câu cố định (`MainApplication.CAM_DAU_RA`).

Muốn đúng y lối Tây Hòa (mọi câu để AgentOS trả lời): `Cai.DOC_NGUYEN_VAN_KHI_KHOP = false`.

### Bộ tìm — hai chốt trước khi dám đọc nguyên văn

Ngưỡng tuyệt đối 0,66 + cách câu đứng nhì ≥ 0,10, rồi:
- **Từ lạ**: khách nói một từ mà cả kho (câu hỏi lẫn câu trả lời) không có — "smecta", "suy thận" → không chắc.
- **Từ hiếm bị lạc**: từ kho có biết nhưng thuộc câu khác — "liều dùng cho **trẻ em**" không được ra câu liều người lớn.

Tiếng Việt tách theo âm tiết nên "hạn sử dụng" và "sử dụng dài hạn" trùng cả ba chữ → điểm phủ tính cả
**cụm hai từ**. Tên sản phẩm là từ đệm (bảng `TEN_SAN_PHAM`) vì bộ nhận dạng giọng nói sẽ nghe
"Gelsectan" ra đủ kiểu.

```
node tools/thu-tim-kiem.mjs              # 358 phép: 25 câu gốc · 159 biến thể · 73 cách hỏi KHÁC · 28 câu phải chặn/không đáp
node tools/thu-tim-kiem.mjs "câu hỏi"    # thử một câu, in cách app phân xử + điểm
```
30/09/2026: **358/358**. Trong 73 cách hỏi khác: 69 câu đọc nguyên văn, 4 câu ra gợi ý, **0 câu đọc nhầm**.

⚠ **Sau mỗi buổi chạy máy thật:** `python tools/day-web.py --lay-ve` kéo nhật ký câu hỏi về, xem cột câu
khách nói — robot nghe "Gelsectan" ra chữ gì thì thêm vào `TEN_SAN_PHAM` (khung-app.html); cách hỏi nào
robot không nhận ra thì thêm vào `BIEN_THE` (dung-du-lieu.py). Đừng chép câu của bộ thử vào `BIEN_THE`.

---

## Nội dung — một nguồn, khách duyệt một chỗ

| Thứ | Ở đâu |
|---|---|
| 25 câu hỏi + câu trả lời | bóc **nguyên văn** từ `du-lieu/nguon/cau-hoi-co-ban-gelsectan.docx` — script không sửa một chữ |
| Bản robot **đọc** (`doc`) | cùng nội dung, số viết chữ + tên riêng phiên âm — bảng `PHAT_AM` trong `dung-du-lieu.py` |
| **33 câu do app soạn** (chào, mời, từ chối, câu du hành, câu lễ tân) | bảng `LOI` · `DU_HANH` · `LE_TAN` trong `dung-du-lieu.py` — **phải gửi Chi Bách Pharma duyệt** |
| Điểm du hành, điểm lễ tân, số giây chờ, ô trong bảng điền | cùng file đó |

```
python dung-du-lieu.py        # DOCX → du-lieu/app-data.json   (CỔNG: compliance, bản đọc còn số, câu > 30 giây)
python dung-app.py            # → demo/ + android/…/assets/    (CỔNG: WebView 66, onclick, lời thiếu, biến tên CAU)
python dung-kho-tri-thuc.py   # → kho-tri-thuc/ để nạp Robot Portal
python google-sheet/dung-huong-dan.py   # → trang hướng dẫn gửi khách
```

⚠ **Phiên âm CHƯA nghe trên máy thật.** "Gen-séc-tan", "Xy-lô-glu-can", "Lô-pê-ra-mít", tên ba tác giả
nghiên cứu… là đoán cách giọng máy đọc. Màn kỹ thuật có nút **Đọc thử tên riêng**; nghe sai thì sửa `PHAT_AM`.

⚠ **Câu 0.25 có claim "đã trúng thầu tại nhiều bệnh viện"** — compliance của chính khách ghi "chỉ nêu khi có
danh sách/quyết định cập nhật". App đang đọc nguyên văn; phải hỏi lại khách trước sự kiện.

---

## Để lại thông tin → Google Sheets

Bốn ô khách yêu cầu: **Họ và tên\*** · **Số điện thoại\*** · Chức vụ · Tên doanh nghiệp / đơn vị.
Bàn phím Telex tự dựng (bàn phím Android trên robot không gõ nổi dấu).

`KhachHang.kt`: **ghi thẻ nhớ robot TRƯỚC** (`files/khach-hang/khach-hang.jsonl` + `.csv`), gửi Sheets sau;
chưa gửi được thì nằm hàng đợi, **30 giây thử lại**, tắt mở app không mất. Mỗi dòng có mã riêng nên gửi lại
không sinh dòng trùng.

Trang tính là **của khách** — robot không giữ mật khẩu Google nào. Quy trình:

1. Gửi khách [`google-sheet/huong-dan-ket-noi-google-sheets.html`](google-sheet/huong-dan-ket-noi-google-sheets.html)
   (một tệp tự đứng, có sẵn đoạn Apps Script để dán — nguồn là [`Code.gs`](google-sheet/Code.gs)).
2. Khách gửi lại **địa chỉ `/exec`** + **mã bí mật**.
3. `python tools/day-web.py --sheet <địa chỉ> --ma <mã>` → ghi `files/google-sheet.json` trên robot.
4. Màn kỹ thuật → **Gửi thử một dòng lên Google Sheets** → phải báo THÔNG và khách thấy dòng thử.

⚠ Địa chỉ + mã **không nằm trong mã nguồn / APK**. ⚠ **Chưa thử với một trang tính thật** — mã Kotlin và
Apps Script viết theo tài liệu, buổi đầu phải làm bước 4.
⚠ Sổ khách là **dữ liệu cá nhân**: `du-lieu/tu-robot/` đã `.gitignore`.

---

## ⚠⚠ Minibot của Roboworld CHƯA CÓ AgentOS

Máy hiện có (SN `MC1BHW0C170230407107`, ROM 07/2023) thiếu gói `com.ainirobot.agentservice`. App tự dò:

| | Máy CÓ AgentOS | Máy CHƯA có |
|---|---|---|
| Micro | Agent SDK, bấm-mới-nghe | tai RobotOS đời cũ (`Cai.MIC_ROBOTOS_CU`, đo được 28/09 ở app Cao Xanh) |
| Câu trong bộ câu hỏi | app đọc nguyên văn | app đọc nguyên văn |
| Câu **ngoài** bộ | AgentOS + kho Portal | robot nói "em chưa có" + mời để lại thông tin |

Đám mây OrionStar bằng chữ (`queryByText`) **tắt có chủ ý** ở app này: đó là mô hình chung, không đọc kho
Portal, không biết compliance — không để nó trả lời câu hỏi y tế (`Cai.HOI_DAM_MAY_KHI_KHONG_CO_AGENTOS`).

**Muốn đúng yêu cầu "AI với AgentOS và Portal":** xác nhận máy nào đi sự kiện, chạy
`python tools/day-web.py --xem` (in luôn máy có AgentOS không); chưa có thì xin OrionStar cài AgentOS cho
đúng SN. Rồi nạp `kho-tri-thuc/gelsectan-hoi-dap.txt` lên Robot Portal.
⚠ Kho Portal **dùng chung mọi robot** của tài khoản Roboworld — sự kiện xong nên gỡ tệp Gelsectan.

## Điểm bản đồ — 6 điểm

`Diem 1` … `Diem 5` (du hành) + `Le tan`. Tên dò mềm: bỏ dấu, hạ chữ thường, bỏ khoảng trắng — `Diem1`,
`diem 1`, `Lễ tân` đều khớp. Màn kỹ thuật → **Kiểm tra bản đồ** in ✓/✗ từng điểm. Một điểm không tới được
thì robot thử điểm kế sau 20 giây, không bỏ cả vòng. Chưa định vị / chưa có điểm `Le tan` thì chế độ Lễ
tân vẫn chạy **tại chỗ robot đang đứng**.

## ⚠ WebView Minibot là Chrome 66 (2018)

`dung-app.py` DỪNG khi thấy: flex `gap` · `inset` · `aspect-ratio` · optional chaining · `??` · `.flat()` ·
lookbehind · `margin:0 auto`… CSS mới bị bỏ qua lặng lẽ, JS mới giết cả khối script. Bộ thử chạy Chromium
MỚI nên không bắt được — buổi máy thật đầu tiên phải **chụp màn hình robot rồi nhìn**.

## Đẩy lên robot

```
powershell tools/build-apk.ps1            # build APK (JDK 17)
python tools/day-web.py --cai             # cài APK + đẩy giao diện (cáp USB ở ĐẦU robot; hoặc --ip <IP>)
python tools/day-web.py                   # chỉ đẩy giao diện + dữ liệu, KHÔNG cần build lại
python tools/day-web.py --lay-ve          # kéo sổ khách + nhật ký câu hỏi về du-lieu/tu-robot/
```
⚠ **Mở app BẰNG TAY từ RobotOS Home** — mở bằng adb là hãng chặn: mất giọng nói, mất quyền đi lại.

## Cổng kiểm — chạy hết trước khi build

| Lệnh | Canh gì | 30/09/2026 |
|---|---|---|
| `python dung-du-lieu.py` | compliance trong câu trả lời · bản đọc còn chữ số · câu quá 30 giây · bảng viết tay lệch DOCX | đạt (1 cảnh báo: câu 0.25) |
| `python dung-app.py` | cú pháp WebView 66 · onclick gọi hàm không có · lời `L.x` không có trong dữ liệu · clip/logo thiếu | đạt |
| `python tools/doi-chieu-cau-noi.py` | JS gọi `CAU.x` mà Kotlin không có, và ngược lại | khớp |
| `node tools/thu-tim-kiem.mjs` | bộ hiểu câu hỏi | 358/358 |
| `node tools/thu-app.mjs` | 22 màn (lỗi JS · cuộn · nút 0×0 · nút dưới dải trạng thái hãng) + **đếm lệnh**: cắt tiếng khi đổi câu, bảng mời khi rời chế độ, Telex, du hành, lễ tân, vắng 60 giây | 79/79 |

## Chưa làm / chưa biết — việc cho buổi máy thật đầu tiên

1. **Chưa chạy máy thật.** Chưa đo trên Minibot: xoay theo người (`DoiDien.kt` chép từ Nova), giọng máy
   đọc phiên âm, tốc độ đọc (đang ước 13 ký tự/giây), WebView 66 vẽ có đúng không.
2. **AgentOS cắt tiếng app?** App đọc nguyên văn bằng `SkillApi.playText` và cắt AgentOS bằng
   `AgentCore.stopTTS` — lối này chạy thật ở app Medinova (Nova, 27/08) nhưng chưa đo trên Minibot có AgentOS.
   Nếu robot đọc nguyên văn mà bị cụt giữa chừng thì đây là chỗ đầu tiên phải soi.
3. **Google Sheets** chưa thử với trang tính thật.
4. **appId riêng**, **tên + ngày + địa điểm sự kiện**, **duyệt 33 câu do app soạn**, **claim câu 0.25** — hỏi anh Trường / khách.
5. Gian hàng có **Wi-Fi** không — mất mạng thì mất AgentOS và Sheets (khách vẫn lưu trong máy, câu trong bộ vẫn trả lời).

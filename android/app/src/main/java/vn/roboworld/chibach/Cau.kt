package vn.roboworld.chibach

import android.os.Handler
import android.os.Looper
import android.util.Log
import android.webkit.JavascriptInterface
import android.webkit.WebView
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * Cây cầu hai chiều giữa giao diện web (khung-app.html) và robot.
 *
 *   Web → Android : đối tượng `CAU` trong JavaScript — các hàm gắn @JavascriptInterface
 *   Android → Web : gọi window.xxx qua evaluateJavascript
 *
 * ⚠ Cầu nối lệch là loại lỗi IM LẶNG NHẤT: JS gọi hàm Kotlin không có thì WebView nuốt lỗi,
 *   Kotlin gọi hàm web không có thì evaluateJavascript nuốt luôn. Sửa tên hàm ở một bên thì
 *   chạy python tools/doi-chieu-cau-noi.py.
 * ⚠ Hàm @JavascriptInterface chạy trên LUỒNG RIÊNG của WebView — đụng WebView phải post.
 */
object Cau {

    private const val TAG = "ChiBachCau"

    @Volatile private var web: WebView? = null
    fun gan(w: WebView) { web = w }
    fun go() { web = null }

    private fun chay(js: String) {
        val w = web ?: return
        w.post { w.evaluateJavascript(js, null) }
    }

    /** Chạy JS và CHỜ kết quả (tối đa hanMs). KHÔNG gọi từ luồng chính — tự khoá mình. */
    private fun hoiWeb(js: String, hanMs: Long = 1500): String {
        val w = web ?: return ""
        if (Looper.myLooper() == Looper.getMainLooper()) { Log.w(TAG, "hoiWeb gọi từ luồng chính — bỏ"); return "" }
        var kq = ""
        val cho = CountDownLatch(1)
        Handler(Looper.getMainLooper()).post {
            w.evaluateJavascript(js) { raw ->
                kq = runCatching {
                    if (raw.isNullOrBlank() || raw == "null") "" else JSONObject("{\"v\":$raw}").getString("v")
                }.getOrDefault("")
                cho.countDown()
            }
        }
        if (!cho.await(hanMs, TimeUnit.MILLISECONDS)) Log.w(TAG, "hoiWeb quá hạn: ${js.take(50)}")
        return kq
    }

    // ───────────────────── Android → Web ─────────────────────

    /** Khai chế độ AI + có mic không — gọi lúc trang nạp xong (MainActivity.onPageFinished). */
    fun baoCheDoAI() {
        chay("window.baoCheDoAI && window.baoCheDoAI(${JSONObject.quote(MainApplication.cheDo())}," +
             "${MainApplication.coMic()})")
        // Tai RobotOS đời cũ không có bước "thăm dò mô hình" — kết nối được SkillApi là nghe được.
        if (!MainApplication.coAgent && MainApplication.coMic()) baoAISanSang(true)
    }
    fun baoAISanSang(sanSang: Boolean) = chay("window.baoAISanSang && window.baoAISanSang($sanSang)")
    fun baoMicKhongNgheDuoc() = chay("window.baoMicKhongNgheDuoc && window.baoMicKhongNgheDuoc()")
    fun baoMicTuTat() = chay("window.baoMicTuTat && window.baoMicTuTat()")
    private fun baoDocXong() = chay("window.robotDocXong && window.robotDocXong()")
    fun danhThucBangLoiChao() = chay("window.danhThucBangLoiChao && window.danhThucBangLoiChao()")

    /** Đẩy lời nói lên màn Giao tiếp AI. ai = "nguoi" | "robot"; xong = câu đã chốt. */
    fun guiLoiNoi(ai: String, chu: String, xong: Boolean) =
        chay("window.nhanLoiNoi && window.nhanLoiNoi(${JSONObject.quote(ai)},${JSONObject.quote(chu)},$xong)")

    /** Câu trả lời do APP quyết định (nguyên văn / câu chặn / "em chưa có") + các câu gợi ý + nút để lại thông tin. */
    fun hienTraLoi(chu: String, idsJson: String, nutForm: Boolean) =
        chay("window.hienTraLoi && window.hienTraLoi(${JSONObject.quote(chu)},${JSONObject.quote(idsJson)},$nutForm)")

    /** Khách nói "tôi muốn để lại thông tin" → mở bảng điền. */
    fun moForm() = chay("window.moFormTuAI && window.moFormTuAI()")

    /**
     * PHÂN XỬ MỘT CÂU — hỏi lớp web (hàm phanXu trong khung-app.html). Toàn bộ các lớp chặn và
     * bộ tìm câu hỏi nằm MỘT chỗ bên đó, có bộ thử tools/thu-tim-kiem.mjs; Kotlin chỉ thi hành.
     * Trả chuỗi JSON {loai, id, hien, doc, goiY, nutForm}; rỗng nếu lớp web không trả lời kịp.
     */
    fun phanXu(cau: String): String =
        hoiWeb("window.phanXuCau ? window.phanXuCau(${JSONObject.quote(cau)}) : ''")

    // ───────────────────── Web → Android ─────────────────────

    @JavascriptInterface
    fun doc(vanBan: String?) {
        val t = vanBan.orEmpty()
        if (t.isNotBlank()) RobotHelper.doc(t) { baoDocXong() }
    }

    @JavascriptInterface fun dungDoc() = RobotHelper.dungDoc()

    @JavascriptInterface fun batMic() = MainApplication.batMicro()
    @JavascriptInterface fun tatMic() = MainApplication.tatMicro()
    @JavascriptInterface fun micDangMo(): Boolean = MainApplication.micDangMo()

    /** Hỏi bằng CHỮ — đi cùng đường với nói miệng (TraLoi). Dùng để tự kiểm từ DevTools. */
    @JavascriptInterface fun hoiBangChu(cau: String?) = TraLoi.hoiBangChu(cau.orEmpty())

    /** Vào màn Giao tiếp AI — khai lại chế độ cho chắc (trang có thể nạp lại giữa chừng). */
    @JavascriptInterface fun vaoChat() = baoCheDoAI()

    @JavascriptInterface fun nguoiDungThaoTac() = MainApplication.nguoiDungThaoTac()
    @JavascriptInterface fun xoaNguCanh() = MainApplication.xoaNguCanh()
    @JavascriptInterface fun thongTinAI(): String = MainApplication.thongTinAI()

    @JavascriptInterface
    fun ghiNhatKy(cau: String?, duong: String?, ghiChu: String?) = TraLoi.ghiNhatKy(cau.orEmpty(), duong.orEmpty(), ghiChu.orEmpty())

    /* ─────────── Màn đang hiện — cho từ đánh thức "Xin chào" ─────────── */
    @Volatile var manDang: String = "mh-cho"; private set
    @JavascriptInterface fun baoManHinh(m: String?) { manDang = m.orEmpty() }

    /* ─────────── Xoay theo người (focus) ─────────── */
    @JavascriptInterface fun batDoiDien() = DoiDien.bat()
    @JavascriptInterface fun tatDoiDien(veHuong: Boolean) = DoiDien.tat(veHuong)

    /* ─────────── Nhảy múa (chép app Cao Xanh / Tây Hòa) — lớp web giữ nhịp theo bài nhạc ─────────── */
    @JavascriptInterface fun batNhay(giay: Int) = NhayMua.bat(giay)
    @JavascriptInterface fun dungNhay(batLai: Boolean) = NhayMua.dung(batLai)
    @JavascriptInterface fun dongTac(ma: String?) = NhayMua.dongTac(ma.orEmpty())

    /* ─────────── Đi lại: du hành qua Diem 1..5 · về điểm Le tan ───────────
       Suốt đường đi lớp web tự lo lời nói; Kotlin chỉ đi và báo tiến độ qua window.baoDanDuong.
       Tên điểm được DÒ MỀM (bỏ dấu, hạ chữ thường, bỏ khoảng trắng): "Diem 1" khớp cả "Diem1",
       "diem 1", "Điểm 1" — Minibot hay được map theo kiểu viết liền. */
    @JavascriptInterface
    fun diToiDiem(tenDiem: String?) {
        val diem = tenDiem.orEmpty().trim()
        if (diem.isEmpty()) { baoDanDuong("loi", "Chưa cấu hình điểm đến."); return }
        RobotHelper.lyDoChuaSanSang()?.let { baoDanDuong("loi", it); return }
        baoDanDuong("bat-dau", "")
        RobotHelper.dieuHuongToi(diem,
            khiToiNoi = { baoDanDuong("toi-noi", "") },
            khiLoi = { loi -> Log.w(TAG, "Không đi được '$diem': $loi"); RobotHelper.dungDieuHuong(); baoDanDuong("loi", loi) },
            khiCapNhat = { tin -> baoDanDuong("dang-di", tin) })
    }

    @JavascriptInterface fun dungDi() { RobotHelper.dungDieuHuong(); baoDanDuong("da-dung", "") }

    @JavascriptInterface fun lyDoChuaDanDuongDuoc(): String = RobotHelper.lyDoChuaSanSang() ?: ""

    /** Trong danh sách tên điểm lớp web khai, những điểm nào THẬT SỰ có trên bản đồ (giữ thứ tự khai). */
    @JavascriptInterface
    fun diemCoTrenBanDo(dsJson: String?): String {
        val ra = JSONArray()
        runCatching {
            val ds = JSONArray(dsJson.orEmpty())
            for (i in 0 until ds.length()) { val t = ds.optString(i); if (RobotHelper.coDiem(t) != null) ra.put(t) }
        }
        return ra.toString()
    }

    /** Màn kỹ thuật: đã định vị chưa · từng điểm app cần khớp với tên nào trên bản đồ · bản đồ có những điểm gì. */
    @JavascriptInterface
    fun kiemTraBanDo(dsJson: String?) {
        RobotHelper.daDinhVi { dinhVi ->
            RobotHelper.napDanhSachDiem {
                val khop = JSONObject()
                runCatching {
                    val ds = JSONArray(dsJson.orEmpty())
                    for (i in 0 until ds.length()) { val t = ds.optString(i); RobotHelper.coDiem(t)?.let { khop.put(t, it) } }
                }
                val j = JSONObject().put("daDinhVi", dinhVi).put("khop", khop).put("tatCa", JSONArray(RobotHelper.tenDiemHienCo()))
                chay("window.baoTinhTrangBanDo && window.baoTinhTrangBanDo(${JSONObject.quote(j.toString())})")
            }
        }
    }

    private fun baoDanDuong(trangThai: String, loiNhan: String) =
        chay("window.baoDanDuong && window.baoDanDuong(${JSONObject.quote(trangThai)},${JSONObject.quote(loiNhan)})")

    /* ─────────── Khách để lại thông tin → thẻ nhớ + Google Sheets ─────────── */
    /** Trả true khi ĐÃ GHI RA THẺ NHỚ (gửi Google Sheets là chuyện sau — xem KhachHang.kt). */
    @JavascriptInterface
    fun ghiKhach(json: String?): Boolean = runCatching { KhachHang.ghi(JSONObject(json.orEmpty())) }.getOrDefault(false)

    @JavascriptInterface fun thongTinKhach(): String = KhachHang.thongTin()

    @JavascriptInterface
    fun guiThuSheet() = KhachHang.guiThu { kq -> chay("window.baoGuiThuSheet && window.baoGuiThuSheet(${JSONObject.quote(kq)})") }
}

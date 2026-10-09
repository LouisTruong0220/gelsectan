package vn.roboworld.chibach

import android.util.Log
import com.ainirobot.agent.AgentCore
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors

/**
 * BỘ ĐIỀU PHỐI CÂU HỎI — câu khách NÓI (mic) và câu gõ thử đi CÙNG một đường.
 *
 *   câu hỏi → Cau.phanXu() (lớp web: các lớp chặn bằng mã + bộ tìm câu hỏi, có bộ thử 358 phép)
 *     · chan / xa-giao / form → app đọc câu cố định; AI không được mở miệng
 *     · kho   → câu nằm trong bộ câu hỏi của khách: app đọc NGUYÊN VĂN câu trả lời đã duyệt;
 *               AgentOS bị cắt ở lượt này (Cai.DOC_NGUYEN_VAN_KHI_KHOP)
 *     · goi-y → chưa chắc: bày 2-3 câu gần nhất cho khách chạm
 *     · khong → ngoài bộ câu hỏi
 *   Hai loại sau: máy CÓ AgentOS → AgentOS trả lời bằng kiến thức Robot Portal (có đồng hồ chờ —
 *   quá 15 giây không thấy nó nói thì app tự nói "em chưa có"); máy CHƯA có → app nói thẳng
 *   "em chưa có" + nút để lại thông tin.
 *
 * Nguyên tắc: câu trả lời khách đã duyệt KHÔNG BAO GIỜ đi qua mô hình. Lớp web không trả lời
 * kịp (hiếm) thì robot nói "em chưa có" chứ không thả cho AI trả lời thiếu lớp chặn.
 */
object TraLoi {

    private const val TAG = "ChiBachTraLoi"
    private val tho = Executors.newSingleThreadExecutor()

    /** Lưới đỡ cuối cùng khi lớp web không trả lời — câu thật nằm ở D.loi.chua_co (khách duyệt). */
    private const val CHUA_CO_CUNG =
        "Nội dung này em chưa có trong dữ liệu nên không dám trả lời ạ. Kính mời anh chị trao đổi với " +
        "chuyên viên tại quầy Chi Bách Phác-ma ạ."

    /** Hỏi bằng chữ (tự kiểm từ DevTools: CAU.hoiBangChu('…')). */
    fun hoiBangChu(cauHoi: String) {
        val cau = cauHoi.trim()
        if (cau.isEmpty()) return
        val luot = MainApplication.batDauLuotMoi()
        if (MainApplication.coAgent) MainApplication.moLuotAgentOS()
        tho.execute { xuLy(cau, tuMic = false, luot = luot) }
    }

    /** Câu vừa nghe từ mic (đã gom vế). Máy có AgentOS thì AgentOS cũng đang cầm câu này. */
    fun hoiTuMic(cau: String, luot: Int) { tho.execute { xuLy(cau, tuMic = true, luot = luot) } }

    private fun xuLy(cau: String, tuMic: Boolean, luot: Int) {
        val x = runCatching { JSONObject(Cau.phanXu(cau)) }.getOrNull()
        if (x == null) {
            Log.w(TAG, "Lớp web không phân xử được câu: $cau")
            MainApplication.appDaDap()
            MainApplication.tuDoc(CHUA_CO_CUNG, CHUA_CO_CUNG, "[]", true, luot)
            ghiNhatKy(cau, "loi-web", ""); return
        }
        /* Câu sau khi app sửa tên sản phẩm ("gentle là gì" → "Gelsectan là gì"). Ghi cả hai vào nhật ký:
           câu GỐC là thứ bộ nhận dạng thật sự nghe ra — nguyên liệu để bổ sung bảng BI_DANH_TEN. */
        val cauSua = x.optString("cauSua")
        if (cauSua.isNotBlank() && cauSua != cau) ghiNhatKy(cau, "sua-ten", cauSua)
        val loai = x.optString("loai")
        val hien = x.optString("hien"); val doc = x.optString("doc").ifBlank { hien }
        val goiY = x.optJSONArray("goiY")?.toString() ?: "[]"
        val nutForm = x.optBoolean("nutForm")
        val appTuDap = when (loai) {
            "chan", "xa-giao", "form" -> true
            "kho" -> Cai.DOC_NGUYEN_VAN_KHI_KHOP || !MainApplication.coAgent
            else -> false
        }

        if (appTuDap) {
            MainApplication.appDaDap()                     // cắt AgentOS cả lượt này
            MainApplication.tuDoc(hien, doc, "[]", nutForm, luot)
            if (loai == "form") Cau.moForm()
            ghiNhatKy(cau, loai, x.optString("id").ifBlank { x.optString("khoa") }); return
        }

        if (MainApplication.coAgent) {
            // AgentOS + kho Portal trả lời. Mic: nó đã cầm câu này rồi. Chữ: phải đưa cho nó.
            Cau.hienTraLoi("", goiY, false)
            if (!tuMic) runCatching { AgentCore.query(cau) }.onFailure { Log.w(TAG, "AgentCore.query lỗi: ${it.message}") }
            MainApplication.choAgentOSNoi(luot) {
                // Quá hạn mà AgentOS im → đừng để khách đứng chờ một robot câm.
                MainApplication.appDaDap()
                MainApplication.tuDoc(hien, doc, goiY, nutForm || loai == "khong", luot)
                ghiNhatKy(cau, "agentos-im", loai)
            }
            ghiNhatKy(cau, "agentos", loai); return
        }

        // Máy chưa có AgentOS.
        if (Cai.HOI_DAM_MAY_KHI_KHONG_CO_AGENTOS && loai == "khong") {
            val dap = RobotHelper.hoiDamMay(cau, Cai.HAN_CHO_DAM_MAY_MS)
            if (!dap.isNullOrBlank()) { MainApplication.tuDoc(dap, dap, "[]", true, luot); ghiNhatKy(cau, "dam-may", dap); return }
        }
        MainApplication.tuDoc(hien, doc, goiY, nutForm, luot)       // "em chưa chắc…" + gợi ý, hoặc "em chưa có"
        ghiNhatKy(cau, if (loai == "goi-y") "goi-y" else "chua-co", goiY)
    }

    /**
     * AgentOS vừa nói ra chữ trái compliance ("chữa khỏi"…) — MainApplication đã cắt tiếng nó;
     * ở đây app đọc thay câu cố định của khách. Lấy câu từ lớp web để chỉ có MỘT bản.
     */
    fun docCauThayThe(luot: Int) {
        tho.execute {
            val x = runCatching { JSONObject(Cau.phanXu("chữa khỏi")) }.getOrNull()
            val hien = x?.optString("hien").orEmpty().ifBlank { CHUA_CO_CUNG }
            MainApplication.tuDoc(hien, x?.optString("doc").orEmpty().ifBlank { hien }, "[]", false, luot)
            ghiNhatKy("(AgentOS nói trái compliance)", "cat-agentos", "")
        }
    }

    /**
     * Nhật ký câu hỏi — để biết khách hỏi gì mà robot chưa nhận ra, và bộ nhận dạng giọng nói
     * nghe tên "Gelsectan" ra chữ gì (bổ sung vào TEN_SAN_PHAM / BIEN_THE).
     *   adb pull /sdcard/Android/data/vn.roboworld.chibach/files/nhat-ky
     * Cột: giờ · đường (kho/goi-y/agentos/chan/…) · câu khách nói · ghi chú (id câu, khoá lời)
     */
    fun ghiNhatKy(cau: String, duong: String, ghiChu: String) {
        runCatching {
            val ctx = MainApplication.boiCanh ?: return
            val thuMuc = File(ctx.getExternalFilesDir(null), "nhat-ky").apply { mkdirs() }
            val ngay = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
            val gio = SimpleDateFormat("HH:mm:ss", Locale.US).format(Date())
            File(thuMuc, "hoi-$ngay.tsv").appendText(
                listOf(gio, duong, cau.replace('\n', ' '), ghiChu.replace('\n', ' ').take(300)).joinToString("\t") + "\n")
        }.onFailure { Log.w(TAG, "Không ghi được nhật ký: ${it.message}") }
    }
}

package vn.roboworld.chibach

import android.app.Application
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import com.ainirobot.agent.AgentCore
import com.ainirobot.agent.AppAgent
import com.ainirobot.agent.LLMCallback
import com.ainirobot.agent.OnTranscribeListener
import com.ainirobot.agent.action.Action
import com.ainirobot.agent.action.Actions
import com.ainirobot.agent.assit.LLMResponse
import com.ainirobot.agent.base.Transcription
import com.ainirobot.agent.base.llm.LLMConfig
import com.ainirobot.agent.base.llm.LLMMessage
import com.ainirobot.agent.base.llm.Role

/**
 * Điểm khởi động app Robot Gelsectan — Chi Bách Pharma — Minibot.
 *
 * Phân vai giữa hai tầng:
 *   • RobotApi / SkillApi → đọc thành tiếng, đi lại, xoay theo người. Chạy trên MỌI máy RobotOS.
 *   • Agent SDK 0.4.7     → micro (ASR) + AgentOS trả lời bằng kiến thức Robot Portal.
 *                           CHỈ chạy khi máy có gói com.ainirobot.agentservice.
 *
 * Chép lối làm của bản chính thức 1.5 app Tây Hòa (24/09/2026) qua app Cao Xanh Minibot. Bốn thứ
 * đã làm mất nhiều ngày ở các app trước, đừng đổi nếu chưa đọc chú thích tại chỗ:
 *   ① Agent SDK lấy từ GÓI OFFLINE (app/libs), không lấy JitPack
 *   ② businessInfo phải là null, không được là ""                   (xem hoiMoHinh)
 *   ③ KHÔNG đụng isMicrophoneMuted — bẫy một chiều, khoá chết mic của máy
 *   ④ việc an toàn chặn bằng MÃ, không chặn bằng lời dặn           (lớp web: hàm phanXu)
 *
 * ⚠⚠ MINIBOT ĐỜI CŨ KHÔNG CÓ AgentOS — xem coAgentOS(). Không có thì KHÔNG dựng AppAgent và
 *   KHÔNG gọi một dòng AgentCore nào (hàm dựng Action đi hỏi AgentCore.appId và NÉM ngoại lệ khi
 *   chưa có AppAgent — đã làm văng app demo-rbw-minibot 13/08/2026). Mọi lời gọi AgentCore đi
 *   qua ag { } — một chốt duy nhất.
 */
class MainApplication : Application() {

    companion object {
        const val TAG = "ChiBach"

        @Volatile private var agent: AppAgent? = null
        @Volatile var boiCanh: android.content.Context? = null; private set

        /** Máy có AgentOS không — dò MỘT lần lúc khởi động. */
        @Volatile var coAgent = false; private set

        /**
         * Có gói AgentOS trên máy không.
         * ⚠ Chỉ tìm com.ainirobot.agentservice. Gói speechasrservice (có trên Minibot ROM 2023)
         *   KHÔNG đủ: nó chỉ có .SpeechService, không có OpenAgentService, Agent SDK bind hỏng
         *   và AgentClientService rơi vào vòng lặp chết-khởi-động-lại (đo 13/08/2026).
         */
        fun coAgentOS(ctx: android.content.Context): Boolean = runCatching {
            ctx.packageManager.getPackageInfo("com.ainirobot.agentservice", 0); true
        }.getOrDefault(false)

        /** Chốt DUY NHẤT cho mọi lời gọi AgentCore — máy không có AgentOS thì bỏ qua êm. */
        inline fun <T> ag(macDinh: T, khoi: () -> T): T =
            if (!coAgent) macDinh else runCatching(khoi).getOrDefault(macDinh)

        /** "agentos" · "du-phong" · "khong" — lớp web đọc để quyết định có hiện nút mic không. */
        fun cheDo(): String = when {
            coAgent -> "agentos"
            Cai.BAT_DU_PHONG -> "du-phong"
            else -> "khong"
        }

        /**
         * AI đã trả lời thật chưa. KHÔNG suy ra từ "agent != null" — dựng được AppAgent chỉ nghĩa
         * là hàm khởi tạo không ném lỗi. Cờ này chỉ bật khi mô hình trả lời thật, hoặc khi nghe
         * được một câu ASR thật. Nút mic bấm không phản ứng tệ hơn không có nút.
         */
        @Volatile private var agentSanSang = false

        /** MIC ĐANG MỞ — cờ của app, không hỏi SDK. Chốt ở onASRResult. */
        @Volatile private var dangChoNghe = false

        /* Chẩn đoán — robot đặt ở quầy, không cắm cáp được mỗi lần. Xem thongTinAI(). */
        @Volatile private var loiAICuoi = ""
        @Volatile private var lanThamDo = 0
        @Volatile private var lucNgheCuoi = 0L
        @Volatile private var lucMoMic = 0L

        /* ═══════════════════════════════════════════════════════════════
           LƯỢT HỎI — "Khách hỏi 1 → robot trả lời 1; thao tác là ngắt lời."
           · nhanCauTraLoi — lượt hỏi này CÒN HIỆU LỰC không. Câu trả lời về muộn khi khách đã
             bấm Kết thúc / chọn chức năng khác thì phải câm — cắt tiếng KHÔNG đủ vì câu đó CHƯA phát.
           · luotHienTai   — số thứ tự lượt. Câu trả lời của lượt cũ về sau khi khách đã hỏi câu
             mới cũng phải câm.
           · daGuiTrongPhien — một lần bấm mic chỉ gửi ĐÚNG MỘT câu (hãng bắn final ở mỗi lần ngắt hơi).
           ═══════════════════════════════════════════════════════════════ */
        @Volatile private var nhanCauTraLoi = false
        @Volatile private var luotHienTai = 0
        @Volatile private var daGuiTrongPhien = false

        @Synchronized fun batDauLuotMoi(): Int { nhanCauTraLoi = true; daCoTiengAgent = false; return ++luotHienTai }

        /** Khách vừa thao tác — bỏ lượt đang chờ, cắt CẢ HAI đường tiếng. */
        fun nguoiDungThaoTac() {
            nhanCauTraLoi = false
            RobotHelper.dungDoc()
            ag(Unit) { AgentCore.stopTTS() }
        }

        fun choPhepNoi(): Boolean = nhanCauTraLoi

        /** Máy có micro dùng được không: AgentOS, hoặc tai RobotOS đời cũ (Cai.MIC_ROBOTOS_CU). */
        fun coMic(): Boolean = coAgent || RobotHelper.taiSanSang()

        /** SkillApi vừa kết nối ở máy không có AgentOS — báo lớp web hiện nút mic. */
        fun baoTaiSanSang() {
            if (coAgent || !RobotHelper.taiSanSang()) return
            Log.w(TAG, "Micro qua TAI RobotOS đời cũ: ${RobotHelper.trangThaiTai()}")
            Cau.baoCheDoAI()
        }

        /**
         * Chữ nghe được bằng tai RobotOS đời cũ (máy không có AgentOS). Cùng luật với onASRResult
         * của Agent SDK: mic đóng thì bỏ (trừ "Xin chào" ở màn chờ), câu chốt thì gom vế rồi gửi.
         * ⚠ Câu chốt về HAI lần — onQueryAsrResult rồi onSendRequest — gộp theo chữ + 5 giây.
         */
        @Volatile private var chuChotCuoi = ""
        @Volatile private var lucChotCuoi = 0L
        fun ngheTaiCu(chu: String, xong: Boolean) {
            val t = chu.trim()
            if (t.isEmpty() || coAgent) return
            val bay = System.currentTimeMillis()
            lucNgheCuoi = bay
            if (!dangChoNghe) {
                if (xong && Cau.manDang == "mh-cho" && laLoiDanhThuc(t) && bay - lucDanhThucCuoi > 8_000L) {
                    lucDanhThucCuoi = bay
                    Cau.danhThucBangLoiChao()
                }
                return
            }
            if (!xong) { Cau.guiLoiNoi("nguoi", t, false); return }
            if (t == chuChotCuoi && bay - lucChotCuoi < 5_000L) return
            chuChotCuoi = t; lucChotCuoi = bay
            Log.d(TAG, "Tai cũ — khách nói: $t")
            Cau.guiLoiNoi("nguoi", t, true)
            quenTuNoi()
            gomVe(t)
            henTatMicSauKhiDutCau { guiCauDaGom() }
        }

        /* ⚠⚠ QUÊN VẾ Ở batMicro, TUYỆT ĐỐI KHÔNG Ở tatMicro — đường gửi câu là dứt câu → hẹn
           → tatMicro() → guiCauDaGom(); quên ở tatMicro là xoá câu NGAY TRƯỚC khi gửi, robot
           nghe xong đứng im (dính ở app Uông Bí v1.5, 08/09/2026). */
        fun batMicro() {
            if (!coMic()) return
            if (!coAgent) RobotHelper.moTaiCu()
            moLuotAgentOS()
            huyHenTatMic(); quenVe()
            lucMoMic = System.currentTimeMillis()
            daGuiTrongPhien = false
            dangChoNghe = true
            datMicro(false)
            henTatMicNeuKhongAiNoi()
        }
        fun tatMicro() { huyHenTatMic(); dangChoNghe = false; datMicro(true) }

        /* ── GOM VẾ: hãng bắn final ở MỖI lần ngắt hơi — gom lại, im một nhịp rồi mới gửi. ── */
        private val ve = StringBuilder()
        @Synchronized fun gomVe(chu: String) {
            if (chu.isBlank()) return
            if (ve.isNotEmpty()) ve.append(' ')
            ve.append(chu.trim())
        }
        @Synchronized fun quenVe() { ve.setLength(0) }

        fun guiCauDaGom() {
            val cau = synchronized(this) { val t = ve.toString().trim(); ve.setLength(0); t }
            if (daGuiTrongPhien) { Log.d(TAG, "Phiên này đã gửi một câu — bỏ phần nghe thêm: ${cau.take(40)}"); return }
            if (cau.isBlank()) {
                Log.w(TAG, "guiCauDaGom: KHÔNG CÒN VẾ NÀO — ai đó đã gọi quenVe() giữa lúc tắt mic và lúc gửi.")
                return
            }
            daGuiTrongPhien = true
            /* Câu nói đi qua bộ điều phối: lớp chặn → bộ câu hỏi của khách (đọc nguyên văn) →
               còn lại mới tới AgentOS + Portal. Máy có AgentOS thì AgentOS cũng đang cầm câu này;
               app quyết định xong sẽ để nó nói hoặc cắt nó (appDaDap). */
            TraLoi.hoiTuMic(cau, batDauLuotMoi())
        }

        private val tayCam = Handler(Looper.getMainLooper())
        private var henTatMic: Runnable? = null
        private fun huyHenTatMic() { henTatMic?.let { tayCam.removeCallbacks(it) }; henTatMic = null }

        private fun henTatMicNeuKhongAiNoi() {
            huyHenTatMic()
            val r = Runnable {
                henTatMic = null
                if (!dangChoNghe) return@Runnable
                tatMicro()
                if (lucNgheCuoi >= lucMoMic) Cau.baoMicTuTat() else Cau.baoMicKhongNgheDuoc()
            }
            henTatMic = r
            tayCam.postDelayed(r, Cai.TRAN_MO_MIC_MS)
        }

        private fun henTatMicSauKhiDutCau(khiTat: () -> Unit) {
            huyHenTatMic()
            val r = Runnable {
                henTatMic = null
                if (!dangChoNghe) return@Runnable
                tatMicro(); Cau.baoMicTuTat(); khiTat()
            }
            henTatMic = r
            tayCam.postDelayed(r, Cai.CHO_DUT_CAU_MS)
        }

        /**
         * Mic và "nghe không cần đánh thức" đi CÙNG NHAU ở đúng một chỗ này.
         * ⚠⚠ KHÔNG ĐỤNG isMicrophoneMuted (bẫy một chiều). Chặn nghe bằng isEnableWakeFree +
         *   cờ dangChoNghe chốt ở onASRResult — cả hai đảo chiều được.
         * ⚠ KHÔNG dùng enableWakeupMode: nó bắt gọi tên robot bằng TIẾNG TRUNG (小豹小豹).
         * ⚠ Điều kiện vận hành: người nói phải ĐỨNG ĐỐI DIỆN robot, trong tầm camera — đứng
         *   cạnh sườn là câu bị xếp tiếng ồn môi trường và bỏ đi.
         */
        private fun datMicro(tat: Boolean) {
            ag(Unit) {
                AgentCore.isEnableWakeFree = !tat
                runCatching { AgentCore.enableWakeupMode(false) }
                Log.d(TAG, "Micro: chờ nghe=$dangChoNghe · nghe tự do=${AgentCore.isEnableWakeFree}")
            }
        }

        fun micDangMo(): Boolean = dangChoNghe

        /** Hết lượt khách — xoá ngữ cảnh để khách sau không bị dính chuyện của khách trước. */
        fun xoaNguCanh() { ag(Unit) { AgentCore.clearContext() } }

        /**
         * Gọi thẳng mô hình — ở app này CHỈ dùng để thăm dò đường AI có thông không.
         * ⚠⚠ businessInfo (tham số thứ 5) PHẢI là null — "" làm máy chủ trả status=2 sau 355 ms.
         *   status=1 mới là thành công. fileSearch (tham số 4) đã bị máy chủ bỏ từ 26/08/2025.
         */
        fun hoiMoHinh(danhSachTin: List<LLMMessage>, hanMs: Long = 20_000L, khiXong: (String?, String?) -> Unit) {
            if (!coAgent) { khiXong(null, "máy chưa có AgentOS"); return }
            val ok = runCatching {
                AgentCore.llm(danhSachTin, LLMConfig(0.6f, 300, 20, false, null), hanMs, false, object : LLMCallback {
                    override fun onTaskEnd(status: Int, result: LLMResponse?) {
                        val chu = result?.message?.content.orEmpty()
                        Log.d(TAG, "hoiMoHinh: status=$status · nguyên văn = $result")
                        if (status == 1 && chu.isNotBlank()) {
                            loiAICuoi = ""
                            if (!agentSanSang) { agentSanSang = true; Cau.baoAISanSang(true) }
                            khiXong(chu, null)
                        } else {
                            loiAICuoi = listOfNotNull("status=$status",
                                result?.error?.takeIf { it.isNotBlank() }?.let { "lỗi=$it" },
                                if (result == null) "không có dữ liệu trả về" else null).joinToString(" · ")
                            khiXong(null, loiAICuoi)
                        }
                    }
                })
            }.isSuccess
            if (!ok) { loiAICuoi = "không gọi được mô hình"; khiXong(null, loiAICuoi) }
        }

        /**
         * Thăm dò đường AI — CÓ ĐỒNG HỒ RIÊNG. Đo ở app Tây Hòa 18/09/2026: llm() gọi lúc SDK
         * chưa bind xong thì bị NUỐT (không callback, không lỗi) — chỉ hẹn lại trong callback
         * là không bao giờ có lần hai, nút mic mất vĩnh viễn. Agent SDK có khi 75 giây mới thông.
         */
        private fun thamDoMotLan() {
            if (agentSanSang || !coAgent) return
            lanThamDo++
            val lan = lanThamDo
            val daTraLoi = java.util.concurrent.atomic.AtomicBoolean(false)
            tayCam.postDelayed({
                if (!agentSanSang && daTraLoi.compareAndSet(false, true)) {
                    Log.w(TAG, "Thăm dò AI lần $lan: không hồi âm sau 25 giây — thử lại")
                    loiAICuoi = "mô hình không hồi âm"
                    thamDoMotLan()
                }
            }, 25_000L)
            hoiMoHinh(listOf(LLMMessage(Role.USER, "Xin chào"))) { chu, loi ->
                if (!daTraLoi.compareAndSet(false, true)) return@hoiMoHinh
                Log.d(TAG, "Thăm dò AI lần $lan: " + (if (chu != null) "THÔNG" else "chưa thông — $loi"))
                Cau.baoAISanSang(chu != null)
                if (chu == null) tayCam.postDelayed({ thamDoMotLan() }, Cai.THAM_DO_LAI_MS)
            }
        }

        private fun loaiMang(): String = runCatching {
            val cm = boiCanh?.getSystemService(android.content.Context.CONNECTIVITY_SERVICE)
                    as? android.net.ConnectivityManager ?: return "?"
            val mang = cm.activeNetwork ?: return "mất mạng"
            val kn = cm.getNetworkCapabilities(mang) ?: return "?"
            when {
                kn.hasTransport(android.net.NetworkCapabilities.TRANSPORT_WIFI) -> "wifi"
                kn.hasTransport(android.net.NetworkCapabilities.TRANSPORT_CELLULAR) -> "4g"
                else -> "khác"
            }
        }.getOrDefault("?")

        /** Settings.Global "microphone": 1 bật · 0 TẮT (di chứng isMicrophoneMuted) · -1 không đọc được. */
        private fun micHeThong(): Int = runCatching {
            android.provider.Settings.Global.getInt(boiCanh!!.contentResolver, "microphone", -1)
        }.getOrDefault(-1)

        @Volatile var nguonNoiDung = ""

        fun thongTinAI(): String {
            val bay = System.currentTimeMillis()
            val o = org.json.JSONObject()
            o.put("cheDo", cheDo())
            o.put("coAgentOS", coAgent)
            o.put("appId", ag(Cai.APP_ID + " (chưa có AgentOS)") { AgentCore.appId })
            o.put("agentSanSang", agentSanSang)
            o.put("micDangMo", dangChoNghe)
            o.put("coMic", coMic())
            if (!coAgent) o.put("taiCu", RobotHelper.trangThaiTai())
            o.put("mang", loaiMang())
            o.put("micHeThong", micHeThong())
            o.put("loiAI", loiAICuoi)
            o.put("lanThamDo", lanThamDo)
            o.put("ngheCuoiGiay", if (lucNgheCuoi == 0L) -1 else (bay - lucNgheCuoi) / 1000)
            o.put("duPhong", if (Cai.HOI_DAM_MAY_KHI_KHONG_CO_AGENTOS) RobotHelper.trangThaiDamMay() else "tắt có chủ ý (nội dung y tế)")
            o.put("robot", RobotHelper.lyDoChuaSanSang() ?: "đã nối RobotOS, sẵn sàng")
            o.put("giong", "Yuna (MP3) · " + Giong.soFile() + " tệp")
            o.put("nguonNoiDung", nguonNoiDung)
            return o.toString()
        }

        /* ── TỪ ĐÁNH THỨC "Xin chào" ở màn biểu cảm (chép app Tây Hòa 24/09/2026) ── */
        @Volatile private var lucDanhThucCuoi = 0L
        fun laLoiDanhThuc(chu: String): Boolean {
            val t = chu.lowercase().replace(Regex("[^\\p{L}\\p{N} ]+"), " ").trim().replace(Regex("\\s+"), " ")
            if (t.isEmpty() || t.split(' ').size > 6) return false
            return t.contains("xin chào") || t.contains("xin chao")
        }

        /* ── CỬA SỔ LƯỢT của AgentOS — đo ở Tây Hòa 22/09: bật hoạch định là AgentOS tự nghe
              tiếng nói chuyện trong phòng và tự đáp (17 lần / 3 phút) dù mic app đóng. Chỉ trong
              30 giây sau khi khách bấm mic AgentOS mới được nói; còn lại cắt ở đầu ra.
              Ở hội nghị đông người đây là chốt giữ cho robot không tự dưng lên tiếng. ── */
        @Volatile private var appDaDapLuotNay = false
        @Volatile private var lucMoLuot = 0L
        @Volatile private var daCoTiengAgent = false
        fun moLuotAgentOS() { lucMoLuot = System.currentTimeMillis(); appDaDapLuotNay = false }
        fun trongLuotAgentOS() = System.currentTimeMillis() - lucMoLuot < 30_000L

        /** App nhận trả lời lượt này → AgentOS bị cắt cho tới lượt sau. */
        fun appDaDap() { appDaDapLuotNay = true; ag(Unit) { AgentCore.stopTTS() } }

        /** Đã giao câu cho AgentOS. Quá hạn mà nó chưa mở miệng thì gọi khiIm (một lần). */
        fun choAgentOSNoi(luot: Int, khiIm: () -> Unit) {
            tayCam.postDelayed({
                if (luot == luotHienTai && nhanCauTraLoi && !daCoTiengAgent && !appDaDapLuotNay) {
                    Log.w(TAG, "AgentOS im quá ${Cai.HAN_CHO_AGENTOS_MS / 1000} giây — app tự đáp")
                    khiIm()
                }
            }, Cai.HAN_CHO_AGENTOS_MS)
        }

        /* ── Nhớ BA câu app vừa đọc — mẩu chữ TTS của câu cũ còn chảy về ~1 giây sau
              (đo ở Medinova 27/08), chỉ nhớ câu cuối là robot tự cắt tiếng mình. ── */
        private val tuNoiGanDay = java.util.ArrayDeque<String>()
        fun ghiNhoTuNoi(cau: String) {
            synchronized(tuNoiGanDay) {
                tuNoiGanDay.addFirst(cau)
                while (tuNoiGanDay.size > 3) tuNoiGanDay.removeLast()
            }
        }
        private fun tuCua(s: String): List<String> =
            s.lowercase().replace(Regex("[^\\p{L}\\p{N}]+"), " ").trim().split(' ').filter { it.isNotEmpty() }
        /** ⚠ So theo TỈ LỆ TỪ TRÙNG (≥60%), đừng so chuỗi con — TTS đổi xuống dòng thành dấu cách. */
        private fun laChuCuaApp(chu: String): Boolean {
            val w = tuCua(chu)
            if (w.isEmpty()) return true
            val can = kotlin.math.ceil(w.size * 0.6).toInt()
            synchronized(tuNoiGanDay) {
                return tuNoiGanDay.any { c -> val tap = tuCua(c).toHashSet(); w.count { it in tap } >= can }
            }
        }
        private fun quenTuNoi() { synchronized(tuNoiGanDay) { tuNoiGanDay.clear() } }

        /**
         * CỬA RA của mọi câu trả lời do app quyết định: kiểm lượt còn hiệu lực, đọc bản `doc`
         * (số viết chữ, tên riêng phiên âm), đưa bản `hien` + gợi ý lên màn.
         */
        fun tuDoc(hien: String, doc: String, goiY: String, nutForm: Boolean, luot: Int) {
            if (hien.isBlank() && doc.isBlank()) return
            if (!choPhepNoi() || luot != luotHienTai) { Log.d(TAG, "Lượt hỏi đã bị bỏ — không đọc: ${hien.take(40)}…"); return }
            RobotHelper.doc(doc.ifBlank { hien }) {}
            Cau.hienTraLoi(hien, goiY, nutForm)
        }

        /**
         * COMPLIANCE Ở ĐẦU RA — khách yêu cầu: "hỗ trợ kiểm soát triệu chứng", KHÔNG "chữa khỏi".
         * Persona đã dặn, nhưng dặn thì mô hình không chắc nghe; chữ nào AgentOS nói ra mà trúng
         * mẫu này thì cắt tiếng ngay và app đọc thay câu cố định.
         */
        private val CAM_DAU_RA = Regex("chữa khỏi|khỏi hẳn|trị dứt|dứt điểm|chữa dứt|khỏi hoàn toàn|thuốc gelsectan|gelsectan là (một )?(loại )?thuốc", RegexOption.IGNORE_CASE)

        /**
         * Persona + mục tiêu cho AgentOS. Sự thật CỐ ĐỊNH đặt ở đây (hãng xác nhận
         * uploadInterfaceInfo chỉ là mô tả màn hình, mô hình không dùng để trả lời kiến thức).
         * Bản chép–dán cho ô persona trên Robot Portal: kho-tri-thuc/persona-robot.md.
         */
        const val PERSONA =
            "Bạn là robot của Chi Bách Pharma, đứng tại quầy giới thiệu Gelsectan trong một sự kiện y khoa. " +
            "Gelsectan là thiết bị y tế (không phải thuốc, không phải thực phẩm chức năng), sản xuất tại Ý, " +
            "do Chi Bách Pharma phân phối độc quyền tại Việt Nam. Người hỏi thường là bác sĩ, dược sĩ. " +
            "Bạn xưng em, gọi người hỏi là anh chị hoặc Bác sĩ. Bạn không phải nhân viên y tế: không tư vấn " +
            "điều trị cho trường hợp cụ thể, không kê đơn."
        const val MUC_TIEU =
            "Trả lời câu hỏi về Gelsectan CHỈ dựa trên KHO KIẾN THỨC đã nạp (bộ hỏi đáp Gelsectan của Chi Bách Pharma). " +
            "Trả lời ngắn gọn, tối đa ba câu, đúng trọng tâm câu hỏi. Bốn nguyên tắc bắt buộc: " +
            "một, nói 'hỗ trợ kiểm soát triệu chứng', tuyệt đối không nói 'chữa khỏi'; " +
            "hai, gọi Gelsectan là 'thiết bị y tế', không gọi là 'thuốc'; " +
            "ba, liều dùng, cách dùng, bảo quản thì theo nhãn và tờ hướng dẫn sử dụng; " +
            "bốn, câu hỏi vượt dữ liệu như trẻ em, thai kỳ, tương tác thuốc, bệnh lý khác, giá bán: nói thẳng là em chưa có " +
            "dữ liệu và mời trao đổi với chuyên viên Medical tại quầy Chi Bách Pharma, không tự suy đoán. " +
            "Không bàn chính trị, không nói về sản phẩm của hãng khác ngoài nội dung có trong kho."
    }

    override fun onCreate() {
        super.onCreate()
        boiCanh = applicationContext
        KhachHang.nap(this)
        Giong.nap(this)
        RobotHelper.ketNoi(this)

        coAgent = coAgentOS(this)
        if (!coAgent) {
            Log.w(TAG, "MÁY CHƯA CÓ AgentOS (thiếu com.ainirobot.agentservice) — KHÔNG dựng AppAgent. " +
                       "Chạy chế độ ${cheDo()}: câu trong bộ câu hỏi vẫn đọc nguyên văn, câu ngoài bộ thì robot " +
                       "nói 'em chưa có'. Muốn AI trả lời câu ngoài bộ: xin OrionStar cài AgentOS cho máy này.")
            return
        }

        agent = object : AppAgent(this) {
            override fun onCreate() {
                /* Công tắc hãng: voiceBar mặc định BẬT (đè giao diện) → tắt. wakeFree mặc định
                   BẬT (robot tự bắt lời người đi ngang) → tắt, chỉ bật khi bấm mic.
                   disablePlan=false: chế độ Portal CẦN bộ hoạch định để AgentOS trả lời. */
                isEnableVoiceBar = false
                isDisablePlan = false
                isEnableWakeFree = false
                setPersona(PERSONA)
                setObjective(MUC_TIEU)
                /* ⚠ Bỏ SAY / KNOWLEDGE_QA là MẤT LUÔN ĐƯỜNG NGHE (đo 26/08/2026). KNOWLEDGE_QA
                   cũng chính là thứ cho AgentOS đọc kho Robot Portal. */
                registerAction(Actions.SAY)
                if (Cai.GIU_KNOWLEDGE_QA) registerAction(Actions.KNOWLEDGE_QA)
                Log.w(TAG, "CHẾ ĐỘ AgentOS + PORTAL · appId=${runCatching { AgentCore.appId }.getOrNull()}")

                setOnTranscribeListener(object : OnTranscribeListener {
                    override fun onASRResult(t: Transcription): Boolean {
                        val chu = t.text
                        if (chu.isNullOrBlank()) return false
                        lucNgheCuoi = System.currentTimeMillis()
                        if (!agentSanSang) { agentSanSang = true; Cau.baoAISanSang(true) }
                        if (!dangChoNghe) {
                            if (t.final && Cau.manDang == "mh-cho" && laLoiDanhThuc(chu) &&
                                System.currentTimeMillis() - lucDanhThucCuoi > 8_000L) {
                                lucDanhThucCuoi = System.currentTimeMillis()
                                Cau.danhThucBangLoiChao()
                            }
                            return false
                        }
                        Cau.guiLoiNoi("nguoi", chu, t.final)
                        if (t.final) {
                            quenTuNoi()
                            gomVe(chu)
                            henTatMicSauKhiDutCau { guiCauDaGom() }
                        }
                        /* ⚠ ĐỪNG trả true để "nuốt" câu — trả true là mất luôn đường nghe (26/08). */
                        return false
                    }

                    override fun onTTSResult(t: Transcription): Boolean {
                        val chu = t.text
                        if (chu.isNullOrBlank()) return false
                        if (laChuCuaApp(chu)) return false
                        /* Chặn ở ĐẦU RA, không ở đầu vào (chặn đầu vào là mất mic). */
                        if (!trongLuotAgentOS() || !nhanCauTraLoi || Cau.manDang != "mh-chat") {
                            Log.w(TAG, "AgentOS tự nói NGOÀI LƯỢT — cắt: '$chu'")
                            runCatching { AgentCore.stopTTS() }; return false
                        }
                        if (appDaDapLuotNay) {
                            Log.w(TAG, "AgentOS nói chen lượt app đã đáp — cắt: '$chu'")
                            runCatching { AgentCore.stopTTS() }; return false
                        }
                        if (CAM_DAU_RA.containsMatchIn(chu)) {
                            Log.w(TAG, "AgentOS nói TRÁI COMPLIANCE — cắt, app đọc thay: '$chu'")
                            appDaDap()
                            TraLoi.docCauThayThe(luotHienTai); return false
                        }
                        daCoTiengAgent = true
                        if (t.final) { Log.d(TAG, "AgentOS nói: $chu"); TraLoi.ghiNhatKy("(AgentOS đáp)", "agentos-dap", chu) }
                        Cau.guiLoiNoi("robot", chu, t.final)
                        return false
                    }
                })
            }

            override fun onExecuteAction(action: Action, params: Bundle?): Boolean = false
        }

        tayCam.postDelayed({ thamDoMotLan() }, 4_000L)
    }
}

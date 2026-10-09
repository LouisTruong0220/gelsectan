package vn.roboworld.chibach

import android.content.Context
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * THÔNG TIN KHÁCH ĐỂ LẠI — nguyên tắc số một: KHÔNG BAO GIỜ MẤT MỘT KHÁCH NÀO.
 *
 * Thứ tự bắt buộc: GHI RA THẺ NHỚ ROBOT TRƯỚC, gửi Google Sheets sau. Wi-Fi hội nghị rớt đúng
 * lúc đông khách nhất — dòng nào chưa gửi được nằm trong hàng đợi, cứ 30 giây thử lại, tắt mở
 * app cũng không mất.
 *
 * Trên robot: /sdcard/Android/data/vn.roboworld.chibach/files/
 *   khach-hang/khach-hang.jsonl   mỗi dòng một khách — bền, không bao giờ ghi đè
 *   khach-hang/khach-hang.csv     bản mở bằng Excel (UTF-8 có BOM) — lưới đỡ khi Sheets hỏng
 *   khach-hang/hang-doi.json      những dòng CHƯA lên được Google Sheets
 *   google-sheet.json             {"url": "https://script.google.com/macros/s/…/exec", "ma": "…"}
 *
 * Google Sheets: trang tính là của KHÁCH. Khách dán đoạn Apps Script (google-sheet/Code.gs) vào
 * trang tính của họ, triển khai thành "ứng dụng web", gửi lại cho Roboworld địa chỉ + mã. Robot
 * chỉ POST một dòng JSON tới địa chỉ đó — không giữ mật khẩu hay khoá Google nào.
 *   ⚠ Địa chỉ và mã KHÔNG ghi trong mã nguồn / APK: ai có địa chỉ là ghi được vào trang tính.
 *     Đẩy lên robot bằng: python tools/day-web.py --sheet <địa chỉ> --ma <mã>
 *   ⚠ Mỗi dòng mang một "id" riêng; Apps Script bỏ qua id đã có → gửi lại không sinh dòng trùng.
 */
object KhachHang {
    private const val TAG = "ChiBachKhach"
    private lateinit var thuMuc: File
    private lateinit var fJsonl: File
    private lateinit var fCsv: File
    private lateinit var fHangDoi: File
    private lateinit var fCauHinh: File
    @Volatile private var daNap = false
    @Volatile private var url = ""
    @Volatile private var ma = ""
    @Volatile private var loiCuoi = ""
    @Volatile private var lucGuiDuocCuoi = 0L
    private val gio = SimpleDateFormat("HH:mm:ss dd/MM/yyyy", Locale.US)
    private val tho = Executors.newSingleThreadScheduledExecutor()

    fun nap(ctx: Context) {
        thuMuc = File(ctx.getExternalFilesDir(null), "khach-hang").also { it.mkdirs() }
        fJsonl = File(thuMuc, "khach-hang.jsonl")
        fCsv = File(thuMuc, "khach-hang.csv")
        fHangDoi = File(thuMuc, "hang-doi.json")
        fCauHinh = File(ctx.getExternalFilesDir(null), "google-sheet.json")
        daNap = true
        docCauHinh()
        // Gửi nốt hàng đợi của lần chạy trước, rồi cứ 30 giây thử lại chừng nào còn dòng chưa gửi.
        tho.scheduleWithFixedDelay({ runCatching { docCauHinh(); guiHangDoi() } }, 5, Cai.SHEET_GUI_LAI_GIAY, TimeUnit.SECONDS)
    }

    /** Đọc lại mỗi lượt gửi — kỹ thuật viên đẩy google-sheet.json lên lúc app đang chạy cũng ăn. */
    private fun docCauHinh() {
        if (!fCauHinh.isFile) { url = ""; ma = ""; return }
        runCatching {
            val j = JSONObject(fCauHinh.readText(Charsets.UTF_8))
            url = j.optString("url").trim(); ma = j.optString("ma").trim()
        }.onFailure { loiCuoi = "google-sheet.json hỏng: ${it.message}"; Log.w(TAG, loiCuoi) }
    }

    private fun coSheet() = url.startsWith("https://")

    fun dem(): Int = runCatching { if (fJsonl.isFile) fJsonl.readLines().count { it.isNotBlank() } else 0 }.getOrDefault(0)

    fun thongTin(): String = JSONObject()
        .put("soKhach", if (daNap) dem() else 0)
        .put("thuMuc", if (daNap) thuMuc.absolutePath else "")
        .put("sheet", when {
            !daNap -> "chưa nạp"
            coSheet() -> "ĐÃ cấu hình" + (if (lucGuiDuocCuoi > 0) " · gửi được lần cuối ${(System.currentTimeMillis() - lucGuiDuocCuoi) / 1000} giây trước" else " · chưa gửi được dòng nào")
            else -> "CHƯA cấu hình — thiếu tệp google-sheet.json trên robot (khách vẫn được lưu trong máy)"
        })
        .put("choGui", if (daNap) docHangDoi().length() else 0)
        .put("loiCuoi", loiCuoi)
        .toString()

    /** Trả true khi ĐÃ GHI RA THẺ NHỚ. Gửi Google Sheets là chuyện sau, không chặn màn hình. */
    @Synchronized
    fun ghi(k: JSONObject): Boolean {
        if (!daNap) return false
        k.put("id", UUID.randomUUID().toString().take(13))
        k.put("thoi_gian", gio.format(Date()))
        k.put("thiet_bi", android.os.Build.SERIAL.takeIf { it.isNotBlank() && it != "unknown" } ?: "Minibot")
        return runCatching {
            fJsonl.appendText(k.toString() + "\n", Charsets.UTF_8)
            if (!fCsv.isFile) fCsv.writeText("﻿Thời gian,Họ và tên,Số điện thoại,Chức vụ,Doanh nghiệp / đơn vị,Nguồn,Câu hỏi đang xem\n", Charsets.UTF_8)
            fCsv.appendText(listOf("thoi_gian", "ten", "sdt", "chuc_vu", "don_vi", "nguon", "quan_tam")
                .joinToString(",") { csv(k.optString(it)) } + "\n", Charsets.UTF_8)
            val m = docHangDoi(); m.put(k); fHangDoi.writeText(m.toString(), Charsets.UTF_8)
            Log.d(TAG, "ĐÃ GHI khách: ${k.optString("ten")} · ${k.optString("sdt")}")
            tho.execute { runCatching { guiHangDoi() } }
            true
        }.onFailure { Log.e(TAG, "KHÔNG GHI ĐƯỢC KHÁCH: ${it.message}") }.getOrDefault(false)
    }

    private fun csv(s: String) = "\"" + s.replace("\"", "\"\"") + "\""
    private fun docHangDoi(): JSONArray =
        runCatching { if (fHangDoi.isFile) JSONArray(fHangDoi.readText(Charsets.UTF_8)) else JSONArray() }.getOrDefault(JSONArray())

    /** Gửi lần lượt từ đầu hàng đợi; hỏng một dòng là dừng, giữ nguyên phần còn lại cho lượt sau. */
    private fun guiHangDoi() {
        if (!daNap || !coSheet()) return
        while (true) {
            val k = synchronized(this) { val m = docHangDoi(); if (m.length() == 0) null else m.getJSONObject(0) } ?: return
            if (!guiMot(k)) return
            synchronized(this) {
                val m = docHangDoi(); val moi = JSONArray()
                for (i in 0 until m.length()) if (m.getJSONObject(i).optString("id") != k.optString("id")) moi.put(m.get(i))
                fHangDoi.writeText(moi.toString(), Charsets.UTF_8)
            }
        }
    }

    /**
     * POST một dòng tới Apps Script. Apps Script trả 302 sang script.googleusercontent.com rồi
     * mới ra JSON — HttpURLConnection tự đi theo. Chỉ coi là XONG khi thân trả về có "ok":true;
     * trang đăng nhập Google (triển khai sai quyền) cũng trả HTTP 200 nên không tin mã HTTP.
     */
    private fun guiMot(k: JSONObject): Boolean = runCatching {
        val than = JSONObject()
            .put("ma", ma).put("id", k.optString("id")).put("thoi_gian", k.optString("thoi_gian"))
            .put("ho_ten", k.optString("ten")).put("so_dien_thoai", k.optString("sdt"))
            .put("chuc_vu", k.optString("chuc_vu")).put("don_vi", k.optString("don_vi"))
            .put("nguon", k.optString("nguon")).put("quan_tam", k.optString("quan_tam"))
            .put("thiet_bi", k.optString("thiet_bi"))
        (URL(url).openConnection() as HttpURLConnection).run {
            requestMethod = "POST"; connectTimeout = 10_000; readTimeout = 20_000; doOutput = true
            instanceFollowRedirects = true
            setRequestProperty("Content-Type", "text/plain; charset=utf-8")   // text/plain: Apps Script nhận thẳng, khỏi preflight
            outputStream.use { it.write(than.toString().toByteArray(Charsets.UTF_8)) }
            val maHttp = responseCode
            val tra = (if (maHttp in 200..299) inputStream else errorStream)?.bufferedReader()?.use { it.readText() }.orEmpty()
            disconnect()
            val ok = maHttp in 200..299 && Regex("\"ok\"\\s*:\\s*true").containsMatchIn(tra)
            if (ok) { loiCuoi = ""; lucGuiDuocCuoi = System.currentTimeMillis(); Log.d(TAG, "Google Sheets ĐÃ NHẬN: ${k.optString("ten")}") }
            else {
                loiCuoi = "HTTP $maHttp · " + (Regex("\"loi\"\\s*:\\s*\"([^\"]+)\"").find(tra)?.groupValues?.get(1)
                    ?: if (tra.contains("<html", true)) "máy chủ trả trang web thay vì JSON — kiểm tra lại quyền truy cập của bản triển khai (phải là 'Bất kỳ ai')" else tra.take(120))
                Log.w(TAG, "Google Sheets từ chối: $loiCuoi")
            }
            ok
        }
    }.onFailure { loiCuoi = "không gửi được: ${it.javaClass.simpleName} ${it.message.orEmpty()}".trim(); Log.w(TAG, loiCuoi) }.getOrDefault(false)

    /** Màn kỹ thuật: gửi một dòng THỬ để biết đường lên Sheets thông chưa. Không ghi vào sổ khách. */
    fun guiThu(khiXong: (String) -> Unit) {
        tho.execute {
            docCauHinh()
            if (!coSheet()) { khiXong("CHƯA cấu hình — thiếu google-sheet.json trên robot"); return@execute }
            val k = JSONObject().put("id", "thu-" + UUID.randomUUID().toString().take(8)).put("thoi_gian", gio.format(Date()))
                .put("ten", "DÒNG THỬ KẾT NỐI — xoá được").put("sdt", "").put("chuc_vu", "").put("don_vi", "")
                .put("nguon", "Màn kỹ thuật").put("quan_tam", "").put("thiet_bi", "Minibot")
            khiXong(if (guiMot(k)) "THÔNG — đã ghi một dòng thử lên trang tính lúc ${gio.format(Date())}" else "HỎNG — $loiCuoi")
        }
    }
}

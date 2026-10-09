package vn.roboworld.chibach

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.os.Handler
import android.os.Looper
import android.util.Log
import java.io.File
import java.security.MessageDigest

/**
 * GIỌNG ROBOT — giọng Yuna (ElevenLabs) sinh sẵn thành MP3, anh Trường yêu cầu 01/10/2026.
 *
 * Tên tệp = SHA-1 của ĐÚNG chuỗi robot đọc (tools/sinh-giong.py băm cùng cách). Tìm theo thứ tự:
 *   <externalFilesDir>/giong/<sha1>.mp3   (đẩy bằng tools/day-web.py — đổi giọng không cần build lại)
 *   assets/giong/<sha1>.mp3               (đóng trong APK)
 * Không có tệp → trả false, RobotHelper rơi về giọng máy (SkillApi) và ghi câu vào files/thieu-giong.txt.
 * ⚠ Lệch MỘT ký tự giữa chuỗi lớp web gửi và chuỗi đã sinh là không khớp — sửa lời thì phải sinh lại.
 */
object Giong {
    private const val TAG = "ChiBachGiong"
    private val main = Handler(Looper.getMainLooper())
    private var ctx: Context? = null
    private var thuMucNgoai: File? = null
    private var assetsCo: Set<String> = emptySet()
    @Volatile private var may: MediaPlayer? = null
    @Volatile private var khiXongDang: (() -> Unit)? = null

    fun nap(c: Context) {
        ctx = c.applicationContext
        thuMucNgoai = File(c.getExternalFilesDir(null), "giong").also { it.mkdirs() }
        assetsCo = runCatching { c.assets.list("giong")?.toSet() }.getOrNull() ?: emptySet()
        Log.d(TAG, "Giọng Yuna: ${assetsCo.size} tệp trong APK · ${thuMucNgoai?.list()?.count { it.endsWith(".mp3") } ?: 0} tệp ở thẻ nhớ")
    }

    fun soFile(): Int = (assetsCo + (thuMucNgoai?.list()?.filter { it.endsWith(".mp3") }?.toSet() ?: emptySet())).size

    private fun sha1(t: String): String =
        MessageDigest.getInstance("SHA-1").digest(t.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }

    /** Phát MP3 của câu này. Trả false nếu không có tệp (người gọi tự rơi về giọng máy). */
    fun noi(vanBan: String, khiXong: () -> Unit): Boolean {
        val c = ctx ?: return false
        val ten = sha1(vanBan) + ".mp3"
        val ngoai = thuMucNgoai?.let { File(it, ten) }
        val coNgoai = ngoai != null && ngoai.isFile
        if (!coNgoai && ten !in assetsCo) { ghiThieu(vanBan); return false }
        im()
        val p = MediaPlayer().apply {
            setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build())
        }
        return runCatching {
            if (coNgoai) p.setDataSource(ngoai!!.absolutePath)
            else c.assets.openFd("giong/$ten").use { p.setDataSource(it.fileDescriptor, it.startOffset, it.length) }
            khiXongDang = khiXong
            p.setOnCompletionListener { xong(p) }
            p.setOnErrorListener { _, w, e -> Log.w(TAG, "Lỗi phát $ten ($w/$e)"); xong(p); true }
            p.prepare(); p.start(); may = p
            Log.d(TAG, "Phát Yuna ${ten.take(10)}… · ${vanBan.take(40)}")
            true
        }.getOrElse { Log.w(TAG, "Không phát được $ten: ${it.message}"); runCatching { p.release() }; false }
    }

    private fun xong(p: MediaPlayer) {
        if (may !== p) return
        may = null; runCatching { p.release() }
        val k = khiXongDang; khiXongDang = null
        if (k != null) main.post(k)
    }

    /** Cắt câu đang phát NGAY (khách chạm, đổi câu, rời chế độ). Báo "đọc xong" cho lớp web như giọng máy. */
    fun im() {
        val m = may ?: return
        may = null
        runCatching { if (m.isPlaying) m.stop() }; runCatching { m.release() }
        val k = khiXongDang; khiXongDang = null
        if (k != null) main.post(k)
    }

    fun dangPhat(): Boolean = may != null

    private fun ghiThieu(vanBan: String) {
        Log.w(TAG, "THIẾU MP3 giọng Yuna cho câu: ${vanBan.take(60)} — rơi về giọng máy. Chạy tools/sinh-giong.py")
        runCatching {
            val f = File(ctx!!.getExternalFilesDir(null), "thieu-giong.txt")
            if (f.isFile && f.readText(Charsets.UTF_8).contains(vanBan)) return
            f.appendText(vanBan.replace('\n', ' ') + "\n", Charsets.UTF_8)
        }
    }
}

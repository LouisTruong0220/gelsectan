package vn.roboworld.chibach

/**
 * MỌI CON SỐ CHỈNH ĐƯỢC GOM MỘT CHỖ — sửa ở đây rồi build lại APK.
 * (Robot Gelsectan — Chi Bách Pharma — Minibot, dựng 30/09/2026)
 *
 * Những thứ KHÔNG nằm ở đây vì đổi được mà không cần build lại (đẩy bằng tools/day-web.py):
 *   · bộ câu hỏi, lời robot nói, điểm du hành, điểm lễ tân, số giây chờ → du-lieu/app-data.json
 *   · địa chỉ Google Sheets của khách                                   → files/google-sheet.json
 */
object Cai {

    /**
     * appId OrionStar.
     * ⚠⚠ ĐANG MƯỢN appId dùng chung của các app sự kiện Roboworld (su-kien-rbw). Anh Trường chưa
     *   cấp appId riêng cho app này — có thì thay ở HAI chỗ phải khớp nhau: hằng số này và
     *   assets/actionRegistry.json (Agent SDK đọc ở đó).
     */
    const val APP_ID = "app_cf616a2925464745b14bc4e3b2275e6d"

    // ══════════════════ GIAO TIẾP AI — AgentOS + kiến thức Robot Portal ══════════════════
    //
    // Anh Trường yêu cầu 30/09/2026: "tham khảo app Tây Hòa, kết nối AI với AgentOS và Portal".
    // Lối chép từ bản chính thức 1.5 app Tây Hòa qua app Cao Xanh Minibot: AgentOS tự hoạch định
    // và trả lời bằng kho kiến thức trên Robot Portal; app lo micro bấm-mới-nghe và cắt AgentOS
    // khi nó nói ngoài lượt.
    //
    // KHÁC hai app đó ở MỘT điểm, vì đây là nội dung y tế đã được khách duyệt từng câu và khách
    // từng gặp giải pháp khác "trả lời không đúng trọng tâm" với câu nằm ngay trong bộ câu hỏi:

    /**
     * Câu khách hỏi mà bộ tìm trong máy nhận ra CHẮC là một trong các câu của bộ câu hỏi →
     * APP tự đọc NGUYÊN VĂN câu trả lời khách đã duyệt và CẮT AgentOS ở lượt đó. AgentOS + Portal
     * chỉ trả lời những câu bộ tìm không chắc.
     * Đặt false = mọi câu nói đều để AgentOS tự trả lời (đúng y lối Tây Hòa) — khi đó độ đúng
     * phụ thuộc hoàn toàn vào kho Portal và mô hình.
     */
    const val DOC_NGUYEN_VAN_KHI_KHOP = true

    /** Có đăng ký KNOWLEDGE_QA không — đăng ký = AgentOS được đọc kho Portal. Bỏ là mất cả đường nghe. */
    const val GIU_KNOWLEDGE_QA = true

    /** Giao câu cho AgentOS mà quá ngần này không thấy nó mở miệng → app nói "em chưa có". Đo ở Tây Hòa: 6,8–11,6 giây. */
    const val HAN_CHO_AGENTOS_MS = 15_000L

    /**
     * ⚠⚠ MINIBOT ĐỜI CŨ KHÔNG CÓ AgentOS (máy MC1BHW0C170230407107, ROM 07/07/2023 thiếu gói
     * com.ainirobot.agentservice). App tự dò lúc khởi động; không có thì KHÔNG dựng AppAgent và
     * chạy chế độ DỰ PHÒNG: micro qua tai RobotOS đời cũ, câu trong bộ câu hỏi vẫn đọc nguyên
     * văn, câu ngoài bộ thì nói thẳng "em chưa có" + mời để lại thông tin.
     */
    const val BAT_DU_PHONG = true

    /** Micro ở chế độ dự phòng — tai RobotOS đời cũ (speechasrservice, Google ASR vi_VN). Đo 28/09/2026. */
    const val MIC_ROBOTOS_CU = true

    /**
     * Ở chế độ dự phòng có gửi câu NGOÀI bộ câu hỏi lên đám mây OrionStar (SkillApi.queryByText) không.
     * TẮT có chủ ý: đám mây đó là mô hình chung, KHÔNG đọc kho Portal, không biết nguyên tắc
     * compliance của khách — để nó trả lời câu hỏi y tế là rủi ro. (28/08/2026 hãng còn chưa bật.)
     */
    const val HOI_DAM_MAY_KHI_KHONG_CO_AGENTOS = false
    const val HAN_CHO_DAM_MAY_MS = 6_000L

    // ══════════════════ MIC ══════════════════
    /** Im lặng quá mức này thì coi là dứt câu → tắt mic và xử lý câu. */
    const val CHO_DUT_CAU_MS = 1_400L

    /** Bấm mic rồi bỏ đi — trần cứng để mic không mở mãi. */
    const val TRAN_MO_MIC_MS = 15_000L

    /** Thăm dò lại xem mô hình gọi được chưa (Agent SDK có khi mất 75 giây mới trả lời lần đầu). */
    const val THAM_DO_LAI_MS = 20_000L

    // ══════════════════ XOAY THEO NGƯỜI (DoiDien.kt) ══════════════════
    // Khách chạm màn hình → robot xoay đối diện người gần nhất và giữ hướng theo họ.
    // ⚠ Chép từ Nova (đo 24/09/2026), CHƯA đo trên Minibot. Thấy khó chịu thì tắt bằng một dòng này.
    const val BAT_XOAY_THEO_NGUOI = true
    const val XOAY_NGUONG_MET = 2.0
    const val XOAY_VANG_MS = 6_000L
    const val XOAY_MAT_DAU_MS = 8_000L
    const val XOAY_TOC_DO = 25f
    const val XOAY_BO_QUA_DO = 8.0

    // ══════════════════ GOOGLE SHEETS ══════════════════
    /** Gửi hỏng (mất mạng) thì thử lại sau ngần này. Wi-Fi hội nghị rớt đúng lúc đông khách nhất. */
    const val SHEET_GUI_LAI_GIAY = 30L
}

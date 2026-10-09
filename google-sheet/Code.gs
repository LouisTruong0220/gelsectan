/**
 * NHẬN THÔNG TIN KHÁCH TỪ ROBOT → ghi vào trang tính này.
 *
 * Cách dùng (làm MỘT lần, bằng tài khoản Google là chủ trang tính):
 *   1. Mở trang tính → Tiện ích mở rộng → Apps Script → xoá hết mã có sẵn → dán toàn bộ tệp này.
 *   2. Đổi MA_BI_MAT bên dưới thành một chuỗi riêng của anh chị (chữ và số, không dấu).
 *   3. Triển khai → Tùy chọn triển khai mới → loại "Ứng dụng web":
 *        Thực thi dưới tên: Tôi  ·  Người có quyền truy cập: Bất kỳ ai
 *   4. Sao chép "URL ứng dụng web" (kết thúc bằng /exec) + mã bí mật, gửi cho kỹ thuật viên robot.
 *
 * Sửa mã sau này thì phải: Triển khai → Quản lý các tùy chọn triển khai → biểu tượng bút chì →
 * Phiên bản: "Phiên bản mới" → Triển khai. Không làm bước đó thì địa chỉ cũ vẫn chạy mã cũ.
 */

/** ĐỔI chuỗi này. Robot phải gửi đúng chuỗi này thì dòng mới được ghi — chặn người lạ có địa chỉ mà ghi bừa. */
var MA_BI_MAT = 'doi-ma-nay-truoc-khi-dung';

/** Tên trang (tab) sẽ chứa dữ liệu — chưa có thì tự tạo. */
var TEN_TRANG = 'Khách để lại thông tin';

var TIEU_DE = ['Thời gian', 'Họ và tên', 'Số điện thoại', 'Chức vụ', 'Doanh nghiệp / đơn vị',
               'Nguồn (chế độ trên robot)', 'Câu hỏi đang xem', 'Robot', 'Mã dòng'];

function doPost(e) {
  var khoa = LockService.getScriptLock();
  try {
    khoa.waitLock(20000);                       // hai robot gửi cùng lúc thì xếp hàng, không ghi đè nhau
    var d = JSON.parse(e.postData.contents);
    if (d.ma !== MA_BI_MAT) return tra({ ok: false, loi: 'sai ma bi mat' });

    var bang = SpreadsheetApp.getActiveSpreadsheet();
    var trang = bang.getSheetByName(TEN_TRANG) || bang.insertSheet(TEN_TRANG);
    if (trang.getLastRow() === 0) {
      trang.appendRow(TIEU_DE);
      trang.getRange(1, 1, 1, TIEU_DE.length).setFontWeight('bold').setBackground('#006097').setFontColor('#ffffff');
      trang.setFrozenRows(1);
      trang.getRange('C:C').setNumberFormat('@');   // cột số điện thoại là CHỮ — không thì mất số 0 đầu
    }

    // Robot gửi lại khi mạng chập chờn — dòng nào đã có "Mã dòng" này rồi thì bỏ qua, không ghi trùng.
    var cuoi = trang.getLastRow();
    if (d.id && cuoi > 1) {
      var tu = Math.max(2, cuoi - 300);
      var ma = trang.getRange(tu, TIEU_DE.length, cuoi - tu + 1, 1).getValues();
      for (var i = 0; i < ma.length; i++) if (ma[i][0] === d.id) return tra({ ok: true, trung: true });
    }

    trang.appendRow([d.thoi_gian || '', d.ho_ten || '', "'" + (d.so_dien_thoai || ''), d.chuc_vu || '',
                     d.don_vi || '', d.nguon || '', d.quan_tam || '', d.thiet_bi || '', d.id || '']);
    return tra({ ok: true });
  } catch (loi) {
    return tra({ ok: false, loi: String(loi) });
  } finally {
    try { khoa.releaseLock(); } catch (x) {}
  }
}

/** Mở địa chỉ /exec bằng trình duyệt để thử: thấy dòng chữ dưới đây là bản triển khai đang sống. */
function doGet() {
  return tra({ ok: true, tin: 'Dia chi nhan thong tin khach tu robot dang hoat dong.' });
}

function tra(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

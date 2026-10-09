/**
 * BỘ THỬ LUỒNG + SOI MÀN HÌNH — app Gelsectan (Chi Bách Pharma · Minibot)
 *
 *   node tools/thu-app.mjs            # chạy hết: chụp từng màn ở 1920×1080 + kiểm các luật
 *
 * Mở demo/index.html bằng Chromium với một cây cầu CAU GIẢ ghi lại MỌI LỆNH lớp web gửi xuống
 * robot. Lỗi của nhóm app này hiếm khi hiện ra trong ảnh chụp — nó nằm ở chỗ "lệnh nào đã được
 * gửi, lúc nào" — nên bộ thử ĐẾM LỆNH:
 *   A  chạm màn biểu cảm → lời chào + bật xoay theo người
 *   B  tra cứu: chọn câu là đọc NGUYÊN VĂN bản đọc của câu đó; chọn câu khác là CẮT NGAY câu cũ
 *   C  rời Tra cứu / Giao tiếp AI → bảng mời để lại thông tin; bỏ qua được; không hỏi lại lần hai
 *   D  bảng điền: bàn phím Telex, kiểm lỗi, ghi khách đúng bốn ô + nguồn
 *   E  giao tiếp AI: mic, câu trả lời, câu gợi ý, mở bảng bằng lời
 *   F  du hành: đi vòng Diem 1..5, tới nơi đi tiếp ngay, vừa đi vừa nói, chạm là dừng, vắng là đi tiếp
 *   G  lễ tân: về điểm Le tan, đứng mời khách; robot chưa sẵn sàng thì đứng tại chỗ vẫn mời
 *   H  robot không tự đánh thức mình bằng chính câu "Xin chào" nó vừa nói
 *   +  mỗi màn: lỗi JS · trang cuộn được · nút 0×0 · nút lọt khỏi khung
 *
 * ⚠ Chromium máy tính là bản MỚI, Minibot là Chrome 66 — bộ này KHÔNG bắt được cú pháp đời mới;
 *   việc đó là của cổng trong dung-app.py. Buổi máy thật đầu tiên vẫn phải chụp màn robot mà nhìn.
 * Playwright mượn của tools/html-video, không cài riêng.
 */
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const APP = resolve(HERE, '..');
const PW = join(APP, '..', '..', 'tools', 'html-video', 'packages', 'adapter-hyperframes', 'node_modules', 'playwright', 'index.mjs');
if (!existsSync(PW)) { console.error(`Không thấy playwright tại:\n  ${PW}`); process.exit(2); }
const { chromium } = await import(pathToFileURL(PW).href);
const RA = join(APP, 'demo', 'anh-soi');
mkdirSync(RA, { recursive: true });
const D = JSON.parse(readFileSync(join(APP, 'du-lieu', 'app-data.json'), 'utf8'));
const cauTheoId = Object.fromEntries(D.cau.map(c => [c.id, c]));

const trinhDuyet = await chromium.launch();
const trang = await trinhDuyet.newPage({ viewport: { width: 1920, height: 1080 } });
const loiJs = [];
trang.on('pageerror', e => loiJs.push('LỖI JS: ' + e.message));
trang.on('console', m => { if (m.type() === 'error' && !/net::ERR_FILE_NOT_FOUND/.test(m.text())) loiJs.push('console: ' + m.text()); });

/* Cầu CAU giả — ghi mọi lệnh vào window.GIA.goi, kèm mốc thời gian. */
await trang.addInitScript(() => {
  const GIA = window.GIA = { goi: [], lyDo: '', t0: Date.now() };
  const ghi = ten => function () { GIA.goi.push([ten].concat(Array.prototype.slice.call(arguments)).concat([Date.now() - GIA.t0])); };
  window.CAU = {
    doc: ghi('doc'), dungDoc: ghi('dungDoc'), nguoiDungThaoTac: ghi('nguoiDungThaoTac'),
    batDoiDien: ghi('batDoiDien'), tatDoiDien: ghi('tatDoiDien'), baoManHinh: ghi('baoManHinh'),
    vaoChat: ghi('vaoChat'), batMic: ghi('batMic'), tatMic: ghi('tatMic'), xoaNguCanh: ghi('xoaNguCanh'),
    ghiNhatKy: ghi('ghiNhatKy'), diToiDiem: ghi('diToiDiem'), dungDi: ghi('dungDi'),
    kiemTraBanDo: ghi('kiemTraBanDo'), guiThuSheet: ghi('guiThuSheet'),
    batNhay: ghi('batNhay'), dungNhay: ghi('dungNhay'), dongTac: ghi('dongTac'),
    ghiKhach(j) { GIA.goi.push(['ghiKhach', j]); return true; },
    diemCoTrenBanDo(j) { return j; },
    lyDoChuaDanDuongDuoc() { return GIA.lyDo; },
    thongTinAI() { return JSON.stringify({ cheDo: 'agentos', coAgentOS: true, appId: 'app_thu', agentSanSang: true, micHeThong: 1, mang: 'wifi', ngheCuoiGiay: 3, robot: 'đã nối RobotOS, sẵn sàng', nguonNoiDung: 'khung: APK · dữ liệu: APK' }); },
    thongTinKhach() { return JSON.stringify({ soKhach: 12, thuMuc: '/sdcard/…/khach-hang', sheet: 'ĐÃ cấu hình · gửi được lần cuối 40 giây trước', choGui: 0, loiCuoi: '' }); },
  };
});
await trang.goto(pathToFileURL(join(APP, 'demo', 'index.html')).href, { waitUntil: 'load' });
await trang.waitForTimeout(600);

let dat = 0; const truot = [];
function kiem(ok, ten, them = '') { if (ok) dat++; else truot.push(ten + (them ? ' — ' + them : '')); console.log((ok ? '  ✓ ' : '  ✗ ') + ten + (ok || !them ? '' : ' — ' + them)); }
const cho = ms => trang.waitForTimeout(ms);
const lenh = ten => trang.evaluate(t => window.GIA.goi.filter(x => x[0] === t), ten);
const xoaLenh = () => trang.evaluate(() => { window.GIA.goi.length = 0; });
const man = () => trang.evaluate(() => manDang);
const hienPhu = id => trang.evaluate(i => document.querySelector(i).classList.contains('hien'), id);

/** Chụp + kiểm bố cục màn đang hiện (và lớp phủ đang mở). */
async function soi(ten) {
  await trang.screenshot({ path: join(RA, ten + '.png') });
  const bao = await trang.evaluate(() => {
    const r = [];
    const h = document.documentElement; h.scrollTop = 50; const cuon = h.scrollTop > 0; h.scrollTop = 0;
    if (cuon) r.push('TRANG CUỘN ĐƯỢC — giao diện sẽ nhúc nhích dưới tay khách');
    const vung = Array.prototype.slice.call(document.querySelectorAll('.phu.hien'));
    const goc = vung.length ? vung : [document.querySelector('.man-hinh.hien')];
    goc.forEach(hien => {
      if (!hien) { r.push('KHÔNG có màn nào đang hiện'); return; }
      hien.querySelectorAll('button, .o, .phim').forEach(e => {
        let cha = e, an = false;
        while (cha && cha !== hien) { if (getComputedStyle(cha).display === 'none') { an = true; break; } cha = cha.parentElement; }
        if (an) return;
        const nhan = (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 30);
        const b = e.getBoundingClientRect();
        if (b.width < 8 || b.height < 8) r.push('NÚT BỊ CO VỀ 0: "' + nhan + '" ' + Math.round(b.width) + '×' + Math.round(b.height));
        let trongCuon = false, o = e.parentElement;
        while (o && o !== hien) { const ov = getComputedStyle(o).overflowY; if ((ov === 'auto' || ov === 'scroll') && o.scrollHeight > o.clientHeight + 2) { trongCuon = true; break; } o = o.parentElement; }
        if (!trongCuon && (b.bottom > innerHeight + 2 || b.right > innerWidth + 2 || b.left < -2)) r.push('NÚT LỌT KHỎI KHUNG: "' + nhan + '"');
        /* Dải trạng thái của hãng phủ 2,9rem trên đỉnh màn — nút nằm trong đó là bị đè. */
        if (!trongCuon && b.top < 44 && b.height > 0) r.push('NÚT NẰM DƯỚI DẢI TRẠNG THÁI CỦA HÃNG: "' + nhan + '" (top ' + Math.round(b.top) + 'px)');
      });
      /* Chữ tràn khỏi ô của nó */
      hien.querySelectorAll('#tc-dap-chu, #ai-cau, .o-che-do .chu, .hop-hoi').forEach(e => {
        if (getComputedStyle(e).display === 'none' || !e.offsetParent) return;
        if (e.scrollHeight > e.clientHeight + 3 && getComputedStyle(e).overflow !== 'visible') r.push('CHỮ BỊ CẮT trong ' + (e.id || e.className));
      });
    });
    return r;
  });
  const het = bao.concat(loiJs.splice(0));
  kiem(het.length === 0, 'màn ' + ten, het.join(' · '));
}

/* ═══ A — chạm màn biểu cảm ═══ */
console.log('\nA. Màn biểu cảm → màn chính');
await cho(900);
kiem(await trang.evaluate(() => { const v = document.querySelector('#clip-cho'); return !!v.getAttribute('src') && v.readyState >= 2; }), 'clip biểu cảm màn chờ đã nạp và giải mã được');
await soi('01-man-bieu-cam');
await trang.click('#mh-cho');
await cho(900);
kiem(await man() === 'mh-chinh', 'chạm → màn chính');
kiem((await lenh('batDoiDien')).length === 1, 'bật xoay theo người đúng MỘT lần');
let d = await lenh('doc');
kiem(d.length === 1 && d[0][1] === D.loi.chao.doc, 'robot đọc lời chào (bản đọc, tên riêng đã phiên âm)', JSON.stringify(d));
await soi('02-man-chinh');

/* ═══ B — tra cứu ═══ */
console.log('\nB. Tra cứu');
await xoaLenh();
await trang.evaluate(() => moTraCuu());
await cho(250);
kiem((await lenh('dungDoc')).length >= 1 && (await lenh('nguoiDungThaoTac')).length >= 1, 'vào Tra cứu là cắt lời chào NGAY (dungDoc + nguoiDungThaoTac)');
await cho(500);
await soi('03-tra-cuu-chua-chon');
kiem(await trang.evaluate(() => document.querySelectorAll('#tc-ds .cau-hoi').length) === D.cau.length, `danh sách đủ ${D.cau.length} câu hỏi`);
await xoaLenh();
await trang.evaluate(() => chonCau('0.10'));
await cho(120);
await trang.evaluate(() => chonCau('0.22'));          // đổi ý ngay, câu 0.10 chưa kịp đọc
await cho(800);
d = await lenh('doc');
kiem(d.length === 1 && d[0][1] === cauTheoId['0.22'].doc, 'đổi câu giữa chừng: chỉ câu SAU được đọc, đúng nguyên văn bản đọc', d.map(x => x[1].slice(0, 30)).join(' | '));
kiem(await trang.evaluate(() => document.querySelector('#tc-dap-chu').textContent) === cauTheoId['0.22'].dap, 'màn hình hiện NGUYÊN VĂN câu trả lời của khách');
await soi('04-tra-cuu-cau-dai-nhat');
await xoaLenh();
await trang.evaluate(() => chonCau('0.5'));
await cho(30);
const ngat = await trang.evaluate(() => window.GIA.goi.map(x => x[0]));
kiem(ngat.indexOf('dungDoc') >= 0 && ngat.indexOf('dungDoc') < (ngat.indexOf('doc') < 0 ? 99 : ngat.indexOf('doc')), 'chọn câu khác lúc đang đọc: lệnh cắt tiếng đi TRƯỚC lệnh đọc mới');
await cho(600);
await soi('05-tra-cuu-cau-ngan');
await xoaLenh();
kiem(await trang.evaluate(() => { chonCau('0.5'); window.robotDocXong(); return document.querySelector('#tc-nut-doc').textContent; }) === 'Dừng đọc',
     'tin "đọc xong" của câu vừa bị cắt về muộn → nút vẫn ghi "Dừng đọc" cho câu mới');
await cho(1100);
kiem(await trang.evaluate(() => { window.robotDocXong(); return document.querySelector('#tc-nut-doc').textContent; }) === 'Nghe lại',
     'câu mới đọc xong thật → nút đổi thành "Nghe lại"');
await trang.evaluate(() => docLaiTraCuu()); await cho(450);   // bấm Nghe lại → đọc lại
await xoaLenh();
await trang.evaluate(() => docLaiTraCuu());            // đang đọc → bấm = dừng
await cho(500);
kiem((await lenh('dungDoc')).length >= 1 && (await lenh('doc')).length === 0, 'nút "Dừng đọc" cắt tiếng, không đọc lại');
await trang.evaluate(() => cauKe(1)); await cho(600);
kiem(await trang.evaluate(() => cauDang.id) === '0.25', 'nút "Câu sau" đi theo thứ tự đang hiện trên màn (sau 0.5 là 0.25 trong nhóm Tổng quan)', await trang.evaluate(() => cauDang.id));

/* ═══ C — rời chế độ → bảng mời để lại thông tin ═══ */
console.log('\nC. Rời Tra cứu / Giao tiếp AI → bảng để lại thông tin');
await xoaLenh();
await trang.evaluate(() => veTrangChu());
await cho(700);
kiem(await hienPhu('#phu-form') && await man() === 'mh-tra-cuu', 'rời Tra cứu → bảng điền bật lên (chưa rời màn)');
d = await lenh('doc');
kiem(d.length === 1 && d[0][1] === D.loi.form_mo.doc, 'robot đọc đúng lời mời của khách', JSON.stringify(d));
await soi('06-bang-de-lai-thong-tin');
await trang.click('#form-bo-qua'); await cho(300);
kiem(!(await hienPhu('#phu-form')) && await man() === 'mh-chinh', 'bấm "Bỏ qua" → về màn chính');
await trang.evaluate(() => moTraCuu()); await cho(200);
await trang.evaluate(() => veTrangChu()); await cho(300);
kiem(!(await hienPhu('#phu-form')) && await man() === 'mh-chinh', 'khách đã bỏ qua một lần → lượt này không hỏi lại');
await trang.evaluate(() => { veManCho(); }); await cho(200);
await trang.click('#mh-cho'); await cho(300);           // khách MỚI
await trang.evaluate(() => { window.baoCheDoAI('agentos', true); window.baoAISanSang(true); moChat(); }); await cho(300);
await trang.evaluate(() => veTrangChu()); await cho(500);
kiem(await hienPhu('#phu-form') && await man() === 'mh-chat', 'khách mới, rời Giao tiếp AI → bảng điền bật lên');

/* ═══ D — bảng điền ═══ */
console.log('\nD. Bảng điền + bàn phím Telex');
await xoaLenh();
await trang.evaluate(() => guiForm()); await cho(200);
kiem((await lenh('ghiKhach')).length === 0 && await hienPhu('#phu-form'), 'để trống mà bấm Gửi → KHÔNG ghi, vẫn ở bảng');
kiem(await trang.evaluate(() => document.querySelector('#o-ten').classList.contains('loi') && document.querySelector('#bao-ten').textContent.length > 0), 'ô bắt buộc được đánh dấu đỏ + có chữ báo');
async function go(chu) { for (const k of chu) { await trang.evaluate(x => goPhim(x), k); } }
await cho(5200);                                         // chờ hộp báo lỗi tự tắt để ảnh chụp bảng không bị che
await trang.evaluate(() => chonO('ten')); await go('nguyeenx vawn an');
await trang.evaluate(() => chonO('sdt')); await go('0912345678');
await soi('07-bang-ban-phim-so');
await trang.evaluate(() => chonO('chuc_vu')); await go('bacs six');
await trang.evaluate(() => chonO('don_vi')); await go('beenhj vieenj bachj mai');
await soi('08-bang-da-dien');
kiem(await trang.evaluate(() => document.querySelector('#o-ten .gia').textContent) === 'Nguyễn Văn An', 'Telex: "nguyeenx vawn an" → "Nguyễn Văn An"', await trang.evaluate(() => document.querySelector('#o-ten .gia').textContent));
/* Bấm phím thật bằng chuột — bộ nghe gắn ở khung bàn phím, phím vẽ lại liên tục */
await trang.click('#ban-phim .phim[data-k="a"]'); await trang.click('#ban-phim .phim[data-k="LUI"]');
kiem(await trang.evaluate(() => raw.don_vi) === 'beenhj vieenj bachj mai', 'bấm phím thật: gõ một chữ rồi xoá lùi, ô trở lại như cũ');
await trang.evaluate(() => guiForm()); await cho(300);
const kh = await lenh('ghiKhach');
const k0 = kh.length ? JSON.parse(kh[0][1]) : {};
kiem(kh.length === 1 && k0.ten === 'Nguyễn Văn An' && k0.sdt === '0912345678' && k0.chuc_vu === 'Bác sĩ' && k0.don_vi === 'Bệnh viện bạch mai' && k0.nguon === 'Giao tiếp AI',
     'ghi khách đúng MỘT lần, đủ bốn ô + nguồn', JSON.stringify(k0));
await cho(500);
await soi('09-bang-cam-on');
d = await lenh('doc');
kiem(d.some(x => x[1] === D.loi.cam_on.doc), 'robot đọc lời cảm ơn');
await trang.evaluate(() => dongForm()); await cho(200);
kiem(await man() === 'mh-chinh' && !(await hienPhu('#phu-form')), 'gửi xong → về màn chính');
await trang.evaluate(() => { moTraCuu(); moForm(null, true); }); await cho(7000);
kiem(await hienPhu('#phu-form'), 'mở lại bảng ngay sau khi gửi: hẹn tự đóng của màn cảm ơn KHÔNG được đóng nhầm bảng mới');
await trang.evaluate(() => boQuaForm()); await cho(150);
await trang.evaluate(() => moTraCuu()); await cho(150);
await trang.evaluate(() => veTrangChu()); await cho(300);
kiem(!(await hienPhu('#phu-form')), 'khách đã để lại thông tin → rời chế độ không hỏi nữa');

/* ═══ E — giao tiếp AI ═══ */
console.log('\nE. Giao tiếp AI');
await xoaLenh();
await trang.evaluate(() => moChat()); await cho(700);
d = await lenh('doc');
kiem(d.length === 1 && d[0][1] === D.loi.chao_ai_mic.doc, 'vào màn AI: robot mời bấm micro');
await soi('10-ai-san-sang');
await trang.click('#thanh-mic'); await cho(100);
kiem((await lenh('batMic')).length === 1, 'bấm nút → mở mic');
await cho(1600);
await soi('11-ai-dang-nghe');
await trang.evaluate(() => window.nhanLoiNoi('nguoi', 'Gelsectan uống mấy viên một ngày', true)); await cho(100);
const px = JSON.parse(await trang.evaluate(() => window.phanXuCau('Gelsectan uống mấy viên một ngày')));
kiem(px.loai === 'kho' && px.id === '0.10' && px.doc === cauTheoId['0.10'].doc && px.hien === cauTheoId['0.10'].dap, 'phanXuCau (Kotlin gọi): câu liều dùng → kho 0.10, trả đúng nguyên văn hai bản');
await trang.evaluate(x => window.hienTraLoi(x.hien, '[]', false), px); await cho(200);
await soi('12-ai-tra-loi-nguyen-van');
kiem(await trang.evaluate(() => document.querySelector('#ai-cau').textContent) === cauTheoId['0.10'].dap, 'màn AI hiện nguyên văn câu trả lời');
await trang.evaluate(x => window.hienTraLoi(x, '[]', false), cauTheoId['0.22'].dap); await cho(200);
await soi('13-ai-tra-loi-dai-nhat');
const gy = JSON.parse(await trang.evaluate(() => window.phanXuCau('sử dụng dài hạn có được không')));
await trang.evaluate(x => window.hienTraLoi(x.hien, JSON.stringify(x.goiY), x.nutForm), gy); await cho(200);
await soi('14-ai-chua-chac-goi-y');
kiem(await trang.evaluate(() => document.querySelectorAll('#goi-y-chat button.xem').length) === gy.goiY.length && gy.goiY.length >= 2, 'câu chưa chắc → hiện các câu gợi ý để chạm', JSON.stringify(gy.goiY));
await xoaLenh();
await trang.click('#goi-y-chat button.xem'); await cho(600);
d = await lenh('doc');
kiem(d.length === 1 && d[0][1] === cauTheoId[gy.goiY[0]].doc, 'chạm câu gợi ý → đọc nguyên văn đúng câu đó');
const ng = JSON.parse(await trang.evaluate(() => window.phanXuCau('Gelsectan giá bao nhiêu')));
await trang.evaluate(x => window.hienTraLoi(x.hien, '[]', x.nutForm), ng); await cho(200);
await soi('15-ai-hoi-gia');
kiem(ng.loai === 'chan' && await trang.evaluate(() => document.querySelectorAll('#goi-y-chat button.form').length) === 1, 'hỏi giá → câu cố định + nút để lại thông tin');
await trang.evaluate(() => window.moFormTuAI()); await cho(300);
kiem(await hienPhu('#phu-form'), 'khách nói muốn để lại thông tin → bảng điền mở');
await trang.evaluate(() => boQuaForm()); await cho(200);
kiem(await man() === 'mh-chat', 'bỏ qua bảng mở từ AI → ở lại màn AI');
await trang.evaluate(() => { window.baoCheDoAI('du-phong', false); moChat(); }); await cho(600);
await soi('16-ai-may-khong-co-mic');
await xoaLenh();
await trang.evaluate(() => ve('mh-chinh')); await cho(100);
kiem((await lenh('tatMic')).length >= 1 && (await lenh('xoaNguCanh')).length === 1, 'rời màn AI: tắt mic + xoá ngữ cảnh của khách vừa rồi');

/* ═══ F — du hành ═══ */
console.log('\nF. Du hành');
/* Rút ngắn đồng hồ cho bộ thử: vắng 4 giây là về, nghỉ 0,3 giây giữa hai câu, coi như câu nào cũng đọc xong tức thì. */
await trang.evaluate(() => { D.cho_ve_giay = 4; D.du_hanh.nghi_giay = 0.3; D.le_tan.nghi_giay = 0.3; TOC_DO_DOC = 100000; });
await trang.evaluate(() => hoiDuHanh()); await cho(200);
await soi('17-hoi-du-hanh');
kiem(await hienPhu('#phu-hoi') && (await lenh('diToiDiem')).length === 0, 'bấm Du hành → hỏi xác nhận trước, robot CHƯA đi');
await xoaLenh();
await trang.click('#hoi-nut .nut-lon.luc'); await cho(900);
let di = await lenh('diToiDiem');
kiem(await man() === 'mh-cho' && di.length === 1 && di[0][1] === 'Diem 1', 'xác nhận → màn biểu cảm + đi tới Diem 1', JSON.stringify(di));
kiem((await lenh('tatDoiDien')).some(x => x[1] === false), 'thôi xoay theo người trước khi đi (không xoay về hướng cũ)');
await soi('18-du-hanh-dang-di');
for (let i = 0; i < 5; i++) { await trang.evaluate(() => window.baoDanDuong('toi-noi', '')); await cho(750); }
di = (await lenh('diToiDiem')).map(x => x[1]);
kiem(di.join(',') === 'Diem 1,Diem 2,Diem 3,Diem 4,Diem 5,Diem 1', 'tới điểm là đi tiếp ngay, hết Diem 5 quay lại Diem 1', di.join(','));
await cho(2600);
d = (await lenh('doc')).map(x => x[1]);
const cauDH = D.du_hanh.cau.map(x => x.doc);
kiem(d.filter(x => cauDH.includes(x)).length >= 2, 'vừa đi vừa giới thiệu (≥ 2 câu, xoay vòng)', d.length + ' câu');
await xoaLenh();
await trang.click('#mh-cho'); await cho(700);
kiem(await man() === 'mh-chinh' && (await lenh('dungDi')).length === 1, 'chạm màn hình lúc đang đi → robot DỪNG + ra màn chính');
kiem((await lenh('batDoiDien')).length === 1, '… và bật xoay theo người');
kiem(await trang.evaluate(() => !document.querySelector('#nhan-dh').hidden), 'ô Du hành ghi "Đang bật"');
await soi('19-man-chinh-dang-du-hanh');
const n0 = (await lenh('doc')).filter(x => cauDH.includes(x[1])).length;
await cho(1500);
kiem((await lenh('doc')).filter(x => cauDH.includes(x[1])).length === n0, 'khách đang thao tác: robot KHÔNG nói câu du hành nào nữa');
await xoaLenh();
kiem(await man() === 'mh-chinh', '… và chưa hết giờ chờ thì vẫn ở màn chính');
await xoaLenh();
await cho(4300);                                         // vắng thao tác quá 4 giây
di = await lenh('diToiDiem');
kiem(await man() === 'mh-cho' && di.length >= 1, 'vắng thao tác → tự về màn biểu cảm và ĐI TIẾP', 'màn ' + await man() + ' · ' + di.length + ' lệnh đi');
await trang.evaluate(() => window.baoDanDuong('loi', 'Chưa có điểm này trên bản đồ.')); await cho(300);
kiem(/thử điểm kế/.test(await trang.evaluate(() => document.querySelector('#cho-tt').textContent)), 'một điểm không đi được → báo trên màn, sẽ thử điểm kế (không bỏ cả vòng)');
await trang.click('#mh-cho'); await cho(300);
await trang.evaluate(() => hoiDuHanh()); await cho(200);
await soi('20-hoi-tat-du-hanh');
await trang.click('#hoi-nut .nut-lon'); await cho(200);  // "Tắt du hành"
kiem(await trang.evaluate(() => nen) === 'cho' && await trang.evaluate(() => document.querySelector('#nhan-dh').hidden), 'tắt được chế độ du hành từ màn chính');

/* ═══ G — lễ tân ═══ */
console.log('\nG. Lễ tân');
await xoaLenh();
await trang.evaluate(() => hoiLeTan()); await cho(200);
await trang.click('#hoi-nut .nut-lon.luc'); await cho(900);
di = await lenh('diToiDiem');
kiem(di.length === 1 && di[0][1] === D.le_tan.diem && await man() === 'mh-cho', 'xác nhận → đi về điểm "Le tan"', JSON.stringify(di));
const cauLT = D.le_tan.cau.map(x => x.doc);
await cho(1200);
kiem((await lenh('doc')).filter(x => cauLT.includes(x[1])).length === 0, 'đang trên đường về điểm lễ tân: chưa mời');
await trang.evaluate(() => window.baoDanDuong('toi-noi', '')); await cho(4200);
d = (await lenh('doc')).filter(x => cauLT.includes(x[1]));
kiem(d.length >= 2, 'tới nơi → đều đặn phát câu mời khách (≥ 2 câu)', d.length + ' câu');
await soi('21-le-tan');
await xoaLenh();
await trang.click('#mh-cho'); await cho(500);
kiem(await man() === 'mh-chinh' && !(await trang.evaluate(() => document.querySelector('#nhan-lt').hidden)), 'chạm → màn chính, ô Lễ tân ghi "Đang bật"');
await trang.evaluate(() => { window.GIA.lyDo = 'Chưa kết nối được với hệ thống của robot.'; });
await xoaLenh();
await trang.evaluate(() => veManCho()); await cho(4500);
kiem((await lenh('diToiDiem')).length === 0 && (await lenh('doc')).filter(x => cauLT.includes(x[1])).length >= 1, 'robot chưa tự đi được → vẫn làm lễ tân TẠI CHỖ, không gửi lệnh đi');
await trang.evaluate(() => { window.GIA.lyDo = ''; });

/* ═══ I — nhảy múa (chép app Cao Xanh) ═══ */
console.log('\nI. Nhảy múa');
await trang.evaluate(() => { datNen('cho'); ve('mh-chinh'); }); await cho(200);
await soi('23-man-chinh-5-che-do');
kiem(await trang.evaluate(() => document.querySelectorAll('#mh-chinh .o-che-do').length) === 5, 'màn chính có đủ 5 chế độ');
await xoaLenh();
await trang.evaluate(() => vaoManMua()); await cho(600);
await soi('24-nhay-chuan-bi');
kiem(await man() === 'mh-mua' && (await lenh('batNhay')).length === 0, 'vào màn nhảy: hỏi chuẩn bị, robot CHƯA lắc');
await trang.evaluate(() => batDauNhay()); await cho(2600);
await soi('25-nhay-dang');
kiem((await lenh('batNhay')).length === 1 && (await lenh('dongTac')).length >= 2, 'bấm Bắt đầu: batNhay một lần + động tác theo phách', (await lenh('dongTac')).length + ' động tác');
await cho(5000);
kiem(await man() === 'mh-mua', 'đang nhảy thì KHÔNG bị đồng hồ vắng thao tác kéo về màn chờ');
await xoaLenh();
await trang.click('#lop-mat'); await cho(300);
kiem((await lenh('dungNhay')).length === 1 && !(await trang.evaluate(() => dangNhay)), 'chạm màn hình lúc nhảy → dừng ngay');
await trang.evaluate(() => batDauNhay()); await cho(800); await xoaLenh();
await trang.evaluate(() => ve('mh-chinh')); await cho(300);
kiem((await lenh('dungNhay')).length === 1 && (await lenh('batDoiDien')).length === 1, 'rời màn nhảy giữa chừng → dừng điệu + bật lại xoay theo người');
await trang.evaluate(() => veManCho()); await cho(200);     // mục H bắt đầu từ màn chờ

/* ═══ H — không tự đánh thức mình ═══ */
console.log('\nH. Từ đánh thức');
await trang.evaluate(() => { lucNoiCuoi = Date.now(); window.danhThucBangLoiChao(); }); await cho(150);
kiem(await man() === 'mh-cho', 'robot vừa nói xong mà nghe "xin chào" → bỏ qua (tiếng của chính nó)');
await trang.evaluate(() => { lucNoiCuoi = 0; window.danhThucBangLoiChao(); }); await cho(300);
kiem(await man() === 'mh-chinh', 'khách nói "xin chào" lúc robot im → ra màn chính');
await trang.evaluate(() => { datNen('cho'); moManKyThuat(); }); await cho(300);
await soi('22-man-ky-thuat');

await trinhDuyet.close();
console.log(`\n${dat}/${dat + truot.length} phép thử đạt · ảnh ở ${RA}`);
if (truot.length) { console.log('\nTRƯỢT:'); truot.forEach(t => console.log('  ✗ ' + t)); process.exit(1); }

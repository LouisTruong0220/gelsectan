/**
 * BỘ THỬ BỘ HIỂU CÂU HỎI — app Gelsectan (Chi Bách Pharma · Minibot)
 *
 *   node tools/thu-tim-kiem.mjs            # chạy hết, in câu trượt
 *   node tools/thu-tim-kiem.mjs -v         # in cả điểm của từng câu
 *   node tools/thu-tim-kiem.mjs "câu hỏi"  # thử một câu, in cách app phân xử
 *
 * Khách yêu cầu: "hỏi cùng một vấn đề nhưng diễn đạt khác nhau vẫn phải trả lời đúng", và họ đã
 * gặp giải pháp khác trả lời lệch trọng tâm ngay với câu nằm trong bộ câu hỏi. Bộ thử canh BA thứ:
 *   A. 25 câu hỏi GỐC — phải nhận ra đúng câu đó, mức CHẮC                (nhận sai = lỗi nặng nhất)
 *   B. cách hỏi KHÁC — KHÔNG trùng bảng BIEN_THE trong dung-du-lieu.py, không thì tự chấm bài mình:
 *        · phải ra đúng câu (chắc), HOẶC đúng câu nằm trong gợi ý — tuỳ cột `muc`
 *        · TUYỆT ĐỐI không được "chắc" vào một câu KHÁC
 *   C. câu NGOÀI bộ câu hỏi / câu phải chặn — không được đọc một câu trả lời nào trong kho
 *
 * Bộ thử BÓC NGUYÊN khối mã giữa hai mốc BAT_DAU_BO_TIM / HET_BO_TIM của khung-app.html nên thử
 * đúng bản sẽ chạy trên robot, không phải một bản chép.
 */
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const khung = readFileSync(join(APP, 'khung-app.html'), 'utf8');
const D = JSON.parse(readFileSync(join(APP, 'du-lieu', 'app-data.json'), 'utf8'));
const a = khung.indexOf('/*__BAT_DAU_BO_TIM__*/'), b = khung.indexOf('/*__HET_BO_TIM__*/');
if (a < 0 || b < 0) { console.error('Không thấy hai mốc bộ tìm trong khung-app.html'); process.exit(2); }
const ma = khung.slice(a, b);
const { phanXu, timCau, suaTenSanPham } = new Function('D', `
  var CAU_HOI = D.cau || [], L = D.loi || {}, THEO_ID = {};
  CAU_HOI.forEach(function(c){ THEO_ID[c.id] = c; });
  function chuDoc(o){ return !o ? '' : (typeof o === 'string' ? o : (o.doc || o.hien || '')); }
  function chuHien(o){ return !o ? '' : (typeof o === 'string' ? o : (o.hien || '')); }
  ${ma}
  return { phanXu: phanXu, timCau: timCau, suaTenSanPham: suaTenSanPham };
`)(D);

const thamSo = process.argv.slice(2);
const chiTiet = thamSo.includes('-v');
const cauThu = thamSo.find(x => !x.startsWith('-'));
if (cauThu) {
  const x = phanXu(cauThu);
  console.log('Câu:     ', cauThu);
  console.log('Phân xử: ', x.loai, x.id || x.khoa, x.goiY.length ? '· gợi ý ' + x.goiY.join(', ') : '');
  console.log('Điểm:    ', JSON.stringify(timCau(cauThu).diem));
  console.log('Robot:   ', x.hien);
  process.exit(0);
}

/* B — cách hỏi khác. muc: 'chac' = phải đọc nguyên văn đúng câu · 'goi-y' = được phép chỉ nằm trong gợi ý */
const B = [
  ['0.1', 'Gelsectan là thuốc à', 'chac'],
  ['0.1', 'cho hỏi Gelsectan là thực phẩm chức năng hay là thuốc vậy', 'chac'],
  ['0.1', 'sản phẩm này là thiết bị y tế hả', 'goi-y'],
  ['0.2', 'Gelsectan có những thành phần nào', 'chac'],
  ['0.2', 'trong viên Gelsectan chứa chất gì', 'chac'],
  ['0.2', 'thành phần chính là gì vậy em', 'chac'],
  ['0.3', 'Gelsectan được chỉ định khi nào', 'chac'],
  ['0.3', 'công dụng của Gelsectan là gì', 'chac'],
  ['0.3', 'Gelsectan trị bệnh gì', 'chac'],
  ['0.4', 'Gelsectan xuất xứ từ đâu', 'chac'],
  ['0.4', 'nước nào sản xuất Gelsectan vậy', 'chac'],
  ['0.4', 'hãng nào làm ra Gelsectan', 'goi-y'],
  ['0.5', 'một hộp có mấy viên', 'chac'],
  ['0.5', 'Gelsectan đóng gói như thế nào', 'chac'],
  ['0.5', 'dạng bào chế của Gelsectan là gì', 'chac'],
  ['0.6', 'cơ chế hoạt động của Gelsectan là gì', 'chac'],
  ['0.6', 'Gelsectan tác dụng theo cơ chế nào', 'chac'],
  ['0.6', 'em giải thích cơ chế tác dụng đi', 'chac'],
  ['0.7', 'hàng rào niêm mạc ruột nghĩa là gì', 'chac'],
  ['0.7', 'thế nào là tăng tính thấm ruột', 'chac'],
  ['0.8', 'Gelsectan có được hấp thu vào máu không', 'chac'],
  ['0.8', 'sản phẩm có hấp thu toàn thân không em', 'chac'],
  ['0.8', 'uống vào có ngấm vào máu không', 'goi-y'],
  ['0.9', 'Gelsectan với men vi sinh khác nhau chỗ nào', 'chac'],
  ['0.9', 'Gelsectan có giống probiotic không', 'chac'],
  ['0.9', 'sao không dùng men vi sinh mà dùng Gelsectan', 'goi-y'],
  ['0.10', 'liều dùng của Gelsectan là bao nhiêu', 'chac'],
  ['0.10', 'một ngày uống mấy viên', 'chac'],
  ['0.10', 'Gelsectan dùng liều thế nào', 'chac'],
  ['0.11', 'uống trước ăn hay sau ăn', 'chac'],
  ['0.11', 'Gelsectan nên uống lúc nào', 'chac'],
  ['0.11', 'uống Gelsectan lúc bụng đói được không', 'goi-y'],
  ['0.12', 'một đợt điều trị bao lâu', 'chac'],
  ['0.12', 'liệu trình Gelsectan là mấy tuần', 'chac'],
  ['0.12', 'uống trong thời gian bao lâu', 'chac'],
  ['0.13', 'dùng bao lâu thì có hiệu quả', 'chac'],
  ['0.13', 'sau bao lâu bệnh nhân thấy đỡ', 'chac'],
  ['0.13', 'mấy tuần thì thấy tác dụng', 'goi-y'],
  ['0.14', 'hết triệu chứng rồi có phải duy trì không', 'chac'],
  ['0.14', 'khi đã đỡ thì có ngưng được không', 'chac'],
  ['0.14', 'ngưng uống có bị tái phát không', 'chac'],
  ['0.15', 'Gelsectan dùng cho trẻ em được không', 'chac'],
  ['0.15', 'trẻ nhỏ có uống được Gelsectan không', 'chac'],
  ['0.15', 'bệnh nhi dùng được không em', 'chac'],
  ['0.16', 'phụ nữ có thai dùng được không', 'chac'],
  ['0.16', 'mẹ đang cho con bú uống Gelsectan được không', 'chac'],
  ['0.16', 'bà bầu có uống được không', 'chac'],
  ['0.17', 'Gelsectan có tương tác với thuốc nào không', 'chac'],
  ['0.17', 'dùng chung với các thuốc khác có được không', 'chac'],
  ['0.17', 'có tương tác thuốc gì không em', 'chac'],
  ['0.18', 'bảo quản Gelsectan ra sao', 'chac'],
  ['0.18', 'Gelsectan cần bảo quản ở điều kiện nào', 'chac'],
  ['0.18', 'hạn dùng của sản phẩm là bao lâu', 'goi-y'],
  ['0.19', 'Gelsectan có tác dụng phụ không', 'chac'],
  ['0.19', 'tác dụng không mong muốn của Gelsectan là gì', 'chac'],
  ['0.19', 'uống có bị phản ứng phụ gì không', 'chac'],
  ['0.20', 'dùng lâu dài có an toàn không', 'chac'],
  ['0.20', 'uống Gelsectan kéo dài có hại gì không', 'chac'],
  // "sử dụng dài hạn" và "hạn sử dụng" (câu 0.18) trùng cả ba âm tiết — bộ tìm cố ý không dám chắc, đưa hai gợi ý.
  ['0.20', 'sử dụng dài hạn có được không', 'goi-y'],
  ['0.21', 'Gelsectan có làm táo bón không', 'chac'],
  ['0.21', 'uống vào có bị táo bón không em', 'chac'],
  ['0.21', 'có bị chuyển pha sang táo bón không', 'chac'],
  ['0.22', 'Gelsectan có nghiên cứu nào chứng minh không', 'chac'],
  ['0.22', 'có bằng chứng lâm sàng không', 'chac'],
  ['0.22', 'thử nghiệm lâm sàng của Gelsectan thế nào', 'chac'],
  ['0.23', 'vì sao chọn Gelsectan thay cho loperamide', 'chac'],
  ['0.23', 'Gelsectan so với loperamide thì thế nào', 'chac'],
  ['0.23', 'Gelsectan hơn gì loperamide', 'chac'],
  ['0.24', 'Gelsectan dùng cho hội chứng ruột kích thích thể tiêu chảy đúng không', 'chac'],
  ['0.24', 'ruột kích thích sau nhiễm trùng có dùng được không', 'chac'],
  ['0.25', 'Gelsectan đã có ở Việt Nam chưa', 'chac'],
  ['0.25', 'Gelsectan có mặt tại Việt Nam chưa em', 'chac'],
  ['0.25', 'các bệnh viện đã có Gelsectan chưa', 'chac'],
];

/* C — không được đọc câu trả lời nào trong kho. loai = phân xử mong đợi ('' = miễn không phải 'kho') */
const C = [
  ['hôm nay thời tiết thế nào', ''],
  ['em đang làm gì', ''],
  ['bạn làm gì ở đây', ''],
  ['robot này giá bao nhiêu', 'chan'],
  ['Gelsectan giá bao nhiêu một hộp', 'chan'],
  ['mua Gelsectan ở đâu', 'chan'],
  ['bảo hiểm y tế có chi trả không', 'chan'],
  ['Gelsectan có chữa khỏi hội chứng ruột kích thích không', 'chan'],
  ['uống bao lâu thì khỏi hẳn', 'chan'],
  ['tôi bị tiêu chảy ba ngày rồi uống được không', 'chan'],
  ['mẹ tôi đang uống thuốc huyết áp có dùng được không', 'chan'],
  ['con tôi 5 tuổi uống mấy viên', 'chan'],
  ['em kê đơn giúp anh với', 'chan'],
  ['có người ngất xỉu ở đây', 'chan'],
  ['em nghĩ gì về bầu cử tổng thống', 'chan'],
  ['xin chào', 'xa-giao'],
  ['em tên là gì', 'xa-giao'],
  ['cảm ơn em nhé', 'xa-giao'],
  ['tôi muốn để lại thông tin', 'form'],
  ['anh muốn được tư vấn thêm', 'form'],
  ['Gelsectan có dùng được cho bệnh nhân viêm loét đại tràng không', ''],
  ['Gelsectan có điều trị táo bón không', ''],
  ['Chi Bách Pharma có bao nhiêu nhân viên', ''],
  ['liều dùng của loperamide là bao nhiêu', ''],
  ['smecta khác gì men vi sinh', ''],
  ['nhà vệ sinh ở đâu', ''],
  ['kể chuyện cười đi', ''],
  ['Gelsectan có gây ung thư không', ''],
  ['bệnh nhân suy thận có dùng được không', ''],
  ['người cao tuổi dùng liều thế nào', ''],
];

let dat = 0, truot = [];
function ghi(ok, nhom, cau, mong, ra) {
  if (ok) dat++; else truot.push(`[${nhom}] "${cau}"\n      mong: ${mong}\n      ra:   ${ra}`);
  if (chiTiet) console.log((ok ? '  ✓ ' : '  ✗ ') + `[${nhom}] ${cau} → ${ra}`);
}
function moTa(x, cau) {
  return `${x.loai} ${x.id || x.khoa}${x.goiY.length ? ' · gợi ý ' + x.goiY.join(',') : ''} · điểm ${JSON.stringify(timCau(cau).diem)}`;
}

// A — câu gốc
for (const c of D.cau) {
  const x = phanXu(c.hoi);
  ghi(x.loai === 'kho' && x.id === c.id, 'A gốc', c.hoi, 'kho ' + c.id, moTa(x, c.hoi));
}
// A2 — mọi cách hỏi trong BIEN_THE cũng phải về đúng câu của nó (chắc), không được chắc sang câu khác
for (const c of D.cau) for (const p of c.bien_the) {
  const x = phanXu(p);
  const ok = (x.loai === 'kho' && x.id === c.id) || (x.loai === 'goi-y' && x.goiY.includes(c.id));
  ghi(ok, 'A2 biến thể', p, 'kho ' + c.id + ' (hoặc gợi ý có nó)', moTa(x, p));
}
// B — cách hỏi khác
let bChac = 0, bGoiY = 0;
for (const [id, cau, muc] of B) {
  const x = phanXu(cau);
  const dungChac = x.loai === 'kho' && x.id === id;
  const trongGoiY = x.loai === 'goi-y' && x.goiY.includes(id);
  if (dungChac) bChac++; else if (trongGoiY) bGoiY++;
  ghi(muc === 'chac' ? dungChac : (dungChac || trongGoiY), 'B khác lời', cau,
      (muc === 'chac' ? 'kho ' : 'kho hoặc gợi ý có ') + id, moTa(x, cau));
}
// C — ngoài kho / phải chặn
for (const [cau, loai] of C) {
  const x = phanXu(cau);
  ghi(x.loai !== 'kho' && (!loai || x.loai === loai), 'C ngoài kho', cau, loai || 'không phải kho', moTa(x, cau));
}
// E — SỬA TÊN "Gelsectan" sau nhận giọng nói: phải sửa đúng các cách nghe lệch…
const SUA = [
  ['gen séc tan là thuốc hay thực phẩm chức năng', 'Gelsectan là thuốc hay thực phẩm chức năng'],
  ['Giơ séc tan có tác dụng phụ không', 'Gelsectan có tác dụng phụ không'],
  ['ghen sếch tăng uống mấy viên', 'Gelsectan uống mấy viên'],
  ['dên xéc tan sản xuất ở đâu', 'Gelsectan sản xuất ở đâu'],
  ['en séc tan dùng cho trẻ em được không', 'Gelsectan dùng cho trẻ em được không'],
  ['jen sét tân có gây táo bón không', 'Gelsectan có gây táo bón không'],
  ['séc tan có hấp thu vào máu không', 'Gelsectan có hấp thu vào máu không'],
  ['Gensectan bảo quản thế nào?', 'Gelsectan bảo quản thế nào?'],
  ['gen sectan khác gì men vi sinh', 'Gelsectan khác gì men vi sinh'],
  ['cho hỏi gel séc tan.', 'cho hỏi Gelsectan.'],
  ['Gelsectan là gì', 'Gelsectan là gì'],
  // nguyên văn NHẬT KÝ ROBOT 01/10/2026 — Google ASR nghe ra chữ tiếng Anh
  ['gentle là gì', 'Gelsectan là gì'],
  ['Translate đang làm gì', 'Gelsectan đang làm gì'],
  ['gen Z là gì', 'Gelsectan là gì'],
  ['sex tư hoạt động như thế nào', 'Gelsectan hoạt động như thế nào'],
  ['your second time tư chứng minh không', 'Gelsectan chứng minh không'],
  ['danh sách an có tác dụng phụ không', 'Gelsectan có tác dụng phụ không'],
  ['cho em hỏi gentle uống mấy viên', 'cho em hỏi Gelsectan uống mấy viên'],
  // nguyên văn nhật ký robot lần 2 (12:08–12:10, 01/10/2026) — mỗi lần một kiểu
  ['giá xe tư là gì', 'Gelsectan là gì'],
  ['danh sách là gì', 'Gelsectan là gì'],
  ['danh sách ta là gì', 'Gelsectan là gì'],
  ['dàn xe tăng có tác dụng phụ gì', 'Gelsectan có tác dụng phụ gì'],
  ['Xem xe tăng khác gì so với men vi sinh', 'Gelsectan khác gì so với men vi sinh'],
  ['ren sex teen có tác dụng gì', 'Gelsectan có tác dụng gì'],
  ['truyện sex thanh là gì', 'Gelsectan là gì'],
  ['settle là gì', 'Gelsectan là gì'],
  // cách nghe CHƯA gặp — phải bắt được nhờ luật cụm lạ đầu câu, không nhờ bảng
  ['sát tăng uống mấy viên một ngày', 'Gelsectan uống mấy viên một ngày'],
  ['em ơi xe tan có dùng cho trẻ em không', 'em ơi Gelsectan có dùng cho trẻ em không'],
];
// …và TUYỆT ĐỐI không đụng vào câu tiếng Việt bình thường.
const GIU = ['xét tăng lương cho nhân viên', 'tôi đã gửi séc cho công ty', 'gen di truyền là gì', 'đường tan chảy',
  'sắc tâm', 'xét tâm lý bệnh nhân', 'robot đến tận nơi', 'liều dùng sáng và tối', 'thuốc này tan trong nước không',
  'sẽ có tác dụng sau tám tuần',
  // bí danh "chỉ đầu câu" không được ăn vào giữa câu
  'cho tôi xem danh sách an toàn', 'thế hệ gen Z thích gì',
  // luật cụm lạ đầu câu KHÔNG được ăn vào mấy câu này
  'giá bao nhiêu một hộp', 'smecta khác gì men vi sinh', 'xin chào bạn', 'tôi bị tiêu chảy có uống được không',
  'nhà vệ sinh ở đâu', 'robot này giá bao nhiêu', 'sẽ có tác dụng sau mấy tuần', 'xét tăng lương được không',
  'thời tiết hôm nay thế nào'];
for (const [vao, mong] of SUA) { const r = suaTenSanPham(vao); ghi(r === mong, 'E sửa tên', vao, mong, r); }
for (const vao of GIU) { const r = suaTenSanPham(vao); ghi(r === vao, 'E giữ nguyên', vao, vao, r); }
// Đi trọn đường: nghe lệch tên mà vẫn ra đúng câu, đọc nguyên văn
for (const [id, cau] of [['0.11', 'giơ séc tan uống trước hay sau ăn'], ['0.19', 'gen sếch tăng có tác dụng phụ gì không'],
                         ['0.4', 'dên xéc tan do nước nào sản xuất'], ['0.15', 'séc tan dùng cho trẻ em được không'],
                         ['0.1', 'gentle là gì'], ['0.6', 'sex tư hoạt động như thế nào'], ['0.19', 'danh sách an có tác dụng phụ không'],
                         ['0.3', 'Translate đang làm gì'], ['0.19', 'có tác dụng phát sinh nào không'],
                         ['0.1', 'giá xe tư là gì'], ['0.9', 'Xem xe tăng khác gì so với men vi sinh'],
                         ['0.19', 'dàn xe tăng có tác dụng phụ gì'], ['0.1', 'settle là gì']]) {
  const x = phanXu(cau); ghi(x.loai === 'kho' && x.id === id, 'E trọn đường', cau, 'kho ' + id, moTa(x, cau));
}

// D — biến thể trong dữ liệu không được trùng câu của bộ thử B (không thì bộ thử tự chấm bài mình)
const tapBienThe = new Set(D.cau.flatMap(c => c.bien_the.map(p => p.toLowerCase())));
for (const [, cau] of B) ghi(!tapBienThe.has(cau.toLowerCase()), 'D không chép', cau, 'khác BIEN_THE', 'trùng BIEN_THE');

const tong = dat + truot.length;
console.log(`\n${dat}/${tong} phép thử đạt · B: ${bChac} câu đọc nguyên văn, ${bGoiY} câu ra gợi ý, trên ${B.length}`);
if (truot.length) { console.log('\nTRƯỢT:'); truot.forEach(t => console.log('  ✗ ' + t)); process.exit(1); }

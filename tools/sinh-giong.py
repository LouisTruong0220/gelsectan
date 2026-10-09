# -*- coding: utf-8 -*-
"""SINH GIỌNG ROBOT bằng ElevenLabs — mọi câu robot đọc → giong/mp3/<sha1 của câu>.mp3

    python tools/sinh-giong.py --nghe        # liệt kê câu cần sinh + số ký tự, KHÔNG gọi API
    python tools/sinh-giong.py               # sinh câu mới / câu đã sửa lời (chạy lại là làm tiếp)
    python tools/sinh-giong.py --giong <id>  # đổi giọng (ghi vào giong/giong-chon.json, sinh lại hết)

Robot (Giong.kt) băm SHA-1 đúng chuỗi lớp web gửi xuống rồi tìm <sha1>.mp3: thẻ nhớ trước, APK sau.
Thiếu file → rơi về giọng máy và ghi tên câu vào files/thieu-giong.txt trên robot.
⚠ Câu phải KHỚP TỪNG KÝ TỰ với chuỗi app gửi — nên script lấy câu từ CHÍNH app-data.json
  (trường `doc`) + câu dự phòng bóc thẳng từ TraLoi.kt. Sửa lời ở dung-du-lieu.py → chạy lại
  dung-du-lieu.py → script này → dung-app.py.
⚠ eleven_v3 trên tài khoản công ty tính nửa credit mỗi ký tự; tài khoản dùng chung cả phòng.
"""
import argparse, hashlib, io, json, os, re, sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__)); APP = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(APP))
sys.path.insert(0, os.path.join(ROOT, "tools", "elevenlabs"))
import rbw_voice as rv  # noqa

RA = os.path.join(APP, "giong", "mp3")
FILE_GIONG = os.path.join(APP, "giong", "giong-chon.json")
VAN_TAY = os.path.join(RA, "_da-sinh.json")


def sha1(t):
    return hashlib.sha1(t.encode("utf-8")).hexdigest()


def moi_cau():
    """Mọi chuỗi robot có thể đọc — {chuỗi: nhãn}."""
    d = json.load(io.open(os.path.join(APP, "du-lieu", "app-data.json"), encoding="utf-8"))
    cau = {}
    for c in d["cau"]:
        cau[c["doc"]] = "cau-" + c["id"]
    for k, v in d["loi"].items():
        cau.setdefault(v["doc"], "loi-" + k)
    for i, v in enumerate(d["du_hanh"]["cau"]):
        cau.setdefault(v["doc"], "du-hanh-%d" % (i + 1))
    for i, v in enumerate(d["le_tan"]["cau"]):
        cau.setdefault(v["doc"], "le-tan-%d" % (i + 1))
    cau.setdefault(d["ten_doc"], "ten-san-pham")
    kt = io.open(os.path.join(APP, "android", "app", "src", "main", "java", "vn", "roboworld", "chibach", "TraLoi.kt"),
                 encoding="utf-8").read()
    m = re.search(r"const val CHUA_CO_CUNG =\s*((?:\"[^\"]*\"\s*\+?\s*)+)", kt)
    if m:
        cau.setdefault("".join(re.findall(r"\"([^\"]*)\"", m.group(1))), "kotlin-chua-co")
    return cau


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nghe", action="store_true"); ap.add_argument("--giong"); ap.add_argument("--lam-lai", action="store_true")
    a = ap.parse_args()
    g = json.load(io.open(FILE_GIONG, encoding="utf-8"))
    if a.giong and a.giong != g["voice_id"]:
        g["voice_id"] = a.giong; g["ten"] = "(đổi bằng --giong)"
        io.open(FILE_GIONG, "w", encoding="utf-8").write(json.dumps(g, ensure_ascii=False, indent=1))
        print("  ⚠ ĐỔI GIỌNG → mọi câu sẽ sinh lại")
    voice, toc = g["voice_id"], float(g.get("toc_do", 1.0))
    cu = json.load(io.open(VAN_TAY, encoding="utf-8")) if os.path.isfile(VAN_TAY) else {}
    os.makedirs(RA, exist_ok=True)
    tat_ca = moi_cau()
    can = []
    for t, nhan in tat_ca.items():
        h = sha1(t); f = os.path.join(RA, h + ".mp3")
        vt = sha1("%s|%s|%s" % (voice, toc, t))[:16]
        if not a.lam_lai and os.path.isfile(f) and cu.get(h) == vt:
            continue
        can.append((t, nhan, h, vt))
    tong = sum(len(t) for t, *_ in can)
    print("  Giọng: %s (%s) · eleven_v3 · ổn định %.1f · tốc độ x%.2f" % (g["ten"], voice, g.get("on_dinh", 0.5), toc))
    print("  %d câu robot đọc · cần sinh %d câu · %s ký tự (≈ %s credit)" % (len(tat_ca), len(can), format(tong, ","), format(tong // 2, ",")))
    if a.nghe or not can:
        for t, nhan, *_ in can: print("   + %-16s %4d ký tự" % (nhan, len(t)))
        return
    env = rv.load_env()
    for i, (t, nhan, h, vt) in enumerate(can, 1):
        out = os.path.join(RA, h + ".mp3")
        print("  [%d/%d] %-16s" % (i, len(can), nhan), end=" ", flush=True)
        try:
            rv.tts(env, t, out, voice_id=voice, model="eleven_v3", stability=float(g.get("on_dinh", 0.5)), similarity=0.9, speed=toc)
        except SystemExit as e:
            print("\n  DỪNG: %s\n  Chạy lại lệnh này để làm tiếp phần còn thiếu." % e); break
        cu[h] = vt
        io.open(VAN_TAY, "w", encoding="utf-8").write(json.dumps(cu, ensure_ascii=False, indent=1))
        print("%d KB" % (os.path.getsize(out) // 1024))
    # Bảng tra để người soát biết tệp nào là câu nào
    io.open(os.path.join(RA, "_bang-tra.json"), "w", encoding="utf-8").write(
        json.dumps({sha1(t): {"nhan": n, "cau": t} for t, n in tat_ca.items()}, ensure_ascii=False, indent=1))
    thieu = [n for t, n in tat_ca.items() if not os.path.isfile(os.path.join(RA, sha1(t) + ".mp3"))]
    print("  %s" % ("✔ ĐỦ %d/%d câu" % (len(tat_ca), len(tat_ca)) if not thieu else "⚠ CÒN THIẾU %d câu: %s" % (len(thieu), ", ".join(thieu))))


if __name__ == "__main__":
    main()

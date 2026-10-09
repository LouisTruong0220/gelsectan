# -*- coding: utf-8 -*-
"""Làm việc với robot Minibot qua adb — app Gelsectan (Chi Bách Pharma).

    python tools/day-web.py                      # đẩy GIAO DIỆN + DỮ LIỆU mới (không cần build lại APK)
    python tools/day-web.py --xem                # chỉ xem trên robot đang có gì
    python tools/day-web.py --cai                # cài APK mới nhất trong apk/ rồi đẩy giao diện
    python tools/day-web.py --sheet <URL> --ma <mã>   # nạp địa chỉ Google Sheets của khách
    python tools/day-web.py --lay-ve             # kéo sổ khách + nhật ký câu hỏi về máy tính
    python tools/day-web.py --ip 192.168.1.50 …  # nối qua Wi-Fi thay vì cáp USB (cáp cắm ở ĐẦU robot)

App đọc THẺ NHỚ TRƯỚC, APK sau (MainActivity.docUuTien) — HAI THƯ MỤC KHÁC NHAU:
    khung   ← files/web/khung-app.html
    dữ liệu ← files/du-lieu/app-data.json
Đẩy cả hai vào cùng một thư mục thì SHA-1 vẫn khớp, script vẫn báo XONG, mà robot vẫn chạy dữ
liệu cũ. Nên sau khi đẩy: mở màn kỹ thuật, dòng "Khung giao diện · dữ liệu" phải ghi THẺ NHỚ.

PHẢI ĐẾM HAI BÊN — đẩy xong so SHA-1 từng tệp.
Script CỐ Ý không mở app hộ: mở bằng adb là hãng chặn (mất giọng nói, mất quyền đi lại).
Mở BẰNG TAY từ màn hình chính RobotOS.
"""
import argparse, hashlib, io, json, os, subprocess, sys, datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.dirname(HERE)
ASSETS = os.path.join(APP, "android", "app", "src", "main", "assets")

GOI = "vn.roboworld.chibach"
GOC_RB = "/sdcard/Android/data/%s/files" % GOI
TEP = [
    ("khung-app.html", "web/khung-app.html"),
    ("app-data.json", "du-lieu/app-data.json"),
]
# adb 1.0.41 của Android SDK. Bản C:\Windows\adb.exe là 1.0.39 của PUDU — lệch phiên bản, hai bên giết nhau.
# SDK đã dời sang ổ D (10/2026) — thử chỗ mới trước, rồi chỗ mặc định cũ.
ADB = next((d for d in (r"D:\Android\Sdk\platform-tools\adb.exe",
                        os.path.expandvars(r"%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"))
            if os.path.isfile(d)), r"D:\Android\Sdk\platform-tools\adb.exe")


def adb(*args):
    r = subprocess.run([ADB] + list(args), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace").strip(), r.stderr.decode("utf-8", "replace").strip()


def sha1_may(duong):
    h = hashlib.sha1()
    with open(duong, "rb") as f:
        for k in iter(lambda: f.read(65536), b""):
            h.update(k)
    return h.hexdigest()


def sha1_robot(duong):
    ma, ra, _ = adb("shell", "sha1sum", duong)
    if ma != 0 or not ra or "No such file" in ra:
        return None
    return ra.split()[0]


def day(nguon, dich):
    """Đẩy một tệp và SO SHA-1 hai bên. Trả True nếu tới nơi nguyên vẹn."""
    adb("shell", "mkdir", "-p", dich.rsplit("/", 1)[0])
    ma, ra, lo = adb("push", nguon, dich)
    if ma != 0:
        print("   ✗ %-20s đẩy hỏng: %s" % (os.path.basename(nguon), (lo or ra)[:70]))
        return False
    bm, br = sha1_may(nguon), sha1_robot(dich)
    if bm != br:
        print("   ✗ %-20s SHA-1 LỆCH — máy %s… robot %s…" % (os.path.basename(nguon), bm[:12], (br or "trống")[:12]))
        return False
    print("   ✓ %-20s %8d byte  %s…" % (os.path.basename(nguon), os.path.getsize(nguon), bm[:12]))
    return True


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ip", help="nối qua Wi-Fi thay vì cáp USB")
    p.add_argument("--xem", action="store_true", help="chỉ xem, không đẩy")
    p.add_argument("--cai", action="store_true", help="cài APK mới nhất trong apk/ trước khi đẩy giao diện")
    p.add_argument("--sheet", help="địa chỉ ứng dụng web Apps Script của khách (kết thúc bằng /exec)")
    p.add_argument("--ma", default="", help="mã bí mật khách đặt trong Apps Script")
    p.add_argument("--lay-ve", action="store_true", help="kéo sổ khách + nhật ký câu hỏi về máy tính")
    a = p.parse_args()

    if not os.path.isfile(ADB):
        print("✗ Không thấy adb ở %s (cần adb 1.0.41 của Android SDK)" % ADB)
        return 2
    ma, ra, _ = adb("version")
    print("① adb: %s" % (ra.splitlines()[0] if ra else "?"))
    if a.ip:
        ma, ra, lo = adb("connect", "%s:5555" % a.ip)
        print("   %s" % (ra or lo))
    ma, ra, _ = adb("devices")
    may = [d.split("\t")[0] for d in ra.splitlines()[1:] if d.strip() and d.endswith("device")]
    if not may:
        print("\n✗ Không thấy robot nào.")
        print("  · Cáp USB cắm ở ĐẦU robot (không phải thân máy)")
        print("  · Robot phải bật 'Gỡ lỗi lâu dài' RỒI KHỞI ĐỘNG LẠI thì adb mới thấy")
        print("  · Hoặc nối Wi-Fi: python tools/day-web.py --ip <IP robot>")
        return 1
    if len(may) > 1:
        print("\n✗ Thấy %d máy: %s — rút bớt, script không đoán máy nào" % (len(may), may))
        return 1
    print("② Robot: %s" % may[0])
    ma, ra, _ = adb("shell", "pm", "list", "packages", "com.ainirobot.agentservice")
    print("   AgentOS: %s" % ("CÓ — Giao tiếp AI dùng AgentOS + Portal" if "agentservice" in ra
                              else "KHÔNG CÓ — câu trong bộ câu hỏi vẫn đọc nguyên văn, câu ngoài bộ robot nói 'em chưa có'"))

    # ── Kéo sổ khách + nhật ký về ──
    if a.lay_ve:
        dich = os.path.join(APP, "du-lieu", "tu-robot", datetime.datetime.now().strftime("%Y-%m-%d-%H%M"))
        os.makedirs(dich, exist_ok=True)
        for thu_muc in ("khach-hang", "nhat-ky"):
            ma, ra, lo = adb("pull", "%s/%s" % (GOC_RB, thu_muc), os.path.join(dich, thu_muc))
            print("   %s %s: %s" % ("✓" if ma == 0 else "·", thu_muc, (ra or lo).splitlines()[-1][:90] if (ra or lo) else ""))
        print("\n✓ Đã kéo về: %s" % dich)
        print("  ⚠ Đây là DỮ LIỆU CÁ NHÂN của khách tham dự — thư mục du-lieu/tu-robot/ đã bị .gitignore, đừng gửi lung tung.")
        return 0

    # ── Nạp địa chỉ Google Sheets ──
    if a.sheet:
        if not a.sheet.startswith("https://script.google.com/") or not a.sheet.rstrip("/").endswith("/exec"):
            print("\n✗ Địa chỉ phải dạng https://script.google.com/macros/s/…/exec (khách sao chép ở bước Triển khai).")
            return 1
        if not a.ma:
            print("\n✗ Thiếu --ma <mã bí mật khách đặt trong Apps Script>.")
            return 1
        tam = os.path.join(os.environ.get("TEMP", APP), "google-sheet.json")
        io.open(tam, "w", encoding="utf-8").write(json.dumps({"url": a.sheet.strip(), "ma": a.ma.strip()}))
        print("\n③ Nạp địa chỉ Google Sheets:")
        ok = day(tam, GOC_RB + "/google-sheet.json")
        os.remove(tam)
        if ok:
            print("\n✓ Đã nạp. App đọc lại tệp này mỗi 30 giây, không cần mở lại app.")
            print("  Kiểm: bấm GIỮ logo Gelsectan ở màn chính 1,2 giây → 'Gửi thử một dòng lên Google Sheets'.")
        return 0 if ok else 1

    print("\n③ Trên robot đang có:")
    for t, duong in TEP:
        dd = "%s/%s" % (GOC_RB, duong)
        bam = sha1_robot(dd)
        print("   · %-20s %s" % (t, "CHƯA CÓ (đang chạy bản trong APK)" if bam is None else bam[:12] + "…"))
    print("   · %-20s %s" % ("google-sheet.json", "CÓ" if sha1_robot(GOC_RB + "/google-sheet.json") else "CHƯA CÓ — khách để lại thông tin chỉ lưu trong máy, chưa lên Sheets"))
    if a.xem:
        return 0

    if a.cai:
        thu_muc = os.path.join(APP, "apk")
        apk = sorted([f for f in os.listdir(thu_muc) if f.endswith(".apk")], key=lambda f: os.path.getmtime(os.path.join(thu_muc, f)))
        if not apk:
            print("\n✗ Không có APK nào trong apk/ — chạy tools/build-apk.ps1 trước")
            return 1
        print("\n④ Cài %s …" % apk[-1])
        ma, ra, lo = adb("install", "-r", "-g", os.path.join(thu_muc, apk[-1]))
        print("   %s" % (ra or lo).splitlines()[-1])
        if ma != 0 or "Success" not in (ra + lo):
            return 1

    print("\n⑤ Đẩy giao diện + dữ liệu:")
    hong = 0
    for t, duong in TEP:
        nguon = os.path.join(ASSETS, t)
        if not os.path.isfile(nguon):
            print("   ✗ %-20s KHÔNG CÓ trên máy tính — chạy dung-app.py trước" % t)
            hong += 1
            continue
        hong += not day(nguon, "%s/%s" % (GOC_RB, duong))
    if hong:
        print("\n✗ %d tệp hỏng — robot đang chạy lẫn bản cũ bản mới, KHÔNG dùng được." % hong)
        return 1

    adb("shell", "am", "force-stop", GOI)
    print("\n✓ XONG, đã đóng app. Còn HAI việc phải làm TẠI MÀN HÌNH ROBOT:")
    print("   ① Mở app BẰNG TAY từ màn hình chính của RobotOS (ĐỪNG mở bằng adb — mất giọng nói và quyền đi lại).")
    print("   ② Chạm màn hình → bấm GIỮ logo Gelsectan 1,2 giây → màn kỹ thuật:")
    print("      dòng 'Khung giao diện · dữ liệu' phải ghi THẺ NHỚ. Ghi APK là bản mới chưa vào.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

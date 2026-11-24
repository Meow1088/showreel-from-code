<div align="center">

# 🎬 code-showreel

**Video 12 giây mà mọi điểm ảnh, mọi nốt nhạc đều là code.**

Không model sinh ảnh, không footage, không nhạc có sẵn: chỉ có `numpy` + `pillow` + `ffmpeg`.

![poster](docs/poster.jpg)

</div>

---

## Có gì trong video

| Thời gian | Cảnh | Kỹ thuật |
|---|---|---|
| 0.0 – 3.5s | **01 Starfield**: bay xuyên 2.600 ngôi sao + tinh vân | chiếu phối cảnh 3D, vệt chuyển động, bloom |
| 3.3 – 6.9s | **02 Crystal**: 2 khối 20 mặt xoay ngược nhau | wireframe 3D, xoay ma trận, glow, tia sáng |
| 6.5 – 12s | **03 Sunrise**: bình minh trên biển + title `C L A U D E` | trời gradient, mặt trời, mây fBm, sóng phối cảnh, lấp lánh |

Overlay HUD: timecode chạy, số cảnh, thanh tiến độ. Nhạc (`music.py`) gồm pad Am → F → C, whoosh lúc chuyển cảnh, tiếng sub-hit khi title hiện, chuông pentatonic, tiếng sóng và reverb, tất cả tổng hợp từ sóng sin và noise.

![contact sheet](docs/contact-sheet.jpg)

## Chạy

```bash
# Linux / VPS / homelab
sudo apt install -y ffmpeg python3-pip
pip install -r requirements.txt
bash run.sh            # -> out/showreel.mp4 + out/contact-sheet.jpg
```

```powershell
# Windows
winget install ffmpeg
pip install -r requirements.txt
.\run.ps1
```

Render khoảng **2,5 phút trên 2 nhân CPU** cho 360 frame 1280×720. Font Inter (OFL) đã kèm sẵn trong `fonts/`, không cần cài.

## Cấu trúc

| File | Vai trò |
|---|---|
| `render.py` | Renderer: 3 cảnh + overlay + compositing, pipe frame thô vào ffmpeg. Chữ sửa ở block `config` đầu file |
| `music.py` | Nhạc nền tổng hợp bằng numpy, ra `out/music.wav` |
| `check.py` | QA gate: đủ stream, khoảng cách keyframe, frame đen, nháy sáng; xuất contact sheet. Exit 1 nếu lỗi |
| `run.sh` / `run.ps1` | Chạy cả pipeline: nhạc → preview → render → check |
| `.claude/skills/code-showreel/` | Skill cho Claude Code, giúp agent dựng video kiểu này theo đúng quy trình |
| `fonts/` | Inter ExtraLight + Medium (hỗ trợ tiếng Việt) và license |

## Lệnh lẻ

```bash
python3 music.py                          # out/music.wav
python3 render.py preview 2 5 10.8        # chỉ render vài frame PNG để duyệt (vài giây)
python3 render.py video out/showreel.mp4  # render đầy đủ
python3 check.py out/showreel.mp4         # PASS/FAIL + contact sheet
```

## Quy trình: duyệt trước, xuất sau

Bài học rút ra khi dựng video bằng AI:

1. **Duyệt 1 khung trước khi xuất.** `render.py preview` ra PNG trong vài giây. Đừng xuất cả video chỉ để xem một cảnh, vì có lần mất 4–5 tiếng.
2. **Keyframe mỗi giây** (`-g FPS -keyint_min FPS`). Thiếu keyframe thì render có thể chạy khoảng 10 phút rồi hỏng mà không báo lý do.
3. **Để máy tự kiểm, rồi xem bằng mắt.** `check.py` bắt lỗi kỹ thuật, còn contact sheet là để người xem. Tự kiểm là để đỡ việc, không phải để khỏi xem.
4. **Số nào lên màn hình cũng phải có nguồn.** Trí nhớ của AI có thể đã cũ.
5. **Đưa phong cách cụ thể.** Để AI tự chọn thì nó lấy mặc định (chữ trắng nền gradient tím).

Ba lỗi đã bắt được ở bước duyệt khung khi làm repo này:
- Mặt trời mọc đè lên title → hạ quỹ đạo mặt trời, đẩy title lên.
- Mặt biển ra lưới chấm đều tăm tắp → thay sóng sin bằng texture fBm lấy mẫu theo phối cảnh, kéo dài theo chiều ngang.
- Đường nối giữa texture → mirror-tile texture thành 2048×2048 liền mạch.

## Tùy biến nhanh

- **Đổi chữ:** sửa `TITLE`, `SUBTITLE`, `HUD_BRAND`, `HUD_STACK` đầu `render.py`.
- **Đổi thời lượng hoặc độ phân giải:** sửa `W, H, FPS, DUR`. Nếu đổi `DUR` thì sửa luôn mốc cảnh trong `frame()` và `DUR` trong `music.py`.
- **Đổi hợp âm:** sửa các dòng `pad([...])` trong `music.py` (số MIDI, 60 = C4).
- **Thêm cảnh:** viết hàm `shot_xxx(u, t)` trả mảng `H×W×3` float (0..1+), rồi chèn vào `frame()` với crossfade 0.4s.

## License

MIT — xem [LICENSE](LICENSE).

---
name: code-showreel
description: Dựng video ngắn (intro, showreel, title card) hoàn toàn bằng code với numpy + pillow + ffmpeg, kèm nhạc tổng hợp bằng code, theo quy trình duyệt khung → render → QA gate. Dùng khi được nhờ làm video/intro/animation bằng code, hoặc khi sửa hay mở rộng repo code-showreel.
---

# code-showreel: dựng video bằng code

Repo mẫu: `render.py` (hình), `music.py` (nhạc), `check.py` (QA), `run.sh`/`run.ps1` (cả pipeline).
Đọc `README.md` để biết cấu trúc cảnh và mốc thời gian trước khi sửa.

## Quy trình bắt buộc

1. **Chốt brief:** thời lượng, độ phân giải, chữ trên màn hình, phong cách (màu, font, nhịp). Brief thiếu phong cách thì hỏi hoặc xin video mẫu, không tự chọn mặc định "chữ trắng nền gradient tím". Con số nào lên màn hình cũng phải có nguồn do người dùng đưa.
2. **Viết hoặc sửa cảnh:** mỗi cảnh là một hàm `shot_xxx(u, t) -> np.ndarray (H, W, 3) float`, trong đó `u` là tiến độ cảnh 0..1 và `t` là giây toàn cục. Ghép trong `frame(t)`, crossfade 0.4s. Chữ đặt trong block config đầu file.
3. **Duyệt khung trước khi xuất:** `python render.py preview <giây...>`, chọn ít nhất 1 frame mỗi cảnh, đọc các PNG trong `out/` và tự nhìn. Sửa đến khi ổn. **Không render cả video chỉ để xem một cảnh.**
4. **Nhạc:** `python music.py`. Mốc whoosh và hit phải khớp mốc chuyển cảnh trong `frame()`.
5. **Render:** `python render.py video out/showreel.mp4 out/music.wav`. Giữ `-g FPS -keyint_min FPS` (keyframe mỗi giây).
6. **QA gate:** `python check.py out/showreel.mp4` phải ra PASS. Sau đó mở `out/contact-sheet.jpg` xem bằng mắt, rồi mới báo "xong". Gửi người dùng contact sheet hoặc video để họ tự xem lại.

## Bẫy đã gặp

- Mặt trời hoặc vật thể sáng đè lên title: kiểm frame cuối khi title đã hiện đủ.
- Pattern sin đều tạo lưới giả: dùng texture fBm lấy mẫu theo tọa độ thế giới (phối cảnh), kéo dài theo trục ngang.
- Texture lặp lộ đường nối: mirror-tile (`concat` với bản lật) rồi lấy chỉ số `% size` **sau khi** ép kiểu `int`. Làm `%` trên float có thể ra đúng `size` và gây IndexError ở frame giữa video.
- Nhãn HUD đổi trễ so với cảnh: mốc nhãn phải nằm trong cửa sổ crossfade.
- Mạng bị chặn (sandbox): không tải được model hay font từ HuggingFace hoặc CDN. Repo đã kèm font, đừng thêm phụ thuộc tải lúc chạy.

## Hiệu năng

Khoảng 0,4 giây mỗi frame 720p trên 1 nhân. Muốn 1080p hay video dài thì preview trước ở 720p, render chính thức sau. Chia đoạn chỉ khi thật cần, và mỗi đoạn vẫn phải qua `check.py`.

# code-showreel

Video dựng hoàn toàn bằng code (numpy + pillow + ffmpeg). Quy trình và các bẫy nằm trong skill `.claude/skills/code-showreel/SKILL.md`; đọc trước khi sửa cảnh hoặc nhạc.

- Chạy cả pipeline: `bash run.sh` (Windows: `.\run.ps1`).
- Luôn duyệt bằng `python render.py preview <giây>` trước khi render cả video.
- Chưa có PASS từ `python check.py` và chưa xem contact sheet thì chưa được báo "xong".
- Output ở `out/` (gitignored), không commit video.

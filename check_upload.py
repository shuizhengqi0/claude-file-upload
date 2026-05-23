"""Claude Code UserPromptSubmit hook — auto-inject uploaded files.

Reads ~/.claude/upload.txt for pending file paths, reads each file's content,
and prepends it to the user's prompt. Clears upload.txt after processing.
"""
import json
import os
import sys

# Fix Windows console encoding for emoji and CJK
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UPLOAD_FILE = os.path.join(os.path.expanduser("~"), ".claude", "upload.txt")
MAX_CHARS = 50000


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError, ValueError):
        sys.exit(0)

    prompt = data.get("prompt", "")
    injected = False

    if os.path.exists(UPLOAD_FILE) and os.path.getsize(UPLOAD_FILE) > 0:
        with open(UPLOAD_FILE, "r", encoding="utf-8", errors="replace") as f:
            paths = [line.strip() for line in f if line.strip()]

        # Deduplicate while preserving order
        seen = set()
        paths = [p for p in paths if not (p in seen or seen.add(p))]

        # Clear the upload file
        with open(UPLOAD_FILE, "w", encoding="utf-8") as f:
            pass

        if paths:
            blocks = []
            for path in paths:
                if not os.path.exists(path):
                    blocks.append(f"[文件不存在: {path}]")
                    continue

                fname = os.path.basename(path)
                ext = os.path.splitext(fname)[1].lower() or "—"

                # Skip binary files
                BINARY_EXT = {
                    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
                    ".mp3", ".mp4", ".wav", ".avi", ".mkv", ".mov",
                    ".zip", ".rar", ".7z", ".tar", ".gz",
                    ".exe", ".dll", ".so", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
                    ".pyc", ".pyd", ".whl",
                }
                if ext in BINARY_EXT:
                    size = os.path.getsize(path)
                    blocks.append(
                        f"[二进制文件] {fname} ({size // 1024}KB)\n"
                        f"路径: {path}\n"
                        f"类型: 二进制文件，无法预览文本内容"
                    )
                    continue

                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                except Exception as e:
                    blocks.append(f"[无法读取 {fname}: {e}]")
                    continue

                truncated = False
                if len(content) > MAX_CHARS:
                    content = content[:MAX_CHARS]
                    truncated = True

                header = f"[FILE UPLOAD] {fname} ({path})"
                blocks.append(f"{header}\n```\n{content}\n```" +
                              (f"\n[已截断，原文件 {os.path.getsize(path):,} 字节]" if truncated else ""))

            file_context = "\n\n".join(blocks)
            prefix = file_context

            if prompt.strip():
                prompt = f"{prefix}\n\n---\n用户消息: {prompt}"
            else:
                prompt = f"{prefix}\n\n请分析以上上传的文件内容。"

            injected = True

    data["prompt"] = prompt
    output = json.dumps(data, ensure_ascii=False)

    if injected:
        # Write to stderr for debugging/logging
        try:
            log_path = os.path.join(os.path.expanduser("~"), "upload_debug.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"Hook injected {len(paths)} file(s)\n")
        except Exception:
            pass

    print(output)


if __name__ == "__main__":
    main()

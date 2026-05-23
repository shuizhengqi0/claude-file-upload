"""Claude File Upload — Borderless, drag-drop, ESC to exit."""
import os, math, sys, traceback

LOG = os.path.join(os.path.expanduser("~"), "upload_debug.log")

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

log("=== START ===")

# DPI awareness — must be before tkinter import
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    log("DPI OK")
except Exception as e:
    log(f"DPI fail: {e}")

import tkinter as tk
from tkinter import filedialog
log("tkinter OK")

# Drag-drop support
DND_MODE = "none"
try:
    import windnd
    DND_MODE = "windnd"
    log("windnd imported")
except ImportError as e:
    log(f"windnd fail: {e}")
    try:
        import tkinterdnd2 as dnd
        DND_MODE = "tkdnd"
        log("tkinterdnd2 imported")
    except ImportError as e2:
        log(f"tkinterdnd2 fail: {e2}")

UPLOAD_FILE = os.path.join(os.path.expanduser("~"), ".claude", "upload.txt")

BG       = "#050505"
SURFACE  = "#0A0A0A"
BORDER   = "#161616"
FG       = "#E8E8E8"
FG_DIM   = "#4A4A4A"
FG_MID   = "#7A7A7A"
AMBER    = "#D97706"
AMBER_L  = "#FBBF24"
AMBER_D  = "#92400E"
GREEN    = "#10B981"
RED      = "#DC2626"
MONO     = "Consolas"
SANS     = "Microsoft YaHei"


class GlowDot:
    def __init__(self, parent, size=6):
        self.cv = tk.Canvas(parent, width=size+4, height=size+4,
                            bg=BG, highlightthickness=0)
        self._id = self.cv.create_oval(2, 2, size+2, size+2, fill=AMBER_D, outline="")
        self._phase = 0.0

    def pack(self, **kw):
        self.cv.pack(**kw)
        return self

    def tick(self):
        self._phase = (self._phase + 0.08) % (2 * math.pi)
        b = int(80 + 75 * (0.5 + 0.5 * math.sin(self._phase)))
        self.cv.itemconfig(self._id, fill=f"#{b:02x}{int(b*0.47):02x}02")
        self.cv.after(60, self.tick)


class UploadApp:
    def __init__(self):
        log(f"DND_MODE={DND_MODE}")

        self.root = tk.Tk()
        log("tk.Tk() OK")

        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", False)
        self.root.config(bg=BORDER)

        self.file_content = ""
        self.file_path = ""

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.W = max(360, int(sw * 0.25))
        self.H = max(320, int(sh * 0.28))
        x = (sw - self.W) // 2
        y = (sh - self.H) // 2
        self.root.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self._build()
        self._setup_drop()
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        log("init done")

    def _build(self):
        self._build_titlebar()
        self._build_drop_zone()
        self._build_info()
        self._build_preview()
        self._build_footer()

    def _bind_drag(self, widget):
        widget.bind("<Button-1>", self._start_drag)
        widget.bind("<B1-Motion>", self._on_drag)

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=BG, height=36, cursor="fleur")
        bar.pack(fill="x", padx=1, pady=(1, 0))
        bar.pack_propagate(False)
        self._bind_drag(bar)

        left = tk.Frame(bar, bg=BG)
        left.pack(side="left", padx=12)
        self._bind_drag(left)
        self.glow = GlowDot(left)
        self.glow.pack(side="left", padx=(0, 8))
        self.glow.tick()
        self._bind_drag(self.glow.cv)
        lbl1 = tk.Label(left, text="CLAUDE", font=(MONO, 10, "bold"),
                        bg=BG, fg=AMBER)
        lbl1.pack(side="left")
        self._bind_drag(lbl1)
        lbl2 = tk.Label(left, text="  file://upload", font=(MONO, 9),
                        bg=BG, fg=FG_DIM)
        lbl2.pack(side="left")
        self._bind_drag(lbl2)

        close = tk.Label(bar, text=" × ", font=(MONO, 12),
                         bg=BG, fg=FG_DIM, cursor="hand2")
        close.pack(side="right", padx=8)
        close.bind("<Button-1>", lambda e: self.root.destroy())
        close.bind("<Enter>", lambda e: close.config(fg=RED, bg="#1A0505"))
        close.bind("<Leave>", lambda e: close.config(fg=FG_DIM, bg=BG))

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _on_drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _build_drop_zone(self):
        h = max(120, int(self.H * 0.20))
        outer = tk.Frame(self.root, bg=BORDER)
        outer.pack(fill="x", padx=1, pady=0)
        self.drop_cv = tk.Canvas(outer, bg=BG, highlightthickness=0, height=h)
        self.drop_cv.pack(fill="x", padx=15, pady=(8, 0))
        self._draw_drop(hover=False)
        self.drop_cv.bind("<Button-1>", lambda e: self._pick())

    def _draw_drop(self, hover=False):
        c = self.drop_cv
        c.delete("all")
        c.update_idletasks()
        w = c.winfo_width() or (self.W - 32)
        h = int(c["height"])

        fill = "#080704" if hover else SURFACE
        outline = AMBER if hover else "#1A1A1A"
        self._rr(c, 1, 1, w-1, h-1, 6, fill=fill, outline=outline, width=1)
        if not hover:
            self._rr(c, 6, 6, w-6, h-6, 3, fill="",
                     outline="#181818", width=1, dash=(4, 4))

        cx, cy = w // 2, h // 2
        if hover:
            c.create_text(cx, cy - 12, text="▲", font=(SANS, 16), fill=AMBER)
            c.create_text(cx, cy + 8, text="释放文件", font=(SANS, 10), fill=FG)
        else:
            c.create_text(cx, cy - 16, text="[ ]", font=(MONO, 14, "bold"), fill="#222")
            c.create_text(cx, cy + 4, text="拖入文件 或 点击选择",
                          font=(SANS, 10), fill=FG_MID)
            c.create_text(cx, cy + 20, text="txt · py · json · md · js · ...",
                          font=(MONO, 8), fill=FG_DIM)

    def _build_info(self):
        f = tk.Frame(self.root, bg=BG)
        f.pack(fill="x", padx=18, pady=(6, 0))
        self.lbl_name = tk.Label(f, text="", font=(MONO, 10, "bold"),
                                 bg=BG, fg=FG, anchor="w")
        self.lbl_name.pack(fill="x")
        row2 = tk.Frame(f, bg=BG)
        row2.pack(fill="x", pady=(2, 0))
        self.lbl_meta = tk.Label(row2, text="", font=(MONO, 8),
                                 bg=BG, fg=FG_DIM, anchor="w")
        self.lbl_meta.pack(side="left", fill="x", expand=True)
        self.lbl_size = tk.Label(row2, text="", font=(MONO, 8),
                                 bg=BG, fg=FG_DIM, anchor="e")
        self.lbl_size.pack(side="right")

    def _build_preview(self):
        outer = tk.Frame(self.root, bg=BORDER)
        outer.pack(fill="both", expand=True, padx=1, pady=0)
        inner = tk.Frame(outer, bg=SURFACE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.preview = tk.Text(inner, bg=SURFACE, fg="#B0B0B0", font=(MONO, 9),
                               relief="flat", wrap="char", state="disabled",
                               padx=10, pady=6, spacing1=1, spacing3=1,
                               selectbackground=AMBER_D, selectforeground=FG,
                               insertbackground=FG, cursor="arrow",
                               highlightthickness=0, bd=0)
        self.preview.pack(fill="both", expand=True)
        self.preview.tag_configure("dim", foreground="#2E2E2E")
        self.preview.tag_configure("info", foreground=AMBER_D)

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=BG, height=52)
        footer.pack(fill="x", padx=1, pady=(0, 1))
        footer.pack_propagate(False)
        inner = tk.Frame(footer, bg=BG)
        inner.pack(fill="both", padx=14, pady=8)

        self.lbl_status = tk.Label(inner, text="waiting", font=(MONO, 9),
                                   bg=BG, fg=FG_MID)
        self.lbl_status.pack(side="left", pady=4)

        self.btn_outer = tk.Frame(inner, bg=AMBER_D, cursor="hand2",
                                  highlightbackground=AMBER, highlightthickness=1)
        self.btn_lbl = tk.Label(self.btn_outer, text="  SEND  ",
                                font=(MONO, 11, "bold"), bg=AMBER_D, fg=FG,
                                padx=24, pady=6)
        self.btn_lbl.pack()
        self.btn_outer.pack(side="right")
        for w in (self.btn_outer, self.btn_lbl):
            w.bind("<Button-1>", lambda e: self._send())
            w.bind("<Enter>", lambda e: self._btn_hover(True))
            w.bind("<Leave>", lambda e: self._btn_hover(False))

    def _rr(self, c, x1, y1, x2, y2, r, **kw):
        pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
               x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
               x1,y2, x1,y2-r, x1,y1+r, x1,y1]
        return c.create_polygon(pts, smooth=True, **kw)

    def _setup_drop(self):
        if DND_MODE == "windnd":
            try:
                windnd.hook_dropfiles(self.root, func=self._on_drop)
                log("windnd hooked OK")
            except Exception as e:
                log(f"windnd hook fail: {e}")
        elif DND_MODE == "tkdnd":
            try:
                self.root.drop_target_register(dnd.DND_FILES)
                self.root.dnd_bind("<<Drop>>", self._on_dnd_drop)
                self.root.dnd_bind("<<DragEnter>>", self._on_dnd_enter)
                self.root.dnd_bind("<<DragLeave>>", self._on_dnd_leave)
                log("tkdnd registered OK")
            except Exception as e:
                log(f"tkdnd register fail: {e}")

    def _on_dnd_drop(self, e):
        path = e.data.strip()
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        if path:
            self._load(path)
            self._draw_drop(hover=False)

    def _on_dnd_enter(self, e):
        self._draw_drop(hover=True)

    def _on_dnd_leave(self, e):
        self._draw_drop(hover=False)

    def _on_drop(self, files):
        log(f"DROP event: {files}")
        if not files:
            return
        f = files[0]
        if isinstance(f, bytes):
            f = f.decode("gbk", errors="replace")
        log(f"DROP file: {f}")
        self._load(str(f))

    def _pick(self):
        path = filedialog.askopenfilename(title="选择文件")
        if path:
            self._load(path)

    def _load(self, path):
        try:
            fname = os.path.basename(path)
            ext = os.path.splitext(fname)[1].lower() or "—"
            size = os.path.getsize(path)

            if size > 10_000_000:
                self._set_error(fname, f"{size // 1024 // 1024}MB — 超过10MB限制")
                return

            BINARY_EXT = {".png",".jpg",".jpeg",".gif",".bmp",".ico",".webp",
                          ".mp3",".mp4",".wav",".avi",".mkv",".mov",
                          ".zip",".rar",".7z",".tar",".gz",
                          ".exe",".dll",".so",".pdf",".doc",".docx",".xls",".xlsx"}

            if ext in BINARY_EXT:
                self.file_path = path
                self.file_content = f"文件: {fname}\n路径: {path}\n类型: 二进制文件\n{'─' * 40}\n[二进制内容，无法预览]"
                self._draw_drop_loaded(fname, 0, size, ext)
                self.lbl_name.config(text=fname, fg=FG)
                self.lbl_meta.config(text=path, fg=FG_DIM)
                self.lbl_size.config(text=f"{size // 1024}KB  {ext}  binary", fg=FG_MID)
                self.preview.config(state="normal")
                self.preview.delete("1.0", "end")
                self.preview.insert("end", f"  {'─' * 40}\n", "dim")
                self.preview.insert("end", f"  FILE  {fname}\n", "info")
                self.preview.insert("end", f"  TYPE  {ext}  ·  {size // 1024}KB  ·  binary\n", "dim")
                self.preview.insert("end", f"\n  二进制文件，无法预览文本内容\n", "dim")
                self.preview.insert("end", f"  路径: {path}\n", "dim")
                self.preview.insert("end", f"\n  {'─' * 40}\n", "dim")
                self.preview.config(state="disabled")
                self.btn_lbl.config(text="  SEND  ", bg=AMBER, fg="#000")
                self.btn_outer.config(bg=AMBER, cursor="hand2")
                self.lbl_status.config(text="ready", fg=FG_DIM)
                log(f"loaded binary: {fname}, btn enabled")
                return

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            lines = content.splitlines()
            lc = len(lines)
            chars = len(content)

            self.file_path = path
            self.file_content = f"文件: {fname}\n路径: {path}\n行数: {lc}\n{'─' * 40}\n{content}"

            self._draw_drop_loaded(fname, lc, chars, ext)
            self.lbl_name.config(text=fname, fg=FG)
            self.lbl_meta.config(text=path, fg=FG_DIM)
            self.lbl_size.config(text=f"{lc}L  {chars:,}ch  {ext}", fg=FG_MID)

            self.preview.config(state="normal")
            self.preview.delete("1.0", "end")
            self._show_analysis(content, lines, ext, fname)
            self.preview.config(state="disabled")

            self.btn_lbl.config(text="  SEND  ", bg=AMBER, fg="#000")
            self.btn_outer.config(bg=AMBER, cursor="hand2")
            self.lbl_status.config(text="ready", fg=FG_DIM)
            log(f"loaded: {fname}, btn enabled")
        except Exception as e:
            log(f"load fail: {e}")
            self._set_error(os.path.basename(path), str(e))

    def _show_analysis(self, content, lines, ext, fname):
        p = self.preview
        lc = len(lines)
        p.insert("end", "─" * 50 + "\n", "dim")
        p.insert("end", f"FILE  {fname}\n", "info")
        p.insert("end", f"TYPE  {ext}  ·  {lc:,}L  ·  {len(content):,}ch\n", "dim")

        has_cjk = any('一' <= c <= '鿿' for c in content[:2000])
        enc = "UTF-8/CJK" if has_cjk else "ASCII/UTF-8"
        p.insert("end", f"ENC   {enc}\n", "dim")

        if ext == ".py":
            funcs = [l.strip() for l in lines if l.strip().startswith("def ")]
            classes = [l.strip() for l in lines if l.strip().startswith("class ")]
            imports = sum(1 for l in lines if l.strip().startswith(("import ", "from ")))
            p.insert("end", f"\nPYTHON: {len(funcs)} funcs, {len(classes)} classes, {imports} imports\n", "info")
            for f in funcs[:15]:
                p.insert("end", f"  {f}\n", "dim")
        elif ext in (".js", ".ts", ".go", ".rs", ".c", ".cpp", ".java"):
            funcs = sum(1 for l in lines if "(" in l and ")" in l)
            p.insert("end", f"\n{ext.upper()}: ~{funcs} functions\n", "info")
        elif ext == ".json":
            import json
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    p.insert("end", f"\nJSON: {len(data)} keys\n", "info")
                elif isinstance(data, list):
                    p.insert("end", f"\nJSON: {len(data)} items\n", "info")
            except Exception:
                p.insert("end", "\nJSON: parse error\n", "info")
        elif ext in (".md", ".txt", ".log"):
            words = len(content.split())
            p.insert("end", f"\nTEXT: {words:,} words\n", "info")

        p.insert("end", "\n" + "─" * 50 + "\n", "dim")
        for i, line in enumerate(lines[:500], 1):
            p.insert("end", f"{i:4d} │ ", "dim")
            p.insert("end", line + "\n")
        if lc > 500:
            p.insert("end", f"\n  · · ·  {lc - 500} more  · · ·\n", "dim")

    def _draw_drop_loaded(self, name, lc, chars, ext):
        c = self.drop_cv
        c.delete("all")
        w = c.winfo_width() or (self.W - 32)
        h = int(c["height"])
        self._rr(c, 1, 1, w-1, h-1, 6, fill="#080604", outline=AMBER_D, width=1)
        cx, cy = w // 2, h // 2
        c.create_text(cx, cy - 20, text="◼", font=(SANS, 14), fill=AMBER)
        c.create_text(cx, cy, text=name, font=(MONO, 10, "bold"), fill=FG)
        c.create_text(cx, cy + 16, text=f"{lc}L  {chars:,}ch  {ext}",
                      font=(MONO, 8), fill=FG_DIM)
        c.create_text(cx, cy + 30, text="✓ loaded", font=(MONO, 8), fill=GREEN)

    def _set_error(self, name, msg):
        self.lbl_name.config(text=name, fg=RED)
        self.lbl_meta.config(text=msg, fg=RED)
        self.lbl_size.config(text="")
        self.lbl_status.config(text="error", fg=RED)
        self.file_content = ""
        self.btn_lbl.config(text="  SEND  ", bg=AMBER_D, fg=FG)
        self.btn_outer.config(bg=AMBER_D)

    def _btn_hover(self, on):
        if not self.file_content:
            return
        bg = AMBER_L if on else AMBER
        self.btn_outer.config(bg=bg)
        self.btn_lbl.config(bg=bg)

    def _send(self):
        log(f"SEND clicked, file_content={bool(self.file_content)}")
        if not self.file_content:
            return
        try:
            os.makedirs(os.path.dirname(UPLOAD_FILE), exist_ok=True)
            with open(UPLOAD_FILE, "a", encoding="utf-8") as f:
                f.write(self.file_path + "\n")
        except Exception:
            pass
        self.root.clipboard_clear()
        self.root.clipboard_append(f"已上传: {os.path.basename(self.file_path)}")
        self.btn_lbl.config(text="  ✓  ", bg=GREEN)
        self.btn_outer.config(bg=GREEN)
        self.lbl_status.config(text="已加入队列 — 切换到 Claude Code 输入任意内容即可", fg=GREEN)
        self.root.after(3000, lambda: (
            self.btn_lbl.config(text="  SEND  ", bg=AMBER),
            self.btn_outer.config(bg=AMBER),
            self.lbl_status.config(text="ready", fg=FG_DIM)
        ))

    def run(self):
        log("mainloop start")
        self.root.mainloop()
        log("mainloop end")


if __name__ == "__main__":
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)) or ".")
        log(f"cwd={os.getcwd()}")
        app = UploadApp()
        app.run()
    except Exception:
        log("FATAL:\n" + traceback.format_exc())

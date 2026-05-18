"""
Installer - Extractor de Trades v1.3.0
Verifica e instala dependencias con UI visual
"""

import tkinter as tk
from tkinter import ttk
import subprocess
import sys
import threading
import importlib.util
import os

VERSION = "1.5.0"
AUTHOR  = "Joaquín García²"

STEPS = [
    ("pip",        "Actualizando pip..."),
    ("playwright", "Instalando Playwright..."),
    ("pandas",     "Instalando pandas..."),
    ("openpyxl",   "Instalando openpyxl..."),
    ("chromium",   "Instalando Chromium..."),
]
 
BG       = "#1e1e2e"
BG2      = "#2a2a3e"
BG3      = "#13131f"
FG       = "#e0e4f5"
FG2      = "#7c82a0"
ACCENT   = "#7aa2f7"
OK_COLOR = "#9ece6a"
ERR_COL  = "#f7768e"
WARN_COL = "#e0af68"
 
 
def is_installed(package):
    return importlib.util.find_spec(package) is not None
 
 
def run_cmd(cmd):
    result = subprocess.run(
        cmd, capture_output=True, text=True
    )
    return result.returncode == 0
 
 
class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Extractor {VERSION} — Instalador")
        self.root.geometry("600x420")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.cancelled = False
        self.success   = False
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Horizontal.TProgressbar",
                        troughcolor=BG2,
                        background=ACCENT,
                        thickness=12)
        self._build_ui()
        threading.Thread(target=self._run_install, daemon=True).start()
 
    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG2, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📦  Instalador de dependencias",
                 font=("Segoe UI", 14, "bold"),
                 bg=BG2, fg=FG).pack()
        tk.Label(header, text=f"Extractor {VERSION}  —  {AUTHOR}",
                 font=("Segoe UI", 9),
                 bg=BG2, fg=FG2).pack()
 
        # Steps frame
        self.steps_frame = tk.Frame(self.root, bg=BG, pady=10, padx=30)
        self.steps_frame.pack(fill="x")
 
        self.step_widgets = []
        for i, (_, label) in enumerate(STEPS):
            row = tk.Frame(self.steps_frame, bg=BG)
            row.pack(fill="x", pady=3)
 
            icon_lbl = tk.Label(row, text="⏳", font=("Segoe UI", 11),
                                bg=BG, fg=FG2, width=3)
            icon_lbl.pack(side="left")
 
            txt_lbl = tk.Label(row, text=label,
                               font=("Segoe UI", 10),
                               bg=BG, fg=FG2, anchor="w")
            txt_lbl.pack(side="left", fill="x", expand=True)
 
            sub_lbl = tk.Label(row, text="",
                               font=("Segoe UI", 8),
                               bg=BG, fg=FG2, anchor="e")
            sub_lbl.pack(side="right")
 
            self.step_widgets.append((icon_lbl, txt_lbl, sub_lbl))
 
        # Separator
        sep = tk.Frame(self.root, bg=BG2, height=1)
        sep.pack(fill="x", padx=30, pady=(4, 0))
 
        # Progress overall
        prog_frame = tk.Frame(self.root, bg=BG, padx=30, pady=10)
        prog_frame.pack(fill="x")
 
        self.lbl_current = tk.Label(prog_frame, text="Iniciando...",
                                    font=("Segoe UI", 10),
                                    bg=BG, fg=FG, anchor="w")
        self.lbl_current.pack(fill="x")
 
        self.progress = ttk.Progressbar(prog_frame,
                                        mode="determinate",
                                        maximum=len(STEPS))
        self.progress.pack(fill="x", pady=(6, 0))
 
        # Log small
        log_frame = tk.Frame(self.root, bg=BG, padx=30, pady=4)
        log_frame.pack(fill="both", expand=True)
 
        self.log = tk.Text(log_frame, font=("Consolas", 8),
                           bg=BG3, fg=FG2, relief="flat", bd=0,
                           state="disabled", height=4, wrap="word")
        self.log.pack(fill="both", expand=True)
 
        # Bottom button
        btn_frame = tk.Frame(self.root, bg=BG, pady=10)
        btn_frame.pack(fill="x")
 
        self.btn_close = tk.Button(btn_frame, text="Cancelar",
                                   font=("Segoe UI", 10), relief="flat",
                                   bg="#2e2e42", fg="#a0a8c8",
                                   activebackground="#3a3a52",
                                   cursor="hand2", width=14, pady=6,
                                   command=self._on_close)
        self.btn_close.pack()
 
    def _log(self, msg, color=None):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        if color:
            start = self.log.index("end-2l")
            end   = self.log.index("end-1c")
            tag   = f"col_{color.replace('#','')}"
            self.log.tag_config(tag, foreground=color)
            self.log.tag_add(tag, start, end)
        self.log.see("end")
        self.log.config(state="disabled")
 
    def _set_step(self, idx, status):
        """status: 'running' | 'ok' | 'skip' | 'error'"""
        icon_lbl, txt_lbl, sub_lbl = self.step_widgets[idx]
        icons  = {"running": "🔄", "ok": "✅", "skip": "☑️", "error": "❌"}
        colors = {"running": ACCENT, "ok": OK_COLOR, "skip": FG2, "error": ERR_COL}
        subs   = {"running": "instalando...", "ok": "listo", "skip": "ya instalado", "error": "falló"}
        icon_lbl.config(text=icons[status],   fg=colors[status])
        txt_lbl.config( fg=colors[status])
        sub_lbl.config( text=subs[status],    fg=colors[status])
 
    def _run_install(self):
        all_ok = True
 
        for i, (pkg, label) in enumerate(STEPS):
            if self.cancelled:
                break
 
            self.root.after(0, lambda l=label: self.lbl_current.config(text=l))
            self.root.after(0, lambda idx=i: self._set_step(idx, "running"))
            self.root.after(0, lambda v=i: setattr(self.progress, "__setitem__",
                            None) or self.progress.config(value=v))
 
            # ── Pip ──────────────────────────────────────────
            if pkg == "pip":
                ok = run_cmd([sys.executable, "-m", "pip", "install",
                              "--upgrade", "pip", "--quiet"])
                status = "ok" if ok else "error"
                self._log("pip actualizado" if ok else "Error actualizando pip",
                          OK_COLOR if ok else ERR_COL)
 
            # ── Chromium ─────────────────────────────────────
            elif pkg == "chromium":
                self._log("Descargando Chromium (puede tardar)...", WARN_COL)
                ok = run_cmd([sys.executable, "-m", "playwright", "install", "chromium"])
                status = "ok" if ok else "error"
                self._log("Chromium instalado" if ok else "Error instalando Chromium",
                          OK_COLOR if ok else ERR_COL)
 
            # ── Python packages ──────────────────────────────
            else:
                if is_installed(pkg if pkg != "playwright" else "playwright"):
                    status = "skip"
                    self._log(f"{pkg} ya está instalado", FG2)
                else:
                    pkgs_map = {
                        "playwright": ["playwright", "pandas", "openpyxl"],
                        "pandas":     ["pandas"],
                        "openpyxl":   ["openpyxl"],
                    }
                    install_pkgs = pkgs_map.get(pkg, [pkg])
                    ok = run_cmd([sys.executable, "-m", "pip", "install",
                                  "--quiet", "--break-system-packages"] + install_pkgs)
                    if not ok:
                        ok = run_cmd([sys.executable, "-m", "pip", "install",
                                      "--quiet"] + install_pkgs)
                    status = "ok" if ok else "error"
                    self._log(f"{pkg} {'instalado' if ok else 'ERROR'}",
                              OK_COLOR if ok else ERR_COL)
 
            if status == "error":
                all_ok = False
 
            self.root.after(0, lambda idx=i, s=status: self._set_step(idx, s))
            self.root.after(0, lambda v=i+1: self.progress.config(value=v))
 
        if self.cancelled:
            return
 
        if all_ok:
            self.success = True
            self.root.after(0, self._show_success)
        else:
            self.root.after(0, self._show_error)
 
    def _show_success(self):
        self.btn_close.config(text="Cerrar", bg="#2d6a4f", fg="#ffffff")
        self._countdown(5)
 
    def _countdown(self, n):
        if self.cancelled:
            return
        if n > 0:
            self.lbl_current.config(
                text=f"✅  Todo listo — lanzando en {n}...", fg=OK_COLOR)
            self.root.after(1000, lambda: self._countdown(n - 1))
        else:
            self.lbl_current.config(
                text="🚀  Lanzando la aplicación...", fg=OK_COLOR)
            self.root.after(500, self._launch_app)
 
    def _show_error(self):
        self.lbl_current.config(
            text="❌  Hubo errores en la instalación. Revisá el log.", fg=ERR_COL)
        self.btn_close.config(text="Cerrar", bg="#6b1a2a", fg="#ffffff")
 
    def _launch_app(self):
        self.root.destroy()
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extractor_ui.py")
        subprocess.Popen([sys.executable, script])
 
    def _on_close(self):
        self.cancelled = True
        self.root.destroy()
 
 
if __name__ == "__main__":
    root = tk.Tk()
    app  = InstallerApp(root)
    root.mainloop()
 
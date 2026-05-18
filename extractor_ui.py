"""
Extractor de Trades - PMP Platform v1.3.0
"""

import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import pandas as pd
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
import json
import os

# ============================================================
#  CONFIGURACIÓN
# ============================================================

VERSION = "1.5.0"
AUTHOR  = "Joaquín García²"
URL_LOGIN     = "https://pmp.abscapco.com/PMP/Login/Login/0"
URL_TRADES    = "https://pmp.abscapco.com/PMP/SearchTradeDetails"
BASE_URL      = "https://pmp.abscapco.com"
COLUMNA_IDS   = "TradeId"

# Rutas dinámicas — funcionan en cualquier PC
APP_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
SESION_DIR    = str(APP_DIR / "chrome_session")
PROGRESO_PATH = str(APP_DIR / "progreso.txt")
CONFIG_PATH   = str(APP_DIR / "config.json")
DEFAULT_DEST  = str(Path.home() / "Desktop" / "PDF_Trades")

MAX_REINTENTOS = 3

# Estados posibles
ESTADO_PENDIENTE = "Pendiente"
ESTADO_OK        = "Descargado"
ESTADO_SIN_ARCH  = "Sin archivo"
ESTADO_ERROR     = "Error"

# ============================================================

THEMES = {
    "dark": {
        "bg":           "#1e1e2e",
        "bg2":          "#2a2a3e",
        "bg3":          "#13131f",
        "bg_panel":     "#252538",
        "fg":           "#e0e4f5",
        "fg2":          "#7c82a0",
        "fg_label":     "#a0a8c8",
        "accent":       "#7aa2f7",
        "ok":           "#9ece6a",
        "error":        "#f7768e",
        "warning":      "#e0af68",
        "info":         "#7aa2f7",
        "btn_start_bg": "#2d6a4f",
        "btn_start_fg": "#ffffff",
        "btn_pause_bg": "#7c5c00",
        "btn_pause_fg": "#ffffff",
        "btn_stop_bg":  "#6b1a2a",
        "btn_stop_fg":  "#ffffff",
        "btn_misc_bg":  "#2e2e42",
        "btn_misc_fg":  "#a0a8c8",
        "btn_acc_bg":   "#2a3f6f",
        "btn_acc_fg":   "#ffffff",
        "progress":     "#7aa2f7",
        "trough":       "#2a2a3e",
        "border":       "#3a3a52",
        "theme_btn_fg": "#7c82a0",
        "list_sel":     "#2a3f6f",
        "list_hover":   "#252538",
        "tag_pending":  "#7c82a0",
        "tag_ok":       "#9ece6a",
        "tag_nofile":   "#e0af68",
        "tag_error":    "#f7768e",
        "tag_active":   "#7aa2f7",
    },
    "light": {
        "bg":           "#f5f6fa",
        "bg2":          "#e8eaf0",
        "bg3":          "#ffffff",
        "bg_panel":     "#eceef5",
        "fg":           "#1a1b2e",
        "fg2":          "#5a5f7a",
        "fg_label":     "#2c2f4a",
        "accent":       "#3b6fd4",
        "ok":           "#2d7a3a",
        "error":        "#c0392b",
        "warning":      "#b07d10",
        "info":         "#2c5faa",
        "btn_start_bg": "#2d7a3a",
        "btn_start_fg": "#ffffff",
        "btn_pause_bg": "#b07d10",
        "btn_pause_fg": "#ffffff",
        "btn_stop_bg":  "#c0392b",
        "btn_stop_fg":  "#ffffff",
        "btn_misc_bg":  "#d0d3e0",
        "btn_misc_fg":  "#1a1b2e",
        "btn_acc_bg":   "#3b6fd4",
        "btn_acc_fg":   "#ffffff",
        "progress":     "#3b6fd4",
        "trough":       "#d0d3e0",
        "border":       "#c5c8d8",
        "theme_btn_fg": "#5a5f7a",
        "list_sel":     "#d0dcf8",
        "list_hover":   "#eceef5",
        "tag_pending":  "#5a5f7a",
        "tag_ok":       "#2d7a3a",
        "tag_nofile":   "#b07d10",
        "tag_error":    "#c0392b",
        "tag_active":   "#3b6fd4",
    }
}

STATUS_ICONS = {
    ESTADO_PENDIENTE: "⏳",
    ESTADO_OK:        "✅",
    ESTADO_SIN_ARCH:  "⚠️",
    ESTADO_ERROR:     "❌",
    "Procesando":     "🔄",
}


class App:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Extractor {VERSION} - {AUTHOR}")
        self.root.geometry("1100x660")
        self.root.minsize(800, 500)
        self.root.resizable(True, True)

        # Cargar config guardada
        cfg = self._load_config()
        self.excel_path   = tk.StringVar(value=cfg.get("excel_path", ""))
        self.carpeta_dest = tk.StringVar(value=cfg.get("carpeta_dest", DEFAULT_DEST))
        self.search_var   = tk.StringVar()
        self.running      = False
        self.paused       = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self.theme_name   = "dark"

        # Trade list: {trade_id: estado}
        self.trades_estado = {}
        self.all_ids       = []

        self._build_ui()
        self._apply_theme()

    # ── BUILD UI ────────────────────────────────────────────

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)
        self.root.rowconfigure(2, weight=0)

        # ── Header ──────────────────────────────────────────
        self.header = tk.Frame(self.root, pady=10)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.columnconfigure(1, weight=1)

        # Branding izquierda
        brand = tk.Frame(self.header)
        brand.grid(row=0, column=0, sticky="w", padx=16)
        self.lbl_brand = tk.Label(brand,
                                  text=f"Extractor {VERSION}  —  {AUTHOR}",
                                  font=("Segoe UI", 10, "bold"))
        self.lbl_brand.pack(anchor="w")
        self.lbl_sub = tk.Label(brand, text="PMP Portfolio Management Platform",
                                font=("Segoe UI", 8))
        self.lbl_sub.pack(anchor="w")

        # Título centro
        self.lbl_title = tk.Label(self.header, text="📄  Extractor de Trades",
                                  font=("Segoe UI", 15, "bold"))
        self.lbl_title.grid(row=0, column=1)

        # Botón tema derecha
        self.btn_theme = tk.Button(self.header, text="☀️  Modo claro",
                                   font=("Segoe UI", 9), relief="flat",
                                   cursor="hand2", bd=0,
                                   command=self._toggle_theme)
        self.btn_theme.grid(row=0, column=2, sticky="e", padx=16)

        # ── Body (izquierda + derecha) ───────────────────────
        self.body = tk.Frame(self.root)
        self.body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.body.columnconfigure(0, weight=3)
        self.body.columnconfigure(1, weight=2)
        self.body.rowconfigure(0, weight=1)

        # ── Panel izquierdo ──────────────────────────────────
        self.left = tk.Frame(self.body)
        self.left.grid(row=0, column=0, sticky="nsew", padx=(14, 6), pady=6)
        self.left.columnconfigure(0, weight=1)
        self.left.rowconfigure(4, weight=1)

        # Excel
        self.lbl_excel = tk.Label(self.left, text="Archivo Excel:",
                                  font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_excel.grid(row=0, column=0, sticky="w", pady=(4, 2))
        row_excel = tk.Frame(self.left)
        row_excel.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        row_excel.columnconfigure(0, weight=1)
        self.entry_excel = tk.Entry(row_excel, textvariable=self.excel_path,
                                    font=("Segoe UI", 10), relief="flat",
                                    bd=0, highlightthickness=1)
        self.entry_excel.grid(row=0, column=0, sticky="ew", ipady=7, padx=(0, 8))
        self.btn_excel = tk.Button(row_excel, text="Buscar...",
                                   font=("Segoe UI", 10), relief="flat",
                                   cursor="hand2", command=self._seleccionar_excel,
                                   padx=14, pady=5)
        self.btn_excel.grid(row=0, column=1)

        # Carpeta destino
        self.lbl_dest = tk.Label(self.left, text="Carpeta de descarga:",
                                 font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_dest.grid(row=2, column=0, sticky="w", pady=(0, 2))
        row_dest = tk.Frame(self.left)
        row_dest.grid(row=3, column=0, sticky="ew", pady=(0, 8))
        row_dest.columnconfigure(0, weight=1)
        self.entry_dest = tk.Entry(row_dest, textvariable=self.carpeta_dest,
                                   font=("Segoe UI", 10), relief="flat",
                                   bd=0, highlightthickness=1)
        self.entry_dest.grid(row=0, column=0, sticky="ew", ipady=7, padx=(0, 8))
        self.btn_dest = tk.Button(row_dest, text="Cambiar...",
                                  font=("Segoe UI", 10), relief="flat",
                                  cursor="hand2", command=self._seleccionar_carpeta,
                                  padx=14, pady=5)
        self.btn_dest.grid(row=0, column=1)

        # Log
        self.lbl_log = tk.Label(self.left, text="Log de actividad:",
                                font=("Segoe UI", 9), anchor="w")
        self.lbl_log.grid(row=4, column=0, sticky="w")
        self.log = scrolledtext.ScrolledText(self.left, font=("Consolas", 9),
                                             relief="flat", bd=0,
                                             state="disabled", wrap="word")
        self.log.grid(row=5, column=0, sticky="nsew", pady=(4, 0))
        self.left.rowconfigure(5, weight=1)

        # ── Panel derecho — Lista de trades ──────────────────
        self.right = tk.Frame(self.body)
        self.right.grid(row=0, column=1, sticky="nsew", padx=(6, 14), pady=6)
        self.right.columnconfigure(0, weight=1)
        self.right.rowconfigure(2, weight=1)

        self.lbl_trades = tk.Label(self.right, text="Lista de Trades",
                                   font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_trades.grid(row=0, column=0, sticky="w", pady=(4, 4))

        # Búsqueda
        self.search_var.trace_add("write", self._filtrar_trades)
        row_search = tk.Frame(self.right)
        row_search.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        row_search.columnconfigure(0, weight=1)
        self.entry_search = tk.Entry(row_search, textvariable=self.search_var,
                                     font=("Segoe UI", 10), relief="flat",
                                     bd=0, highlightthickness=1)
        self.entry_search.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self.lbl_search_icon = tk.Label(row_search, text="🔍",
                                        font=("Segoe UI", 12))
        self.lbl_search_icon.grid(row=0, column=1)

        # Listbox + scrollbar
        list_frame = tk.Frame(self.right)
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(list_frame, font=("Consolas", 9),
                                  relief="flat", bd=0,
                                  selectmode="browse",
                                  activestyle="none")
        self.listbox.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(list_frame, orient="vertical",
                           command=self.listbox.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=sb.set)

        # Leyenda
        self.lbl_leyenda = tk.Label(self.right,
                                    text="⏳ Pendiente  ✅ Descargado  ⚠️ Sin archivo  ❌ Error",
                                    font=("Segoe UI", 8), anchor="w")
        self.lbl_leyenda.grid(row=3, column=0, sticky="w", pady=(6, 0))

        # Contador
        self.lbl_counter = tk.Label(self.right, text="",
                                    font=("Segoe UI", 8), anchor="e")
        self.lbl_counter.grid(row=4, column=0, sticky="e")

        # ── Botones de acción ────────────────────────────────
        self.frame_btns = tk.Frame(self.root, padx=14, pady=8)
        self.frame_btns.grid(row=2, column=0, sticky="ew")

        self.btn_start = tk.Button(self.frame_btns, text="▶  Iniciar",
                                   font=("Segoe UI", 10, "bold"), relief="flat",
                                   cursor="hand2", command=self._iniciar,
                                   padx=16, pady=7)
        self.btn_start.pack(side="left", padx=(0, 6))

        self.btn_pause = tk.Button(self.frame_btns, text="⏸  Pausar",
                                   font=("Segoe UI", 10), relief="flat",
                                   cursor="hand2", command=self._pausar,
                                   padx=16, pady=7, state="disabled")
        self.btn_pause.pack(side="left", padx=(0, 6))

        self.btn_stop = tk.Button(self.frame_btns, text="⏹  Detener",
                                  font=("Segoe UI", 10), relief="flat",
                                  cursor="hand2", command=self._detener,
                                  padx=16, pady=7, state="disabled")
        self.btn_stop.pack(side="left", padx=(0, 6))

        self.btn_limpiar = tk.Button(self.frame_btns, text="🗑  Limpiar log",
                                     font=("Segoe UI", 10), relief="flat",
                                     cursor="hand2", command=self._limpiar_log,
                                     padx=12, pady=7)
        self.btn_limpiar.pack(side="left", padx=(0, 6))

        self.btn_reset = tk.Button(self.frame_btns, text="🔄  Empezar de cero",
                                   font=("Segoe UI", 10), relief="flat",
                                   cursor="hand2", command=self._reset_progreso,
                                   padx=12, pady=7)
        self.btn_reset.pack(side="right")

        # Progreso + status en la misma barra
        prog_frame = tk.Frame(self.frame_btns)
        prog_frame.pack(side="right", padx=(0, 12), fill="x", expand=True)

        self.label_prog = tk.Label(prog_frame, text="En espera...",
                                   font=("Segoe UI", 8), anchor="w")
        self.label_prog.pack(anchor="w")

        self.style = ttk.Style()
        self.style.theme_use("default")
        self.progress = ttk.Progressbar(prog_frame, mode="determinate", length=260)
        self.progress.pack(fill="x")

        # Status bar
        self.status = tk.Label(self.root, text=f"Extractor {VERSION}  |  Listo",
                               font=("Segoe UI", 8), anchor="w", padx=14, pady=3)
        self.status.grid(row=3, column=0, sticky="ew")
        self.root.rowconfigure(3, weight=0)

    # ── THEME ────────────────────────────────────────────────

    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self._apply_theme()

    def _apply_theme(self):
        t = THEMES[self.theme_name]
        icon = "🌙  Modo oscuro" if self.theme_name == "light" else "☀️  Modo claro"

        self.root.configure(bg=t["bg"])
        self.body.configure(bg=t["bg"])

        # Header
        self.header.configure(bg=t["bg2"])
        self.header.winfo_children()[0].configure(bg=t["bg2"])  # brand frame
        self.lbl_brand.configure(bg=t["bg2"], fg=t["fg"])
        self.lbl_sub.configure(bg=t["bg2"], fg=t["fg2"])
        self.lbl_title.configure(bg=t["bg2"], fg=t["fg"])
        self.btn_theme.configure(bg=t["bg2"], fg=t["theme_btn_fg"],
                                 activebackground=t["bg2"],
                                 activeforeground=t["fg"], text=icon)

        # Left panel
        self.left.configure(bg=t["bg"])
        self.lbl_excel.configure(bg=t["bg"], fg=t["fg_label"])
        self.lbl_dest.configure(bg=t["bg"], fg=t["fg_label"])
        self.entry_excel.master.configure(bg=t["bg"])
        self.entry_dest.master.configure(bg=t["bg"])
        self.entry_excel.configure(bg=t["bg3"], fg=t["fg"],
                                   insertbackground=t["fg"],
                                   highlightbackground=t["border"],
                                   highlightcolor=t["accent"])
        self.entry_dest.configure(bg=t["bg3"], fg=t["fg"],
                                  insertbackground=t["fg"],
                                  highlightbackground=t["border"],
                                  highlightcolor=t["accent"])
        self.btn_excel.configure(bg=t["btn_acc_bg"], fg=t["btn_acc_fg"],
                                 activebackground=t["btn_acc_bg"])
        self.btn_dest.configure(bg=t["btn_acc_bg"], fg=t["btn_acc_fg"],
                                activebackground=t["btn_acc_bg"])
        self.lbl_log.configure(bg=t["bg"], fg=t["fg2"])
        self.log.configure(bg=t["bg3"], fg=t["fg"],
                           insertbackground=t["fg"],
                           selectbackground=t["accent"])
        self.log.tag_config("ok",      foreground=t["ok"])
        self.log.tag_config("error",   foreground=t["error"])
        self.log.tag_config("warning", foreground=t["warning"])
        self.log.tag_config("info",    foreground=t["info"])
        self.log.tag_config("normal",  foreground=t["fg"])

        # Right panel
        self.right.configure(bg=t["bg"])
        self.lbl_trades.configure(bg=t["bg"], fg=t["fg_label"])
        self.entry_search.master.configure(bg=t["bg"])
        self.entry_search.configure(bg=t["bg3"], fg=t["fg"],
                                    insertbackground=t["fg"],
                                    highlightbackground=t["border"],
                                    highlightcolor=t["accent"])
        self.lbl_search_icon.configure(bg=t["bg"], fg=t["fg2"])
        self.listbox.master.configure(bg=t["bg"])
        self.listbox.configure(bg=t["bg_panel"], fg=t["fg"],
                               selectbackground=t["list_sel"],
                               selectforeground=t["fg"])
        self.lbl_leyenda.configure(bg=t["bg"], fg=t["fg2"])
        self.lbl_counter.configure(bg=t["bg"], fg=t["fg2"])

        # Buttons
        self.frame_btns.configure(bg=t["bg"])
        self.btn_start.configure(bg=t["btn_start_bg"], fg=t["btn_start_fg"],
                                 activebackground=t["btn_start_bg"],
                                 activeforeground=t["btn_start_fg"])
        self.btn_pause.configure(bg=t["btn_pause_bg"], fg=t["btn_pause_fg"],
                                 activebackground=t["btn_pause_bg"],
                                 activeforeground=t["btn_pause_fg"])
        self.btn_stop.configure(bg=t["btn_stop_bg"], fg=t["btn_stop_fg"],
                                activebackground=t["btn_stop_bg"],
                                activeforeground=t["btn_stop_fg"])
        self.btn_limpiar.configure(bg=t["btn_misc_bg"], fg=t["btn_misc_fg"],
                                   activebackground=t["btn_misc_bg"])
        self.btn_reset.configure(bg=t["btn_misc_bg"], fg=t["btn_misc_fg"],
                                 activebackground=t["btn_misc_bg"])

        prog_frame = self.label_prog.master
        prog_frame.configure(bg=t["bg"])
        self.label_prog.configure(bg=t["bg"], fg=t["fg2"])
        self.style.configure("TProgressbar",
                             troughcolor=t["trough"],
                             background=t["progress"],
                             thickness=8)

        self.status.configure(bg=t["bg2"], fg=t["fg2"])

        # Refresh list colors
        self._refresh_list()

    # ── TRADE LIST ───────────────────────────────────────────

    def _cargar_trades(self, ids):
        """Inicializa la lista verificando archivos reales en la carpeta de descarga."""
        self.all_ids = ids
        self.trades_estado = {id_: ESTADO_PENDIENTE for id_ in ids}
        # Verificar qué IDs ya tienen archivo en la carpeta de destino
        carpeta = Path(self.carpeta_dest.get())
        if carpeta.exists():
            archivos = [f.name for f in carpeta.iterdir() if f.is_file()]
            for id_ in ids:
                if any(id_ in nombre for nombre in archivos):
                    self.trades_estado[id_] = ESTADO_OK
        self._refresh_list()

    def _set_estado(self, trade_id, estado):
        self.trades_estado[trade_id] = estado
        self.root.after(0, self._refresh_list)

    def _refresh_list(self):
        t = THEMES[self.theme_name]
        query = self.search_var.get().lower().strip()

        self.listbox.delete(0, "end")
        shown = 0
        for id_ in self.all_ids:
            if query and query not in id_.lower():
                continue
            estado = self.trades_estado.get(id_, ESTADO_PENDIENTE)
            icon   = STATUS_ICONS.get(estado, "⏳")
            label  = f" {icon}  {id_}  —  {estado}"
            self.listbox.insert("end", label)

            # Color por estado
            color_map = {
                ESTADO_PENDIENTE: t["tag_pending"],
                ESTADO_OK:        t["tag_ok"],
                ESTADO_SIN_ARCH:  t["tag_nofile"],
                ESTADO_ERROR:     t["tag_error"],
                "Procesando":     t["tag_active"],
            }
            self.listbox.itemconfig("end", fg=color_map.get(estado, t["fg"]))
            shown += 1

        total  = len(self.all_ids)
        ok     = sum(1 for v in self.trades_estado.values() if v == ESTADO_OK)
        self.lbl_counter.config(text=f"Mostrando {shown} / {total}  |  ✅ {ok}")

    def _filtrar_trades(self, *_):
        self._refresh_list()

    # ── HELPERS ──────────────────────────────────────────────

    def _load_config(self):
        try:
            if Path(CONFIG_PATH).exists():
                return json.loads(Path(CONFIG_PATH).read_text())
        except Exception:
            pass
        return {}

    def _save_config(self):
        try:
            cfg = {
                "excel_path":   self.excel_path.get(),
                "carpeta_dest": self.carpeta_dest.get(),
            }
            Path(CONFIG_PATH).write_text(json.dumps(cfg, indent=2))
        except Exception:
            pass

    def _seleccionar_excel(self):
        path = filedialog.askopenfilename(
            title="Seleccionar Excel con IDs",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if path:
            self.excel_path.set(path)
            self._save_config()

    def _seleccionar_carpeta(self):
        path = filedialog.askdirectory(title="Seleccionar carpeta de descarga")
        if path:
            self.carpeta_dest.set(path)
            self._save_config()

    def _limpiar_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _reset_progreso(self):
        if Path(PROGRESO_PATH).exists():
            Path(PROGRESO_PATH).unlink()
            for id_ in self.trades_estado:
                self.trades_estado[id_] = ESTADO_PENDIENTE
            self._refresh_list()
            self._log("🔄 Progreso reseteado — próxima ejecución empieza de cero.", "warning")
        else:
            self._log("ℹ️  No hay progreso guardado.", "info")

    def _log(self, msg, tag="normal"):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_progress(self, value, maximo, label=""):
        self.progress["maximum"] = maximo
        self.progress["value"]   = value
        self.label_prog.config(text=label or f"{value} / {maximo}")

    # ── CONTROL ──────────────────────────────────────────────

    def _iniciar(self):
        if not self.excel_path.get():
            self._log("❌ Seleccioná un archivo Excel primero.", "error")
            return
        if not self.carpeta_dest.get():
            self._log("❌ Seleccioná una carpeta de destino.", "error")
            return
        self.running = True
        self.paused  = False
        self._pause_event.set()
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.status.config(text=f"Extractor {VERSION}  |  Ejecutando...")
        threading.Thread(target=self._run_async, daemon=True).start()

    def _pausar(self):
        if not self.paused:
            self.paused = True
            self._pause_event.clear()
            self.btn_pause.config(text="▶  Reanudar")
            self._log("⏸  Pausado — hacé click en Reanudar para continuar.", "warning")
            self.status.config(text=f"Extractor {VERSION}  |  Pausado")
        else:
            self.paused = False
            self._pause_event.set()
            self.btn_pause.config(text="⏸  Pausar")
            self._log("▶  Reanudando...", "ok")
            self.status.config(text=f"Extractor {VERSION}  |  Ejecutando...")

    def _detener(self):
        self.running = False
        self._pause_event.set()
        self._log("⏹  Deteniendo... (termina el trade actual)", "warning")
        self.status.config(text=f"Extractor {VERSION}  |  Deteniendo...")

    def _run_async(self):
        asyncio.run(self._extraer())

    def _finalizar_ui(self):
        self.running = False
        self.paused  = False
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸  Pausar")
        self.btn_stop.config(state="disabled")
        self.status.config(text=f"Extractor {VERSION}  |  Listo")

    # ── LÓGICA PRINCIPAL ─────────────────────────────────────

    async def _extraer(self):
        excel   = self.excel_path.get()
        carpeta = Path(self.carpeta_dest.get())
        carpeta.mkdir(exist_ok=True)

        self._log(f"📄 Leyendo: {excel}", "info")
        try:
            df = pd.read_excel(excel)
        except Exception as e:
            self._log(f"❌ Error leyendo Excel: {e}", "error")
            self.root.after(0, self._finalizar_ui)
            return

        if COLUMNA_IDS not in df.columns:
            self._log(f"❌ Columna '{COLUMNA_IDS}' no encontrada.", "error")
            self._log(f"   Columnas: {list(df.columns)}", "warning")
            self.root.after(0, self._finalizar_ui)
            return

        ids = df[COLUMNA_IDS].dropna().astype(str).str.strip().tolist()
        self._log(f"   → {len(ids)} IDs encontrados", "info")

        # Cargar lista
        self.root.after(0, lambda: self._cargar_trades(ids))

        # Verificar qué IDs ya tienen archivo descargado en la carpeta destino
        carpeta_check = Path(self.carpeta_dest.get())
        ya_descargados = set()
        if carpeta_check.exists():
            archivos_existentes = [f.name for f in carpeta_check.iterdir() if f.is_file()]
            for id_ in ids:
                if any(id_ in nombre for nombre in archivos_existentes):
                    ya_descargados.add(id_)
        if ya_descargados:
            self._log(f"   → {len(ya_descargados)} ya tienen archivo en la carpeta, se saltean...", "info")

        ids_pendientes = [id_ for id_ in ids if id_ not in ya_descargados]
        total = len(ids_pendientes)
        self._log(f"   → {total} pendientes\n", "info")
        resultados = []

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=SESION_DIR,
                headless=False,
                accept_downloads=True,
                args=["--start-maximized"],
                no_viewport=True,
            )
            page = context.pages[0] if context.pages else await context.new_page()

            await page.goto(URL_LOGIN)
            await page.wait_for_load_state("networkidle")

            if "Login" in page.url or "login" in page.url:
                self._log("🔐 Loguéate en el navegador. El script espera...", "warning")
                await page.wait_for_url(
                    lambda url: "Login" not in url and "login" not in url,
                    timeout=120_000
                )
                self._log("✅ Login detectado.\n", "ok")
            else:
                self._log("✅ Sesión activa.\n", "ok")

            for i, trade_id in enumerate(ids_pendientes, 1):
                if not self.running:
                    break

                self._pause_event.wait()
                if not self.running:
                    break

                self._log(f"[{i}/{total}] Procesando: {trade_id}", "info")
                self._set_estado(trade_id, "Procesando")
                self.root.after(0, lambda v=i, m=total, t=trade_id:
                                self._set_progress(v, m, f"Procesando {t}  ({v}/{m})"))
                exito = False

                for intento in range(1, MAX_REINTENTOS + 1):
                    try:
                        archivos, estado = await self._procesar_trade(page, trade_id, carpeta)
                        resultados.append({"ID": trade_id, "Estado": estado, "Archivos": archivos})
                        self._set_estado(trade_id, estado)
                        # Progreso basado en archivos reales, no txt
                        exito = True
                        break
                    except Exception as e:
                        self._log(f"   ⚠️  Intento {intento}/{MAX_REINTENTOS}: {e}", "warning")
                        if intento < MAX_REINTENTOS:
                            self._log("   🔄 Reintentando en 5s...", "warning")
                            await asyncio.sleep(5)
                            try:
                                await page.goto(URL_TRADES)
                                await page.wait_for_load_state("networkidle")
                            except Exception:
                                pass

                if not exito:
                    self._log(f"   ❌ Falló después de {MAX_REINTENTOS} intentos", "error")
                    self._set_estado(trade_id, ESTADO_ERROR)
                    resultados.append({"ID": trade_id, "Estado": ESTADO_ERROR, "Archivos": 0})

            await context.close()

        df_log = pd.DataFrame(resultados)
        ok   = len(df_log[df_log["Estado"] == ESTADO_OK])  if not df_log.empty else 0
        err  = len(df_log[df_log["Estado"] == ESTADO_ERROR]) if not df_log.empty else 0
        pdfs = int(df_log["Archivos"].sum())                if not df_log.empty else 0

        self._log("\n" + "─" * 46, "normal")
        self._log("📊  RESUMEN FINAL", "info")
        self._log("─" * 46, "normal")
        self._log(f"✅  Descargados     : {ok}",   "ok")
        self._log(f"❌  Con error       : {err}",  "error")
        self._log(f"📁  PDFs descargados: {pdfs}", "info")

        if not df_log.empty:
            log_path = f"log_descargas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_log.to_excel(log_path, index=False)
            self._log(f"📋  Log guardado en : {log_path}", "info")

        self._log("\n✔️  Proceso finalizado.", "ok")
        self.root.after(0, self._finalizar_ui)

    async def _procesar_trade(self, page, trade_id, carpeta):
        await page.goto(URL_TRADES)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)

        try:
            checkbox = page.locator("input[type='checkbox']").first
            if await checkbox.is_checked():
                await checkbox.uncheck()
                await page.wait_for_timeout(500)
                self._log("   🗓️  'As of Date' desmarcado", "normal")
        except Exception:
            pass

        await page.locator("#tradeDiv span.select2-selection--single").click()
        await page.wait_for_timeout(700)
        search_input = page.locator("input.select2-search__field")
        await search_input.wait_for(timeout=5_000)
        await search_input.fill("")
        await search_input.type(trade_id, delay=80)
        await page.wait_for_timeout(1500)
        opcion = page.locator(f"li.select2-results__option:has-text('{trade_id}')").first
        await opcion.wait_for(state="visible", timeout=8_000)
        await opcion.click()
        await page.wait_for_timeout(1000)
        self._log("   ✅ Trade seleccionado", "ok")

        await page.wait_for_selector(f"td:has-text('{trade_id}')", timeout=10_000)
        fila = page.locator(f"tr:has-text('{trade_id}')").first
        await fila.click()
        await page.wait_for_timeout(2000)
        await page.wait_for_selector("#myModal.in", timeout=10_000)
        await page.wait_for_timeout(1000)

        links = page.locator(f"#myModal a[href*='/PMP/File/Download/']:has-text('{trade_id}')")
        count = await links.count()

        hrefs, nombres = [], []
        for j in range(count):
            link = links.nth(j)
            nombre_raw = (await link.inner_text()).strip()
            if not nombre_raw.lower().endswith('.pdf'):
                continue
            href   = await link.get_attribute("href")
            nombre = nombre_raw.replace("/", "-").replace("\\", "-")
            hrefs.append(href)
            nombres.append(nombre)

        if not hrefs:
            self._log(f"   ⚠️  Sin PDFs con '{trade_id}'", "warning")
            return 0, ESTADO_SIN_ARCH

        self._log(f"   📂 {len(hrefs)} PDF(s) encontrado(s)", "normal")
        archivos_descargados = 0

        for href, nombre in zip(hrefs, nombres):
            url_descarga = f"{BASE_URL}{href}"
            self._log(f"   📥 Descargando: {nombre}", "normal")
            try:
                async with page.expect_download(timeout=30_000) as dl_info:
                    await page.evaluate(f"""
                        const a = document.createElement('a');
                        a.href = '{url_descarga}';
                        a.download = '';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    """)
                download = await dl_info.value
                destino  = carpeta / f"{nombre}.pdf"
                await download.save_as(str(destino))
                archivos_descargados += 1
                self._log(f"   ✅ Guardado: {nombre}", "ok")
                await page.wait_for_timeout(500)
            except Exception as e_dl:
                self._log(f"   ❌ Error: {e_dl}", "error")

        estado_final = ESTADO_OK if archivos_descargados > 0 else ESTADO_ERROR
        return archivos_descargados, estado_final


if __name__ == "__main__":
    root = tk.Tk()
    app  = App(root)
    root.mainloop()
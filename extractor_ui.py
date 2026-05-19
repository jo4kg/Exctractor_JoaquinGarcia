# -*- coding: utf-8 -*-
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
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ============================================================
#  CONFIGURACIÓN
# ============================================================

VERSION       = "2.2.0"
AUTHOR        = "Joaquín García²"
URL_LOGIN     = "https://pmp.abscapco.com/PMP/Login/Login/0"
URL_TRADES    = "https://pmp.abscapco.com/PMP/SearchTradeDetails"
BASE_URL      = "https://pmp.abscapco.com"
COLUMNA_IDS   = "TradeId"

# Rutas dinámicas — funcionan en cualquier PC
APP_DIR       = Path(os.path.dirname(os.path.abspath(__file__)))
SESION_DIR    = str(APP_DIR / "chrome_session")
PROGRESO_PATH = str(APP_DIR / "progreso.txt")
CONFIG_PATH   = str(APP_DIR / "config.json")
LOGS_DIR      = APP_DIR / "Logs"
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
    },
    "bordo": {
        "bg":           "#1a0a0d",
        "bg2":          "#2b1018",
        "bg3":          "#110508",
        "bg_panel":     "#221018",
        "fg":           "#f0d8dc",
        "fg2":          "#a06070",
        "fg_label":     "#d4a0a8",
        "accent":       "#e05070",
        "ok":           "#a0c878",
        "error":        "#ff6060",
        "warning":      "#e8b060",
        "info":         "#e05070",
        "btn_start_bg": "#3a6030",
        "btn_start_fg": "#ffffff",
        "btn_pause_bg": "#8a5010",
        "btn_pause_fg": "#ffffff",
        "btn_stop_bg":  "#7a1020",
        "btn_stop_fg":  "#ffffff",
        "btn_misc_bg":  "#2b1018",
        "btn_misc_fg":  "#d4a0a8",
        "btn_acc_bg":   "#7a2030",
        "btn_acc_fg":   "#ffffff",
        "progress":     "#e05070",
        "trough":       "#2b1018",
        "border":       "#4a2030",
        "theme_btn_fg": "#a06070",
        "list_sel":     "#4a1828",
        "list_hover":   "#221018",
        "tag_pending":  "#a06070",
        "tag_ok":       "#a0c878",
        "tag_nofile":   "#e8b060",
        "tag_error":    "#ff6060",
        "tag_active":   "#e05070",
    },
    "verde": {
        "bg":           "#0a1a0f",
        "bg2":          "#102018",
        "bg3":          "#061008",
        "bg_panel":     "#0e1a12",
        "fg":           "#d0f0d8",
        "fg2":          "#5a8a68",
        "fg_label":     "#90c8a0",
        "accent":       "#40b060",
        "ok":           "#70d080",
        "error":        "#e06060",
        "warning":      "#c8a030",
        "info":         "#40b060",
        "btn_start_bg": "#1a5a28",
        "btn_start_fg": "#ffffff",
        "btn_pause_bg": "#7a6010",
        "btn_pause_fg": "#ffffff",
        "btn_stop_bg":  "#6a1818",
        "btn_stop_fg":  "#ffffff",
        "btn_misc_bg":  "#102018",
        "btn_misc_fg":  "#90c8a0",
        "btn_acc_bg":   "#1a6030",
        "btn_acc_fg":   "#ffffff",
        "progress":     "#40b060",
        "trough":       "#102018",
        "border":       "#204830",
        "theme_btn_fg": "#5a8a68",
        "list_sel":     "#1a4828",
        "list_hover":   "#0e1a12",
        "tag_pending":  "#5a8a68",
        "tag_ok":       "#70d080",
        "tag_nofile":   "#c8a030",
        "tag_error":    "#e06060",
        "tag_active":   "#40b060",
    },
    "marron": {
        "bg":           "#1a1208",
        "bg2":          "#271a0c",
        "bg3":          "#110c04",
        "bg_panel":     "#201408",
        "fg":           "#f0e0c8",
        "fg2":          "#907050",
        "fg_label":     "#c8a878",
        "accent":       "#c88040",
        "ok":           "#90c060",
        "error":        "#e06060",
        "warning":      "#e8b040",
        "info":         "#c88040",
        "btn_start_bg": "#285020",
        "btn_start_fg": "#ffffff",
        "btn_pause_bg": "#806020",
        "btn_pause_fg": "#ffffff",
        "btn_stop_bg":  "#702018",
        "btn_stop_fg":  "#ffffff",
        "btn_misc_bg":  "#271a0c",
        "btn_misc_fg":  "#c8a878",
        "btn_acc_bg":   "#804820",
        "btn_acc_fg":   "#ffffff",
        "progress":     "#c88040",
        "trough":       "#271a0c",
        "border":       "#503818",
        "theme_btn_fg": "#907050",
        "list_sel":     "#4a3018",
        "list_hover":   "#201408",
        "tag_pending":  "#907050",
        "tag_ok":       "#90c060",
        "tag_nofile":   "#e8b040",
        "tag_error":    "#e06060",
        "tag_active":   "#c88040",
    },
}

THEME_LABELS = {
    "dark":   "🌑 Oscuro",
    "light":  "☀️ Claro",
    "bordo":  "🍷 Bordo",
    "verde":  "🌿 Verde",
    "marron": "🪵 Marrón",
}
THEME_COLORS = {
    "dark":   "#7aa2f7",
    "light":  "#3b6fd4",
    "bordo":  "#e05070",
    "verde":  "#40b060",
    "marron": "#c88040",
}

# Manual sections
MANUAL_SECTIONS = [
    {
        "title": "📋  Formato del Excel",
        "img":   "01_pantalla_principal.png",
        "text":  (
            "El archivo Excel debe tener una columna llamada exactamente TradeId "
            "(respetando mayúsculas). Cada fila debe contener un ID en el formato "
            "T123456-01 (letra T, 6 dígitos, guión, 2 dígitos).\n\n"
            "Ejemplo válido:\n"
            "  T004521-01\n"
            "  T106729-01\n"
            "  T003513-01\n\n"
            "Podés tener otras columnas en el Excel — el extractor solo lee TradeId."
        ),
    },
    {
        "title": "📂  Cargar Excel y carpeta",
        "img":   "03_cargar_excel.png",
        "text":  (
            "1. Click en Buscar... para seleccionar tu archivo Excel con los IDs.\n"
            "2. Click en Cambiar... para elegir la carpeta donde se guardarán los archivos descargados.\n\n"
            "La app recuerda ambas rutas entre sesiones — no necesitás configurarlas cada vez."
        ),
    },
    {
        "title": "⚙️  Tipo de archivo y filtro",
        "img":   "05_tipo_y_filtro.png",
        "text":  (
            "Descargar:\n"
            "  • Solo PDF — descarga únicamente archivos .pdf\n"
            "  • Solo XLSX — descarga únicamente archivos .xlsx / .xls\n"
            "  • Todos — descarga cualquier tipo de archivo\n\n"
            "Filtro:\n"
            "  • Match ID — solo archivos cuyo nombre contiene el ID del trade (default)\n"
            "  • Todos — descarga todos los archivos del trade sin filtrar\n"
            "  • Palabra clave — solo archivos que contengan la palabra escrita en el campo\n\n"
            "Ambos filtros se aplican en simultáneo."
        ),
    },
    {
        "title": "▶️  Iniciar, Pausar y Detener",
        "img":   "07_pausar_reanudar.png",
        "text":  (
            "Iniciar — comienza el proceso de descarga con los IDs del Excel.\n\n"
            "Pausar — pausa el proceso después de terminar el trade actual. "
            "El botón cambia a Reanudar. Click de nuevo para continuar.\n\n"
            "Detener — detiene el proceso completamente después del trade actual. "
            "Al volver a Iniciar, retoma desde donde quedó (los ya descargados se saltean).\n\n"
            "La sesión de Chrome se abre automáticamente. Si pide login, "
            "ingresá tus credenciales manualmente — el script espera hasta que estés dentro."
        ),
    },
    {
        "title": "✏️  Editor de IDs",
        "img":   "08_editor_ids.png",
        "text":  (
            "Click en Editar IDs para abrir el panel de edición.\n\n"
            "  • Agregar — escribí un ID en el campo y presioná Enter o click en + Agregar. "
            "El sistema detecta duplicados automáticamente.\n"
            "  • Eliminar — seleccioná un ID de la lista y click en Eliminar seleccionado.\n"
            "  • Guardar en Excel — guarda los cambios en el archivo Excel. "
            "Los cambios se reflejan en la próxima ejecución, no en la corrida actual.\n\n"
            "El panel se puede abrir y cerrar sin interrumpir el proceso."
        ),
    },
    {
        "title": "❌  Errores comunes",
        "img":   "09_errores_comunes.png",
        "text":  (
            "Timeout / Trade no encontrado\n"
            "  El ID no existe en PMP o la página tardó demasiado. "
            "El script reintenta 3 veces automáticamente.\n\n"
            "ERR_NETWORK_CHANGED\n"
            "  Se cortó la conexión a internet. El script reintenta en 5 segundos. "
            "Si falla 3 veces, marca el trade como Error y continúa con el siguiente.\n\n"
            "Sin archivos / Sin PDFs\n"
            "  El trade existe pero no tiene archivos del tipo solicitado. "
            "Cambiá el filtro de tipo o verificá manualmente en PMP.\n\n"
            "Chrome no abre\n"
            "  Cerrá Chrome completamente (incluso desde el administrador de tareas) y volvé a intentar."
        ),
    },
    {
        "title": "📊  Resumen y Logs",
        "img":   "10_resumen_final.png",
        "text":  (
            "Al finalizar cada corrida, el log muestra un resumen con:\n"
            "  • Exitosos — trades descargados correctamente\n"
            "  • Con error — trades que fallaron después de 3 intentos\n"
            "  • PDFs descargados — total de archivos guardados\n\n"
            "Un archivo Excel con el detalle se guarda automáticamente en:\n"
            "  Extractor/Logs/log_descargas_YYYYMMDD_HHMMSS.xlsx\n\n"
            "Podés revisar los logs anteriores en esa carpeta para ver el historial de descargas."
        ),
    },
]

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
        self.root.minsize(900, 580)
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
        self.theme_name   = cfg.get("theme", "dark")

        # Trade list: {trade_id: estado}
        self.trades_estado = {}
        self.all_ids       = []

        self._editor_labels = []
        self.file_type   = tk.StringVar(value=cfg.get("file_type", "pdf"))
        self.filter_mode   = tk.StringVar(value=cfg.get("filter_mode", "id"))
        self.keyword       = tk.StringVar(value=cfg.get("keyword", ""))
        self.turbo_workers = tk.IntVar(value=cfg.get("turbo_workers", 1))
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

        # Logo + nombre izquierda
        brand = tk.Frame(self.header)
        brand.grid(row=0, column=0, sticky="w", padx=16)

        self.logo_label = tk.Label(brand)
        self.logo_label.pack(side="left", padx=(0, 10))
        self._load_logo()

        brand_text = tk.Frame(brand)
        brand_text.pack(side="left")
        self.lbl_brand = tk.Label(brand_text, text="Extractor de Trades",
                                  font=("Segoe UI", 12, "bold"))
        self.lbl_brand.pack(anchor="w")
        self.lbl_sub = tk.Label(brand_text, text="PMP Portfolio Management Platform",
                                font=("Segoe UI", 8))
        self.lbl_sub.pack(anchor="w")

        # Botón tema derecha
        # Manual button top-right
        self.btn_manual = tk.Button(self.header, text="❓  Manual",
                                    font=("Segoe UI", 9), relief="flat",
                                    cursor="hand2", bd=0, padx=12, pady=6,
                                    command=self._toggle_manual)
        self.btn_manual.grid(row=0, column=2, sticky="e", padx=16)
        self.manual_visible = False

        # Theme frame (placeholder, circles added in _build_theme_circles)
        self.theme_frame = tk.Frame(self.header)
        self.theme_buttons = {}

        # Título centro (invisible, solo para balance)
        self.lbl_title = tk.Label(self.header, text="",
                                  font=("Segoe UI", 15, "bold"))
        self.lbl_title.grid(row=0, column=1)

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
        # Only log row expands, everything else is fixed height
        self.left.rowconfigure(0, weight=0)  # excel label
        self.left.rowconfigure(1, weight=0)  # excel input
        self.left.rowconfigure(2, weight=0)  # dest label
        self.left.rowconfigure(3, weight=0)  # dest input
        self.left.rowconfigure(4, weight=0)  # file type
        self.left.rowconfigure(5, weight=0)  # filter
        self.left.rowconfigure(6, weight=0)  # turbo
        self.left.rowconfigure(7, weight=0)  # log label
        self.left.rowconfigure(8, weight=1)  # log (expands)

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
        self.entry_excel.grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, 8))
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
        self.entry_dest.grid(row=0, column=0, sticky="ew", ipady=5, padx=(0, 8))
        self.btn_dest = tk.Button(row_dest, text="Cambiar...",
                                  font=("Segoe UI", 10), relief="flat",
                                  cursor="hand2", command=self._seleccionar_carpeta,
                                  padx=14, pady=5)
        self.btn_dest.grid(row=0, column=1)

        # Tipo de archivo
        frame_tipo = tk.Frame(self.left)
        frame_tipo.grid(row=4, column=0, sticky="ew", pady=(4, 2))
        self.frame_tipo = frame_tipo

        # Compact single row: label + radios inline
        self.lbl_tipo = tk.Label(frame_tipo, text="Descargar:",
                                 font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_tipo.pack(side="left", padx=(0, 10))

        radio_row = tk.Frame(frame_tipo)
        radio_row.pack(side="left", anchor="w")
        self.radio_row = radio_row

        self.rb_pdf = tk.Radiobutton(radio_row, text="Solo PDF",
                                     variable=self.file_type, value="pdf",
                                     font=("Segoe UI", 10),
                                     command=self._save_config)
        self.rb_pdf.pack(side="left", padx=(0, 12))

        self.rb_xlsx = tk.Radiobutton(radio_row, text="Solo XLSX",
                                      variable=self.file_type, value="xlsx",
                                      font=("Segoe UI", 10),
                                      command=self._save_config)
        self.rb_xlsx.pack(side="left", padx=(0, 12))

        self.rb_all = tk.Radiobutton(radio_row, text="Todos",
                                     variable=self.file_type, value="all",
                                     font=("Segoe UI", 10),
                                     command=self._save_config)
        self.rb_all.pack(side="left")

        # Filtro de archivos
        frame_filtro = tk.Frame(self.left)
        frame_filtro.grid(row=5, column=0, sticky="ew", pady=(4, 2))
        self.frame_filtro = frame_filtro

        self.lbl_filtro = tk.Label(frame_filtro, text="Filtro:",
                                   font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_filtro.pack(side="left", padx=(0, 10))

        filtro_row = tk.Frame(frame_filtro)
        filtro_row.pack(side="left", anchor="w", fill="x", expand=True)
        self.filtro_row = filtro_row

        self.rb_id = tk.Radiobutton(filtro_row, text="Match ID",
                                    variable=self.filter_mode, value="id",
                                    font=("Segoe UI", 10),
                                    command=self._on_filter_change)
        self.rb_id.pack(side="left", padx=(0, 12))

        self.rb_all_files = tk.Radiobutton(filtro_row, text="Todos",
                                           variable=self.filter_mode, value="all",
                                           font=("Segoe UI", 10),
                                           command=self._on_filter_change)
        self.rb_all_files.pack(side="left", padx=(0, 12))

        self.rb_keyword = tk.Radiobutton(filtro_row, text="Palabra clave:",
                                         variable=self.filter_mode, value="keyword",
                                         font=("Segoe UI", 10),
                                         command=self._on_filter_change)
        self.rb_keyword.pack(side="left", padx=(0, 6))

        self.entry_keyword = tk.Entry(filtro_row, textvariable=self.keyword,
                                      font=("Segoe UI", 10), relief="flat",
                                      bd=0, highlightthickness=1, width=14)
        self.entry_keyword.pack(side="left", ipady=4)
        self.entry_keyword.bind("<KeyRelease>", lambda e: self._save_config())

        # Modo turbo
        frame_turbo = tk.Frame(self.left)
        frame_turbo.grid(row=6, column=0, sticky="ew", pady=(4, 2))
        self.frame_turbo = frame_turbo

        self.lbl_turbo = tk.Label(frame_turbo, text="Modo turbo:",
                                  font=("Segoe UI", 10, "bold"), anchor="w")
        self.lbl_turbo.pack(side="left", padx=(0, 10))

        turbo_row = tk.Frame(frame_turbo)
        turbo_row.pack(side="left", anchor="w")
        self.turbo_row = turbo_row

        for val, label in [(1, "1x  (normal)"), (2, "2x"), (3, "3x")]:
            rb = tk.Radiobutton(turbo_row, text=label,
                                variable=self.turbo_workers, value=val,
                                font=("Segoe UI", 10),
                                command=self._save_config)
            rb.pack(side="left", padx=(0, 12))
            if not hasattr(self, '_turbo_rbs'):
                self._turbo_rbs = []
            self._turbo_rbs.append(rb)

        self.lbl_turbo_warn = tk.Label(frame_turbo,
                                       text="⚠️ experimental",
                                       font=("Segoe UI", 8))
        self.lbl_turbo_warn.pack(side="left", padx=(4, 0))

        # Log
        self.lbl_log = tk.Label(self.left, text="Log de actividad:",
                                font=("Segoe UI", 9), anchor="w")
        self.lbl_log.grid(row=7, column=0, sticky="w")
        self.log = scrolledtext.ScrolledText(self.left, font=("Consolas", 9),
                                             relief="flat", bd=0,
                                             state="disabled", wrap="word")
        self.log.grid(row=8, column=0, sticky="nsew", pady=(4, 0))
        self.left.rowconfigure(8, weight=1)

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

        # Theme circles
        self.circles_frame = tk.Frame(self.right)
        self.circles_frame.grid(row=5, column=0, sticky="e", pady=(8, 2))
        self._build_theme_circles()

        # Manual panel
        self.frame_manual = tk.Frame(self.body)
        self.frame_manual.columnconfigure(0, weight=1)
        self.frame_manual.rowconfigure(1, weight=1)

        lbl_manual_title = tk.Label(self.frame_manual,
                                    text="📖  Manual de uso",
                                    font=("Segoe UI", 11, "bold"), anchor="w")
        lbl_manual_title.grid(row=0, column=0, sticky="w", pady=(4, 6))
        self._manual_header_labels = [lbl_manual_title]

        # Scrollable content
        manual_canvas = tk.Canvas(self.frame_manual, highlightthickness=0)
        manual_canvas.grid(row=1, column=0, sticky="nsew")
        manual_sb = ttk.Scrollbar(self.frame_manual, orient="vertical",
                                   command=manual_canvas.yview)
        manual_sb.grid(row=1, column=1, sticky="ns")
        manual_canvas.configure(yscrollcommand=manual_sb.set)

        self.manual_inner = tk.Frame(manual_canvas)
        self.manual_window = manual_canvas.create_window((0, 0), window=self.manual_inner,
                                                          anchor="nw")
        self.manual_canvas = manual_canvas
        self.manual_inner.bind("<Configure>",
                               lambda e: manual_canvas.configure(
                                   scrollregion=manual_canvas.bbox("all")))
        manual_canvas.bind("<Configure>",
                           lambda e: manual_canvas.itemconfig(
                               self.manual_window, width=e.width))

        # Bind mousewheel
        def _on_mousewheel(e):
            manual_canvas.yview_scroll(int(-1*(e.delta/120)), "units")
        manual_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.manual_inner.bind("<MouseWheel>", _on_mousewheel)

        # Build sections
        self._manual_section_frames = []
        self._manual_section_title_labels = []
        self._manual_section_text_labels = []
        self._manual_img_labels = []
        self._manual_img_refs = []

        for sec in MANUAL_SECTIONS:
            sec_frame = tk.Frame(self.manual_inner, pady=8)
            sec_frame.pack(fill="x", padx=8)
            self._manual_section_frames.append(sec_frame)

            # Separator line
            sep = tk.Frame(sec_frame, height=1)
            sep.pack(fill="x", pady=(0, 6))
            self._manual_section_frames.append(sep)

            # Title
            t_lbl = tk.Label(sec_frame, text=sec["title"],
                             font=("Segoe UI", 10, "bold"), anchor="w",
                             wraplength=320, justify="left")
            t_lbl.pack(anchor="w")
            self._manual_section_title_labels.append(t_lbl)

            # Image placeholder
            img_path = APP_DIR / "Capturas_manual" / sec["img"]
            img_lbl = tk.Label(sec_frame, anchor="w")
            img_lbl.pack(anchor="w", pady=(4, 4))
            self._manual_img_labels.append(img_lbl)
            self._manual_img_refs.append(None)
            if img_path.exists() and PIL_AVAILABLE:
                try:
                    img = Image.open(img_path)
                    img.thumbnail((320, 200), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_lbl.config(image=photo)
                    self._manual_img_refs[-1] = photo
                except Exception:
                    pass

            # Text
            txt_lbl = tk.Label(sec_frame, text=sec["text"],
                               font=("Segoe UI", 9), anchor="w",
                               wraplength=320, justify="left")
            txt_lbl.pack(anchor="w", pady=(2, 0))
            self._manual_section_text_labels.append(txt_lbl)

        # Editor panel
        self.editor_visible = False
        self.frame_editor = tk.Frame(self.body)
        self.frame_editor.columnconfigure(0, weight=1)
        self.frame_editor.rowconfigure(1, weight=1)

        lbl_editor = tk.Label(self.frame_editor, text="Editor de IDs",
                              font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_editor.grid(row=0, column=0, sticky="w", pady=(4, 4))
        self._editor_labels.append(lbl_editor)

        list_edit_frame = tk.Frame(self.frame_editor)
        list_edit_frame.grid(row=1, column=0, sticky="nsew")
        list_edit_frame.columnconfigure(0, weight=1)
        list_edit_frame.rowconfigure(0, weight=1)
        self.listbox_editor = tk.Listbox(list_edit_frame, font=("Consolas", 9),
                                         relief="flat", bd=0, selectmode="browse",
                                         activestyle="none")
        self.listbox_editor.grid(row=0, column=0, sticky="nsew")
        sb_editor = ttk.Scrollbar(list_edit_frame, orient="vertical",
                                  command=self.listbox_editor.yview)
        sb_editor.grid(row=0, column=1, sticky="ns")
        self.listbox_editor.configure(yscrollcommand=sb_editor.set)

        row_add = tk.Frame(self.frame_editor)
        row_add.grid(row=2, column=0, sticky="ew", pady=(8, 4))
        row_add.columnconfigure(0, weight=1)
        self.entry_new_id = tk.Entry(row_add, font=("Segoe UI", 10),
                                     relief="flat", bd=0, highlightthickness=1)
        self.entry_new_id.grid(row=0, column=0, sticky="ew", ipady=6, padx=(0, 6))
        self.entry_new_id.bind("<Return>", lambda e: self._editor_agregar())
        self.btn_add_id = tk.Button(row_add, text="+ Agregar",
                                    font=("Segoe UI", 10), relief="flat",
                                    cursor="hand2", padx=10, pady=5,
                                    command=self._editor_agregar)
        self.btn_add_id.grid(row=0, column=1)

        row_edit_btns = tk.Frame(self.frame_editor)
        row_edit_btns.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        self.btn_del_id = tk.Button(row_edit_btns, text="Eliminar seleccionado",
                                    font=("Segoe UI", 10), relief="flat",
                                    cursor="hand2", padx=10, pady=6,
                                    command=self._editor_eliminar)
        self.btn_del_id.pack(side="left", padx=(0, 6))
        self.btn_save_ids = tk.Button(row_edit_btns, text="Guardar en Excel",
                                      font=("Segoe UI", 10, "bold"), relief="flat",
                                      cursor="hand2", padx=10, pady=6,
                                      command=self._editor_guardar)
        self.btn_save_ids.pack(side="right")

        self.lbl_editor_status = tk.Label(self.frame_editor, text="",
                                          font=("Segoe UI", 8), anchor="w")
        self.lbl_editor_status.grid(row=4, column=0, sticky="w")

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
                                   padx=16, pady=7, state="disabled",
                                   disabledforeground="#ffffff")
        self.btn_pause.pack(side="left", padx=(0, 6))

        self.btn_stop = tk.Button(self.frame_btns, text="⏹  Detener",
                                  font=("Segoe UI", 10), relief="flat",
                                  cursor="hand2", command=self._detener,
                                  padx=16, pady=7, state="disabled",
                                  disabledforeground="#ffffff")
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

        self.btn_editor = tk.Button(self.frame_btns, text="✏️  Editar IDs",
                                    font=("Segoe UI", 10), relief="flat",
                                    cursor="hand2", command=self._toggle_editor,
                                    padx=12, pady=7)
        self.btn_editor.pack(side="right", padx=(0, 6))

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
        self.status = tk.Label(self.root,
                               text=f"Extractor {VERSION}  —  {AUTHOR}  |  Listo",
                               font=("Segoe UI", 8), anchor="w", padx=14, pady=3)
        self.status.grid(row=3, column=0, sticky="ew")
        self.root.rowconfigure(3, weight=0)

    def _toggle_editor(self):
        if not self.editor_visible:
            # Close manual if open
            if self.manual_visible:
                self._toggle_manual()
            self.body.columnconfigure(2, weight=2)
            self.frame_editor.grid(row=0, column=2, sticky="nsew", padx=(6, 14), pady=6)
            self.frame_editor.rowconfigure(1, weight=1)
            self._editor_cargar()
            self.btn_editor.config(text="Cerrar editor")
            self.editor_visible = True
        else:
            self.frame_editor.grid_remove()
            self.btn_editor.config(text="Editar IDs")
            self.editor_visible = False

    def _editor_cargar(self):
        self.listbox_editor.delete(0, "end")
        excel = self.excel_path.get()
        if not excel or not Path(excel).exists():
            self.lbl_editor_status.config(text="Carga un Excel primero.")
            return
        try:
            df = pd.read_excel(excel)
            if COLUMNA_IDS not in df.columns:
                self.lbl_editor_status.config(text=f"Columna {COLUMNA_IDS} no encontrada.")
                return
            ids = df[COLUMNA_IDS].dropna().astype(str).str.strip().tolist()
            for id_ in ids:
                self.listbox_editor.insert("end", f"  {id_}")
            self.lbl_editor_status.config(text=f"{len(ids)} IDs cargados.")
        except Exception as e:
            self.lbl_editor_status.config(text=f"Error: {e}")

    def _editor_agregar(self):
        new_id = self.entry_new_id.get().strip()
        if not new_id:
            return
        existing = [self.listbox_editor.get(i).strip() for i in range(self.listbox_editor.size())]
        if new_id in existing:
            self.lbl_editor_status.config(text=f"'{new_id}' ya existe.")
            return
        self.listbox_editor.insert("end", f"  {new_id}")
        self.entry_new_id.delete(0, "end")
        self.lbl_editor_status.config(text=f"'{new_id}' agregado. Total: {self.listbox_editor.size()}")

    def _editor_eliminar(self):
        sel = self.listbox_editor.curselection()
        if not sel:
            self.lbl_editor_status.config(text="Selecciona un ID para eliminar.")
            return
        id_text = self.listbox_editor.get(sel[0]).strip()
        self.listbox_editor.delete(sel[0])
        self.lbl_editor_status.config(text=f"'{id_text}' eliminado. Total: {self.listbox_editor.size()}")

    def _editor_guardar(self):
        excel = self.excel_path.get()
        if not excel or not Path(excel).exists():
            self.lbl_editor_status.config(text="No hay Excel seleccionado.")
            return
        try:
            ids = [self.listbox_editor.get(i).strip() for i in range(self.listbox_editor.size())]
            ids = [id_ for id_ in ids if id_]
            df = pd.read_excel(excel)
            df_new = pd.DataFrame({COLUMNA_IDS: ids})
            for col in df.columns:
                if col != COLUMNA_IDS:
                    df_new[col] = df[col].reindex(df_new.index)
            df_new.to_excel(excel, index=False)
            self.lbl_editor_status.config(text=f"Guardado — {len(ids)} IDs en {Path(excel).name}")
            if self.all_ids:
                self.all_ids = ids
                self.trades_estado = {id_: self.trades_estado.get(id_, ESTADO_PENDIENTE) for id_ in ids}
                self._refresh_list()
        except Exception as e:
            self.lbl_editor_status.config(text=f"Error guardando: {e}")


    # ── LOGO ─────────────────────────────────────────────────

    def _load_logo(self):
        try:
            if not PIL_AVAILABLE:
                return
            logo_path = APP_DIR / "logo.png"
            if not logo_path.exists():
                return
            img = Image.open(logo_path)
            img = img.resize((56, 56), Image.LANCZOS)
            self._logo_img = ImageTk.PhotoImage(img)
            self.logo_label.config(image=self._logo_img)
        except Exception:
            pass

    # ── THEME ────────────────────────────────────────────────

    def _set_theme(self, name):
        self.theme_name = name
        self._apply_theme()
        self._save_config()

    def _build_theme_circles(self):
        for w in self.circles_frame.winfo_children():
            w.destroy()
        self.theme_buttons = {}
        for t_name in ["dark", "light", "bordo", "verde", "marron"]:
            color = THEME_COLORS[t_name]
            is_active = t_name == self.theme_name
            size = 22 if is_active else 18
            canvas = tk.Canvas(self.circles_frame, width=size, height=size,
                               highlightthickness=0, cursor="hand2")
            canvas.pack(side="left", padx=3)
            # Outer ring if active
            if is_active:
                canvas.create_oval(1, 1, size-1, size-1,
                                   fill=color, outline="white", width=2)
            else:
                canvas.create_oval(2, 2, size-2, size-2,
                                   fill=color, outline="")
            canvas.bind("<Button-1>", lambda e, n=t_name: self._set_theme(n))
            canvas.bind("<Enter>", lambda e, c=canvas, col=color:
                        c.config(cursor="hand2"))
            self.theme_buttons[t_name] = canvas

    def _toggle_manual(self):
        if not self.manual_visible:
            # Close editor if open
            if self.editor_visible:
                self._toggle_editor()
            self.body.columnconfigure(2, weight=2)
            self.frame_manual.grid(row=0, column=2, sticky="nsew",
                                   padx=(6, 14), pady=6)
            self.frame_manual.rowconfigure(1, weight=1)
            self.btn_manual.config(text="✕  Cerrar manual")
            self.manual_visible = True
        else:
            self.frame_manual.grid_remove()
            self.btn_manual.config(text="❓  Manual")
            self.manual_visible = False

    def _apply_theme(self):
        t = THEMES[self.theme_name]
        icon = "🌙  Modo oscuro" if self.theme_name == "light" else "☀️  Modo claro"

        self.root.configure(bg=t["bg"])
        self.body.configure(bg=t["bg"])

        # Header
        self.header.configure(bg=t["bg2"])
        for w in self.header.winfo_children():
            if isinstance(w, tk.Frame):
                w.configure(bg=t["bg2"])
                for ww in w.winfo_children():
                    if isinstance(ww, tk.Frame):
                        ww.configure(bg=t["bg2"])
                    if isinstance(ww, tk.Label):
                        ww.configure(bg=t["bg2"])
        self.logo_label.configure(bg=t["bg2"])
        self.lbl_brand.configure(bg=t["bg2"], fg=t["fg"])
        self.lbl_sub.configure(bg=t["bg2"], fg=t["fg2"])
        self.lbl_title.configure(bg=t["bg2"], fg=t["fg"])
        self._build_theme_circles()
        # Update circles background
        for canvas in self.circles_frame.winfo_children():
            canvas.configure(bg=t["bg2"])
        self.circles_frame.configure(bg=t["bg"])

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
                                 activeforeground=t["btn_pause_fg"],
                                 disabledforeground="#ffffff")
        self.btn_stop.configure(bg=t["btn_stop_bg"], fg=t["btn_stop_fg"],
                                activebackground=t["btn_stop_bg"],
                                activeforeground=t["btn_stop_fg"],
                                disabledforeground="#ffffff")
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

        # Radio buttons - tipo archivo
        if hasattr(self, "frame_tipo"):
            self.frame_tipo.configure(bg=t["bg"])
            self.lbl_tipo.configure(bg=t["bg"], fg=t["fg_label"])
            self.radio_row.configure(bg=t["bg"])
            for rb in [self.rb_pdf, self.rb_xlsx, self.rb_all]:
                rb.configure(bg=t["bg"], fg=t["fg"],
                             selectcolor=t["bg2"],
                             activebackground=t["bg"],
                             activeforeground=t["fg"])

        # Turbo
        if hasattr(self, "frame_turbo"):
            self.frame_turbo.configure(bg=t["bg"])
            self.lbl_turbo.configure(bg=t["bg"], fg=t["fg_label"])
            self.turbo_row.configure(bg=t["bg"])
            self.lbl_turbo_warn.configure(bg=t["bg"], fg=t["warning"])
            if hasattr(self, "_turbo_rbs"):
                for rb in self._turbo_rbs:
                    rb.configure(bg=t["bg"], fg=t["fg"],
                                 selectcolor=t["bg2"],
                                 activebackground=t["bg"],
                                 activeforeground=t["fg"])

        # Radio buttons - filtro
        if hasattr(self, "frame_filtro"):
            self.frame_filtro.configure(bg=t["bg"])
            self.lbl_filtro.configure(bg=t["bg"], fg=t["fg_label"])
            self.filtro_row.configure(bg=t["bg"])
            for rb in [self.rb_id, self.rb_all_files, self.rb_keyword]:
                rb.configure(bg=t["bg"], fg=t["fg"],
                             selectcolor=t["bg2"],
                             activebackground=t["bg"],
                             activeforeground=t["fg"])
            self.entry_keyword.configure(bg=t["bg3"], fg=t["fg"],
                                         insertbackground=t["fg"],
                                         highlightbackground=t["border"],
                                         highlightcolor=t["accent"])
        if hasattr(self, "frame_editor"):
            self.frame_editor.configure(bg=t["bg"])
            for lbl in self._editor_labels:
                lbl.configure(bg=t["bg"], fg=t["fg_label"])
            self.listbox_editor.configure(bg=t["bg_panel"], fg=t["fg"],
                                          selectbackground=t["list_sel"])
            self.listbox_editor.master.configure(bg=t["bg"])
            self.entry_new_id.configure(bg=t["bg3"], fg=t["fg"],
                                        insertbackground=t["fg"],
                                        highlightbackground=t["border"],
                                        highlightcolor=t["accent"])
            self.entry_new_id.master.configure(bg=t["bg"])
            self.btn_add_id.configure(bg=t["btn_start_bg"], fg=t["btn_start_fg"])
            self.btn_del_id.configure(bg=t["btn_stop_bg"], fg=t["btn_stop_fg"])
            self.btn_save_ids.configure(bg=t["btn_acc_bg"], fg=t["btn_acc_fg"])
            self.lbl_editor_status.configure(bg=t["bg"], fg=t["fg2"])
            for w in self.frame_editor.winfo_children():
                if isinstance(w, tk.Frame):
                    w.configure(bg=t["bg"])
        if hasattr(self, "btn_editor"):
            self.btn_editor.configure(bg=t["btn_misc_bg"], fg=t["btn_misc_fg"])

        # Refresh list colors
        self._refresh_list()

    # ── TRADE LIST ───────────────────────────────────────────

    def _cargar_trades(self, ids):
        """Inicializa la lista verificando archivos reales en la carpeta de descarga."""
        self.all_ids = ids
        self.trades_estado = {id_: ESTADO_PENDIENTE for id_ in ids}
        # Verificar qué IDs ya tienen archivo en la carpeta de destino
        carpeta = Path(self.carpeta_dest.get())
        file_type_c = self.file_type.get()
        keyword_c   = self.keyword.get().strip().lower()
        filter_c    = self.filter_mode.get()
        if carpeta.exists():
            archivos = [f.name for f in carpeta.iterdir() if f.is_file()]
            for id_ in ids:
                archivos_id = [n for n in archivos if id_ in n]
                if not archivos_id:
                    continue
                if file_type_c == "pdf":
                    match = any(n.lower().endswith(".pdf") for n in archivos_id)
                elif file_type_c == "xlsx":
                    match = any(n.lower().endswith((".xlsx", ".xls")) for n in archivos_id)
                else:
                    match = False  # "all" mode: check file by file
                if match and filter_c == "keyword" and keyword_c:
                    match = any(keyword_c in n.lower() for n in archivos_id)
                if match:
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

    def _on_filter_change(self):
        # Enable/disable keyword entry based on mode
        if self.filter_mode.get() == "keyword":
            self.entry_keyword.config(state="normal")
            self.entry_keyword.focus()
        else:
            self.entry_keyword.config(state="disabled")
        self._save_config()

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
                "theme":        self.theme_name,
                "file_type":    self.file_type.get(),
                "filter_mode":   self.filter_mode.get(),
                "keyword":       self.keyword.get(),
                "turbo_workers": self.turbo_workers.get(),
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
        self.status.config(text=f"Extractor {VERSION}  —  {AUTHOR}  |  Ejecutando...")
        threading.Thread(target=self._run_async, daemon=True).start()

    def _pausar(self):
        if not self.paused:
            self.paused = True
            self._pause_event.clear()
            self.btn_pause.config(text="▶  Reanudar")
            self._log("⏸  Pausado — hacé click en Reanudar para continuar.", "warning")
            self.status.config(text=f"Extractor {VERSION}  —  {AUTHOR}  |  Pausado")
        else:
            self.paused = False
            self._pause_event.set()
            self.btn_pause.config(text="⏸  Pausar")
            self._log("▶  Reanudando...", "ok")
            self.status.config(text=f"Extractor {VERSION}  —  {AUTHOR}  |  Ejecutando...")

    def _detener(self):
        self.running = False
        self._pause_event.set()
        self._log("⏹  Deteniendo... (termina el trade actual)", "warning")
        self.status.config(text=f"Extractor {VERSION}  —  {AUTHOR}  |  Deteniendo...")

    def _run_async(self):
        asyncio.run(self._extraer())

    def _finalizar_ui(self):
        self.running = False
        self.paused  = False
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled", text="⏸  Pausar")
        self.btn_stop.config(state="disabled")
        self.status.config(text=f"Extractor {VERSION}  —  {AUTHOR}  |  Listo")

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
        file_type_check = self.file_type.get()
        filter_mode_check = self.filter_mode.get()
        keyword_check = self.keyword.get().strip().lower()

        if carpeta_check.exists():
            archivos_existentes = [f.name for f in carpeta_check.iterdir() if f.is_file()]
            for id_ in ids:
                archivos_id = [n for n in archivos_existentes if id_ in n]
                if not archivos_id:
                    continue
                # Filter by type to check if the right type already exists
                if file_type_check == "pdf":
                    match = any(n.lower().endswith(".pdf") for n in archivos_id)
                elif file_type_check == "xlsx":
                    match = any(n.lower().endswith((".xlsx", ".xls")) for n in archivos_id)
                else:
                    # "all" mode: never skip the trade, check file by file during download
                    match = False
                # Also consider keyword filter
                if match and filter_mode_check == "keyword" and keyword_check:
                    match = any(keyword_check in n.lower() for n in archivos_id)
                if match:
                    ya_descargados.add(id_)
        if ya_descargados:
            self._log(f"   → {len(ya_descargados)} ya tienen archivo del tipo requerido, se saltean...", "info")

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

            workers = self.turbo_workers.get()
            processed = 0
            results_lock = asyncio.Lock()

            async def _worker(worker_id, trade_id, page_w, trade_idx):
                nonlocal processed
                self._log(f"[{trade_idx}/{total}] [{worker_id}x] Procesando: {trade_id}", "info")
                self._set_estado(trade_id, "Procesando")
                exito = False
                for intento in range(1, MAX_REINTENTOS + 1):
                    try:
                        archivos, estado = await self._procesar_trade(page_w, trade_id, carpeta)
                        async with results_lock:
                            resultados.append({"ID": trade_id, "Estado": estado, "Archivos": archivos})
                            processed += 1
                        self._set_estado(trade_id, estado)
                        self.root.after(0, lambda v=trade_idx, m=total, t=trade_id:
                                        self._set_progress(v, m, f"Procesando {t}  ({v}/{m})"))
                        exito = True
                        break
                    except Exception as e:
                        self._log(f"   ⚠️  [{worker_id}x] Intento {intento}/{MAX_REINTENTOS}: {e}", "warning")
                        if intento < MAX_REINTENTOS:
                            self._log("   🔄 Reintentando en 5s...", "warning")
                            await asyncio.sleep(5)
                            try:
                                await page_w.goto(URL_TRADES)
                                await page_w.wait_for_load_state("networkidle")
                            except Exception:
                                pass
                if not exito:
                    self._log(f"   ❌ [{worker_id}x] Falló: {trade_id}", "error")
                    self._set_estado(trade_id, ESTADO_ERROR)
                    async with results_lock:
                        resultados.append({"ID": trade_id, "Estado": ESTADO_ERROR, "Archivos": 0})
                        processed += 1

            if workers == 1:
                # Modo normal — una sola página
                for i, trade_id in enumerate(ids_pendientes, 1):
                    if not self.running:
                        break
                    self._pause_event.wait()
                    if not self.running:
                        break
                    await _worker(1, trade_id, page, i)
            else:
                # Modo turbo — múltiples páginas en paralelo
                self._log(f"⚡ Modo turbo {workers}x activado", "info")
                extra_pages = []
                for _ in range(workers - 1):
                    p = await context.new_page()
                    await p.goto(URL_TRADES)
                    await p.wait_for_load_state("networkidle")
                    extra_pages.append(p)
                all_pages = [page] + extra_pages

                # Procesar en tandas de N
                for batch_start in range(0, len(ids_pendientes), workers):
                    if not self.running:
                        break
                    self._pause_event.wait()
                    if not self.running:
                        break
                    batch = ids_pendientes[batch_start:batch_start + workers]
                    tasks = [
                        _worker(idx + 1, tid, all_pages[idx], batch_start + idx + 1)
                        for idx, tid in enumerate(batch)
                    ]
                    await asyncio.gather(*tasks)

                for p in extra_pages:
                    try:
                        await p.close()
                    except Exception:
                        pass

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
            LOGS_DIR.mkdir(exist_ok=True)
            log_path = LOGS_DIR / f"log_descargas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df_log.to_excel(str(log_path), index=False)
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

        # Esperar que el Select2 esté completamente inicializado
        await page.wait_for_selector("#tradeDiv span.select2-selection--single",
                                     state="visible", timeout=15_000)
        await page.wait_for_timeout(500)

        # Intentar abrir el Select2 con reintento si no aparece el input
        for attempt in range(3):
            await page.locator("#tradeDiv span.select2-selection--single").click()
            await page.wait_for_timeout(1200)
            search_input = page.locator("input.select2-search__field")
            try:
                await search_input.wait_for(state="visible", timeout=5_000)
                break
            except Exception:
                if attempt == 2:
                    raise
                # Cerrar el dropdown si quedó abierto y reintentar
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(800)

        await search_input.fill("")
        await search_input.type(trade_id, delay=80)
        await page.wait_for_timeout(2000)
        opcion = page.locator(f"li.select2-results__option:has-text('{trade_id}')").first
        await opcion.wait_for(state="visible", timeout=10_000)
        await opcion.click()
        await page.wait_for_timeout(1000)
        self._log("   ✅ Trade seleccionado", "ok")

        await page.wait_for_selector(f"td:has-text('{trade_id}')", timeout=10_000)
        fila = page.locator(f"tr:has-text('{trade_id}')").first
        await fila.click()
        await page.wait_for_timeout(2000)
        await page.wait_for_selector("#myModal.in", timeout=10_000)
        await page.wait_for_timeout(1000)

        # Select links based on filter mode
        filter_mode = self.filter_mode.get()
        keyword     = self.keyword.get().strip().lower()
        file_type   = self.file_type.get()

        if filter_mode == "id":
            links = page.locator(f"#myModal a[href*='/PMP/File/Download/']:has-text('{trade_id}')")
        else:
            links = page.locator("#myModal a[href*='/PMP/File/Download/']")

        count = await links.count()

        hrefs, nombres = [], []
        for j in range(count):
            link = links.nth(j)
            nombre_raw   = (await link.inner_text()).strip()
            nombre_lower = nombre_raw.lower()

            # Apply keyword filter
            if filter_mode == "keyword" and keyword and keyword not in nombre_lower:
                self._log(f"   Ignorando (no contiene '{keyword}'): {nombre_raw}", "normal")
                continue

            # Apply file type filter
            ext = nombre_lower.rsplit(".", 1)[-1] if "." in nombre_lower else ""
            if file_type == "pdf" and ext != "pdf":
                self._log(f"   Ignorando (no es PDF): {nombre_raw}", "normal")
                continue
            elif file_type == "xlsx" and ext not in ("xlsx", "xls"):
                self._log(f"   Ignorando (no es XLSX): {nombre_raw}", "normal")
                continue

            href   = await link.get_attribute("href")
            nombre = nombre_raw.replace("/", "-").replace(chr(92), "-")
            hrefs.append(href)
            nombres.append(nombre)

        if not hrefs:
            tipo_label = {"pdf": "PDFs", "xlsx": "XLSXs", "all": "archivos"}.get(file_type, "archivos")
            filtro_label = {"id": f"ID '{trade_id}'", "all": "sin filtro", "keyword": f"keyword '{keyword}'"}.get(filter_mode, "")
            self._log(f"   ⚠️  Sin {tipo_label} que coincidan ({filtro_label})", "warning")
            return 0, ESTADO_SIN_ARCH

        tipo_label = {"pdf": "PDF", "xlsx": "XLSX", "all": "archivo(s)"}.get(file_type, "archivo(s)")
        self._log(f"   📂 {len(hrefs)} {tipo_label}(s) encontrado(s)", "normal")
        archivos_descargados = 0

        carpeta_existentes = set(f.name for f in carpeta.iterdir() if f.is_file()) if carpeta.exists() else set()

        for href, nombre in zip(hrefs, nombres):
            # Skip if this exact file already exists
            destino_nombre = f"{nombre}.pdf" if not nombre.lower().endswith(('.pdf','.xlsx','.xls')) else nombre
            if destino_nombre in carpeta_existentes or nombre in carpeta_existentes:
                self._log(f"   ⏭️  Ya existe: {nombre}", "normal")
                archivos_descargados += 1  # count as ok
                continue
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
# -*- coding: utf-8 -*-
"""
Cerebrino HD+ — Calculadora, Graficadora y 'Derivando con Borre'
Requisitos:
    pip install matplotlib numpy
    # (opcional) pip install pillow   ← para ver la imagen de Borre
Ejecución:
    python cerebrino_hd_plus.py

Atajos:
    F11 → alternar pantalla completa
    Esc  → salir
"""

import tkinter as tk
from tkinter import messagebox as mb
from tkinter import ttk
import random, ast, operator, math
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# -------- (opcional) Pillow para la imagen de Borre --------
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ==========================
#      PALETA Y FUENTES
# ==========================
COL_BG_DARK   = "#1f2544"
COL_BG_CARD   = "#2b3160"
COL_ACCENT_1  = "#ffb703"
COL_ACCENT_2  = "#8ecae6"
COL_ACCENT_3  = "#ff6b6b"
COL_ACCENT_4  = "#90be6d"
COL_TEXT_MAIN = "#f1f5ff"
COL_TEXT_MUTED= "#d7def7"
COL_BORDER    = "#3b4278"

COL_PLOT_GRID = "#d7def7"
COL_PLOT_AXES = "#f1f5ff"

FONT_FAMILY = "Poppins"
F_H1  = (FONT_FAMILY, 44, "bold")
F_H2  = (FONT_FAMILY, 20, "bold")
F_H3  = (FONT_FAMILY, 14, "bold")
F_BTN = (FONT_FAMILY, 16, "bold")
F_P   = (FONT_FAMILY, 12)
F_SM  = (FONT_FAMILY, 10, "italic")

# ==========================
#    EVALUADOR SEGURO AST
# ==========================
_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg, ast.Mod: operator.mod,
}
_ALLOWED_NAMES = {
    "pi": math.pi, "e": math.e, "tau": math.tau,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "sqrt": math.sqrt, "log": math.log, "log10": math.log10, "exp": math.exp, "abs": abs,
    "np": np, "arcsin": np.arcsin, "arccos": np.arccos, "arctan": np.arctan,
}
def safe_eval_expr(expr: str, x_value=None):
    expr = (expr or "").strip().lower().replace("^", "**")
    node = ast.parse(expr, mode="eval")
    def _eval(n):
        if isinstance(n, ast.Expression): return _eval(n.body)
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int,float)): return n.value
            raise ValueError("Constante no numérica")
        if isinstance(n, ast.Num): return n.n
        if isinstance(n, ast.BinOp) and type(n.op) in _ALLOWED_OPS:
            return _ALLOWED_OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _ALLOWED_OPS: return _ALLOWED_OPS[type(n.op)](_eval(n.operand))
        if isinstance(n, ast.Name):
            if n.id == "x" and x_value is not None: return x_value
            if n.id in _ALLOWED_NAMES: return _ALLOWED_NAMES[n.id]
            raise ValueError(f"Nombre no permitido: {n.id}")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            fname = n.func.id
            if fname in _ALLOWED_NAMES: return _ALLOWED_NAMES[fname](*[_eval(a) for a in n.args])
            raise ValueError(f"Función no permitida: {fname}")
        raise ValueError("Expresión no permitida")
    return _eval(node)

# ==========================
#         APP ROOT
# ==========================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cerebrino HD+")
        self.configure(bg=COL_BG_DARK)
        self.resizable(True, True)

        # Pantalla completa desde el inicio
        self.attributes("-fullscreen", True)
        # Atajos globales
        self.bind("<F11>", self._toggle_fullscreen)
        self.bind("<Escape>", lambda e: self._exit())

        # ttk theme
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("TCheckbutton", background=COL_BG_CARD, foreground=COL_TEXT_MAIN, focuscolor=COL_BG_CARD)
        style.configure("TScale", background=COL_BG_CARD)

        self.container = tk.Frame(self, bg=COL_BG_DARK)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (MenuFrame, CalculatorFrame, GrapherFrame, DerivandoFrame):
            frame = F(self.container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.current = None
        self.show_frame(MenuFrame, animate=False)

    def _toggle_fullscreen(self, *_):
        fs = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not fs)

    def _exit(self):
        if mb.askokcancel("Salir", "¿Seguro que quieres salir?"):
            self.destroy()

    def _fade(self, start, end, steps=8, delay=12):
        delta = (end - start) / max(1, steps)
        val = start
        for _ in range(steps):
            val += delta
            self.attributes('-alpha', max(0.75, min(1.0, val)))
            self.update_idletasks(); self.after(delay)
        self.attributes('-alpha', end)

    def show_frame(self, cont, animate=True):
        frame = self.frames[cont]
        if animate and self.current is not None and self.current is not frame:
            self._fade(1.0, 0.88, steps=6, delay=10)
            frame.tkraise()
            self._fade(0.88, 1.0, steps=6, delay=10)
        else:
            frame.tkraise()
        self.current = frame

# ==========================
#       MENU PRINCIPAL
# ==========================
class MenuFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COL_BG_DARK)
        self.controller = controller

        title = tk.Label(self, text="Cerebrino", font=F_H1, fg=COL_TEXT_MAIN, bg=COL_BG_DARK)
        subtitle = tk.Label(self, text="Aprende jugando — 8 a 12 años", font=F_SM, fg=COL_TEXT_MUTED, bg=COL_BG_DARK)
        powered = tk.Label(self, text="Powered by Borre", font=F_SM, fg=COL_TEXT_MUTED, bg=COL_BG_DARK)
        title.pack(pady=(36, 0))
        subtitle.pack(pady=(2, 2))
        powered.pack(pady=(0, 26))

        cards = tk.Frame(self, bg=COL_BG_DARK); cards.pack()

        def mk_btn(txt, bg, cmd):
            btn = tk.Button(cards, text=txt, font=F_BTN, bg=bg, fg="#102a43",
                            activebackground=COL_ACCENT_2, activeforeground="#102a43",
                            bd=0, relief="flat", padx=26, pady=16, height=2, width=18,
                            highlightthickness=2, highlightbackground=COL_BORDER, cursor="hand2")
            btn.bind("<Enter>", lambda e: btn.config(bg=COL_ACCENT_2))
            btn.bind("<Leave>", lambda e, c=bg: btn.config(bg=c))
            btn.config(command=cmd)
            return btn

        mk_btn("🧮 Calculadora", COL_ACCENT_1, lambda: controller.show_frame(CalculatorFrame)).grid(row=0, column=0, padx=14, pady=14)
        mk_btn("📈 Graficadora", COL_ACCENT_4, lambda: controller.show_frame(GrapherFrame)).grid(row=0, column=1, padx=14, pady=14)
        mk_btn("🐶 Derivando con Borre", COL_ACCENT_1, lambda: controller.show_frame(DerivandoFrame)).grid(row=1, column=0, padx=14, pady=14)
        mk_btn("🚪 Salir", COL_ACCENT_3, controller._exit).grid(row=1, column=1, padx=14, pady=14)

# ==========================
#        CALCULADORA
# ==========================
class CalculatorFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COL_BG_DARK)
        self.controller = controller
        self.expression = ""
        self._build()

    def _build(self):
        topbar = tk.Frame(self, bg=COL_BG_DARK)
        topbar.pack(fill="x")
        tk.Button(topbar, text="⬅ Menú", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MAIN,
                  bd=0, padx=12, pady=8, command=lambda: self.controller.show_frame(MenuFrame)).pack(anchor="w", pady=8, padx=8)

        display = tk.Frame(self, bg=COL_BG_CARD, bd=0, highlightthickness=2, highlightbackground=COL_BORDER)
        display.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.lbl = tk.Label(display, text="", font=(FONT_FAMILY, 40, "bold"), fg=COL_TEXT_MAIN, bg=COL_BG_CARD, anchor="e", padx=16)
        self.lbl.pack(fill="both", expand=True)

        grid = tk.Frame(self, bg=COL_BG_DARK)
        grid.pack(fill="both", expand=True, padx=12, pady=12)
        for i in range(5): grid.grid_rowconfigure(i, weight=1)
        for i in range(4): grid.grid_columnconfigure(i, weight=1)

        layout = [
            ('C',0,0,2,'sp'),('del',2,0,1,'sp'),('/',3,0,1,'op'),
            ('7',0,1,1,'n'),('8',1,1,1,'n'),('9',2,1,1,'n'),('*',3,1,1,'op'),
            ('4',0,2,1,'n'),('5',1,2,1,'n'),('6',2,2,1,'n'),('-',3,2,1,'op'),
            ('1',0,3,1,'n'),('2',1,3,1,'n'),('3',2,3,1,'n'),('+',3,3,1,'op'),
            ('0',0,4,2,'n'),('.',2,4,1,'n'),('=',3,4,1,'op'),
        ]
        for (t,c,r,cs,kind) in layout:
            bg = COL_ACCENT_2 if kind=='n' else (COL_ACCENT_4 if kind=='op' else COL_ACCENT_3)
            btn = tk.Button(grid, text=t, font=F_BTN, bg=bg, fg="#102a43", bd=0, height=2,
                            activebackground=COL_ACCENT_2, cursor="hand2",
                            highlightthickness=2, highlightbackground=COL_BORDER,
                            command=lambda x=t: self._press(x))
            btn.grid(column=c, row=r, columnspan=cs, sticky="nsew", padx=6, pady=6)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COL_ACCENT_2))
            btn.bind("<Leave>", lambda e, b=btn, color=bg: b.config(bg=color))

        self.bind_all("<Return>", lambda e: self._press('='))
        self.bind_all("<BackSpace>", lambda e: self._press('del'))
        self.bind_all("<Escape>", lambda e: self.controller._exit())

    def _press(self, val):
        if val == 'C':
            self.expression = ""
            self.lbl.config(highlightbackground=COL_BORDER)
        elif val == 'del':
            self.expression = self.expression[:-1]
        elif val == '=':
            try:
                res = safe_eval_expr(self.expression)
                self.expression = str(res)
                self.lbl.config(highlightbackground=COL_BORDER)
            except Exception:
                self.lbl.config(highlightbackground=COL_ACCENT_3)
        else:
            self.expression += str(val)
        self._update()

    def _update(self):
        txt = self.expression or ""
        size = 40
        if len(txt)>12: size=34
        if len(txt)>16: size=28
        if len(txt)>20: size=24
        self.lbl.config(text=txt[:24], font=(FONT_FAMILY,size,"bold"))

# ==========================
#   WIDGET: Panel lateral grande de Borre
# ==========================
class BigBorrePanel:
    """Panel con Borre grande, escalado automático y mensajes."""
    def __init__(self, parent):
        self.frame = tk.Frame(parent, bg=COL_BG_CARD, padx=14, pady=14,
                              highlightthickness=2, highlightbackground=COL_BORDER)

        tk.Label(self.frame, text="Borre", font=F_H2, bg=COL_BG_CARD, fg=COL_TEXT_MAIN)\
          .pack(anchor="center", pady=(0,8))

        self.canvas = tk.Canvas(self.frame, bg=COL_BG_DARK, highlightthickness=0, width=320, height=440)
        self.canvas.pack(fill="both", expand=True)

        self.msg = tk.Label(self.frame, text="¡Listo para aprender! 🐾",
                            font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED, wraplength=360, justify="center")
        self.msg.pack(pady=(10,0))

        # Carga imagen original (si existe) y guarda para reescalar
        self._pil_original = None
        self._imgtk = None
        self._item = None
        self._phase = 0.0
        self._y_center = 0

        if PIL_AVAILABLE:
            for p in ["borre.png", "/mnt/data/e8e2cb69-dbce-45aa-b57e-e71d249bc84f.png"]:
                try:
                    self._pil_original = Image.open(p).convert("RGBA")
                    break
                except Exception:
                    pass

        if self._pil_original is None:
            self._item = None
            self._ascii = [" (\\_/)", " ( •_•)", " / > 🦴 "]
        else:
            self._item = self.canvas.create_image(0, 0, anchor="center")

        self.canvas.bind("<Configure>", self._on_resize)
        self._animate()

    def _on_resize(self, event):
        w, h = max(100, event.width), max(140, event.height)
        self._y_center = h // 2
        if self._pil_original is None:
            self.canvas.delete("all")
            y0 = self._y_center - 36
            for i, line in enumerate(self._ascii):
                self.canvas.create_text(w//2, y0 + i*22, text=line, fill=COL_TEXT_MAIN, font=(FONT_FAMILY, 18))
            return

        max_w = int(w * 0.9); max_h = int(h * 0.9)
        img = self._pil_original.copy()
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        self._imgtk = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self._item = self.canvas.create_image(w//2, self._y_center, image=self._imgtk)

    def _animate(self):
        self._phase += 0.15
        dy = int(8*np.sin(self._phase))
        if self._item is not None:
            coords = self.canvas.coords(self._item)
            if coords:
                self.canvas.coords(self._item, coords[0], self._y_center + dy)
        self.canvas.after(80, self._animate)

    def flash(self, text, good=True):
        self.msg.config(text=text, fg=(COL_ACCENT_4 if good else COL_ACCENT_3))
        self.frame.after(1200, lambda: self.msg.config(text="¡Listo para aprender! 🐾", fg=COL_TEXT_MUTED))

# ==========================
#         GRAFICADORA
# ==========================
class GrapherFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COL_BG_DARK)
        self.controller = controller
        self.target = None
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=COL_BG_DARK)
        top.pack(fill="x")
        tk.Button(top, text="⬅ Menú", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MAIN, bd=0, padx=12, pady=8,
                  command=lambda: self.controller.show_frame(MenuFrame)).pack(anchor="w", pady=8, padx=8)

        body = tk.Frame(self, bg=COL_BG_DARK); body.pack(fill="both", expand=True)

        # Panel izquierdo: controles
        panel = tk.Frame(body, bg=COL_BG_CARD, bd=0, highlightthickness=2, highlightbackground=COL_BORDER, padx=16, pady=16)
        panel.pack(side="left", fill="y")

        tk.Label(panel, text="y =", font=F_H2, bg=COL_BG_CARD, fg=COL_TEXT_MAIN).pack(anchor="w")
        self.entry_func = tk.Entry(panel, font=F_H3, bg="#1b2043", fg=COL_TEXT_MAIN, insertbackground=COL_TEXT_MAIN)
        self.entry_func.pack(fill="x", pady=(2,8))
        self.entry_func.insert(0, "2*x + 1")

        tk.Label(panel, text="Rango de x", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MUTED).pack(anchor="w")
        self.xmin = tk.DoubleVar(value=-10)
        self.xmax = tk.DoubleVar(value=10)
        frx = tk.Frame(panel, bg=COL_BG_CARD); frx.pack(fill="x")
        ttk.Scale(frx, from_=-20, to=0, variable=self.xmin, command=lambda e: self._sync_ranges()).pack(fill="x", padx=2)
        ttk.Scale(frx, from_=0, to=20, variable=self.xmax, command=lambda e: self._sync_ranges()).pack(fill="x", padx=2, pady=(4,8))

        self.show_grid = tk.BooleanVar(value=True)
        ttk.Checkbutton(panel, text="Mostrar cuadrícula", variable=self.show_grid, command=self._plot).pack(anchor="w")

        tk.Label(panel, text="Recta y = m·x + b", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MUTED).pack(anchor="w", pady=(10,0))
        self.m_val = tk.DoubleVar(value=2.0)
        self.b_val = tk.DoubleVar(value=1.0)
        tk.Scale(panel, from_=-10, to=10, orient="horizontal", resolution=0.1, variable=self.m_val, bg=COL_BG_CARD,
                 troughcolor=COL_ACCENT_2, highlightthickness=0, command=lambda e: self._from_mb()).pack(fill="x")
        tk.Scale(panel, from_=-10, to=10, orient="horizontal", resolution=0.1, variable=self.b_val, bg=COL_BG_CARD,
                 troughcolor=COL_ACCENT_2, highlightthickness=0, command=lambda e: self._from_mb()).pack(fill="x", pady=(0,8))

        quick = tk.Frame(panel, bg=COL_BG_CARD); quick.pack(fill="x", pady=(6,6))
        for txt, f in [("Recta","x"),("Parábola","x**2"),("Seno","np.sin(x)")]:
            b = tk.Button(quick, text=txt, font=F_P, bg=COL_ACCENT_2, fg="#102a43", bd=0, padx=10, pady=6,
                          command=lambda s=f: self._set_func(s))
            b.pack(side="left", padx=4)

        tk.Button(panel, text="📈 Graficar", font=F_BTN, bg=COL_ACCENT_4, fg="#102a43", bd=0,
                  padx=12, pady=10, command=self._plot).pack(fill="x", pady=(10,6))

        sep = ttk.Separator(panel, orient="horizontal"); sep.pack(fill="x", pady=8)
        tk.Label(panel, text="🎯 Mini-juego de puntos", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MAIN).pack(anchor="w")
        self.lbl_goal = tk.Label(panel, text="Meta: coloca el punto en (3, 4)", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED)
        self.lbl_goal.pack(anchor="w", pady=(2,4))
        self.lbl_score = tk.Label(panel, text="Puntos: 0", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED)
        self.lbl_score.pack(anchor="w")
        tk.Button(panel, text="🔁 Nueva meta", font=F_P, bg=COL_ACCENT_1, fg="#102a43", bd=0,
                  command=self._new_goal).pack(fill="x", pady=(6,2))
        tk.Button(panel, text="🧹 Limpiar", font=F_P, bg=COL_ACCENT_3, fg="#102a43", bd=0,
                  command=self._clear_points).pack(fill="x")

        # Centro: gráfico
        center = tk.Frame(body, bg=COL_BG_DARK)
        center.pack(side="left", fill="both", expand=True, padx=(10,12))
        self.fig = Figure(figsize=(9.6, 7.2), dpi=100, facecolor=COL_BG_CARD)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=center)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Derecha: Borre grande siempre visible
        self.borre_panel = BigBorrePanel(body)
        self.borre_panel.frame.pack(side="left", fill="both", padx=(6,14), pady=(0,0))

        self._setup_axes()
        self._new_goal()
        self._plot()
        self.cid_click = self.canvas.mpl_connect('button_press_event', self._on_click_plot)

    def _setup_axes(self):
        self.ax.clear()
        self.ax.set_facecolor("#1b2043")
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(COL_PLOT_AXES)
        self.ax.spines['bottom'].set_color(COL_PLOT_AXES)
        self.ax.tick_params(axis='x', colors=COL_PLOT_AXES)
        self.ax.tick_params(axis='y', colors=COL_PLOT_AXES)
        self.ax.axhline(0, color=COL_PLOT_AXES, linewidth=1.5)
        self.ax.axvline(0, color=COL_PLOT_AXES, linewidth=1.5)

    def _sync_ranges(self):
        if self.xmin.get() >= self.xmax.get():
            self.xmax.set(self.xmin.get()+1)
        self._plot()

    def _set_func(self, s):
        self.entry_func.delete(0, tk.END)
        self.entry_func.insert(0, s)
        self._plot()

    def _from_mb(self):
        m = self.m_val.get(); b = self.b_val.get()
        self.entry_func.delete(0, tk.END)
        self.entry_func.insert(0, f"{m:.2f}*x + {b:.2f}")
        self._plot()

    def _plot(self):
        func = self.entry_func.get()
        x1, x2 = float(self.xmin.get()), float(self.xmax.get())
        if x2 - x1 < 1e-6: x2 = x1 + 1
        x = np.linspace(x1, x2, 600)
        try:
            y = safe_eval_expr(func, x_value=x)
            y = np.asarray(y, dtype=float)
            y[~np.isfinite(y)] = np.nan
        except Exception:
            self._setup_axes()
            self.ax.set_xlim(x1, x2)
            self.ax.set_ylim(-10, 10)
            if True: self.ax.grid(True, linestyle='--', color=COL_PLOT_GRID, alpha=0.25)
            self.canvas.draw(); return

        self._setup_axes()
        self.ax.grid(True, linestyle='--', color=COL_PLOT_GRID, alpha=0.25)
        self.ax.plot(x, y, linewidth=3)
        self.ax.set_xlim(x1, x2)
        valid = y[np.isfinite(y)]
        if valid.size:
            ymin, ymax = float(np.nanmin(valid)), float(np.nanmax(valid))
            pad = 0.1 * (ymax - ymin + 1e-6)
            self.ax.set_ylim(ymin - pad, ymax + pad)
        else:
            self.ax.set_ylim(-10, 10)
        self._draw_goal()
        if hasattr(self, 'placed_points'):
            for (px, py, ok) in self.placed_points:
                self.ax.scatter(px, py, s=60, c=(COL_ACCENT_4 if ok else COL_ACCENT_3), zorder=5)
        self.canvas.draw()

    # ------------- Minijuego -------------
    def _new_goal(self):
        tx = random.randint(-5, 5)
        ty = random.randint(-5, 5)
        self.target = (tx, ty)
        self.lbl_goal.config(text=f"Meta: coloca el punto en ({tx}, {ty})")
        self.placed_points = []
        self._plot()

    def _clear_points(self):
        self.placed_points = []
        self._plot()

    def _draw_goal(self):
        if not self.target: return
        tx, ty = self.target
        self.ax.scatter([tx], [ty], s=160, marker='*', c=COL_ACCENT_1, edgecolors='k', linewidths=0.6, zorder=6)
        self.ax.scatter([tx], [ty], s=400, facecolors='none', edgecolors=COL_ACCENT_1, alpha=0.25, zorder=4)

    def _on_click_plot(self, event):
        if event.inaxes != self.ax: return
        px, py = event.xdata, event.ydata
        ok = False
        if self.target:
            tx, ty = self.target
            dist = math.hypot(px - tx, py - ty)
            ok = dist <= 0.6
        self.placed_points.append((px, py, ok))
        if ok:
            current = int(self.lbl_score.cget('text').split(':')[-1])
            current += 1
            self.lbl_score.config(text=f"Puntos: {current}")
            self.borre_panel.flash("¡Exacto! ⭐", good=True)
            self._new_goal()
        else:
            self.lbl_goal.config(text=f"Casi… prueba más cerca de ({tx}, {ty})")
            self.borre_panel.flash("Casi… 😅", good=False)
        self._plot()

# ==========================
#   DERIVANDO CON BORRE — juego principal
# ==========================
class DerivandoFrame(tk.Frame):
    FUNCS = [
        ("x",           "Recta"),
        ("2*x+1",       "Recta inclinada"),
        ("x**2",        "Parábola"),
        ("-0.5*x**2+4", "Parábola invertida"),
        ("x**3/8",      "Cúbica suave"),
        ("np.sin(x)",   "Seno"),
        ("np.cos(x)",   "Coseno"),
    ]

    def __init__(self, parent, controller):
        super().__init__(parent, bg=COL_BG_DARK)
        self.controller = controller

        # Estado
        self.score = 0
        self.level = 1
        self.lives = 3
        self.bones = 0
        self.mode = tk.StringVar(value="signo")  # "signo" | "valor"
        self.in_boss = False

        self.func_str = "x"
        self.x0 = 0.0
        self.correct_answer = None

        # ---- Top bar
        top = tk.Frame(self, bg=COL_BG_DARK); top.pack(fill="x")
        tk.Button(top, text="⬅ Menú", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MAIN, bd=0, padx=12, pady=8,
                  command=lambda: self.controller.show_frame(MenuFrame)).pack(side="left", pady=8, padx=8)
        tk.Label(top, text="Derivando con Borre", font=F_H1, bg=COL_BG_DARK, fg=COL_TEXT_MAIN)\
          .pack(side="left", padx=16, pady=10)

        tk.Button(top, text="Pantalla completa (F11)", font=F_P, bg=COL_ACCENT_2, fg="#102a43", bd=0, padx=12, pady=8,
                  command=self.controller._toggle_fullscreen).pack(side="right", padx=12)
        tk.Button(top, text="Salir (Esc)", font=F_P, bg=COL_ACCENT_3, fg="#102a43", bd=0, padx=12, pady=8,
                  command=self.controller._exit).pack(side="right", padx=12)

        # ---- Layout: Controles | Gráfico | Borre grande
        body = tk.Frame(self, bg=COL_BG_DARK); body.pack(fill="both", expand=True)

        # Controles
        left = tk.Frame(body, bg=COL_BG_CARD, padx=16, pady=16,
                        highlightthickness=2, highlightbackground=COL_BORDER)
        left.pack(side="left", fill="y")

        tk.Label(left, text="Modo de juego", font=F_H2, bg=COL_BG_CARD, fg=COL_TEXT_MAIN).pack(anchor="w")
        rb1 = ttk.Radiobutton(left, text="¿Sube, baja o plano? (signo)", value="signo", variable=self.mode,
                              command=lambda: self.nueva_pregunta(force_mode=True))
        rb2 = ttk.Radiobutton(left, text="Velocidad en un punto (valor)", value="valor", variable=self.mode,
                              command=lambda: self.nueva_pregunta(force_mode=True))
        for rb in (rb1, rb2):
            rb.configure(style="TCheckbutton"); rb.pack(anchor="w", pady=2)

        self.lbl_state = tk.Label(left, text="Nivel 1  |  Vidas: 3  |  Huesitos: 0",
                                  font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED)
        self.lbl_state.pack(anchor="w", pady=(8,10))

        tk.Label(left, text="Función (y = …)", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MUTED).pack(anchor="w")
        self.lbl_func = tk.Label(left, text="x", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MAIN)
        self.lbl_func.pack(anchor="w")

        tk.Label(left, text="Evaluar en x =", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MUTED).pack(anchor="w", pady=(10,2))
        self.var_x0 = tk.DoubleVar(value=1.0)
        tk.Scale(left, from_=-6, to=6, orient="horizontal", resolution=0.5, variable=self.var_x0, bg=COL_BG_CARD,
                 troughcolor=COL_ACCENT_2, highlightthickness=0, command=lambda e: self._refresh_plot()).pack(fill="x")

        self.lbl_question = tk.Label(left, text="Pulsa «Nueva pregunta»", font=F_H3, bg=COL_BG_CARD, fg=COL_TEXT_MAIN, wraplength=260, justify="left")
        self.lbl_question.pack(anchor="w", pady=(10,8))

        self.opt_frame = tk.Frame(left, bg=COL_BG_CARD); self.opt_frame.pack(fill="x")
        self.btns_opts = []
        for i in range(4):
            b = tk.Button(self.opt_frame, text="—", font=F_P, bg=COL_ACCENT_2, fg="#102a43", bd=0, padx=10, pady=8,
                          command=lambda idx=i: self._choose(idx))
            b.pack(fill="x", pady=4)
            self.btns_opts.append(b)

        self.lbl_feedback = tk.Label(left, text="", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED, wraplength=260, justify="left")
        self.lbl_feedback.pack(anchor="w", pady=(8,6))
        self.lbl_score = tk.Label(left, text="Racha: 0/5 para Jefe", font=F_P, bg=COL_BG_CARD, fg=COL_TEXT_MUTED)
        self.lbl_score.pack(anchor="w", pady=(0,10))

        tk.Button(left, text="🎲 Nueva pregunta", font=F_BTN, bg=COL_ACCENT_1, fg="#102a43", bd=0,
                  command=self.nueva_pregunta).pack(fill="x", pady=(6,4))
        tk.Button(left, text="🧹 Reiniciar Nivel", font=F_P, bg=COL_ACCENT_3, fg="#102a43", bd=0,
                  command=self._reset_level).pack(fill="x")

        # Centro (gráfico)
        center = tk.Frame(body, bg=COL_BG_DARK)
        center.pack(side="left", fill="both", expand=True, padx=(10,12))
        self.fig = Figure(figsize=(9.6, 7.2), dpi=100, facecolor=COL_BG_CARD)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=center)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Derecha: Borre grande siempre visible
        self.borre_panel = BigBorrePanel(body)
        self.borre_panel.frame.pack(side="left", fill="both", padx=(6,14), pady=(0,0))

        # Inicializa
        self._setup_axes()
        self.nueva_pregunta()

    # -------- utilidades matemáticas
    def _y(self, x): return safe_eval_expr(self.func_str, x_value=x)
    def _deriv_num(self, x0, h=1e-4): return (self._y(x0+h) - self._y(x0-h)) / (2*h)

    # -------- progreso
    def _update_statebar(self):
        self.lbl_state.config(text=f"Nivel {self.level}  |  Vidas: {self.lives}  |  Huesitos: {self.bones}")

    def _gain_bone(self, amount=1):
        self.bones += amount
        self._update_statebar()
        self.borre_panel.flash("+1 huesito 🎉", good=True)

    def _lose_life(self):
        self.lives -= 1
        self._update_statebar()
        self.borre_panel.flash("-1 vida 😅", good=False)
        if self.lives <= 0:
            mb.showwarning("Juego terminado", "Borre se cansó… ¡Inténtalo otra vez!")
            self.level = 1; self.lives = 3; self.bones = 0; self.score = 0; self.in_boss = False
            self.lbl_score.config(text="Racha: 0/5 para Jefe")
            self._update_statebar()

    def _level_up(self):
        self.level += 1
        self.score = 0
        self.in_boss = False
        mb.showinfo("¡Nivel superado!", f"Subiste al Nivel {self.level}. ¡Borre está orgulloso! 🐾")
        self.lbl_score.config(text="Racha: 0/5 para Jefe")
        self._update_statebar()
        self.borre_panel.flash("¡Nivel ↑!", good=True)

    # -------- preguntas
    def nueva_pregunta(self, force_mode=False):
        if not self.in_boss and self.score >= 5:
            self.in_boss = True
            mb.showinfo("🐺 ¡Jefe!", "Reto de Jefe: combina pendiente y valor.\n¡Consigue 2 aciertos seguidos!")
            self.mode.set("signo")

        self.func_str, _ = random.choice(self.FUNCS)
        self.lbl_func.config(text=self.func_str)
        self.x0 = round(random.uniform(-3, 3), 1)
        self.var_x0.set(self.x0)
        self.lbl_feedback.config(text="")
        self._setup_axes()
        self._refresh_plot()

        m = self.mode.get()
        if self.in_boss:
            m = "signo" if (getattr(self, "_boss_toggle", 0) % 2 == 0) else "valor"
            self._boss_toggle = getattr(self, "_boss_toggle", 0) + 1
        elif force_mode:
            m = self.mode.get()

        if m == "signo": self._q_signo()
        else: self._q_valor()

    def _q_signo(self):
        self.lbl_question.config(text=f"En y = {self.func_str} y en x = {self.x0}, ¿la pendiente es…?")
        slope = self._deriv_num(self.x0)
        if abs(slope) < 1e-2:
            self.correct_answer = "Plana (0)"; opciones = ["Plana (0)", "Positiva", "Negativa", "No se puede"]
        elif slope > 0:
            self.correct_answer = "Positiva"; opciones = ["Positiva", "Negativa", "Plana (0)", "No se puede"]
        else:
            self.correct_answer = "Negativa"; opciones = ["Negativa", "Positiva", "Plana (0)", "No se puede"]
        random.shuffle(opciones); self._fill_options(opciones)

    def _q_valor(self):
        self.lbl_question.config(text=f"Velocidad de Borre: estima f'(x) en x = {self.x0}")
        slope = self._deriv_num(self.x0)
        corr = round(slope, 1)
        self.correct_answer = f"{corr}"
        opciones = {corr}
        while len(opciones) < 4:
            delta = random.choice([0.1, 0.2, 0.3, 0.5, 1.0]) * random.choice([-1,1])
            opciones.add(round(corr + delta, 1))
        opciones = [str(o) for o in opciones]; random.shuffle(opciones)
        self._fill_options(opciones)

    def _fill_options(self, opciones):
        for b, txt in zip(self.btns_opts, opciones): b.config(text=txt, state="normal")

    def _choose(self, idx):
        txt = self.btns_opts[idx].cget("text")
        ok = (txt == self.correct_answer)
        if ok:
            if self.in_boss:
                streak = getattr(self, "_boss_streak", 0) + 1
                self._boss_streak = streak
                if streak >= 2:
                    self._boss_streak = 0
                    self._level_up()
            else:
                self.score += 1
                self._gain_bone(1)
                self.lbl_score.config(text=f"Racha: {self.score}/5 para Jefe")
            self.lbl_feedback.config(text="⭐ ¡Correcto!")
        else:
            self._lose_life()
            self.lbl_feedback.config(text=f"Ups… La respuesta era: {self.correct_answer}")
            if self.in_boss: self._boss_streak = 0

        for b in self.btns_opts: b.config(state="disabled")
        self.after(900, self.nueva_pregunta)

    def _reset_level(self):
        self.score = 0; self.in_boss = False
        self.lbl_score.config(text="Racha: 0/5 para Jefe")
        self._update_statebar(); self.nueva_pregunta()

    # -------- gráfico
    def _setup_axes(self):
        self.ax.clear()
        self.ax.set_facecolor("#1b2043")
        for side in ('top','right'): self.ax.spines[side].set_visible(False)
        self.ax.spines['left'].set_color(COL_PLOT_AXES)
        self.ax.spines['bottom'].set_color(COL_PLOT_AXES)
        self.ax.tick_params(axis='x', colors=COL_PLOT_AXES)
        self.ax.tick_params(axis='y', colors=COL_PLOT_AXES)
        self.ax.axhline(0, color=COL_PLOT_AXES, linewidth=1.5)
        self.ax.axvline(0, color=COL_PLOT_AXES, linewidth=1.5)
        self.ax.grid(True, linestyle='--', color=COL_PLOT_GRID, alpha=0.25)

    def _refresh_plot(self):
        x0 = float(self.var_x0.get()); self.x0 = x0
        x = np.linspace(-6, 6, 600)
        try:
            y = self._y(x); y = np.asarray(y, dtype=float); y[~np.isfinite(y)] = np.nan
        except Exception:
            self._setup_axes(); self.ax.set_xlim(-6,6); self.ax.set_ylim(-6,6); self.canvas.draw(); return

        self._setup_axes(); self.ax.plot(x, y, linewidth=3)
        try:
            y0 = float(self._y(x0)); m = float(self._deriv_num(x0))
            xt = np.linspace(x0-2, x0+2, 40); yt = m*(xt - x0) + y0
            self.ax.plot(xt, yt, linewidth=2); self.ax.scatter([x0],[y0], s=80, zorder=5)
        except Exception:
            pass
        self.ax.set_xlim(-6,6); self.ax.set_ylim(-6,6); self.canvas.draw()

# ==========================
#            RUN
# ==========================
if __name__ == "__main__":
    app = App()
    app.mainloop()

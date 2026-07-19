"""Limpiador de Caché y Temporales para Windows - GUI (tkinter, solo stdlib)."""
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import cleaner


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Limpiador de Caché y Temporales")
        self.geometry("900x640")
        self.minsize(720, 420)

        self.scanned = {}
        self.vars = {}
        self.size_labels = {}
        self.close_before_vars = {}
        self.log_queue = queue.Queue()
        self.busy = False

        self._build_ui()
        self.after(150, self._poll_log_queue)

    # ---------- UI ----------
    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(side="top", fill="x")

        admin = cleaner.is_admin()
        status = "Ejecutando como Administrador" if admin else "Sin privilegios de Administrador"
        ttk.Label(top, text=status, font=("Segoe UI", 10, "bold")).pack(side="left")
        if not admin:
            ttk.Button(
                top, text="Reiniciar como Administrador",
                command=self._relaunch_admin,
            ).pack(side="right")

        # Botonera y registro se anclan abajo primero para que siempre queden visibles;
        # el panel con scroll de categorías ocupa el espacio restante en el medio.
        btn_frame = ttk.Frame(self, padding=10)
        btn_frame.pack(side="bottom", fill="x")
        self.scan_btn = ttk.Button(btn_frame, text="Analizar", command=self._on_scan)
        self.scan_btn.pack(side="left")
        self.select_all_btn = ttk.Button(
            btn_frame, text="Seleccionar todo", command=self._on_select_all,
        )
        self.select_all_btn.pack(side="left", padx=8)
        self.delete_btn = ttk.Button(
            btn_frame, text="Eliminar seleccionado", command=self._on_delete, state="disabled",
        )
        self.delete_btn.pack(side="left", padx=8)
        self.total_lbl = ttk.Label(btn_frame, text="")
        self.total_lbl.pack(side="right")

        log_frame = ttk.LabelFrame(self, text="Registro", padding=6)
        log_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        self.log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, side="left")
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text["yscrollcommand"] = scroll.set

        self._build_category_panel()

    def _build_category_panel(self, columns=2):
        outer = ttk.Frame(self, padding=(10, 4, 10, 4))
        outer.pack(side="top", fill="both", expand=True)

        canvas = tk.Canvas(outer, highlightthickness=0)
        vscroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        grid_frame = ttk.Frame(canvas)
        frame_id = canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        for col in range(columns):
            grid_frame.columnconfigure(col, weight=1)

        def on_frame_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(frame_id, width=event.width)

        grid_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_wheel(_event=None):
            canvas.bind_all("<MouseWheel>", on_mousewheel)

        def unbind_wheel(_event=None):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", bind_wheel)
        canvas.bind("<Leave>", unbind_wheel)

        for i, cat in enumerate(cleaner.CATEGORIES):
            row, col = divmod(i, columns)
            card = ttk.Frame(grid_frame, padding=8, relief="groove", borderwidth=1)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

            head = ttk.Frame(card)
            head.pack(fill="x")
            var = tk.BooleanVar(value=False)
            self.vars[cat["key"]] = var
            ttk.Checkbutton(head, variable=var, text=cat["label"]).pack(side="left", anchor="w")

            size_lbl = ttk.Label(card, text="—", anchor="e", foreground="#555")
            size_lbl.pack(fill="x")
            self.size_labels[cat["key"]] = size_lbl

            if cat.get("requires_admin"):
                ttk.Label(card, text="requiere admin", foreground="#a15c00").pack(anchor="w")

            if cat.get("warning"):
                ttk.Label(
                    card, text="⚠ " + cat["warning"], foreground="#a15c00",
                    wraplength=340, justify="left",
                ).pack(fill="x", pady=(4, 0))

            if cat["key"] in cleaner.CLOSE_BEFORE_CLEAN:
                _fn, label_text = cleaner.CLOSE_BEFORE_CLEAN[cat["key"]]
                close_var = tk.BooleanVar(value=False)
                self.close_before_vars[cat["key"]] = close_var
                ttk.Checkbutton(card, variable=close_var, text=label_text).pack(
                    fill="x", pady=(4, 0), anchor="w",
                )

    def _on_select_all(self):
        all_selected = all(v.get() for v in self.vars.values())
        for v in self.vars.values():
            v.set(not all_selected)

    def _relaunch_admin(self):
        cleaner.relaunch_as_admin()

    def _log(self, msg):
        self.log_queue.put(msg)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_text.configure(state="normal")
                self.log_text.insert("end", msg + "\n")
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(150, self._poll_log_queue)

    def _set_busy(self, busy):
        self.busy = busy
        state = "disabled" if busy else "normal"
        self.scan_btn.configure(state=state)
        self.delete_btn.configure(state="disabled" if busy else ("normal" if self.scanned else "disabled"))

    # ---------- Escaneo ----------
    def _on_scan(self):
        if self.busy:
            return
        self._set_busy(True)
        self.total_lbl.configure(text="Analizando...")
        for key in self.size_labels:
            self.size_labels[key].configure(text="…")
        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self):
        self._log("Analizando cachés y temporales...")
        result = cleaner.scan()
        self.after(0, self._scan_done, result)

    def _scan_done(self, result):
        self.scanned = result
        total = 0
        for key, entry in result.items():
            self.size_labels[key].configure(text=cleaner.human_size(entry["total"]))
            total += entry["total"]
        self.total_lbl.configure(text=f"Total detectado: {cleaner.human_size(total)}")
        self._log("Análisis completado.")
        self._set_busy(False)
        self.delete_btn.configure(state="normal")

    # ---------- Borrado ----------
    def _on_delete(self):
        if self.busy or not self.scanned:
            return
        selected = [k for k, v in self.vars.items() if v.get()]
        if not selected:
            messagebox.showinfo("Nada seleccionado", "Marca al menos una categoría para eliminar.")
            return

        lines = ["Se eliminará el contenido de:"]
        total = 0
        warnings = []
        needs_admin = []
        for key in selected:
            entry = self.scanned.get(key, {})
            size = entry.get("total", 0)
            total += size
            lines.append(f"  • {entry.get('label', key)} — {cleaner.human_size(size)}")
            if entry.get("warning"):
                warnings.append(entry["label"] + ": " + entry["warning"])
            if entry.get("requires_admin") and not cleaner.is_admin():
                needs_admin.append(entry["label"])

        if needs_admin:
            messagebox.showerror(
                "Se requiere Administrador",
                "Estas categorías requieren privilegios de Administrador:\n- "
                + "\n- ".join(needs_admin)
                + "\n\nReinicia la aplicación como Administrador para continuar.",
            )
            return

        lines.append(f"\nTotal aproximado a liberar: {cleaner.human_size(total)}")
        if warnings:
            lines.append("\nAdvertencias:")
            for w in warnings:
                lines.append("  ⚠ " + w)
        lines.append("\n¿Deseas continuar?")

        if not messagebox.askyesno("Confirmar eliminación", "\n".join(lines)):
            return

        self._set_busy(True)
        threading.Thread(target=self._delete_worker, args=(selected,), daemon=True).start()

    def _delete_worker(self, selected):
        for key, var in self.close_before_vars.items():
            if key in selected and var.get():
                kill_fn, label_text = cleaner.CLOSE_BEFORE_CLEAN[key]
                self._log(f"Cerrando: {label_text.split(' antes')[0]}...")
                kill_fn()

        for key in selected:
            entry = self.scanned.get(key, {})
            self._log(f"--- {entry.get('label', key)} ---")
            try:
                cleaner.delete_category(key, entry, self._log)
            except Exception as e:
                self._log(f"Error al limpiar {key}: {e}")

        self._log("Listo. Vuelve a analizar para ver el espacio actual.")
        self.after(0, self._delete_done)

    def _delete_done(self):
        self._set_busy(False)
        self.delete_btn.configure(state="normal")
        for key in self.size_labels:
            self.size_labels[key].configure(text="—")
        self.total_lbl.configure(text="Vuelve a analizar para ver tamaños actualizados.")


if __name__ == "__main__":
    App().mainloop()

# ==========================================================
# PROYECTO: SISTEMA DE GESTIÓN OPERATIVA DE RESTAURANTE (SIGOR)
# Asignatura: Algoritmia y Programación - UAO
# Integrantes:
#   1. Juan Camilo Cano Zaraza
#   2. Alejandro Herrera Lozano
#   3. Andrés Felipe Rojas Díaz
#   4. Breyner Stiven Soto
# ----------------------------------------------------------
# FRONTEND (Checklist punto 3) en Tkinter.
# Solo dibuja la pantalla y llama al backend (backend.py), que
# valida, calcula y guarda en datos_restaurante.json (punto 4).
#
# Ejecutar:  python Interfaz.py
# ==========================================================

import functools
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from backend import STOCK_MINIMO, ErrorRestaurante, Restaurante, formatear_pesos
from auth_sigor import registrar_usuario, iniciar_sesion as autenticar, listar_asistencias, registrar_asistencia, editar_asistencia, eliminar_asistencia, exigir_admin

COLOR_OK = "#1b7f3b"
COLOR_ERROR = "#b3261e"


def manejar_errores(funcion):
    """Convierte los ErrorRestaurante del backend en mensajes claros en pantalla."""

    @functools.wraps(funcion)
    def interno(self, *args, **kwargs):
        try:
            return funcion(self, *args, **kwargs)
        except ErrorRestaurante as error:
            self.mensaje(str(error), error=True)
            messagebox.showerror("No se pudo completar la acción", str(error), parent=self)
            return None

    return interno


class App(tk.Tk):
    def __init__(self, sistema=None):
        super().__init__()
        self.sistema = sistema or Restaurante()
        self.es_admin = False
        self.sesion = None
        self.mesa_sel = None
        self.producto_sel = None

        self.title("Sistema de Gestión de Restaurante - UAO")
        self.geometry("1020x640")
        self.minsize(940, 580)

        self._construir_barra_superior()
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 4))

        self.tab_mesas = ttk.Frame(self.notebook)
        self.tab_inventario = ttk.Frame(self.notebook)
        self.tab_ventas = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_mesas, text="  Mesas y pedidos  ")
        self.notebook.add(self.tab_inventario, text="  Inventario (admin)  ")
        self.notebook.add(self.tab_ventas, text="  Ventas del día (admin)  ")
        self.tab_asistencia = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_asistencia, text="  Asistencia (admin)  ")

        self._construir_tab_mesas()
        self._construir_tab_inventario()
        self._construir_tab_ventas()
        self._construir_tab_asistencia()

        self.estado = tk.StringVar(value="Bienvenido. Seleccione una mesa para comenzar.")
        self.lbl_estado = tk.Label(self, textvariable=self.estado, anchor="w", relief="sunken", padx=8)
        self.lbl_estado.pack(fill="x", side="bottom")

        self.notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)
        self.refrescar_todo()
        self.notebook.pack_forget()
        self.lbl_estado.pack_forget()
        self._pantalla_acceso()

    # ------------------------------------------------------
    # Utilidades de interfaz
    # ------------------------------------------------------
    def mensaje(self, texto, error=False):
        self.estado.set(texto)
        self.lbl_estado.config(fg=COLOR_ERROR if error else COLOR_OK)

    def refrescar_todo(self):
        self.refrescar_mesas()
        self.refrescar_inventario()
        self.refrescar_ventas()
        self._actualizar_combo_productos()
        self._refrescar_asistencia()

    # ------------------------------------------------------
    # Seguridad: sesión de administrador
    # ------------------------------------------------------
    def _construir_barra_superior(self):
        barra = tk.Frame(self, bg="#2b2d42")
        barra.pack(fill="x")
        tk.Label(
            barra, text="🍽  Sistema de Restaurante", bg="#2b2d42", fg="white",
            font=("Segoe UI", 15, "bold"), pady=8, padx=10,
        ).pack(side="left")
        self.btn_sesion = ttk.Button(barra, text="Cerrar sesión", command=self.cerrar_sesion)
        self.btn_sesion.pack(side="right", padx=10)
        self.lbl_rol = tk.Label(barra, text="Sesión: no iniciada", bg="#2b2d42", fg="#edf2f4")
        self.lbl_rol.pack(side="right")

    def _actualizar_rol(self):
        rol = self.sesion["rol"] if self.sesion else "Sin sesión"
        usuario = self.sesion["usuario"] if self.sesion else ""
        self.lbl_rol.config(text=f"Sesión: {usuario} | Rol: {rol}")
        self.btn_sesion.config(text="Cerrar sesión")

    def _pantalla_acceso(self):
        self.acceso = tk.Frame(self, bg="#edf2f4")
        self.acceso.pack(fill="both", expand=True)

        # Contenedor central más amplio y proporcionado
        contenedor = tk.Frame(self.acceso, bg="white", relief="ridge", bd=1)
        contenedor.place(relx=0.5, rely=0.5, anchor="center", width=460, height=380)

        tk.Label(
            contenedor, text="SIGOR", font=("Segoe UI", 28, "bold"), 
            bg="white", fg="#2b2d42"
        ).pack(pady=(35, 5))
        
        tk.Label(
            contenedor, text="Sistema de Gestión Operativa de Restaurante", 
            font=("Segoe UI", 11), bg="white", fg="#555"
        ).pack(pady=(0, 15))

        self.progreso = ttk.Progressbar(contenedor, mode="indeterminate", length=300)
        self.progreso.pack(pady=25)
        
        tk.Label(
            contenedor, text="Cargando sistema...", font=("Segoe UI", 10), 
            bg="white", fg="#666"
        ).pack()
        
        self.progreso.start(12)
        self.after(1300, self._mostrar_opciones_acceso)

    def _mostrar_opciones_acceso(self):
        self.progreso.stop()
        for widget in self.acceso.winfo_children(): 
            widget.destroy()

        # Contenedor central ampliado para las opciones de botones
        contenedor = tk.Frame(self.acceso, bg="white", relief="ridge", bd=1)
        contenedor.place(relx=0.5, rely=0.5, anchor="center", width=460, height=380)

        tk.Label(
            contenedor, text="Bienvenido a SIGOR", font=("Segoe UI", 22, "bold"), 
            bg="white", fg="#2b2d42"
        ).pack(pady=(45, 15))

        # Uso de tk.Button para soportar fuentes y estilos de color de forma directa
        btn_login = tk.Button(
            contenedor, text="Iniciar sesión", command=self._dialogo_login,
            font=("Segoe UI", 11), width=22, bg="#2b2d42", fg="white", relief="flat", cursor="hand2"
        )
        btn_login.pack(pady=10, ipady=4)

        btn_reg = tk.Button(
            contenedor, text="Registrarse", command=self._dialogo_registro,
            font=("Segoe UI", 11), width=22, bg="#e0e0e0", fg="#2b2d42", relief="flat", cursor="hand2"
        )
        btn_reg.pack(pady=10, ipady=4)

        tk.Label(
            contenedor, text="Debe autenticarse para acceder a los módulos.", 
            font=("Segoe UI", 9), bg="white", fg="#777"
        ).pack(pady=(20, 0))

    def _dialogo_login(self):
        usuario = simpledialog.askstring("Inicio de sesión", "Usuario:", parent=self)
        if usuario is None: return
        clave = simpledialog.askstring("Inicio de sesión", "Contraseña:", show="*", parent=self)
        if clave is None: return
        try: 
            sesion = autenticar(usuario, clave)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Acceso", str(error), parent=self)
            return
        if not sesion:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.", parent=self)
            return
        self.sesion = sesion
        self.es_admin = sesion["rol"] == "Administrador"
        self.acceso.destroy()
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 4))
        self.lbl_estado.pack(fill="x", side="bottom")
        self._actualizar_rol()
        self.notebook.select(self.tab_mesas)
        self.refrescar_todo()
        self.mensaje(f"Bienvenido {sesion['usuario']} ({sesion['rol']}).")

    def _dialogo_registro(self):
        usuario = simpledialog.askstring("Registro", "Nuevo usuario:", parent=self)
        if usuario is None: return
        clave = simpledialog.askstring("Registro", "Contraseña (mínimo 6 caracteres):", show="*", parent=self)
        if clave is None: return
        rol = simpledialog.askstring("Registro", "Rol (Administrador o Mesero):", parent=self)
        if rol is None: return
        codigo = simpledialog.askstring("Código de seguridad", "Ingrese el código numérico de 4 dígitos:", parent=self)
        if codigo is None: return
        rol = rol.strip().capitalize()
        try: 
            registrar_usuario(usuario, clave, rol, codigo)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Registro denegado", str(error), parent=self)
            return
        messagebox.showinfo("Registro", "Usuario creado correctamente. Ahora puede iniciar sesión.", parent=self)

    def cerrar_sesion(self):
        self.sesion = None
        self.es_admin = False
        self._actualizar_rol()
        self.notebook.pack_forget()
        self.lbl_estado.pack_forget()
        self._pantalla_acceso()

    def requiere_admin(self):
        if self.sesion and self.sesion.get("rol") == "Administrador": 
            return True
        messagebox.showerror("Permisos", "Esta función es exclusiva para Administradores.", parent=self)
        return False

    def _al_cambiar_pestana(self, _evento=None):
        actual = self.notebook.select()
        admin_tabs = (str(self.tab_inventario), str(self.tab_ventas), str(self.tab_asistencia))
        if actual in admin_tabs and not self.es_admin:
            messagebox.showerror("Permisos", "Esta sección es exclusiva para Administradores.", parent=self)
            self.notebook.select(self.tab_mesas)
        self.refrescar_todo()

    # ------------------------------------------------------
    # PESTAÑA 1: MESAS Y PEDIDOS (Módulos 2 y 3)
    # ------------------------------------------------------
    def _construir_tab_mesas(self):
        izq = ttk.LabelFrame(self.tab_mesas, text="Mesas")
        izq.pack(side="left", fill="both", expand=False, padx=8, pady=8)

        self.tree_mesas = ttk.Treeview(
            izq, columns=("mesa", "estado", "comensales", "total"), show="headings", height=14, selectmode="browse"
        )
        for col, texto, ancho in (
            ("mesa", "Mesa", 60), ("estado", "Estado", 90), ("comensales", "Comensales", 90), ("total", "Total", 110),
        ):
            self.tree_mesas.heading(col, text=texto)
            self.tree_mesas.column(col, width=ancho, anchor="center")
        self.tree_mesas.tag_configure("Ocupada", background="#ffe8cc")
        self.tree_mesas.tag_configure("Libre", background="#e3f6e8")
        self.tree_mesas.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree_mesas.bind("<<TreeviewSelect>>", self._al_seleccionar_mesa)

        fila = ttk.Frame(izq)
        fila.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(fila, text="Agregar mesa", command=self.agregar_mesa).pack(side="left", expand=True, fill="x")
        ttk.Button(fila, text="Eliminar mesa", command=self.eliminar_mesa).pack(side="left", expand=True, fill="x", padx=(4, 0))
        ttk.Label(izq, text="Agregar/eliminar mesas requiere administrador.", foreground="#555").pack(pady=(0, 6))

        der = ttk.LabelFrame(self.tab_mesas, text="Pedido de la mesa")
        der.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=8)
        self.marco_pedido = der

        self.tree_pedido = ttk.Treeview(
            der, columns=("producto", "cantidad", "precio", "subtotal"), show="headings", height=8, selectmode="browse"
        )
        for col, texto, ancho in (
            ("producto", "Producto", 160), ("cantidad", "Cant.", 60), ("precio", "Precio", 100), ("subtotal", "Subtotal", 110),
        ):
            self.tree_pedido.heading(col, text=texto)
            self.tree_pedido.column(col, width=ancho, anchor="center")
        self.tree_pedido.pack(fill="both", expand=True, padx=6, pady=6)

        self.lbl_total = tk.Label(der, text="Total: $0", font=("Segoe UI", 13, "bold"), anchor="e")
        self.lbl_total.pack(fill="x", padx=8)

        form = ttk.Frame(der)
        form.pack(fill="x", padx=6, pady=6)
        self.var_comensales = tk.StringVar()
        self.var_producto = tk.StringVar()
        self.var_cantidad = tk.StringVar(value="1")

        ttk.Label(form, text="Comensales (mesa libre):").grid(row=0, column=0, sticky="w", pady=2)
        self.ent_comensales = ttk.Entry(form, textvariable=self.var_comensales, width=8)
        self.ent_comensales.grid(row=0, column=1, sticky="w", padx=6)

        ttk.Label(form, text="Producto:").grid(row=1, column=0, sticky="w", pady=2)
        self.combo_producto = ttk.Combobox(form, textvariable=self.var_producto, state="readonly", width=18)
        self.combo_producto.grid(row=1, column=1, sticky="w", padx=6)
        self.combo_producto.bind("<<ComboboxSelected>>", lambda _e: self._info_producto())
        self.lbl_info_producto = ttk.Label(form, text="", foreground="#555")
        self.lbl_info_producto.grid(row=1, column=2, sticky="w")

        ttk.Label(form, text="Cantidad:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Spinbox(form, from_=1, to=999, textvariable=self.var_cantidad, width=6).grid(row=2, column=1, sticky="w", padx=6)

        botones = ttk.Frame(der)
        botones.pack(fill="x", padx=6, pady=(0, 8))
        ttk.Button(botones, text="➕ Agregar al pedido", command=self.agregar_al_pedido).pack(side="left", expand=True, fill="x")
        ttk.Button(botones, text="🗑 Quitar línea", command=self.quitar_linea).pack(side="left", expand=True, fill="x", padx=4)
        ttk.Button(botones, text="💵 Cobrar y liberar", command=self.cobrar_mesa).pack(side="left", expand=True, fill="x")

    def refrescar_mesas(self):
        seleccion = self.mesa_sel
        self.tree_mesas.delete(*self.tree_mesas.get_children())
        for m in self.sistema.listar_mesas():
            self.tree_mesas.insert(
                "", "end", iid=str(m["numero"]), tags=(m["estado"],),
                values=(m["numero"], m["estado"], m["comensales"], formatear_pesos(m["total"])),
            )
        if seleccion is not None and str(seleccion) in self.tree_mesas.get_children():
            self.tree_mesas.selection_set(str(seleccion))
        else:
            self.mesa_sel = None
        self._mostrar_pedido()

    def _al_seleccionar_mesa(self, _evento=None):
        seleccion = self.tree_mesas.selection()
        self.mesa_sel = int(seleccion[0]) if seleccion else None
        self._mostrar_pedido()

    def _mostrar_pedido(self):
        self.tree_pedido.delete(*self.tree_pedido.get_children())
        if self.mesa_sel is None or self.mesa_sel not in self.sistema.mesas:
            self.marco_pedido.config(text="Pedido de la mesa (seleccione una)")
            self.lbl_total.config(text="Total: $0")
            self.ent_comensales.config(state="disabled")
            return
        mesa = self.sistema.mesas[self.mesa_sel]
        self.marco_pedido.config(text=f"Pedido de la mesa {self.mesa_sel} - {mesa['estado']}")
        for i, item in enumerate(mesa["pedido"]):
            self.tree_pedido.insert(
                "", "end", iid=str(i),
                values=(item["producto"], item["cantidad"], formatear_pesos(item["precio"]),
                        formatear_pesos(item["precio"] * item["cantidad"])),
            )
        self.lbl_total.config(text=f"Total: {formatear_pesos(self.sistema.total_mesa(self.mesa_sel))}")
        self.ent_comensales.config(state="normal" if mesa["estado"] == "Libre" else "disabled")

    def _actualizar_combo_productos(self):
        nombres = [p["nombre"] for p in self.sistema.listar_productos()]
        self.combo_producto["values"] = nombres
        if self.var_producto.get() not in nombres:
            self.var_producto.set(nombres[0] if nombres else "")
        self._info_producto()

    def _info_producto(self):
        producto = self.sistema.buscar_producto(self.var_producto.get())
        if producto is None:
            self.lbl_info_producto.config(text="")
            return
        self.lbl_info_producto.config(
            text=f"{formatear_pesos(self.sistema.precios[producto])} | stock: {self.sistema.inventario[producto]}"
        )

    def _exigir_mesa(self):
        if self.mesa_sel is None:
            raise ErrorRestaurante("Seleccione primero una mesa de la lista.")
        return self.mesa_sel

    @manejar_errores
    def agregar_al_pedido(self):
        numero = self._exigir_mesa()
        mesa_libre = self.sistema.mesas[numero]["estado"] == "Libre"
        total = self.sistema.agregar_al_pedido(
            numero,
            self.var_producto.get(),
            self.var_cantidad.get(),
            self.var_comensales.get() if mesa_libre else None,
        )
        self.var_cantidad.set("1")
        self.var_comensales.set("")
        self.refrescar_todo()
        self.mensaje(f"Producto agregado a la mesa {numero}. Total parcial: {formatear_pesos(total)}.")

    @manejar_errores
    def quitar_linea(self):
        numero = self._exigir_mesa()
        seleccion = self.tree_pedido.selection()
        if not seleccion:
            raise ErrorRestaurante("Seleccione la línea del pedido que desea quitar.")
        self.sistema.quitar_del_pedido(numero, int(seleccion[0]))
        self.refrescar_todo()
        self.mensaje("Línea eliminada; las unidades volvieron al inventario.")

    @manejar_errores
    def cobrar_mesa(self):
        numero = self._exigir_mesa()
        mesa = self.sistema.mesas[numero]
        if mesa["estado"] == "Libre":
            raise ErrorRestaurante("La mesa ya está libre.")
        total = formatear_pesos(self.sistema.total_mesa(numero))
        if not messagebox.askyesno("Confirmar cobro", f"¿Cobrar la mesa {numero} por {total} y liberarla?", parent=self):
            return
        cuenta = self.sistema.cobrar_mesa(numero)
        lineas = [f"{i['cantidad']} x {i['producto']:<10} {formatear_pesos(i['subtotal']):>12}" for i in cuenta["detalle"]]
        lineas.append("-" * 32)
        lineas.append(f"{'TOTAL':<14} {formatear_pesos(cuenta['total']):>12}")
        self.refrescar_todo()
        self.mensaje(f"Mesa {numero} cobrada y liberada.")
        messagebox.showinfo(f"Cuenta mesa {numero}", "\n".join(lineas), parent=self)

    @manejar_errores
    def agregar_mesa(self):
        if not self.requiere_admin(): return
        numero = self.sistema.crear_mesa()
        self.refrescar_todo()
        self.mensaje(f"Mesa {numero} creada.")

    @manejar_errores
    def eliminar_mesa(self):
        if not self.requiere_admin(): return
        numero = self._exigir_mesa()
        if not messagebox.askyesno("Confirmar", f"¿Eliminar la mesa {numero}?", parent=self):
            return
        self.sistema.eliminar_mesa(numero)
        self.mesa_sel = None
        self.refrescar_todo()
        self.mensaje(f"Mesa {numero} eliminada.")

    # ------------------------------------------------------
    # PESTAÑA 2: INVENTARIO (Módulo 4 - solo administrador)
    # ------------------------------------------------------
    def _construir_tab_inventario(self):
        izq = ttk.LabelFrame(self.tab_inventario, text="Productos")
        izq.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.tree_inv = ttk.Treeview(
            izq, columns=("nombre", "precio", "stock", "estado"), show="headings", height=14, selectmode="browse"
        )
        for col, texto, ancho in (("nombre", "Producto", 180), ("precio", "Precio", 110), ("stock", "Stock", 80), ("estado", "Estado", 110)):
            self.tree_inv.heading(col, text=texto)
            self.tree_inv.column(col, width=ancho, anchor="center")
        self.tree_inv.tag_configure("bajo", foreground=COLOR_ERROR)
        self.tree_inv.pack(fill="both", expand=True, padx=6, pady=6)
        self.tree_inv.bind("<<TreeviewSelect>>", self._al_seleccionar_producto)

        der = ttk.LabelFrame(self.tab_inventario, text="Crear / editar producto")
        der.pack(side="left", fill="y", padx=(0, 8), pady=8)
        self.var_nombre = tk.StringVar()
        self.var_precio = tk.StringVar()
        self.var_stock = tk.StringVar()
        self.var_reabastecer = tk.StringVar(value="10")
        for fila, (texto, var) in enumerate((("Nombre:", self.var_nombre), ("Precio:", self.var_precio), ("Stock:", self.var_stock))):
            ttk.Label(der, text=texto).grid(row=fila, column=0, sticky="w", padx=8, pady=4)
            ttk.Entry(der, textvariable=var, width=20).grid(row=fila, column=1, padx=8, pady=4)
        ttk.Button(der, text="Crear producto nuevo", command=self.crear_producto).grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(10, 2))
        ttk.Button(der, text="Guardar cambios del seleccionado", command=self.actualizar_producto).grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        ttk.Button(der, text="Eliminar seleccionado", command=self.eliminar_producto).grid(row=5, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        ttk.Button(der, text="Limpiar formulario", command=self._limpiar_form_producto).grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=2)

        ttk.Separator(der).grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Label(der, text="Reabastecer seleccionado:").grid(row=8, column=0, columnspan=2, sticky="w", padx=8)
        ttk.Label(der, text="Cantidad:").grid(row=9, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(der, textvariable=self.var_reabastecer, width=20).grid(row=9, column=1, padx=8)
        ttk.Button(der, text="Reabastecer", command=self.reabastecer).grid(row=10, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        ttk.Label(der, text=f"Stock bajo: {STOCK_MINIMO} unidades o menos.", foreground="#555").grid(
            row=11, column=0, columnspan=2, padx=8, pady=(10, 0), sticky="w"
        )

    def refrescar_inventario(self):
        self.tree_inv.delete(*self.tree_inv.get_children())
        for p in self.sistema.listar_productos():
            self.tree_inv.insert(
                "", "end", iid=p["nombre"], tags=("bajo",) if p["stock_bajo"] else (),
                values=(p["nombre"], formatear_pesos(p["precio"]), p["stock"], "Stock bajo" if p["stock_bajo"] else "OK"),
            )
        if self.producto_sel in self.tree_inv.get_children():
            self.tree_inv.selection_set(self.producto_sel)
        else:
            self.producto_sel = None

    def _al_seleccionar_producto(self, _evento=None):
        seleccion = self.tree_inv.selection()
        if not seleccion:
            return
        self.producto_sel = seleccion[0]
        self.var_nombre.set(self.producto_sel)
        self.var_precio.set(str(self.sistema.precios[self.producto_sel]))
        self.var_stock.set(str(self.sistema.inventario[self.producto_sel]))

    def _limpiar_form_producto(self):
        self.producto_sel = None
        self.tree_inv.selection_remove(self.tree_inv.selection())
        for var in (self.var_nombre, self.var_precio, self.var_stock):
            var.set("")

    def _exigir_producto(self):
        if self.producto_sel is None:
            raise ErrorRestaurante("Seleccione primero un producto de la tabla.")
        return self.producto_sel

    @manejar_errores
    def crear_producto(self):
        if not self.requiere_admin(): return
        nombre = self.sistema.crear_producto(self.var_nombre.get(), self.var_precio.get(), self.var_stock.get())
        self._limpiar_form_producto()
        self.refrescar_todo()
        self.mensaje(f"Producto '{nombre}' creado.")

    @manejar_errores
    def actualizar_producto(self):
        if not self.requiere_admin(): return
        producto = self._exigir_producto()
        self.sistema.actualizar_producto(producto, precio=self.var_precio.get(), stock=self.var_stock.get())
        self.refrescar_todo()
        self.mensaje(f"Producto '{producto}' actualizado.")

    @manejar_errores
    def eliminar_producto(self):
        if not self.requiere_admin(): return
        producto = self._exigir_producto()
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el producto '{producto}'?", parent=self):
            return
        self.sistema.eliminar_producto(producto)
        self._limpiar_form_producto()
        self.refrescar_todo()
        self.mensaje(f"Producto '{producto}' eliminado.")

    @manejar_errores
    def reabastecer(self):
        if not self.requiere_admin(): return
        producto = self._exigir_producto()
        nuevo = self.sistema.reabastecer(producto, self.var_reabastecer.get())
        self.refrescar_todo()
        self.mensaje(f"Ahora hay {nuevo} unidades de {producto}.")

    # ------------------------------------------------------
    # PESTAÑA 4: ASISTENCIA (solo administrador)
    # ------------------------------------------------------
    def _construir_tab_asistencia(self):
        marco = ttk.LabelFrame(self.tab_asistencia, text="Registro de asistencia del personal")
        marco.pack(fill="both", expand=True, padx=8, pady=8)
        self.tree_asistencia = ttk.Treeview(marco, columns=("nombre", "fecha_hora", "estado"), show="headings", selectmode="browse")
        for col, txt, w in (("nombre", "Trabajador", 220), ("fecha_hora", "Fecha y hora", 220), ("estado", "Estado", 120)):
            self.tree_asistencia.heading(col, text=txt)
            self.tree_asistencia.column(col, width=w, anchor="center")
        self.tree_asistencia.pack(fill="both", expand=True, padx=6, pady=6)
        self.var_asistencia_nombre = tk.StringVar()
        self.var_asistencia_estado = tk.StringVar(value="Presente")
        formulario = ttk.Frame(marco)
        formulario.pack(fill="x", padx=6, pady=6)
        ttk.Label(formulario, text="Nombre:").grid(row=0, column=0, padx=4)
        ttk.Entry(formulario, textvariable=self.var_asistencia_nombre, width=28).grid(row=0, column=1, padx=4)
        ttk.Label(formulario, text="Estado:").grid(row=0, column=2, padx=4)
        ttk.Combobox(formulario, textvariable=self.var_asistencia_estado, values=("Presente", "Ausente", "Tarde"), state="readonly", width=12).grid(row=0, column=3, padx=4)
        ttk.Button(formulario, text="Registrar presente", command=self._asistencia_registrar).grid(row=1, column=0, padx=4, pady=5)
        ttk.Button(formulario, text="Editar seleccionado", command=self._asistencia_editar).grid(row=1, column=1, padx=4, pady=5)
        ttk.Button(formulario, text="Eliminar seleccionado", command=self._asistencia_eliminar).grid(row=1, column=2, padx=4, pady=5)

    def _refrescar_asistencia(self):
        if not hasattr(self, "tree_asistencia"): return
        self.tree_asistencia.delete(*self.tree_asistencia.get_children())
        for ix, registro in enumerate(listar_asistencias()):
            self.tree_asistencia.insert("", "end", iid=str(ix), values=(registro["nombre"], registro["fecha_hora"], registro["estado"]))

    def _asistencia_registrar(self):
        if not self.requiere_admin(): return
        try: 
            registrar_asistencia(self.var_asistencia_nombre.get(), "Presente")
        except (ValueError, RuntimeError) as e: 
            messagebox.showerror("Asistencia", str(e), parent=self)
            return
        self.var_asistencia_nombre.set("")
        self._refrescar_asistencia()

    def _asistencia_editar(self):
        if not self.requiere_admin(): return
        sel = self.tree_asistencia.selection()
        if not sel: 
            messagebox.showwarning("Asistencia", "Seleccione un registro.", parent=self)
            return
        try: 
            editar_asistencia(int(sel[0]), self.var_asistencia_nombre.get(), self.var_asistencia_estado.get())
        except (ValueError, RuntimeError) as e: 
            messagebox.showerror("Asistencia", str(e), parent=self)
            return
        self._refrescar_asistencia()

    def _asistencia_eliminar(self):
        if not self.requiere_admin(): return
        sel = self.tree_asistencia.selection()
        if not sel: 
            messagebox.showwarning("Asistencia", "Seleccione un registro.", parent=self)
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar el registro seleccionado?", parent=self): 
            return
        try: 
            eliminar_asistencia(int(sel[0]))
        except (ValueError, RuntimeError) as e: 
            messagebox.showerror("Asistencia", str(e), parent=self)
            return
        self._refrescar_asistencia()

    # ------------------------------------------------------
    # PESTAÑA 3: VENTAS (Módulo 4 - solo administrador)
    # ------------------------------------------------------
    def _construir_tab_ventas(self):
        izq = ttk.LabelFrame(self.tab_ventas, text="Ventas de hoy")
        izq.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        self.tree_ventas = ttk.Treeview(izq, columns=("hora", "mesa", "total", "detalle"), show="headings", height=14)
        for col, texto, ancho in (("hora", "Hora", 80), ("mesa", "Mesa", 60), ("total", "Total", 110), ("detalle", "Detalle", 260)):
            self.tree_ventas.heading(col, text=texto)
            self.tree_ventas.column(col, width=ancho, anchor="center")
        self.tree_ventas.pack(fill="both", expand=True, padx=6, pady=6)
        self.lbl_total_ventas = tk.Label(izq, text="Total recaudado: $0", font=("Segoe UI", 13, "bold"), anchor="e")
        self.lbl_total_ventas.pack(fill="x", padx=8, pady=(0, 6))

        der = ttk.LabelFrame(self.tab_ventas, text="Unidades vendidas por producto")
        der.pack(side="left", fill="both", padx=(0, 8), pady=8)
        self.canvas = tk.Canvas(der, width=320, height=300, bg="white", highlightthickness=0)
        self.canvas.pack(padx=8, pady=8)

    def refrescar_ventas(self):
        ventas = self.sistema.ventas_del_dia()
        self.tree_ventas.delete(*self.tree_ventas.get_children())
        unidades = {}
        for v in ventas:
            detalle = ", ".join(f"{i['cantidad']} x {i['producto']}" for i in v["detalle"])
            self.tree_ventas.insert("", "end", values=(v["fecha"][11:], v["mesa"], formatear_pesos(v["total"]), detalle))
            for i in v["detalle"]:
                unidades[i["producto"]] = unidades.get(i["producto"], 0) + i["cantidad"]
        self.lbl_total_ventas.config(text=f"Total recaudado: {formatear_pesos(self.sistema.total_ventas_del_dia())}")
        self._dibujar_grafico(unidades)

    def _dibujar_grafico(self, unidades):
        c = self.canvas
        c.delete("all")
        if not unidades:
            c.create_text(160, 150, text="Aún no hay ventas hoy", fill="#777")
            return
        maximo = max(unidades.values())
        ancho_barra = min(60, 280 // len(unidades) - 10)
        base = 260
        for i, (producto, cantidad) in enumerate(unidades.items()):
            x0 = 25 + i * (ancho_barra + 10)
            alto = int(200 * cantidad / maximo)
            c.create_rectangle(x0, base - alto, x0 + ancho_barra, base, fill="#4a7bd0", outline="")
            c.create_text(x0 + ancho_barra / 2, base - alto - 10, text=str(cantidad))
            c.create_text(x0 + ancho_barra / 2, base + 14, text=producto[:9], font=("Segoe UI", 8))


if __name__ == "__main__":
    App().mainloop()
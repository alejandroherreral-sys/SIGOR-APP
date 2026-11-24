# SIGOR - Aplicación de consola integrada con backend.py y auth_sigor.py
import time
from datetime import datetime
from backend import Restaurante, ErrorRestaurante, formatear_pesos
from auth_sigor import registrar_usuario, iniciar_sesion, listar_asistencias, registrar_asistencia, editar_asistencia, eliminar_asistencia, exigir_admin

def carga():
    print("\nIniciando SIGOR")
    for i in range(1,6):
        print(f"\rCargando módulos [{'#'*i}{'.'*(5-i)}] {i*20}%",end="",flush=True)
        time.sleep(0.25)
    print("\n")

def acceso():
    while True:
        print("=== ACCESO SIGOR ===\n1. Iniciar sesión\n2. Registrarse\n0. Salir")
        op=input("Opción: ").strip()
        if op=="0": return None
        if op=="2":
            usuario=input("Nombre de usuario: ").strip()
            clave=input("Contraseña (mín. 6 caracteres): ")
            rol=input("Rol (Administrador/Mesero): ").strip().capitalize()
            codigo=input("Código de seguridad de 4 dígitos: ").strip()
            try:
                registrar_usuario(usuario,clave,rol,codigo)
                print("Cuenta registrada. Ya puede iniciar sesión.\n")
            except ValueError as e: print("Registro denegado:",e)
        elif op=="1":
            usuario=input("Usuario: ").strip()
            clave=input("Contraseña: ")
            ses=iniciar_sesion(usuario,clave)
            if ses: print(f"Acceso concedido: {ses['usuario']} ({ses['rol']}) - {ses['fecha_hora']}"); return ses
            print("Usuario o contraseña incorrectos.")
        else: print("Opción inválida.")

def menu():
    carga()
    ses=acceso()
    if not ses: print("Programa finalizado."); return
    sistema=Restaurante()
    admin=ses["rol"]=="Administrador"
    while True:
        print(f"\n=== SIGOR | {ses['usuario']} | {ses['rol']} ===")
        print("1. Estado de mesas\n2. Registrar pedido\n3. Cobrar y liberar mesa\n4. Consultar menú/inventario")
        if admin:
            print("5. Crear producto\n6. Actualizar stock/precio\n7. Eliminar producto\n8. Reabastecer\n9. Ver ventas del día\n10. Gestionar asistencia\n11. Consultar auditoría de sesiones")
        print("0. Cerrar sesión y salir")
        op=input("Opción: ").strip()
        try:
            if op=="0": break
            if op=="1":
                for m in sistema.listar_mesas(): print(f"Mesa {m['numero']} | {m['estado']} | comensales {m['comensales']} | {formatear_pesos(m['total'])}")
            elif op=="2":
                n=int(input("Mesa: "))
                p=input("Producto: ")
                c=input("Cantidad: ")
                com=input("Comensales (solo mesa libre): ")
                print("Total parcial:",formatear_pesos(sistema.agregar_al_pedido(n,p,c,com or None)))
            elif op=="3":
                n=int(input("Mesa a cobrar: "))
                venta=sistema.cobrar_mesa(n); print("Cuenta cobrada:",formatear_pesos(venta["total"]))
            elif op=="4":
                for p in sistema.listar_productos(): print(f"{p['nombre']}: stock {p['stock']} | {formatear_pesos(p['precio'])}")
            elif op in {"5","6","7","8","9","10","11"}:
                exigir_admin(ses)
                if op=="5":
                    sistema.crear_producto(input("Nombre: "),input("Precio: "),input("Stock: "))
                elif op=="6":
                    for p in sistema.listar_productos(): print(p["nombre"],p["precio"],p["stock"])
                    p=sistema.buscar_producto(input("Producto: "))
                    if not p: raise ErrorRestaurante("Producto no encontrado.")
                    sistema.actualizar_producto(p,input("Nuevo precio: "),input("Nuevo stock: "))
                elif op=="7":
                    p=sistema.buscar_producto(input("Producto a eliminar: "))
                    if not p: raise ErrorRestaurante("Producto no encontrado.")
                    sistema.eliminar_producto(p)
                elif op=="8":
                    p=sistema.buscar_producto(input("Producto: "))
                    if not p: raise ErrorRestaurante("Producto no encontrado.")
                    sistema.reabastecer(p,input("Cantidad: "))
                elif op=="9": print("Total ventas de hoy:",formatear_pesos(sistema.total_ventas_del_dia()))
                elif op=="10":
                    while True:
                        print("\nASISTENCIA: 1 Registrar presente | 2 Listar | 3 Editar | 4 Eliminar | 0 Volver")
                        a=input("Opción: ").strip()
                        if a=="0": break
                        registros=listar_asistencias()
                        if a=="1": registrar_asistencia(input("Nombre trabajador: ")); print("Asistencia registrada.")
                        elif a=="2":
                            for ix,r in enumerate(registros): print(ix,r["nombre"],r["fecha_hora"],r["estado"])
                        elif a=="3":
                            ix=int(input("Índice: ")); nombre=input("Nombre actualizado: "); estado=input("Estado (Presente/Ausente/Tarde): ").strip().capitalize()
                            editar_asistencia(ix,nombre,estado); print("Registro actualizado.")
                        elif a=="4": eliminar_asistencia(int(input("Índice: "))); print("Registro eliminado.")
                        else: print("Opción inválida.")
                elif op=="11":
                    from auth_sigor import listar_sesiones
                    for r in listar_sesiones(): print(r["usuario"],r["rol"],r["fecha_hora"])
            else: print("Opción inválida.")
        except (ValueError,ErrorRestaurante,PermissionError,RuntimeError,KeyError) as e: print("Error:",e)
    print("Sesión finalizada.")

if __name__=="__main__":
    try: menu()
    except (KeyboardInterrupt,EOFError): print("\nSIGOR cerrado.")

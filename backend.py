# Backend SIGOR para interfaz.py. Datos operativos compartidos en JSON.
import os, json
from datetime import datetime
STOCK_MINIMO=5
ARCHIVO_DATOS=os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_restaurante.json")
class ErrorRestaurante(Exception): pass
def formatear_pesos(valor): return f"${valor:,.0f}".replace(",", ".")
class Restaurante:
    def __init__(self):
        self.inventario={"Carne":10,"Arroz":20,"Papas":15,"Bebida":30}
        self.precios={"Carne":25000,"Arroz":8000,"Papas":9000,"Bebida":5000}
        self.mesas={i:{"estado":"Libre","comensales":0,"pedido":[]} for i in range(1,4)}
        self.ventas=[]
        self.cargar()
    def guardar(self):
        d={"inventario":self.inventario,"precios":self.precios,
           "mesas":{str(n):{"estado":m["estado"],"comensales":m["comensales"],"pedido":m["pedido"]} for n,m in self.mesas.items()},
           "ventas":self.ventas}
        with open(ARCHIVO_DATOS+".tmp","w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)
        os.replace(ARCHIVO_DATOS+".tmp",ARCHIVO_DATOS)
    def cargar(self):
        if not os.path.exists(ARCHIVO_DATOS): self.guardar(); return
        try:
            with open(ARCHIVO_DATOS,encoding="utf-8") as f: d=json.load(f)
            self.inventario={k:int(v) for k,v in d["inventario"].items()}; self.precios={k:int(v) for k,v in d["precios"].items()}
            self.mesas={int(n):{"estado":m["estado"],"comensales":int(m["comensales"]),"pedido":m["pedido"]} for n,m in d["mesas"].items()}
            self.ventas=d.get("ventas",[])
        except (OSError,ValueError,KeyError,TypeError):
            raise ErrorRestaurante("No se pudo leer datos_restaurante.json.")
    def listar_mesas(self):
        return [{"numero":n,"estado":m["estado"],"comensales":m["comensales"],"total":self.total_mesa(n)} for n,m in self.mesas.items()]
    def listar_productos(self):
        return [{"nombre":p,"precio":self.precios[p],"stock":s,"stock_bajo":s<=STOCK_MINIMO} for p,s in self.inventario.items()]
    def buscar_producto(self,nombre):
        return next((p for p in self.inventario if p.casefold()==str(nombre).strip().casefold()),None)
    def total_mesa(self,n): return sum(int(i["precio"])*int(i["cantidad"]) for i in self.mesas[n]["pedido"])
    def agregar_al_pedido(self,n,producto,cantidad,comensales=None):
        p=self.buscar_producto(producto)
        if p is None: raise ErrorRestaurante("Producto inexistente.")
        try: c=int(cantidad)
        except ValueError: raise ErrorRestaurante("Cantidad debe ser un entero.")
        if c<1 or c>self.inventario[p]: raise ErrorRestaurante("Cantidad inválida o stock insuficiente.")
        m=self.mesas[n]
        if m["estado"]=="Libre":
            try: com=int(comensales)
            except (TypeError,ValueError): raise ErrorRestaurante("Indique comensales para la mesa.")
            if com<1: raise ErrorRestaurante("Comensales debe ser al menos 1.")
            m["comensales"]=com; m["estado"]="Ocupada"
        self.inventario[p]-=c; m["pedido"].append({"producto":p,"cantidad":c,"precio":self.precios[p]}); self.guardar()
        return self.total_mesa(n)
    def quitar_del_pedido(self,n,idx):
        m=self.mesas[n]
        if idx<0 or idx>=len(m["pedido"]): raise ErrorRestaurante("Línea de pedido inválida.")
        item=m["pedido"].pop(idx); self.inventario[item["producto"]]+=int(item["cantidad"])
        if not m["pedido"]: m.update({"estado":"Libre","comensales":0})
        self.guardar()
    def cobrar_mesa(self,n):
        m=self.mesas[n]
        if m["estado"]=="Libre": raise ErrorRestaurante("La mesa ya está libre.")
        detalle=[dict(i,subtotal=int(i["precio"])*int(i["cantidad"])) for i in m["pedido"]]
        venta={"fecha":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"mesa":n,"total":self.total_mesa(n),"detalle":detalle}
        self.ventas.append(venta); m.update({"estado":"Libre","comensales":0,"pedido":[]}); self.guardar(); return venta
    def crear_mesa(self):
        n=max(self.mesas.keys(),default=0)+1; self.mesas[n]={"estado":"Libre","comensales":0,"pedido":[]}; self.guardar(); return n
    def eliminar_mesa(self,n):
        if self.mesas[n]["estado"]!="Libre": raise ErrorRestaurante("No se puede eliminar mesa ocupada.")
        del self.mesas[n]; self.guardar()
    def crear_producto(self,nombre,precio,stock):
        nombre=str(nombre).strip()
        if not nombre or len(nombre)>30 or self.buscar_producto(nombre): raise ErrorRestaurante("Nombre vacío, demasiado largo o duplicado.")
        try: pr=int(precio); st=int(stock)
        except ValueError: raise ErrorRestaurante("Precio y stock deben ser enteros.")
        if pr<1 or st<0: raise ErrorRestaurante("Precio debe ser positivo y stock no negativo.")
        self.inventario[nombre]=st; self.precios[nombre]=pr; self.guardar(); return nombre
    def actualizar_producto(self,p,precio,stock):
        try: pr=int(precio); st=int(stock)
        except ValueError: raise ErrorRestaurante("Precio y stock deben ser enteros.")
        if pr<1 or st<0: raise ErrorRestaurante("Precio inválido o stock negativo.")
        self.precios[p]=pr; self.inventario[p]=st; self.guardar()
    def eliminar_producto(self,p):
        if any(any(i["producto"]==p for i in m["pedido"]) for m in self.mesas.values()): raise ErrorRestaurante("Producto está en un pedido.")
        del self.inventario[p]; del self.precios[p]; self.guardar()
    def reabastecer(self,p,cantidad):
        try: c=int(cantidad)
        except ValueError: raise ErrorRestaurante("Cantidad inválida.")
        if c<1: raise ErrorRestaurante("Cantidad debe ser positiva.")
        self.inventario[p]+=c; self.guardar(); return self.inventario[p]
    def ventas_del_dia(self):
        hoy=datetime.now().strftime("%Y-%m-%d"); return [v for v in self.ventas if v["fecha"].startswith(hoy)]
    def total_ventas_del_dia(self): return sum(int(v["total"]) for v in self.ventas_del_dia())

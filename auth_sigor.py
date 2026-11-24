# SIGOR - Autenticacion, auditoria y asistencia compartidas
import os, json, hashlib, hmac, secrets
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVO = os.path.join(DIR, "usuarios_sigor.json")
CODIGO_REGISTRO = "2703"
MIN_CLAVE = 6

def _leer():
    if not os.path.exists(ARCHIVO):
        return {"usuarios": [], "sesiones": [], "asistencias": []}
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            data=json.load(f)
        for key in ("usuarios","sesiones","asistencias"):
            data.setdefault(key, [])
        return data
    except (OSError, ValueError):
        raise RuntimeError("El archivo usuarios_sigor.json está dañado.")

def _guardar(data):
    tmp=ARCHIVO+".tmp"
    with open(tmp,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(tmp,ARCHIVO)

def _hash(clave, sal):
    return hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal), 200000).hex()

def registrar_usuario(usuario, clave, rol, codigo):
    usuario=usuario.strip()
    if codigo != CODIGO_REGISTRO:
        raise ValueError("Código de seguridad incorrecto. Registro denegado.")
    if not usuario or len(usuario)>40:
        raise ValueError("El usuario debe tener entre 1 y 40 caracteres.")
    if len(clave)<MIN_CLAVE:
        raise ValueError(f"La contraseña debe tener al menos {MIN_CLAVE} caracteres.")
    if rol not in ("Administrador","Mesero"):
        raise ValueError("Rol no válido.")
    data=_leer()
    if any(u["usuario"].casefold()==usuario.casefold() for u in data["usuarios"]):
        raise ValueError("Ese nombre de usuario ya existe.")
    sal=secrets.token_hex(16)
    data["usuarios"].append({"usuario":usuario,"rol":rol,"sal":sal,"hash":_hash(clave,sal)})
    _guardar(data)
    return True

def iniciar_sesion(usuario, clave):
    data=_leer()
    for u in data["usuarios"]:
        if u["usuario"].casefold()==usuario.strip().casefold() and hmac.compare_digest(_hash(clave,u["sal"]),u["hash"]):
            ses={"usuario":u["usuario"],"rol":u["rol"],"fecha_hora":datetime.now().isoformat(sep=" ",timespec="seconds")}
            data["sesiones"].append(ses)
            _guardar(data)
            return {"usuario":u["usuario"],"rol":u["rol"],"fecha_hora":ses["fecha_hora"]}
    return None

def listar_sesiones():
    return list(_leer()["sesiones"])

def registrar_asistencia(nombre, estado="Presente"):
    nombre=nombre.strip()
    if not nombre: raise ValueError("El nombre del trabajador es obligatorio.")
    data=_leer()
    data["asistencias"].append({"nombre":nombre,"fecha_hora":datetime.now().isoformat(sep=" ",timespec="seconds"),"estado":estado})
    _guardar(data)
    return len(data["asistencias"])-1

def listar_asistencias():
    return list(_leer()["asistencias"])

def editar_asistencia(indice, nombre, estado):
    data=_leer()
    if indice<0 or indice>=len(data["asistencias"]): raise ValueError("Registro de asistencia inexistente.")
    if not nombre.strip(): raise ValueError("El nombre es obligatorio.")
    data["asistencias"][indice]["nombre"]=nombre.strip()
    data["asistencias"][indice]["estado"]=estado
    data["asistencias"][indice]["fecha_hora"]=datetime.now().isoformat(sep=" ",timespec="seconds")
    _guardar(data)

def eliminar_asistencia(indice):
    data=_leer()
    if indice<0 or indice>=len(data["asistencias"]): raise ValueError("Registro de asistencia inexistente.")
    del data["asistencias"][indice]
    _guardar(data)

def exigir_admin(sesion):
    if not sesion or sesion.get("rol")!="Administrador":
        raise PermissionError("Acción permitida únicamente a Administradores.")

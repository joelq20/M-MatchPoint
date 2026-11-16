"""Funciones de registro, acceso y administración del menú administrativo."""

import json

from jinja2 import Template
import random as rn

from reader import read_admin
from reader import read_courts
from writer import write_admin
from writer import write_courts
from notifications import mostrar_notificaciones_admin

def validar_dni()-> int:
    """Precondición: el archivo de administradores puede leerse.

    Postcondición: devuelve un DNI entero único de 7 u 8 dígitos; sigue
    solicitándolo hasta recibir uno válido.
    """

    data = read_admin() # ahora data poseea todo el contenido de disccionarios 

    while True:
        try:
            dni= int(input("dni:  "))
        except(ValueError):
            print("X - ERROR DNI - USE SOLO NUMEROS - X")
            continue

        duplicado = any(u.get("dni") == dni for u in data)
        if duplicado: # si es dupli
            print("X - DNI YA EXISTENTE - X")
            continue

        
        longitud = list(str(dni)) # conversion 
        if len(longitud) >= 7 and len(longitud) <= 8: 
                return dni
        else:
            print("X - DNI INVALIDO - X")


def validar_name():
    """Precondición: ninguna; solicita un nombre por consola.

    Postcondición: devuelve el nombre sin espacios externos si contiene solo
    letras; en caso contrario, vuelve a solicitarlo.
    """

    while True:

        name = input("INGRESE SU NOMBRE:  ").strip()
        if name.isalpha():
            return name
        
        else:
            print("X - EL NOMBRE SOLO DEBE CONTENER LETRAS - X")
            

def validar_psw():
    """Precondición: ninguna; solicita una contraseña por consola.

    Postcondición: devuelve una contraseña de seis caracteres con al menos una
    letra y un número; en caso contrario, vuelve a solicitarla.
    """

    while True:

        psw = input("ingrese una contraseña de 6 caracteres que combine letras y numeros: ")
        longi = list(psw)

        contiene_letr = any(i.isalpha() for i in psw) #buscador de letras
        contiene_num = any(i.isdigit() for i in psw)# buscador de numeros

        if len(longi) == 6:
            if contiene_letr and contiene_num:
                return psw
            else:
                print("X - LA CONTRASEÑA DEBE CONTENER AL MENOS LETRAS Y NUMEROS- X")
        elif len(longi) > 6:
            print("X - ERROR - CONTRASEÑA DEMASIADO LARGA - X")
        else:
            print("X - ERROR - CONTRASEÑA DEMASIADO CORTA - X")

def choose_court():
    """Precondición: el archivo de canchas puede leerse.

    Postcondición: muestra una cancha existente y devuelve su ID para asociarla
    al administrador; repite la solicitud ante IDs inválidos.
    """
    data = read_courts() # vuelve a llamar al json correspondiente 


    while True:
        try:
            id_empresa = int(input("INGRESE EL ID DE LA EMPRESA:  "))
        except(ValueError):
            print("X - INGRESE SOLO NÚMEROS - X")    
            continue
        
        confirm = any(u.get("id") == id_empresa for u in data)
        if confirm:
            court = [i for i in data if i["id"] == id_empresa]

            plantilla = """
----------------------------------------------------------------
                    EMPRESA SELECCIONADA
----------------------------------------------------------------
{% for info in cancha -%}
{{ info.data | join(',') | upper  }}
-----------------------------------------------------------------
{% endfor %}
"""
            mi_plantilla = Template(plantilla)
            print(mi_plantilla.render(cancha = court))

            return id_empresa
        
        else:
            print("X - ID NO VÁLIDO - X")

            
def mostrar_admin_courts() -> None:
    """Precondición: ninguna; intenta leer el archivo de canchas.

    Postcondición: muestra las canchas sin modificarlas y espera 0 para volver;
    si falla la lectura, informa el error y regresa.
    """

    try:
        courts = read_courts()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar las canchas: {error}")
        return

    plantilla = """
===================================================================
                    CANCHAS REGISTRADAS
===================================================================
{% for cancha in canchas %}
ID: {{ cancha.id }}
CANCHA: {{ cancha.data | default([]) | join(', ') | upper }}
HORARIO: {{ cancha.apertura }}:00 a {{ cancha.cierre }}:00
DIAS: {{ cancha.dias_abiertos | join(', ') | upper }}
TELÉFONO: {{ cancha.phone | default([]) | join(', ') }}
ESTADO: {{ "HABILITADA" if cancha.available else "NO DISPONIBLE" }}
-------------------------------------------------------------------
{% endfor %}
"""
    print(Template(plantilla).render(canchas=courts))

    while input("Ingrese 0 para regresar al menú: ").strip() != "0":
        print("Opción inválida. Ingrese 0 para regresar.")


def administrar_admin_courts() -> None:
    """Precondición: el archivo contiene canchas con disponibilidad booleana.

    Postcondición: si el administrador confirma, invierte y guarda el estado de
    la cancha elegida; si cancela o ocurre un error, informa y regresa.
    """

    try:
        courts = read_courts()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar las canchas: {error}")
        return

    if not courts:
        print("No hay canchas registradas para administrar.")
        return

    plantilla = """
===================================================================
                    ADMINISTRAR CANCHAS
===================================================================
{% for cancha in canchas %}
ID: {{ cancha.id }}
CANCHA: {{ cancha.data | default([]) | join(', ') | upper }}
ESTADO ACTUAL: {{ "HABILITADA" if cancha.available else "BLOQUEADA" }}
-------------------------------------------------------------------
{% endfor %}
"""
    print(Template(plantilla).render(canchas=courts))

    # Se vuelve a pedir el ID si no es numérico o no corresponde a una cancha.
    while True:

        entrada = input("Ingrese el ID de la cancha (0 para volver): ").strip()
        if entrada == "0":
            return
        
        if not entrada.isdigit():
            print("Ingrese un ID numérico.")
            continue

        court_id = int(entrada)
        court = next((item for item in courts if item.get("id") == court_id), None)

        if court is None:
            print("No existe una cancha con ese ID.")
            continue

        if not isinstance(court.get("available"), bool): # si no ser bool
            print("No se puede cambiar el estado: el dato de disponibilidad no es válido.")
            return

        # El nuevo estado siempre invierte el actual: habilitada pasa a bloqueada y viceversa.

        nuevo_estado = not court["available"] # invierte el valor 
        accion = "habilitar" if nuevo_estado else "bloquear" 

        confirmacion = input(
            f"¿Confirma que desea {accion} esta cancha? (s/n): "
        ).strip().lower()

        if confirmacion not in ("s", "si","sí"):
            print("Cambio cancelado.")
            return

        # Solo se modifica y persiste después de que el administrador confirma.
        court["available"] = nuevo_estado 

        try:
            write_courts(courts)
        except OSError as error:
            print(f"No se pudo guardar el estado de la cancha: {error}")
            return

        estado = "habilitada" if nuevo_estado else "bloqueada"
        print(f"Cancha {estado} correctamente.")
        return


def admin_menu(admin: dict) -> None:
    """Precondición: ``admin`` es el administrador autenticado.

    Postcondición: dirige las opciones disponibles y regresa al seleccionar
    cerrar sesión. La consulta administrativa de reservas sigue provisional.
    """
    plantilla = """
===================================================================
               MATCH POINT - MENÚ ADMINISTRATIVO
===================================================================
BIENVENIDO, {{ name | upper }}
-------------------------------------------------------------------
1 - CONSULTAR CANCHAS
2 - ADMINISTRAR CANCHAS
3 - CONSULTAR RESERVAS
4 - VER NOTIFICACIONES
5 - CERRAR SESIÓN
-------------------------------------------------------------------
    """
    while True:
        print(Template(plantilla).render(admin))
        try:
            opcion = int(input("Seleccione una opción: "))
        except ValueError:
            print("X - INGRESE SOLO NÚMEROS - X")
            continue

        match opcion:
            case 1:
                mostrar_admin_courts()
            case 2:
                administrar_admin_courts()
            case 3:
                # Esta sección todavía es provisional y no consulta reservas.
                print("La consulta de reservas todavía no está implementada, falta definir.")
            case 4:
                mostrar_notificaciones_admin()
            case 5:
                print("CERRANDO SESIÓN ADMINISTRATIVA.")
                return
            case _:
                print("X - OPCIÓN FUERA DE RANGO - X")


def iniciar_sesion_admin() -> dict | None:
    """Precondición: el archivo de administradores puede leerse.

    Postcondición: devuelve el registro si coinciden DNI y contraseña; en caso
    de credenciales incorrectas o error de lectura, informa y devuelve None.
    """

    try:
        data = read_admin()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar los administradores: {error}")
        return None

    dni = input("DNI: ").strip()
    psw = input("Contraseña: ")

    if not dni.isdigit() or not 7 <= len(dni) <= 8:
        print("DNI o contraseña incorrectos.")
        return None

    admin = next(
        (
            item
            for item in data
            if item.get("dni") is not None
            and str(item.get("dni")) == dni
            and item.get("psw") == psw
        ),
        None,
    )
    if admin is None:
        print("DNI o contraseña incorrectos.")
        return None

    print(f"INICIO DE SESIÓN CORRECTO. BIENVENIDO, {admin.get('name', '').upper()}.")
    return admin

def registro_admin():
    """Precondición: los datos solicitados son válidos y los archivos necesarios
    de administradores y canchas pueden leerse y escribirse.

    Postcondición: agrega y devuelve el administrador asociado a una cancha;
    propaga errores de lectura o escritura.
    """
    dni= validar_dni()
    name = validar_name()
    psw = validar_psw()
    idc = choose_court()

    data = read_admin()
    admin_id = rn.randint(1_000_000, 99_000_000)
    while any(admin.get("id") == admin_id for admin in data):
        admin_id = rn.randint(1_000_000, 99_000_000)

    new_admin = { "id": admin_id,
                 "dni" : dni,
                 "name": name,
                 "psw" : psw,
                 "court": idc
    } 

    data.append(new_admin)

    write_admin(data)
    print("ADMINISTRADOR REGISTRADO CORRECTAMENTE.")
    return new_admin

def admin_menu_login():
    """Precondición: ninguna; presenta el menú de acceso administrativo.

    Postcondición: regresa al menú principal al salir, tras una sesión exitosa o
    después de agotar los tres intentos de inicio de sesión.
    """
    plantilla = """
--------------------------------------------------------
                LOGIN ADMINISTRATIVO
--------------------------------------------------------
1 REGISTRAR NUEVO ADMIN
2 INICIAR SESIÓN
3 SALIR

    """
    mi_plantilla = Template(plantilla)
    while True:
        print(mi_plantilla.render())
        try:
            opcion = int(input())
        except ValueError:
            print("X - ERROR MENU - INGRESE SOLO NUMEROS - X")
            continue

        match opcion:
            case 1:
                try:
                    registro_admin()
                except (OSError, json.JSONDecodeError, ValueError) as error:
                    print(f"No se pudo registrar el administrador: {error}")

            case 2:
                for intento in range(3):
                    admin = iniciar_sesion_admin()

                    if admin is not None:
                        admin_menu(admin)
                        return

                    if intento < 2:
                        print(f"Te quedan {2 - intento} intentos.")

                print("Se alcanzó el máximo de intentos.")
                return
            case 3:
                return
            case _:
                print("-----------------------------------------------------")
                print("            x - OPCION FUERA DE RANGO - x            ")
                print("-----------------------------------------------------")

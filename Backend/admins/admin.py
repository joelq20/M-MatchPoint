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
    """Precondición: el archivo de administradores puede leerse y la entrada
    estándar está disponible.

    Postcondición: devuelve un DNI entero único de 7 u 8 dígitos, solicitándolo
    de nuevo hasta recibir una entrada válida. Propaga errores al leer el archivo.
    """
    # Obtiene los administradores registrados para comprobar DNI duplicados
    data = read_admin() 

    while True:
        
        entrada = input("dni:  ").strip()

         # Comprueba que la entrada contenga únicamente dígitos.
        if not entrada.isascii() or not entrada.isdigit():
            print("X - ERROR DNI - USE SOLO NUMEROS - X")
            continue

        # Comprueba que el DNI tenga entre 7 y 8 dígitos.
        dni = int(entrada)
        if not 7 <= len(str(dni)) <= 8:
            print("X - DNI INVALIDO - X")
            continue

        duplicado = False
        # Busca si el DNI ya pertenece a otro administrador.
        for usuario in data:
            if usuario.get("dni") == dni:
                duplicado = True
                break

        if duplicado:
            print("X - DNI YA EXISTENTE - X")
            continue

        return dni


def validar_name():
    """Precondición: la entrada estándar está disponible.

    Postcondición: devuelve el nombre sin espacios externos cuando contiene
    solo letras; en caso contrario, vuelve a solicitarlo.
    """

    while True:

        name = input("INGRESE SU NOMBRE:  ").strip()
        if name.isalpha():
            return name
        
        else:
            print("X - EL NOMBRE SOLO DEBE CONTENER LETRAS - X")
            

def validar_psw():
    """Precondición: la entrada estándar está disponible.

    Postcondición: devuelve una contraseña de seis caracteres con al menos una
    letra y un dígito; en caso contrario, vuelve a solicitarla.
    """

    while True:
        psw = input(
            "Ingrese una contraseña de 6 caracteres que combine letras y números: "
        )

        if len(psw) > 6:
            print("X - ERROR - CONTRASEÑA DEMASIADO LARGA - X")
            continue

        if len(psw) < 6:
            print("X - ERROR - CONTRASEÑA DEMASIADO CORTA - X")
            continue

        contiene_letr = False
        contiene_num = False

        # Recorre la contraseña para comprobar si contiene letras y números.
        for caracter in psw:
            if caracter.isalpha():
                contiene_letr = True

            if caracter.isdigit():
                contiene_num = True

        if contiene_letr and contiene_num:
            return psw

        print("X - LA CONTRASEÑA DEBE CONTENER AL MENOS LETRAS Y NUMEROS - X")

def choose_court():
    """Precondición: el archivo de canchas puede leerse y la entrada estándar
    está disponible.

    Postcondición: muestra la cancha cuyo ID se ingresó y devuelve ese ID;
    vuelve a solicitarlo si no es un entero o no corresponde a una cancha.
    Propaga errores al leer el archivo.
    """ 
    # Obtiene las canchas registradas en el archivo JSON.
    data = read_courts()

    while True:
        try:
            id_empresa = int(input("INGRESE EL ID DE LA EMPRESA:  "))
        except ValueError:
            print("X - INGRESE SOLO NÚMEROS - X")
            continue

        # Busca la cancha que coincide con el ID ingresado.
        court = []

        for empresa in data:
            if empresa.get("id") == id_empresa:
                court.append(empresa)
                break

        if court:
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
            print(mi_plantilla.render(cancha=court))

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
    """Precondición: los archivos de canchas están disponibles y la entrada
    estándar está disponible.

    Postcondición: permite invertir y guardar la disponibilidad de una cancha
    después de confirmarlo. Regresa si se cancela, no hay canchas o informa un
    error de lectura, datos o escritura.
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
        # Busca la cancha correspondiente al ID ingresado.
        court = None

        for item in courts:
            if item.get("id") == court_id:
                court = item
                break

        if court is None:
            print("No existe una cancha con ese ID.")
            continue

        if not isinstance(court.get("available"), bool):
            print("No se puede cambiar el estado: el dato de disponibilidad no es válido.")
            return

        # Invierte el estado actual de la cancha.
        nuevo_estado = not court["available"]

        if nuevo_estado:
            accion = "habilitar"
        else:
            accion = "bloquear"

        confirmacion = input(
            f"¿Confirma que desea {accion} esta cancha? (s/n): "
        ).strip().lower()

        if confirmacion not in ("s", "si", "sí"):
            print("Cambio cancelado.")
            return

        # Solo se modifica y persiste después de que el administrador confirma.
        court["available"] = nuevo_estado

        try:
            write_courts(courts)
        except (OSError, TypeError) as error:
            print(f"No se pudo guardar el estado de la cancha: {error}")
            return

        if nuevo_estado:
            estado = "habilitada"
        else:
            estado = "bloqueada"

        print(f"Cancha {estado} correctamente.")
        return


def admin_menu(admin: dict) -> None:
    """Precondición: ``admin`` es el diccionario del administrador autenticado
    y la entrada estándar está disponible.

    Postcondición: muestra el menú y ejecuta la opción elegida hasta que el
    administrador selecciona cerrar sesión.
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
    """Precondición: la entrada estándar está disponible.

    Postcondición: devuelve el registro si coinciden DNI y contraseña; si las
    credenciales son inválidas o falla la lectura, informa y devuelve ``None``.
    """

    try:
        data = read_admin()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar los administradores: {error}")
        return None

    dni = input("DNI: ").strip()
    psw = input("Contraseña: ")

    # Comprueba que el DNI tenga entre 7 y 8 dígitos.
    if not dni.isascii() or not dni.isdigit() or not 7 <= len(dni) <= 8:
        print("DNI o contraseña incorrectos.")
        return None

    # Busca un administrador que coincida con las dos credenciales.
    admin = None

    for item in data:
        if (
            item.get("dni") is not None
            and str(item.get("dni")) == dni
            and item.get("psw") == psw
        ):
            admin = item
            break

    if admin is None:
        print("DNI o contraseña incorrectos.")
        return None

    print(f"INICIO DE SESIÓN CORRECTO. BIENVENIDO, {admin.get('name', '').upper()}.")
    return admin

def registro_admin() -> dict | None:
    """Precondición: los archivos de administradores y canchas pueden leerse,
    el archivo de administradores puede escribirse y la entrada estándar está
    disponible.

    Postcondición: agrega y devuelve el administrador asociado a una cancha.
    Si falla la escritura, informa y devuelve ``None``; los errores de lectura
    se propagan a quien llama esta función.
    """

    dni = validar_dni()
    name = validar_name()
    psw = validar_psw()
    idc = choose_court()

    data = read_admin()

    # Genera un ID que no esté asignado a otro administrador.
    admin_id = rn.randint(1_000_000, 99_000_000)

    duplicado = True

    while duplicado:
        duplicado = False

        for admin in data:
            if admin.get("id") == admin_id:
                duplicado = True
                admin_id = rn.randint(1_000_000, 99_000_000)
                break

    new_admin = {
        "id": admin_id,
        "dni": dni,
        "name": name,
        "psw": psw,
        "court": idc
    }

    data.append(new_admin)

    try:
        write_admin(data)
    except (OSError, TypeError, ValueError) as error:
        print(f"No se pudo guardar el administrador: {error}")
        return None

    print("ADMINISTRADOR REGISTRADO CORRECTAMENTE.")
    return new_admin

def admin_menu_login():
    """Precondición: la entrada estándar está disponible.

    Postcondición: vuelve al menú principal al elegir salir, tras una sesión
    exitosa o después de agotar los tres intentos de inicio de sesión.
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
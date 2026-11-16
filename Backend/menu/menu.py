#Importaciones de librerias 
# este se da cuando ya has iniciado sesion !!
# Ajuste reciente: la opción de reservas muestra las del usuario y permite
# cancelar una propia.
import json

from jinja2 import Template

#Importaciones de archivos locales
from reserve import (
    cancelar_reserva,
    court_lista,
    mostrar_all_courts,
    user_reservas,
)
from user_account import user_account


# Muestra las reservas del usuario y permite cancelar una; 0 vuelve sin cambios.
def cancel_court(user: dict) -> None:
    """Precondición: ``user`` es el usuario autenticado y tiene un ID válido.

    Postcondición: cancela y conserva en el historial la reserva activa elegida;
    si se elige 0, la entrada es inválida o ocurre un error, regresa sin cancelar.
    """
    try:
        reservas = user_reservas(user)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar tus reservas: {error}")
        return

    if not reservas:
        print("No tenés reservas activas.")
        return

    plantilla_reservas = """
TUS RESERVAS ACTIVAS
{% for reserva in reservas %}
{{ loop.index }} - {{ reserva.court_name }} | {{ reserva.date }} | {{ reserva.time }}
{% endfor %}
"""
    print(Template(plantilla_reservas).render(reservas=reservas))

    try:
        numero = int(input("Número de reserva a cancelar (0 para volver): "))
    except ValueError:
        print("Ingrese un número válido.")
        return

    if numero == 0:
        return

    try:
        cancelar_reserva(user, numero)
    except ValueError as error:
        print(f"No se pudo cancelar la reserva: {error}")
        return
    except (OSError, json.JSONDecodeError) as error:
        print(f"No se pudo guardar la cancelación: {error}")
        return

    print("RESERVA CANCELADA. EL TURNO VOLVIÓ A ESTAR DISPONIBLE.")
    return


def menu(user: list[dict]):
    """Precondición: ``user`` contiene al menos el diccionario del usuario
    autenticado en la posición 0.

    Postcondición: muestra el menú y deriva cada opción a su función; termina
    cuando el usuario selecciona cerrar sesión.
    """

    usuario = user[0]

    plantilla = """
===================================================================
         MATCH POINT   ---------   JUGÁ SEGURO - JUGÁ SANO
===================================================================
{{ name | upper }} ¿QUE NECESITAS?
------------------------------------------------------------------- 
1 RESERVAR UN TURNO
2 VER / CANCELAR MIS RESERVAS
3 VER TODAS LAS CANCHAS
4 MI CUENTA
5 CERRAR SESIÓN
------------------------------------------------------------------- 
    """
    mi_plantilla = Template(plantilla)
    
    while True:
        print(mi_plantilla.render(usuario))

        try:
            opcion= int(input(""))
        except ValueError:
            print("-----------------------------------------------------")
            print("        X - ERROR - INGRESE SOLO NÚMEROS - X         ")
            print("-----------------------------------------------------") 
            continue  


        match opcion:
            case 1:
                court_lista(usuario)
            case 2:
                cancel_court(usuario)
            case 3:
                mostrar_all_courts()
            case 4:
                user_account(usuario)
            case 5:
                print("-----------------------------------------------------")
                print("         CERRANDO SESIÓN ------ HASTA LUEGO          ")
                print("-----------------------------------------------------")
                break
            case _ :
                print("-----------------------------------------------------")
                print("         x - OPCIÓN NO FUERA DE RANGO - X            ")
                print("-----------------------------------------------------")
    return

#IMPORTACION DE LIBRERIÁS
# Ajuste reciente: permite consultar y cancelar reservas propias sin borrar
# el historial; los turnos cancelados vuelven a quedar disponibles.
import json
import re
from datetime import date, time
from pathlib import Path

from jinja2 import Template

#IMPORTACION DE ARCHIVOS LOCALES
from notifications import agregar_notificacion
from reader import read_courts

RESERVATIONS_FILE = Path(__file__).resolve().parent / "reservations.json"
DIAS_SEMANA = [
    "lunes",
    "martes",
    "miércoles",
    "jueves",
    "viernes",
    "sábado",
    "domingo",
]


def _registrar_notificacion(evento: str, reserva: dict) -> None:
    """Precondición: ``evento`` y ``reserva`` contienen los datos del aviso.

    Postcondición: intenta guardar la notificación; si falla, informa el error
    sin revertir la reserva ni propagar los errores esperados.
    """
    try:
        agregar_notificacion(evento, reserva)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(
            "AVISO: la operación se guardó, pero no se pudo registrar "
            f"la notificación: {error}"
        )


class TurnoOcupadoError(ValueError):
    # Permite manejar un choque de horario distinto de otros datos inválidos.
    pass


def _validar_date(value: str) -> str:
    """Precondición: ``value`` es texto con formato AAAA-MM-DD.

    Postcondición: devuelve la fecha normalizada o lanza ``ValueError`` si el
    formato o la fecha del calendario no son válidos. Acepta fechas pasadas.
    """
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value): # esto valida la fehca 
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("La fecha ingresada no es válida.") from error


def _validar_hora(value: str) -> str:
    """Precondición: ``value`` es texto con formato HH:MM de 24 horas.

    Postcondición: devuelve la hora normalizada o lanza ``ValueError`` si no
    representa una hora válida.
    """
    if not re.fullmatch(r"\d{2}:\d{2}", value):
        raise ValueError("El horario debe tener el formato HH:MM.")
    try:
        return time.fromisoformat(value).isoformat(timespec="minutes")
    except ValueError as error:
        raise ValueError("El horario ingresado no es válido.") from error


def _leer_reservaciones(path: Path) -> list[dict]:
    """Precondición: ``path`` apunta al archivo JSON de reservas.

    Postcondición: devuelve una lista de diccionarios; si el archivo no existe,
    devuelve una lista vacía. Propaga errores de lectura, JSON o estructura.
    """
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig") as file:
        reservations = json.load(file)

    if not isinstance(reservations, list) or not all(
        isinstance(reservation, dict) for reservation in reservations
    ):
        raise ValueError("El archivo de reservas debe contener una lista de objetos.")
    return reservations


def _horarios_de_una_hora(court: dict, fecha_reserva: str) -> list[str]:
    """Precondición: la fecha es válida y la cancha tiene horas y días abiertos.

    Postcondici?n: devuelve los inicios de turnos de una hora para esa fecha;
    todav?a no filtra los horarios ocupados.
    """
    fecha = date.fromisoformat(_validar_date(fecha_reserva))
    # weekday() devuelve lunes=0 y domingo=6.
    dia_reserva = DIAS_SEMANA[fecha.weekday()]
    dias_abiertos = court.get("dias_abiertos", [])
    if not isinstance(dias_abiertos, list):
        raise ValueError("Los días abiertos deben estar en una lista.")
    if dia_reserva not in dias_abiertos:
        return []

    apertura = court.get("apertura")
    cierre = court.get("cierre")
    if not isinstance(apertura, int) or isinstance(apertura, bool):
        raise ValueError("La apertura debe ser una hora entera.")
    if not isinstance(cierre, int) or isinstance(cierre, bool):
        raise ValueError("El cierre debe ser una hora entera.")
    if apertura < 0 or apertura > 23 or cierre < 1 or cierre > 24:
        raise ValueError("El horario contiene una hora fuera de rango.")
    if cierre <= apertura:
        raise ValueError("El cierre debe ser posterior a la apertura.")

    horarios = []
    for hora in range(apertura, cierre):
        horarios.append(f"{hora:02d}:00")
    return horarios


def _reserva_ocupa_horario(
    reserva: dict,
    court_id: int,
    fecha_reserva: str,
    booking_time: str,
) -> bool:
    """Precondición: reserva y parámetros usan cancha, fecha y hora comparables.

    Postcondición: devuelve ``True`` si coinciden cancha, fecha, hora y estado
    activo; de lo contrario devuelve ``False``.
    """
    if (
        reserva.get("court_id") != court_id
        or reserva.get("date") != fecha_reserva
        or reserva.get("status", "active") != "active"
    ):
        return False

    hora_reservada = _validar_hora(str(reserva.get("time", "")))
    return hora_reservada == booking_time


def horas_disponibles(
    court: dict,
    fecha_reserva: str,
    *,
    reservations_file: Path = RESERVATIONS_FILE,
) -> list[str]:
    """Precondición: la cancha tiene ID y horario; la fecha tiene formato válido.

    Postcondición: devuelve los turnos de atención que no están ocupados en el
    archivo indicado. Puede propagar errores de lectura o datos inválidos.
    """
    normalized_date = _validar_date(fecha_reserva)
    horarios = _horarios_de_una_hora(court, normalized_date)
    reservas = _leer_reservaciones(reservations_file)
    return [
        horario
        for horario in horarios
        if not any(
            _reserva_ocupa_horario(
                reserva,
                court["id"],
                normalized_date,
                horario,
            )
            for reserva in reservas
        )
    ]


# Devuelve solo las reservas activas del usuario identificado en la sesión.
def user_reservas(
    user: dict,
    *,
    reservations_file: Path = RESERVATIONS_FILE,
) -> list[dict]:
    """Precondición: el usuario de sesión tiene un ID entero.

    Postcondición: devuelve sus reservas activas en el orden del archivo; una
    identidad inválida o un archivo ilegible produce una excepción.
    """
    # El ID de sesión limita la consulta a las reservas de este usuario.
    user_id = user.get("id")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("No se pudo identificar al usuario de la sesión.")

    reservations = _leer_reservaciones(reservations_file)
    return [
        reservation
        for reservation in reservations
        if reservation.get("user_id") == user_id
        and reservation.get("status", "active") == "active"
    ]


# Marca como cancelada una reserva propia para conservar el historial y liberar el turno.
def cancelar_reserva(
    user: dict,
    reservation_number: int,
    *,
    reservations_file: Path = RESERVATIONS_FILE,
) -> dict:
    """Precondición: el usuario tiene ID entero y el número identifica, desde 1,
    una reserva activa suya.

    Postcondición: marca la reserva como ``cancelled``, guarda el historial y
    devuelve el registro cancelado. Propaga errores al leer o guardar.
    """
    user_id = user.get("id")
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("No se pudo identificar al usuario de la sesión.")
    if not isinstance(reservation_number, int) or isinstance(reservation_number, bool):
        raise ValueError("El número de reserva no es válido.")

    reservations = _leer_reservaciones(reservations_file)
    reservas_usuario = [
        reservation
        for reservation in reservations
        if reservation.get("user_id") == user_id
        and reservation.get("status", "active") == "active"
    ]
    if not 1 <= reservation_number <= len(reservas_usuario):
        raise ValueError("No existe una reserva activa con ese número.")

    reserva_elegida = reservas_usuario[reservation_number - 1]
    # Se conserva el registro y se libera el turno cambiando solo su estado.
    reserva_elegida["status"] = "cancelled"
    with reservations_file.open("w", encoding="utf-8") as file:
        json.dump(reservations, file, ensure_ascii=False, indent=4)
        file.write("\n")
    _registrar_notificacion("Reserva cancelada", reserva_elegida)
    return reserva_elegida


def crear_reserva(
    user: dict,
    court_id: int,
    fecha_reserva: str,
    booking_time: str,
    *,
    reservations_file: Path = RESERVATIONS_FILE,
) -> dict:
    """Precondición: usuario, cancha, fecha y hora son válidos; la cancha está
    habilitada, el turno cae dentro de atención y no está ocupado.

    Postcondición: guarda y devuelve una reserva activa. Si falla el aviso, la
    reserva permanece guardada y ``_registrar_notificacion`` informa el fallo.
    """
    # Valida primero la identidad y los datos para no guardar reservas incompletas.
    user_id = user.get("id")
    username = user.get("username")
    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or not isinstance(username, str)
        or not username.strip()
    ):
        raise ValueError("No se pudo identificar al usuario de la sesión.")
    if not isinstance(court_id, int) or isinstance(court_id, bool):
        raise ValueError("El identificador de la cancha no es válido.")

    normalizado_date = _validar_date(fecha_reserva)
    normalizado_time = _validar_hora(booking_time)

    courts = read_courts()
    court = next((item for item in courts if item.get("id") == court_id), None)
    if court is None:
        raise ValueError("No existe una cancha con ese identificador.")
    if court.get("available") is not True:
        raise ValueError("La cancha no está habilitada para reservar.")

    horarios = _horarios_de_una_hora(court, normalizado_date)
    if normalizado_time not in horarios:
        raise ValueError(
            "Elegí un turno de una hora disponible dentro del horario de atención."
        )

    # Comprueba conflictos antes de agregar la nueva reserva a la lista.
    reservations = _leer_reservaciones(reservations_file)
    if any(
        _reserva_ocupa_horario(
            reservation,
            court_id,
            normalizado_date,
            normalizado_time,
        )
        for reservation in reservations
    ):
        raise TurnoOcupadoError(
            "Ese turno ya está reservado para la cancha seleccionada."
        )

    court_data = court.get("data", [])
    court_name = court_data[0] if court_data else f"Cancha {court_id}"
    reservation = {
        "user_id": user_id,
        "username": username.strip(),
        "court_id": court_id,
        "court_name": court_name,
        "date": normalizado_date,
        "time": normalizado_time,
        "status": "active",
    }
    reservations.append(reservation)
    with reservations_file.open("w", encoding="utf-8") as file:
        json.dump(reservations, file, ensure_ascii=False, indent=4)
        file.write("\n")
        
    _registrar_notificacion("Nueva reserva", reservation)
    return reservation


def confirm_court(court: dict, user: dict) -> bool:
    """Precondición: recibe la cancha elegida y el usuario de la sesión.

    Postcondición: devuelve ``True`` si crea la reserva; devuelve ``False`` al
    cancelar o cuando informa un error al usuario.
    """
    while True:
        fecha_reserva = input("Ingrese la fecha (AAAA-MM-DD, 0 para volver): ").strip()
        if fecha_reserva == "0":
            return False

        try:
            _validar_date(fecha_reserva)
        except ValueError as error:
            print(error)
            continue

        try:
            horarios_disponibles = horas_disponibles(court, fecha_reserva)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"No se pudieron consultar los horarios: {error}")
            return False
        
        if not horarios_disponibles:
            print("No hay turnos disponibles para esa fecha.")
            continue

        plantilla_horarios = """
TURNOS DISPONIBLES (1 HORA)
{% for horario in horarios %}
{{ loop.index }} - {{ horario }}
{% endfor %}
        """
        print(Template(plantilla_horarios).render(horarios=horarios_disponibles))
        # La persona elige el índice mostrado; 0 cancela y vuelve al menú.
        while True:
            entrada_horario = input(
                "Elija el número de horario (0 para volver): "
            ).strip()
            if entrada_horario == "0":
                return False
            try:
                numero_horario = int(entrada_horario)

                if 1 <= numero_horario <= len(horarios_disponibles):
                    booking_time = horarios_disponibles[numero_horario - 1]
                    break
                print("X - OPCIÓN FUERA DE RANGO - X")
            except ValueError:
                print("X - INGRESE SOLO NÚMEROS - X")

        while True:
            answer = input(
                "¿Confirma la reserva? (si/no, 0 para volver): "
            ).strip().lower()
            if answer == "0" or answer == "no":
                print("RESERVA ANULADA.")
                return False
            if answer == "si":
                break
            print("Respuesta incorrecta. Ingrese si, no o 0.")

        try:
            reserva = crear_reserva(
                user,
                court["id"],
                fecha_reserva,
                booking_time,
            )
        except TurnoOcupadoError as error:
            print(error)
            continue
        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"No se pudo completar la reserva: {error}")
            return False

        plantilla = """ 
* RESERVA CONFIRMADA *
SU RESERVA HA SIDO CONFIRMADA CON EXITO
        """
        print(Template(plantilla).render())
        detalles_reserva = """
CANCHA: {{ court_name | upper }}
FECHA: {{ date }}    HORARIO: {{ time }}
        """
        print(Template(detalles_reserva).render(reserva))
        return True


def elegir_court(courts: list[dict], user: dict) -> None:
    """Precondición: ``courts`` contiene las canchas habilitadas para elegir.

    Postcondición: muestra y confirma la cancha elegida; con 0 regresa sin
    iniciar una reserva.
    """
    while True:
        entrada = input("Elija el número de la cancha (0 para volver): ").strip()
        if entrada == "0":
            return

        try:
            option = int(entrada)
            if 1 <= option <= len(courts):
                selec_court = courts[option - 1]
                break

            print("x - OPCION FUERA DE RANGO - X")
        except ValueError:
            print("ERROR - INGRESE SOLO NÚMEROS")

    plantilla ="""
* DETALLES DEL LUGAR *
    
{{ data | join(',') | upper }}
{{ info | upper }}
TEL: {{ phone | join(',') }}
CANTIDAD DE CANCHAS: {{ courts }}
PAREDES: {{ walls | upper }}
TIENDA: {{ "SI INCLUYE" if shop else "NO INCLUYE" }}
ENTRENADOR: {{ "DISPONIBLES" if trainer else "NO DISPONIBLES" }}
            """
    mi_plantilla= Template(plantilla)
    print(mi_plantilla.render(selec_court))

    confirm_court(selec_court, user)


def court_lista(user: dict) -> None:
    """Precondición: recibe el usuario autenticado.

    Postcondición: muestra las canchas y permite elegir una; si falla la lectura
    o no hay canchas habilitadas, informa y regresa.
    """
    try:
        courts = read_courts()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar las canchas: {error}")
        return

    available_courts = [
        court for court in courts if court.get("available") is True
    ]
    not_available_courts = [
        court for court in courts if court.get("available") is not True
    ]
    if not available_courts:
        print("No hay canchas habilitadas para reservar.")
        return

    plantilla = """
-----------------------------------------------------------------                  
CANCHAS DISPONIBLES PARA RESERVAR
    
{% for info in cancha -%}
{{ loop.index }} (INGRESE {{ loop.index }}) - {{ info.data | join(',') | upper }}
HORARIO: {{ info.apertura }}:00 a {{ info.cierre }}:00
DIAS: {{ info.dias_abiertos | join(', ') | upper }}
Tel: {{ info.phone | join(',') | upper }}
-----------------------------------------------------------------
{% endfor %}
-----------------------------------------------------------------
CANCHAS NO DISPONIBLES
    
{% for info in not_available_courts -%}
{{ loop.index }} {{ info.data | join(',') | upper  }}
HORARIO: {{ info.apertura }}:00 a {{ info.cierre }}:00
DIAS: {{ info.dias_abiertos | join(', ') | upper }}
Tel: {{ info.phone | join(',') }}
----------------------------------------------------------------
{% endfor %}
    
-------- INGRESE EL NUMERO DE LA CANCHA QUE DESEA ELEGIR -------
    """
    mi_plantilla = Template(plantilla)
    print(
        mi_plantilla.render(
            cancha=available_courts,
            not_available_courts=not_available_courts,
        )
    )
    elegir_court(available_courts, user)


# Muestra todas las canchas con su estado, sin iniciar una reserva.
def mostrar_all_courts() -> None:
    """Precondición: el archivo de canchas puede leerse.

    Postcondición: muestra todas las canchas y espera 0 para volver; si la
    lectura falla, informa el error y regresa.
    """
    try:
        courts = read_courts()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar las canchas: {error}")
        return

    plantilla = """
TODAS LAS CANCHAS
{% for cancha in canchas %}
{{ loop.index }}
------------------------------------- - {{ cancha.data | join(',') | upper }}
HORARIO: {{ cancha.apertura }}:00 a {{ cancha.cierre }}:00
DIAS: {{ cancha.dias_abiertos | join(', ') | upper }}
ESTADO: {{ "HABILITADA" if cancha.available else "NO DISPONIBLE" }}----------------------------
{% endfor %}
"""
    print(Template(plantilla).render(canchas=courts))
    while input("Seleccione 0 para regresar al menú: ").strip() != "0":
        print("Opción inválida. Ingrese 0 para regresar.")

# este controla el login del main.py cuando iniciamos sesion
# Ajuste reciente: informa si no puede cargar los usuarios y evita continuar
# con datos inválidos.
import json

from jinja2 import Template

from menu.menu import menu
from reader import read_user


def save_usuario( psw: str, coincidencia: list[dict]) -> dict | None:
    """Precondición: recibe una contraseña y las cuentas con el usuario indicado.

    Postcondición: devuelve la primera cuenta cuya contraseña coincide o
    ``None`` si ninguna coincide; no modifica las cuentas.
    """
    return next(
        (
            item for item in coincidencia
            if item.get("psw") == psw
        ),
        None,
    )


def welcome(user: list[dict]) -> None:
    """Precondición: ``user`` contiene la cuenta autenticada en la posición 0.

    Postcondición: muestra el saludo y ejecuta el menú hasta que se cierre la
    sesión; no devuelve un valor.
    """
    plantilla = """
========================================================
            BIENVENIDO: {{ name | upper }}
========================================================
    """
    print(Template(plantilla).render(user[0]))
    menu(user)


def iniciar_sesion_user() -> None:
    """Precondición: el archivo de usuarios puede leerse.

    Postcondición: ante credenciales válidas, abre el menú de usuario y regresa
    al terminar la sesión; ante un error de lectura o tres contraseñas
    incorrectas, informa el problema y regresa. Si el nombre no existe, vuelve
    a solicitarlo.
    """
    try:
        datos = read_user()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar los usuarios: {error}")
        return

    # Repite la solicitud del nombre hasta encontrar una cuenta registrada.
    while True:
        plantilla = """
=======================================================
        MATCH POINT     -----    LOGIN USUARIO
=======================================================
Ingrese su nombre de usuario:
        """
        print(Template(plantilla).render())


        username = input("").strip().lower()
        # Conserva las cuentas con ese nombre para comprobar después la contraseña.
        coincidencia = [user for user in datos if user.get("username") == username]

        if not coincidencia:
            print("EL USUARIO NO EXISTE.")
            continue

        intentos = 3
        while intentos > 0:
            plantilla = """
=======================================================
        MATCH POINT     ----    LOGIN CONTRASEÑA
=======================================================
Ingrese su contraseña:
            """
            print(Template(plantilla).render())

            password = input("")
            # Comprueba la contraseña entre las cuentas que coinciden con el nombre.
            usuario = save_usuario(password, coincidencia)

            if usuario is not None:
                welcome([usuario])
                return

            intentos -= 1
            print(f"LA CONTRASEÑA ES INCORRECTA. Intentos restantes --> {intentos}")

        # Después de tres errores, termina el login para volver al menú principal.
        print("DEMASIADOS INTENTOS.")
        return

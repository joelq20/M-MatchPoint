import json

from jinja2 import Template

from reader import read_user
from writer import write_user


def _guardar_cambio(       
    usuarios: list[dict],
    usuario_guardado: dict,
    usuario_actualizado: dict,
    usuario_sesion: dict,
) -> None:
    """Precondición: la lista contiene ``usuario_guardado`` y se recibió una
    copia actualizada de esa cuenta.

    Postcondición: persiste los usuarios y actualiza las referencias guardada y
    de sesión. Si falla la escritura, propaga ``OSError`` y no actualiza ambas
    referencias en memoria.
    """
    
    # Sustituye solo el registro de la cuenta editada y conserva las demás.
    usuarios_actualizados = [
        usuario_actualizado if usuario is usuario_guardado else usuario
        for usuario in usuarios
    ]
    write_user(usuarios_actualizados)
    # Actualiza ambas referencias en memoria después de guardar correctamente.
    usuario_guardado.update(usuario_actualizado)
    usuario_sesion.update(usuario_actualizado)


def _pedir_nuevo_usuario(usuarios: list[dict], user_id: object) -> str | None:
    """Precondición: recibe los usuarios cargados y el ID de la cuenta editada.

    Postcondición: devuelve el nombre normalizado si no está vacío ni ocupado
    por otra cuenta; si no cumple, informa y devuelve ``None``.
    """

    nuevo_usuario = input("Ingrese el nuevo nombre de usuario: ").strip().lower()
    if not nuevo_usuario:
        print("El nombre de usuario no puede quedar vacío.")
        return None

    if any(
        otro.get("id") != user_id
        and str(otro.get("username", "")).strip().lower() == nuevo_usuario
        for otro in usuarios
    ):
        print("Ese nombre de usuario ya está en uso.")
        return None
    return nuevo_usuario


def _pedir_nueva_edad() -> int | None:
    """Precondición: ninguna; solicita una edad por consola.

    Postcondición: devuelve un entero entre 18 y 90 inclusive; si la entrada no
    es válida, informa el motivo y devuelve ``None``.
    """
    try:
        nueva_edad = int(input("Ingrese la nueva edad: ").strip())
    except ValueError:
        print("La edad debe ser un número entero.")
        return None

    if not 18 <= nueva_edad <= 90: # si la nueva edad no esta entre 18 y 90 
        print("La edad debe estar entre 18 y 90.")
        return None
    return nueva_edad


def _pedir_nueva_contraseña(usuario_guardado: dict) -> str | None:
    """Precondición: ``usuario_guardado`` contiene la contraseña actual.

    Postcondición: devuelve la nueva contraseña sin espacios si la actual es
    correcta y la confirmación coincide; si no, informa y devuelve ``None``.
    """
    
    contrasena_actual = input("Ingrese la contraseña actual: ")
    if contrasena_actual != usuario_guardado.get("psw"):
        print("La contraseña actual no es correcta.")
        return None

    # Mantiene la misma regla del registro: quitar los espacios de la contraseña nueva.
    nueva_contraseña = input("Ingrese la nueva contraseña: ").replace(" ", "")
    if not nueva_contraseña.strip():
        print("La contraseña no puede quedar vacía.")
        return None
    
    # La primera entrada ya no contiene espacios, así que se confirma en ese formato.
    confirmacion = input(
        "Confirme la contraseña nueva sin espacios (se eliminan de la primera entrada): "
    )
    if nueva_contraseña != confirmacion:
        print("Las contraseñas no coinciden.")
        return None
    return nueva_contraseña


def user_account(usuario_sesion: dict) -> None:
    """Precondición: ``usuario_sesion`` identifica una cuenta de usuario.

    Postcondición: permite editar usuario, edad o contraseña; los cambios
    aceptados se guardan y actualizan la sesión. Al volver o ante un error, sale
    sin aplicar cambios pendientes.
    """
    try:
        usuarios = read_user()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudo cargar la cuenta: {error}")
        return

    user_id = usuario_sesion.get("id")
    # Busca el registro persistido para asegurar que la edición corresponda a esta sesión.
    usuario_guardado = next(
        (usuario for usuario in usuarios if usuario.get("id") == user_id),
        None,
    )
    if usuario_guardado is None:
        print("No se encontró la cuenta del usuario conectado.")
        return

    plantilla = """
========================================================
                    MI CUENTA
========================================================
USUARIO: {{ usuario.username | upper }}
NOMBRE: {{ usuario.name | upper }}
APELLIDO: {{ usuario.user.secname | upper }}
EDAD: {{ usuario.user.years }}
CIUDAD: {{ usuario.user.location | upper }}
--------------------------------------------------------
¿QUÉ DESEA MODIFICAR?
1 - Nombre de usuario
2 - Edad
3 - Contraseña
0 - Regresar al menú
========================================================
"""

    while True:
        print(Template(plantilla).render(usuario=usuario_guardado))

        opcion = input("Seleccione una opción: ").strip()
        if opcion == "0":
            return
        # Copia también el diccionario anidado para editarlo sin modificar el original antes de guardar.
        usuario_actualizado = usuario_guardado.copy()
        usuario_actualizado["user"] = usuario_guardado.get("user", {}).copy()

        if opcion == "1":
            nuevo_usuario = _pedir_nuevo_usuario(usuarios, user_id)
            if nuevo_usuario is None:
                continue
            usuario_actualizado["username"] = nuevo_usuario

        elif opcion == "2":
            nueva_edad = _pedir_nueva_edad()

            if nueva_edad is None:
                continue
            usuario_actualizado["user"]["years"] = nueva_edad

        elif opcion == "3":
            nueva_contrasena = _pedir_nueva_contraseña(usuario_guardado)
            if nueva_contrasena is None:
                continue
            usuario_actualizado["psw"] = nueva_contrasena

        else:
            print("Opción fuera de rango.")
            continue

        try:
            _guardar_cambio(
                usuarios,
                usuario_guardado,
                usuario_actualizado,
                usuario_sesion,
            )
        except OSError as error:
            print(f"No se pudo guardar el cambio: {error}")
            return
        
        print("CAMBIO GUARDADO CORRECTAMENTE.")

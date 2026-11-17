#IMPORTACION DE LIBRERIÁS
# este apartado relacionado con main.py controla el registro 
# Ajuste reciente: informa errores de lectura/escritura y vuelve al menú con
# el nombre correcto de la función.
import json

from jinja2 import Template
import random as rn

#IMPORTACIONES DE ARCHIVOS LOCALES
from reader import read_user
from writer import write_user


def pedir_texto_obligatorio(mensaje: str) -> str:

    while True:
        valor = input(mensaje).strip()
        if not valor: # si el valor(aux) esta vacio se reproduce el print 
            print("Este campo no puede quedar vacío.")
        else: 
            return valor.lower()


def confirmar_edad() -> int:
    """Solicita una edad entre 18 y 90 años.

    Pre: ninguna.

    Post: devuelve un número entero dentro del rango permitido.
    """
    entrada_valida = False

    while not entrada_valida:
        try:
            edad = int(input("Ingrese su edad: "))

        except ValueError:
            print("ERROR... INGRESE SOLO NUMEROS ENTEROS")
            continue

        if edad >= 18 and edad <= 90:
            entrada_valida = True
            return edad
        else:
            print("ERROR... INGRESE UNA EDAD ENTRE 18 Y 90")


def validacion_psw():

    while True:

        psw = input("Ingrese su contraseña:  ").replace(" ","")
        if not psw.strip(): # si cadena psw esta vacia has lo siguiente 
            print("ERROR... LA CONTRASEÑA NO PUEDE ESTAR VACÍA!!")

            continue

        psw2 = input("Confirme su contraseña(si ingreso algun espacio anteriomente este habra sido borrado):  ")

        while psw2 != psw:
            print("ERROR...LAS CONTRASEÑAS NO COINCIDEN")

            psw2 = input("Confirme su contraseña:  ")
        return psw

def cuenta_nueva() -> list[dict] | None:
    """Esta función recibe los datos necesarios para crear una nueva cuenta
    y los guarda en el archivo JSON.

    Precondición: la entrada estándar está disponible.

    Postcondición: devuelve la lista actualizada de usuarios si el registro
    se guarda correctamente; si falla la lectura o escritura del archivo,
    informa el error y devuelve ``None``.
    """
    try:
        datos = read_user()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"No se pudieron cargar los usuarios: {error}")
        return None

    plantilla = """
=========================================================
                MATCH POINT  REGISTRO
=========================================================
    """

    mi_plantilla = Template(plantilla)
    print(mi_plantilla.render())

    # Genera un ID que no esté asignado a otra cuenta.
    id_usuario = rn.randint(100_000_000, 999_000_000)
    duplicado = True

    while duplicado:
        duplicado = False

        for usuario in datos:
            if usuario.get("id") == id_usuario:
                duplicado = True
                id_usuario = rn.randint(100_000_000, 999_000_000)
                break

    username = pedir_texto_obligatorio("Ingrese su nombre de usuario: ")

    # Comprueba que el nombre de usuario no esté registrado.
    duplicado = False

    for usuario in datos:
        if usuario.get("username") == username:
            duplicado = True
            break

    while duplicado:
        print("Nombre de usuario ya existente, pruebe otro por favor.")
        username = pedir_texto_obligatorio("Ingrese su nombre de usuario: ")

        duplicado = False

        for usuario in datos:
            if usuario.get("username") == username:
                duplicado = True
                break

    firname = pedir_texto_obligatorio("Ingrese su nombre: ")
    secname = pedir_texto_obligatorio("Ingrese su apellido: ")

    edad = confirmar_edad()
    psw = validacion_psw()

    lugar = pedir_texto_obligatorio(
        "Ingrese la ciudad donde reside actualmente: "
    )

    new_usuario = {
        "id": id_usuario,
        "username": username,
        "name": firname,
        "psw": psw,
        "user": {
            "secname": secname,
            "years": edad,
            "location": lugar
        }
    }

    datos.append(new_usuario)

    try:
        write_user(datos)
    except (OSError, TypeError) as error:
        print(f"No se pudo guardar el registro: {error}")
        return None

    plantilla = """
==========================================================
                !REGISTRO COMPLETADO!
                BIENVENIDO  {{ name | upper }}
==========================================================
    """

    template = Template(plantilla)
    print(template.render(new_usuario))

    return datos

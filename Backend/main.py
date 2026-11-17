#desde aqui se ejecuta para que funcione  todo 
# ejecutarlo desde otro lado no tirara nada 
from jinja2 import Template
from admins.admin import admin_menu_login
from registrarse import cuenta_nueva
from users.login import iniciar_sesion_user

def mi_funcion():
    """Pre: están disponibles los flujos de registro, usuario y admin.

    Post: muestra el menú principal y deriva las opciones elegidas;
    termina cuando el usuario selecciona la opción 4.
    """
    while True:
        plantilla= """
==============================================================
                  BIENVENIDOS A  MATCH POINT    
==============================================================  
-D 1 CREAR NUEVA CUENTA
-D 2 INICIAR SESIÓN
-D 3 INGRESAR COMO ADMINISTRADOR
 X 4 SALIR
    """
        mi_plantilla = Template (plantilla)
        print(mi_plantilla.render())
    
        try:
            opcion = int(input(""))
        except ValueError:
            print("----------------------------------------------------")
            print("         X - POR FAVOR USE SOLO NUMEROS - X         ")
            print("----------------------------------------------------")
            
            continue

        if opcion == 1:
            cuenta_nueva()

        elif opcion == 2:
            iniciar_sesion_user()

        elif opcion == 3:
            admin_menu_login()

        elif opcion == 4:
            print("HASTA LUEGO")
            break
        else :
            print("-----------------------------------------------------")
            print("            x - OPCION FUERA DE RANGO - x            ")
            print("-----------------------------------------------------")


def main():
    """Precondición: las dependencias y datos del backend están disponibles.

    Postcondición: ejecuta el menú principal hasta que el usuario sale; no
    devuelve un valor.
    """
    mi_funcion()

# Inicia el menú solo al ejecutar este archivo directamente, no al importarlo.
if __name__ == '__main__':
    main()

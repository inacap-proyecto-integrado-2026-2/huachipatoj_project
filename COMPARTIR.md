# Compartir la prueba de Huachipato

## Opción 1 — Ejecutar una copia en otro PC Windows

1. Envía Huachipato-prueba.zip por el medio que prefieras. El ZIP contiene código y un documento ficticio de ejemplo; no incluye cuentas, base de datos, documentos personales ni entorno virtual.
2. En el otro PC instala Python 3.11, 3.12, 3.13 o 3.14 desde https://www.python.org/downloads/ y comprueba que `python --version` funciona. No es necesario instalar Visual Studio Code para usar la aplicación.
3. Extrae todo el ZIP en una carpeta local. No ejecutes el programa dentro del ZIP.
4. Abre INICIAR.cmd. La primera ejecución instala dependencias (requiere Internet), crea la base de datos y levanta el servidor. Deja esa ventana abierta.
5. Abre otra terminal PowerShell en esa misma carpeta, donde está manage.py. Ejecuta una vez:

```powershell
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py createsuperuser
```

El primer comando crea 18 jugadores ficticios y datos para probar los módulos. El segundo permite elegir usuario y contraseña propios: no se comparten las credenciales de Diego. La contraseña no se muestra al escribirla.

6. Abre http://127.0.0.1:8000/ e ingresa con la cuenta recién creada.
7. Para las próximas veces basta con abrir INICIAR.cmd y dejar la ventana funcionando. Ctrl+C detiene el servidor.

Cada PC tiene su propia base de datos. Las modificaciones NO se sincronizan entre computadores. No vuelvas a cargar la demo para reiniciar el escenario: el comando conserva los cambios existentes.

## Opción 2 — macOS o Linux

Con Python 3.11–3.14 instalado, abre la carpeta extraída en una terminal:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py cargar_demo
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Abre http://127.0.0.1:8000/. Para volver a iniciar solo necesitas el último comando. Estas instrucciones no se han probado en macOS/Linux en esta sesión.

## Opción 3 — Abrir un enlace desde cualquier computador o celular

Para que el entrenador abra solo un enlace, sin instalar Python, hay que publicar la aplicación en un servidor. Esa modalidad permite compartir una sola base de datos. La dirección 127.0.0.1 siempre apunta al equipo que la abre; no sirve como enlace remoto.

Esta entrega aún NO está publicada. Antes del despliegue hay que configurar servidor de aplicación, HTTPS, secretos fuera del código, DEBUG=False, hosts permitidos, base de datos y almacenamiento de archivos persistentes, además de cuentas y copias de respaldo. El servidor runserver se usa para desarrollo local, no para publicación en producción.

Documentación oficial: https://docs.djangoproject.com/en/5.2/howto/deployment/

## Guion breve para probar

- Plantilla: buscar “DEMO”, editar un jugador y cambiarlo de categoría.
- Calendario: probar las vistas mensual, semanal y listado; programar una clase con categoría y objetivo. Para evaluarla debe estar Realizada y no tener fecha futura.
- Pista: elegir una clase Realizada, cambiar asistencia y calificar. Esperar Guardado y recargar. Añadir una observación privada y comprobar que se conserva.
- Evolución: abrir el historial de un jugador para ver seis fechas y sus notas.
- Rutinas: editar una pendiente, marcarla completada y registrar observaciones.
- Justificativos: revisar el pendiente de Martina Lagos [DEMO], descargar el documento ficticio y aprobarlo; su asistencia debe quedar justificada.
- Inventario: prestar un equipo libre, comprobar devoluciones pendientes y registrar una devolución. Hay un equipo en reparación que no se puede prestar.
- Reportes: elegir un mes y un jugador o categoría; descargar el PDF. Las observaciones privadas no se incluyen y las ausencias no cuentan como nota cero.
- Autorizaciones: registrar un documento ficticio, editar responsable y estado, y comprobar su descarga desde una cuenta de personal autorizado.

Anota qué intentó hacer el entrenador, qué esperaba y qué ocurrió; especialmente si necesitó ayuda para encontrar un botón o comprender un estado.

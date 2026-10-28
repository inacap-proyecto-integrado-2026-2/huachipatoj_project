# Huachipato — versión de prueba local

## Abrir y ejecutar
Abre esta carpeta (la que contiene manage.py) en Visual Studio Code. Detén el servidor de la versión anterior con Ctrl+C y ejecuta en PowerShell:

```powershell
.\INICIAR.cmd
```

Requiere Python 3.11 o superior instalado y acceso a Internet para instalar las dependencias. El script crea un entorno .venv propio, instala Django 5.2.17, aplica migraciones e inicia el servidor local. Abre http://127.0.0.1:8000/. La copia de trabajo conserva los usuarios y datos que existían al copiar el proyecto. No se sincronizan los cambios posteriores con Downloads.

Si usas el ZIP de entrega, comienza con una base de datos vacía. Tras el primer inicio crea la cuenta en otra terminal:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

## Recorrido de prueba con el entrenador
1. Plantilla jugadores: agregar un jugador, buscarlo y editar su categoría u observaciones.
2. Evaluación en pista: programar una clase desde Calendario, marcarla Realizada cuando se imparta, seleccionar asistencia y tocar notas. Esperar «Guardado» y recargar para comprobar persistencia. Cero interno se presenta como sin evaluar, no como nota deportiva.
3. Plantilla jugadores → Ver evolución: consultar tabla y gráfico de habilidades.
4. Rutinas: asignar ejercicios con fecha, objetivo y dosis; editar para marcar completada y registrar observaciones.
5. Registrar una ausencia o atraso y luego adjuntar un justificativo PDF/JPG de prueba. Revisarlo y aprobarlo: la asistencia cambia a Ausente justificado.
6. Inventario: crear patines o stick con código único, prestarlo y registrar devolución. Probar el filtro de devoluciones pendientes y el historial.

## Alcance de esta versión
Prueba local supervisada. Justificativos solo accesibles al personal autorizado; no hay rutas públicas a los archivos. Entrenadores se identifican mediante is_staff. El administrador crea cuentas desde /admin/; para asociar un alumno, su nombre de usuario debe coincidir exactamente con su RUT registrado. Las modificaciones dejan un registro de auditoría.

Pendientes para despliegue real: permisos por categorías y roles de apoderado, invitaciones y recuperación de cuentas, revisión de privacidad y almacenamiento cifrado, HTTPS/hosting, copias de seguridad operativas y pruebas de concurrencia/carga en cancha. Sin modo offline. La aprobación de justificativos es definitiva en esta interfaz. No incluye eliminación de registros históricos. No afirmar cumplimiento normativo ni rendimiento menor a un segundo hasta validarlo.

Usar documentos ficticios durante la prueba local. El servidor de desarrollo no está publicado en Internet; el entrenador necesita ejecutar la copia en su computador o probarla contigo.

## Validación
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe manage.py test seguimiento
```
Dieciséis pruebas cubren páginas, persistencia y validación, permisos, préstamos/devoluciones, justificativos, rutinas, edición de jugadores, calendario, comentarios privados, reportes PDF y autorizaciones.

## Datos de demostración y entrega
Consulta COMPARTIR.md para preparar la demo en otro computador o conocer los pasos pendientes para compartir un enlace. El comando `python manage.py cargar_demo` añade datos identificados como DEMO y no crea cuentas ni sobrescribe cambios.

## Actualización posterior a la reunión
- Calendario semanal, mensual y listado. Clases manuales con fecha, hora, categoría, entrenador, objetivo y estado. Sin repetición automática. Una clase con evaluaciones no permite cambiar fecha/categoría ni volver a programada; se puede cancelar conservando historial.
- Para evaluar, la clase debe estar Realizada y no tener fecha futura. Los estados de asistencia incluyen Atraso.
- Observación privada por evaluación completa. Acceso desde la grilla tras guardar asistencia o desde el historial. No aparece al alumno ni se exporta.
- Reportes mensuales PDF por jugador o categoría. Promedios excluyen ausencias, notas cero y clases no realizadas. Las categorías anteriores se reconstruyeron con la ficha disponible en la migración, porque no existía registro histórico de cambios de categoría.
- Autorizaciones de apoderados con PDF/JPG, fecha, responsable y estados Pendiente, Vigente o Revocada. Solo personal is_staff. El registro no comprueba firmas ni certifica cumplimiento legal.

Para actualizar una instalación existente: detener el servidor, hacer respaldo privado de db.sqlite3 y private_media, copiar el código nuevo conservando esos datos y ejecutar INICIAR.cmd. No sustituir la base de datos por otra. El script instala reportlab y aplica las migraciones. Los ejemplos nuevos se cargan con `python manage.py cargar_demo`; repetirlos no reinicia los cambios.

from datetime import date, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from seguimiento.models import Jugador, ClaseEntrenamiento, Evaluacion, Rutina, Equipo, Prestamo, Justificativo, Autorizacion

class Command(BaseCommand):
    help = 'Añade datos ficticios DEMO sin reemplazar registros existentes ni crear cuentas.'

    @transaction.atomic
    def handle(self, *args, **options):
        today = timezone.localdate()
        names = ['Martina Lagos', 'Tomás Vera', 'Antonia Soto', 'Benjamín Rojas', 'Sofía Díaz', 'Lucas Muñoz', 'Valentina Pérez', 'Vicente Torres', 'Isidora Fuentes', 'Joaquín Silva', 'Florencia Reyes', 'Matías Castro', 'Catalina Herrera', 'Diego Navarro', 'Camila Vidal', 'Nicolás Bravo', 'Francisca Morales', 'Sebastián Leiva']
        players=[]
        added=0
        for i,name in enumerate(names):
            category=['ESC','S15','ADU'][i//6]
            p,created=Jugador.objects.get_or_create(rut=f'DEMO-{i+1:03}', defaults=dict(nombre_completo=f'{name} [DEMO]',categoria=category,fecha_nacimiento=date([2017,2013,2002][i//6],i%12+1,i%25+1),contacto_emergencia='NO REAL',observaciones='Jugador ficticio para pruebas. Sin datos personales reales.'))
            players.append(p); added+=created
        sessions=[]
        for j in range(6):
            marker=f'DEMO-HUACHIPATO-V1-SESION-{j+1}'
            s,created=ClaseEntrenamiento.objects.get_or_create(observaciones=marker,defaults={'profesor':'Entrenador de prueba'})
            if created:
                ClaseEntrenamiento.objects.filter(pk=s.pk).update(fecha=today-timedelta(days=(5-j)*4))
                s.refresh_from_db()
            sessions.append(s)
            for i,p in enumerate(players):
                status='A' if (i+j)%9==0 else 'T' if (i+j)%7==0 else 'P'
                if j==5 and i in (0,1,2): status=['A','J','A'][i]
                base=min(10,3+i%4+j//2)
                Evaluacion.objects.get_or_create(jugador=p,clase=s,defaults=dict(categoria_registrada=p.categoria,asistencia=status,nota_frenado=base if status in ('P','T') else 0,nota_pase=min(10,base+1) if status in ('P','T') else 0,nota_tiro=max(1,base-1) if status in ('P','T') else 0))
        for i,p in enumerate(players):
            for j in range(2):
                Rutina.objects.get_or_create(jugador=p,titulo=f'[DEMO] {"Control y pase" if j==0 else "Frenado y tiro"}',defaults=dict(objetivo='Ejemplo de planificación para revisar con el entrenador.',ejercicios='Contenido ficticio para probar la aplicación.\nEjercicio de control: 3 series de 5 repeticiones.\nPase y recepción: 2 series de 8 repeticiones.\nDescanso: 60 segundos entre series.\nEl entrenador debe adaptar la rutina antes de su uso deportivo.',fecha=today+timedelta(days=j*3-3),completada=j==0 and i%3!=0,observaciones='Registro ficticio: mejor control durante la segunda serie.' if j==0 else ''))
        for i in range(12):
            equipment,_=Equipo.objects.get_or_create(codigo=f'DEMO-EQ-{i+1:02}',defaults=dict(nombre=f'{"Patines" if i%2==0 else "Stick"} de prueba {i+1}',estado='reparacion' if i==11 else 'desgastado' if i==10 else 'bueno'))
            if i<8:
                if not Prestamo.objects.filter(equipo=equipment).exists():
                    Prestamo.objects.create(equipo=equipment,jugador=players[i],devuelto=timezone.now() if i>=5 else None)
        fixture=Path(__file__).resolve().parents[2]/'demo'/'justificativo-demo.jpg'
        for i,state in enumerate(['pendiente','aprobado','rechazado']):
            e=Evaluacion.objects.get(jugador=players[i],clase=sessions[-1])
            if not Justificativo.objects.filter(evaluacion=e,motivo='DEMO: documento ficticio, sin validez médica.').exists():
                doc=Justificativo(evaluacion=e,motivo='DEMO: documento ficticio, sin validez médica.',estado=state)
                doc.archivo.save(f'demo-{i}.jpg',ContentFile(fixture.read_bytes()),save=True)
        for i,category in enumerate(['ESC','S15','ADU']):
            for future in [False,True]:
                marker=f'DEMO-HUACHIPATO-V2-{category}-{future}'
                session,created=ClaseEntrenamiento.objects.get_or_create(observaciones=marker,defaults=dict(fecha=today+timedelta(days=3+i) if future else today.replace(day=max(1,today.day-2)),hora='18:00',categoria=category,profesor='Entrenador DEMO',objetivo='Planificación y evaluación de demostración',estado='programada' if future else 'realizada'))
                if not future:
                    for player in players[i*6:i*6+6]:
                        Evaluacion.objects.get_or_create(jugador=player,clase=session,defaults=dict(categoria_registrada=category,asistencia='P',nota_frenado=7,nota_pase=8,nota_tiro=6,observacion_privada='DEMO privada: mejoró el control, reforzar el tiro.'))
        for i,state in enumerate(['pendiente','vigente','revocada']):
            if not Autorizacion.objects.filter(jugador=players[i],apoderado='Apoderado ficticio DEMO').exists():
                authorization=Autorizacion(jugador=players[i],apoderado='Apoderado ficticio DEMO',fecha=today,responsable='Registro DEMO',estado=state)
                authorization.archivo.save(f'autorizacion-demo-{i}.jpg',ContentFile(fixture.read_bytes()),save=True)
        # Escenario fechado: repetir la carga el mismo día conserva lo probado.
        demo_tag = f'DEMO-RECORRIDO-{today.isoformat()}'
        for category_index, category in enumerate(['ESC', 'S15', 'ADU']):
            group = [player for player in players if player.categoria == category]
            for step, days in enumerate([-6, -3, 0, 1, 4, 2]):
                state = 'realizada' if step < 3 else 'cancelada' if step == 5 else 'programada'
                session, _ = ClaseEntrenamiento.objects.get_or_create(
                    observaciones=f'{demo_tag}-{category}-{step}',
                    defaults=dict(fecha=today + timedelta(days=days),
                                  hora=f'{17 + category_index}:00', categoria=category,
                                  profesor='Entrenador ficticio DEMO', estado=state,
                                  objetivo='[DEMO] Cancelada por mantenimiento de pista' if state == 'cancelada' else '[DEMO] Circuito de control, pase y tiro'))
                if step < 3:
                    for index, player in enumerate(group):
                        attendance = ['P', 'P', 'T', 'A', 'J', 'P'][(index + step) % 6]
                        score = min(10, 4 + index % 3 + step)
                        evaluation, _ = Evaluacion.objects.get_or_create(
                            jugador=player, clase=session,
                            defaults=dict(categoria_registrada=category, asistencia=attendance,
                                          nota_frenado=score if attendance in ('P', 'T') else 0,
                                          nota_pase=min(10, score + 1) if attendance in ('P', 'T') else 0,
                                          nota_tiro=max(1, score - 1) if attendance in ('P', 'T') else 0,
                                          observacion_privada='[DEMO] Mejoró la recepción; revisar postura en la próxima clase.'))
                        if step == 2 and attendance in ('A', 'J'):
                            doc, created = Justificativo.objects.get_or_create(
                                evaluacion=evaluation, motivo=f'{demo_tag}: documento ficticio sin validez médica.',
                                defaults={'estado': 'aprobado' if attendance == 'J' else 'pendiente'})
                            if created:
                                doc.archivo.save('justificativo-demo.jpg', ContentFile(fixture.read_bytes()), save=True)
            for index, player in enumerate(group):
                for completed in (False, True):
                    Rutina.objects.get_or_create(
                        jugador=player, titulo=f'[{demo_tag}] {"Coordinación completada" if completed else "Pase y recepción pendiente"}',
                        defaults=dict(fecha=today + timedelta(days=-1 if completed else 1), completada=completed,
                                      objetivo='Ejemplo ficticio para probar planificación y seguimiento.',
                                      ejercicios='Ejemplo de demostración: control entre conos, 3 series de 5 recorridos.\nPase y recepción: 2 series de 8 repeticiones.\nDescanso: 60 segundos. El entrenador debe adaptar el contenido antes de usarlo.',
                                      observaciones='[DEMO] Completó el circuito con mayor control.' if completed else ''))
                authorization, created = Autorizacion.objects.get_or_create(
                    jugador=player, apoderado=f'Apoderado ficticio {demo_tag}',
                    defaults=dict(fecha=today, responsable='Registro ficticio DEMO', estado=['pendiente', 'vigente', 'revocada'][index % 3]))
                if created:
                    authorization.archivo.save('autorizacion-demo.jpg', ContentFile(fixture.read_bytes()), save=True)
        for index in range(6):
            equipment, created = Equipo.objects.get_or_create(
                codigo=f'RECORRIDO-{today:%Y%m%d}-{index + 1}',
                defaults=dict(nombre=f'[DEMO] {"Patines" if index % 2 == 0 else "Stick"} recorrido {index + 1}',
                              estado='reparacion' if index == 5 else 'desgastado' if index == 4 else 'bueno'))
            if created and index in (2, 3):
                Prestamo.objects.create(equipo=equipment, jugador=players[index],
                                        devuelto=timezone.now() if index == 3 else None)
        self.stdout.write(self.style.SUCCESS(f'Datos DEMO listos: {added} jugadores nuevos. Recorrido {today}: clases realizadas, programadas y canceladas; rutinas, evaluaciones, inventario, justificativos y autorizaciones ficticias. No se restablecen cambios existentes.'))

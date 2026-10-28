import json
from functools import wraps
from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Jugador, ClaseEntrenamiento, Evaluacion, Justificativo, Equipo, Prestamo, Rutina, Auditoria
from .forms import JugadorForm

def coach(view):
    @login_required
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff: raise PermissionDenied
        return view(request, *args, **kwargs)
    return wrapped

def log(request, text):
    Auditoria.objects.create(usuario=request.user, accion=text)

@login_required
def home(request):
    if not request.user.is_staff:
        player = Jugador.objects.filter(rut=request.user.username).first()
        return render(request, 'seguimiento/student.html', {'player': player, 'evaluaciones': Evaluacion.objects.filter(jugador=player).select_related('clase').order_by('-clase__fecha', '-id'), 'rutinas': Rutina.objects.filter(jugador=player).order_by('-fecha')})
    sessions = ClaseEntrenamiento.objects.exclude(estado='cancelada').order_by('-fecha', '-id')
    session = get_object_or_404(ClaseEntrenamiento, pk=request.GET['sesion']) if request.GET.get('sesion') else (sessions.filter(fecha__lte=timezone.localdate()).first() or sessions.first())
    players = Jugador.objects.order_by('nombre_completo')
    if session and session.categoria:
        players = players.filter(Q(categoria=session.categoria) | Q(evaluacion__clase=session)).distinct()
    category = request.GET.get('categoria', '')
    if category: players = players.filter(categoria=category)
    scores = {e.jugador_id: e for e in Evaluacion.objects.filter(clase=session)}
    return render(request, 'seguimiento/pista.html', {'sesiones': sessions, 'sesion': session, 'filas': [(p, scores.get(p.pk)) for p in players], 'categorias': Jugador.CATEGORIAS, 'categoria': category, 'bloqueada': bool(session and (session.estado != 'realizada' or session.fecha > timezone.localdate()))})

@coach
@require_POST
def new_session(request):
    return redirect('programar_clase')

@coach
@require_POST
def save_score(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict): raise ValueError
        attendance = data['asistencia']
        if attendance not in ('P', 'A', 'T'): raise ValueError
        notes = {k: data[k] for k in ('nota_frenado', 'nota_pase', 'nota_tiro')}
        if any(type(v) is not int or not 0 <= v <= 10 for v in notes.values()): raise ValueError
        if attendance == 'A': notes = dict.fromkeys(notes, 0)
        player = get_object_or_404(Jugador, pk=data['jugador'])
        session = get_object_or_404(ClaseEntrenamiento, pk=data['sesion'])
        if session.estado != 'realizada' or session.fecha > timezone.localdate():
            return JsonResponse({'error': 'Marca la clase como realizada antes de evaluar.'}, status=409)
        if session.categoria and player.categoria != session.categoria and not Evaluacion.objects.filter(jugador=player, clase=session).exists():
            return JsonResponse({'error': 'El jugador no pertenece a esta categoría.'}, status=400)
        with transaction.atomic():
            existing = Evaluacion.objects.filter(jugador=player, clase=session).first()
            if existing and existing.asistencia == 'J': return JsonResponse({'error': 'La ausencia ya está justificada.'}, status=409)
            e, _ = Evaluacion.objects.update_or_create(jugador=player, clase=session, defaults={'asistencia': attendance, **notes})
            if not e.categoria_registrada:
                e.categoria_registrada = session.categoria or player.categoria
                e.save(update_fields=['categoria_registrada'])
            log(request, f'Evaluó jugador {player.pk} en entrenamiento {session.pk}')
        return JsonResponse({'ok': True, 'evaluacion': e.pk})
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'error': 'Datos inválidos.'}, status=400)

@coach
def players(request):
    q = request.GET.get('q', '').strip()
    rows = Jugador.objects.filter(Q(nombre_completo__icontains=q) | Q(rut__icontains=q)).order_by('nombre_completo')
    return render(request, 'seguimiento/players.html', {'jugadores': rows, 'q': q})

@coach
def player_edit(request, pk=None):
    instance = get_object_or_404(Jugador, pk=pk) if pk else None
    old_rut = instance.rut if instance else None
    form = JugadorForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        if old_rut and old_rut != form.cleaned_data['rut']:
            form.add_error('rut', 'El RUT vincula la cuenta del jugador. No se puede cambiar en esta versión.')
        else:
            obj = form.save()
            log(request, f'Guardó jugador {obj.pk}')
            return redirect('jugadores')
    return render(request, 'seguimiento/form.html', {'form': form, 'titulo': 'Editar jugador' if pk else 'Agregar jugador'})

@coach
def history(request, pk):
    player = get_object_or_404(Jugador, pk=pk)
    evaluations = Evaluacion.objects.filter(jugador=player).select_related('clase').order_by('clase__fecha', 'id')
    chart = [{'fecha': str(e.clase.fecha), 'frenado': e.nota_frenado or None, 'pase': e.nota_pase or None, 'tiro': e.nota_tiro or None} for e in evaluations if e.asistencia in ('P', 'T') and e.clase.estado == 'realizada']
    return render(request, 'seguimiento/history.html', {'player': player, 'evaluaciones': evaluations, 'chart': chart, 'rutinas': Rutina.objects.filter(jugador=player).order_by('-fecha')})

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Justificativo
        fields = ['evaluacion', 'motivo', 'archivo']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['evaluacion'].queryset = Evaluacion.objects.filter(asistencia__in=['A', 'T']).select_related('jugador', 'clase')
        self.fields['evaluacion'].label_from_instance = lambda e: f'{e.jugador.nombre_completo} · {e.clase.fecha} · sesión {e.clase_id}'
    def clean_archivo(self):
        file = self.cleaned_data['archivo']; head = file.read(8); file.seek(0)
        ext = file.name.lower().rsplit('.', 1)[-1]
        if file.size > 10 * 1024 * 1024 or not ((ext == 'pdf' and head.startswith(b'%PDF-')) or (ext in ('jpg', 'jpeg') and head.startswith(b'\xff\xd8\xff'))):
            raise forms.ValidationError('Adjunta un PDF o JPG válido de hasta 10 MB.')
        return file

@coach
def documents(request):
    return render(request, 'seguimiento/documents.html', {'documentos': Justificativo.objects.select_related('evaluacion__jugador', 'evaluacion__clase').order_by('-creado')})

@coach
def document_add(request):
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(); log(request, f'Cargó justificativo {obj.pk}')
        return redirect('justificativos')
    return render(request, 'seguimiento/form.html', {'form': form, 'titulo': 'Adjuntar justificativo', 'ayuda': 'Selecciona una asistencia registrada como ausente o atraso. Al aprobar se marcará Ausente justificado.'})

@coach
def document_file(request, pk):
    doc = get_object_or_404(Justificativo, pk=pk)
    return FileResponse(doc.archivo.open('rb'), as_attachment=True, filename=f'justificativo-{pk}.{doc.archivo.name.rsplit(".", 1)[-1]}')

@coach
@require_POST
def document_review(request, pk):
    decision = request.POST.get('estado')
    if decision not in ('aprobado', 'rechazado'): raise PermissionDenied
    with transaction.atomic():
        doc = get_object_or_404(Justificativo.objects.select_for_update(), pk=pk)
        if doc.estado == 'pendiente':
            doc.estado = decision; doc.save()
            if decision == 'aprobado': Evaluacion.objects.filter(pk=doc.evaluacion_id).update(asistencia='J', nota_frenado=0, nota_pase=0, nota_tiro=0)
            log(request, f'Justificativo {pk}: {decision}')
    return redirect('justificativos')

@coach
def inventory(request):
    active = {p.equipo_id: p for p in Prestamo.objects.filter(devuelto__isnull=True).select_related('jugador')}
    rows = [(e, active.get(e.pk)) for e in Equipo.objects.order_by('codigo') if not request.GET.get('pendientes') or e.pk in active]
    return render(request, 'seguimiento/inventory.html', {'filas': rows, 'prestamos': Prestamo.objects.select_related('jugador', 'equipo').order_by('-fecha')[:100]})

@coach
def equipment_edit(request, pk=None):
    Form = forms.modelform_factory(Equipo, fields=['codigo', 'nombre', 'estado'])
    form = Form(request.POST or None, instance=get_object_or_404(Equipo, pk=pk) if pk else None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(); log(request, f'Guardó equipo {obj.pk}')
        return redirect('inventario')
    return render(request, 'seguimiento/form.html', {'form': form, 'titulo': 'Equipamiento del club'})

@coach
def loan(request, pk):
    equipment = get_object_or_404(Equipo, pk=pk)
    Form = forms.modelform_factory(Prestamo, fields=['jugador'])
    form = Form(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        if equipment.estado == 'reparacion': form.add_error(None, 'Este equipo está en reparación.')
        else:
            try:
                with transaction.atomic():
                    p = form.save(commit=False); p.equipo = equipment; p.save()
                    log(request, f'Prestó equipo {pk} al jugador {p.jugador_id}')
                return redirect('inventario')
            except IntegrityError: form.add_error(None, 'Este equipo ya tiene un préstamo pendiente.')
    return render(request, 'seguimiento/form.html', {'form': form, 'titulo': f'Prestar {equipment}'})

@coach
@require_POST
def return_loan(request, pk):
    if Prestamo.objects.filter(pk=pk, devuelto__isnull=True).update(devuelto=timezone.now()): log(request, f'Devolvió préstamo {pk}')
    return redirect('inventario')

@coach
def routines(request):
    return render(request, 'seguimiento/routines.html', {'rutinas': Rutina.objects.select_related('jugador').order_by('-fecha')})

@coach
def routine_edit(request, pk=None):
    Form = forms.modelform_factory(Rutina, fields=['jugador', 'titulo', 'objetivo', 'ejercicios', 'fecha', 'completada', 'observaciones'], widgets={'fecha': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')})
    form = Form(request.POST or None, instance=get_object_or_404(Rutina, pk=pk) if pk else None, initial={'fecha': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        obj = form.save(); log(request, f'Guardó rutina {obj.pk}')
        return redirect('rutinas')
    return render(request, 'seguimiento/form.html', {'form': form, 'titulo': 'Rutina individual'})

def registration_closed(request):
    return render(request, 'seguimiento/registration_closed.html')

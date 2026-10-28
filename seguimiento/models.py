from django.db import models
from django.utils import timezone

class Jugador(models.Model):
    CATEGORIAS = [
        ('ESC', 'Escuelita'),
        ('S15', 'Sub-15'),
        ('ADU', 'Adulta'),
    ]
    rut = models.CharField(max_length=12, unique=True)
    nombre_completo = models.CharField(max_length=100)
    categoria = models.CharField(max_length=3, choices=CATEGORIAS, default='S15')
    fecha_nacimiento = models.DateField()
    contacto_emergencia = models.CharField(max_length=15)
    observaciones = models.TextField(blank=True, null=True, default="Sin observaciones registradas.") # <-- Campo nuevo para las notas del profesor

    def __str__(self):
        return f"{self.nombre_completo} - {self.get_categoria_display()}"

class ClaseEntrenamiento(models.Model):
    fecha = models.DateField(default=timezone.localdate)
    hora = models.TimeField(null=True, blank=True)
    categoria = models.CharField(max_length=3, choices=Jugador.CATEGORIAS, blank=True, default='')
    objetivo = models.CharField(max_length=250, blank=True)
    estado = models.CharField(max_length=12, choices=[('programada', 'Programada'), ('realizada', 'Realizada'), ('cancelada', 'Cancelada')], default='realizada')
    profesor = models.CharField(max_length=50, default='Waldo Rivas')
    observaciones = models.TextField(blank=True, null=True)

class Evaluacion(models.Model):
    ESTADOS_ASISTENCIA = [
        ('P', 'Presente'),
        ('A', 'Ausente'),
        ('T', 'Atraso'),
        ('J', 'Ausente Justificado'),
    ]
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE)
    clase = models.ForeignKey(ClaseEntrenamiento, on_delete=models.CASCADE)
    asistencia = models.CharField(max_length=1, choices=ESTADOS_ASISTENCIA, default='P')
    nota_frenado = models.IntegerField(default=0)
    nota_pase = models.IntegerField(default=0)
    nota_tiro = models.IntegerField(default=0)
    observacion_privada = models.TextField(blank=True, default='')
    categoria_registrada = models.CharField(max_length=3, choices=Jugador.CATEGORIAS, blank=True, default='')

    class Meta:
        unique_together = ('jugador', 'clase')
from .pilot_models import Justificativo, Equipo, Prestamo, Rutina, Auditoria, Autorizacion

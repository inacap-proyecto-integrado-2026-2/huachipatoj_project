from collections import Counter
from datetime import timedelta
from io import BytesIO
from xml.sax.saxutils import escape
from django.db.models import Q
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Line, String, Circle
from .models import ClaseEntrenamiento, Evaluacion, Jugador

METRICS=[('nota_frenado','Frenado'),('nota_pase','Pase'),('nota_tiro','Tiro')]

def mean(rows,key):
    values=[getattr(e,key) for e in rows if e.clase.estado=='realizada' and e.asistencia in ('P','T') and getattr(e,key)>0]
    return sum(values)/len(values) if values else None

def report_data(month,player=None,category=''):
    start=month.replace(day=1);end=(start+timedelta(days=32)).replace(day=1)
    evaluations=Evaluacion.objects.filter(clase__fecha__gte=start,clase__fecha__lt=end).select_related('jugador','clase').order_by('clase__fecha','clase_id','jugador__nombre_completo')
    if player:evaluations=evaluations.filter(jugador=player)
    else:evaluations=evaluations.filter(categoria_registrada=category)
    rows=list(evaluations)
    target=player.categoria if player else category
    sessions=ClaseEntrenamiento.objects.filter(fecha__gte=start,fecha__lt=end).filter(Q(categoria=target)|Q(pk__in=[e.clase_id for e in rows])).distinct().order_by('fecha','hora','id')
    valid=[e for e in rows if e.clase.estado=='realizada']
    return rows,list(sessions),valid

def build_report(month,player=None,category=''):
    rows,sessions,valid=report_data(month,player,category)
    styles=getSampleStyleSheet()
    for name in ['Title','Heading1','Heading2']:
        styles[name].textColor=colors.black
        styles[name].keepWithNext=True
    styles.add(ParagraphStyle(name='SmallText',fontSize=8,leading=11,spaceAfter=4))
    styles['BodyText'].fontSize=10;styles['BodyText'].leading=14
    def para(s,style='BodyText'):return Paragraph(escape(str(s)),styles[style])
    def table(data,widths):
        cells=[[para(v,'SmallText') for v in row] for row in data]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5edf4')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#cbd5e1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f6f8fa')])]))
        return t
    width=17.5*cm
    title=player.nombre_completo if player else dict(Jugador.CATEGORIAS).get(category,category)
    story=[para('Informe mensual de rendimiento','Title'),para('CD Huachipato · Hockey en patines'),para(month.strftime('%m/%Y')+' · '+title),Spacer(1,12)]
    counts=Counter(s.estado for s in sessions)
    story+=[para('Entrenamientos del período','Heading2'),table([['Programadas','Realizadas','Canceladas'],[counts['programada'],counts['realizada'],counts['cancelada']]],[width/3]*3)]
    story.append(para('Las cifras corresponden al estado actual de las clases del mes. Se incluyen clases de la categoría seleccionada y clases con registros del jugador o categoría. En informes individuales se usa la categoría actual para clases sin evaluación; no equivale a una matrícula histórica.','SmallText'))
    attendance=Counter(e.asistencia for e in valid)
    story+=[para('Asistencia registrada en clases realizadas','Heading2'),table([['Presente','Atraso','Ausente','Justificado'],[attendance['P'],attendance['T'],attendance['A'],attendance['J']]],[width/4]*4)]
    story.append(para('Son registros, no porcentajes de asistencia. Los alumnos sin registro no se consideran ausentes automáticamente.','SmallText'))
    avgs=[mean(valid,k) for k,label in METRICS]
    story+=[para('Promedios de habilidades','Heading2'),table([[label for k,label in METRICS],['Sin evaluar' if x is None else f'{x:.2f} / 10' for x in avgs]],[width/3]*3)]
    story.append(para('Solo se promedian notas de 1 a 10 de presentes o atrasados en clases realizadas. Se excluyen ausencias, clases canceladas/programadas y habilidades sin evaluar.','SmallText'))
    by_date={}
    for e in valid:by_date.setdefault(e.clase.fecha,[]).append(e)
    if by_date:
        dates=sorted(by_date);drawing=Drawing(width,165)
        for n in [1,4,7,10]:
            y=30+(n-1)*12;drawing.add(Line(25,y,width-10,y,strokeColor=colors.HexColor('#dddddd')));drawing.add(String(4,y-3,str(n),fontSize=8))
        for idx,(key,label) in enumerate(METRICS):
            color=[colors.HexColor('#0369a1'),colors.HexColor('#047857'),colors.HexColor('#a16207')][idx]
            last=None
            for i,day in enumerate(dates):
                value=mean(by_date[day],key)
                if value is None:last=None;continue
                x=30+i*(width-60)/max(1,len(dates)-1);y=30+(value-1)*12
                if last:drawing.add(Line(*last,x,y,strokeColor=color,strokeWidth=1.5))
                drawing.add(Circle(x,y,2.5,fillColor=color,strokeColor=color));last=(x,y)
            drawing.add(String(30+idx*145,153,label,fontSize=9,fillColor=color))
        drawing.add(String(25,12,dates[0].strftime('%d/%m'),fontSize=8))
        if len(dates)>1:drawing.add(String(width-45,12,dates[-1].strftime('%d/%m'),fontSize=8))
        story += [para('Evolución del período','Heading2'),drawing,para('Cada punto representa el promedio de las notas disponibles de ese día. En informes de categoría puede variar el grupo evaluado entre fechas.','SmallText')]
    if not rows:story.append(para('No hay evaluaciones registradas para esta selección.'))
    if not player and valid:
        grouped={}
        for e in valid:grouped.setdefault(e.jugador,[]).append(e)
        data=[['Jugador','Frenado','Pase','Tiro']]
        for p,ev in sorted(grouped.items(),key=lambda x:x[0].nombre_completo):
            data.append([p.nombre_completo]+['Sin evaluar' if mean(ev,k) is None else f'{mean(ev,k):.2f}' for k,label in METRICS])
        story += [para('Resumen por jugador','Heading2'),table(data,[width*.49,width*.17,width*.17,width*.17])]
    data=[['Fecha / clase','Jugador','Estado / asistencia','Frenado','Pase','Tiro']]
    for e in rows:
        scored=e.clase.estado=='realizada' and e.asistencia in ('P','T')
        data.append([str(e.clase.fecha)+' / #'+str(e.clase_id),e.jugador.nombre_completo,e.clase.get_estado_display()+' / '+e.get_asistencia_display()]+[str(getattr(e,k)) if scored and getattr(e,k)>0 else '—' for k,label in METRICS])
    if rows:story += [para('Detalle de registros','Heading2'),table(data,[width*.19,width*.27,width*.24,width*.10,width*.10,width*.10])]
    if sessions:
        story += [para('Agenda del período','Heading2'),table([['Fecha y hora','Categoría','Estado']]+[[str(s.fecha)+' '+(s.hora.strftime('%H:%M') if s.hora else ''),s.get_categoria_display() or 'Histórica sin categoría',s.get_estado_display()] for s in sessions],[width*.4,width*.35,width*.25])]
    story.append(Spacer(1,12));story.append(para('Este informe no incluye observaciones privadas, contactos, RUT ni documentos de autorización o salud. Las categorías de evaluaciones anteriores a esta actualización se reconstruyeron con la ficha disponible al migrar.','SmallText'))
    output=BytesIO()
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.grey);canvas.drawString(1.75*cm,1*cm,'Huachipato · Informe mensual');canvas.drawRightString(19.25*cm,1*cm,str(doc.page))
    doc=SimpleDocTemplate(output,pagesize=(21*cm,29.7*cm),leftMargin=1.75*cm,rightMargin=1.75*cm,topMargin=1.5*cm,bottomMargin=1.7*cm)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    return output.getvalue()

"""Landing de la Ley N.° 21.719 y su checklist descargable: fuente única del contenido."""

import datetime

ENTRY_INTO_FORCE = datetime.date(2026, 12, 1)
CHECKLIST_LEAD = "checklist-21719"

KEY_POINTS = [
    {
        "icon": "bi-calendar-check",
        "title": "Rige desde el 1 de diciembre de 2026",
        "text": (
            "La Ley N.° 21.719 modifica la Ley N.° 19.628 sobre protección de la vida privada. "
            "Fue publicada en diciembre de 2024 y dio dos años para adecuarse."
        ),
    },
    {
        "icon": "bi-building",
        "title": "Aplica a toda empresa que trate datos",
        "text": (
            "Clientes, trabajadores, proveedores, postulantes o contactos comerciales: si su empresa guarda o usa "
            "datos de personas, la ley le aplica, sin importar su tamaño."
        ),
    },
    {
        "icon": "bi-bank",
        "title": "Nueva Agencia que fiscaliza y sanciona",
        "text": (
            "Se crea la Agencia de Protección de Datos Personales, con facultades para fiscalizar, "
            "resolver reclamos de los titulares y aplicar multas."
        ),
    },
    {
        "icon": "bi-percent",
        "title": "Multas de hasta 20.000 UTM",
        "text": (
            "Las infracciones se clasifican en leves, graves y gravísimas, con multas de hasta 5.000, "
            "10.000 y 20.000 UTM respectivamente, y quedan en un registro público de sanciones."
        ),
    },
]

OBLIGATIONS = [
    ("Base de licitud", "Cada tratamiento debe apoyarse en el consentimiento del titular u otra base que la ley reconoce."),
    ("Deber de información", "Informar con claridad qué datos se recogen, para qué, por cuánto tiempo y con quién se comparten."),
    (
        "Derechos de los titulares",
        "Responder solicitudes de acceso, rectificación, supresión, oposición, portabilidad y bloqueo dentro de plazo.",
    ),
    ("Seguridad", "Adoptar medidas técnicas y organizativas proporcionales al riesgo de los datos que se tratan."),
    ("Vulneraciones de seguridad", "Registrar los incidentes y notificar a la Agencia y, en ciertos casos, a los afectados."),
    ("Encargados y transferencias", "Regular por contrato a los proveedores que tratan datos por cuenta de la empresa."),
]

FAQS = [
    (
        "¿Mi pyme está obligada a cumplir la Ley N.° 21.719?",
        "Sí. La ley aplica a toda persona natural o jurídica que trate datos personales, sin importar su tamaño. "
        "Las obligaciones se gradúan según el volumen y el riesgo de los datos, pero los principios, el deber de "
        "información y la atención de derechos rigen para todas.",
    ),
    (
        "¿Qué pasa si no me adecúo antes del 1 de diciembre de 2026?",
        "Desde esa fecha la Agencia puede fiscalizar y sancionar. Además de las multas, las sanciones se publican en el "
        "Registro Nacional de Sanciones y Cumplimiento, lo que afecta la reputación de la empresa frente a clientes y socios.",
    ),
    (
        "¿Los datos de mis trabajadores también están cubiertos?",
        "Sí. Fichas de personal, licencias médicas, control de asistencia, biometría y videovigilancia son tratamientos "
        "de datos personales, y algunos involucran datos sensibles con exigencias mayores.",
    ),
    (
        "¿Qué es el modelo de prevención de infracciones?",
        "Es un programa voluntario de cumplimiento que la empresa puede adoptar y certificar. Si se implementa de forma "
        "efectiva, la ley lo considera para atenuar la responsabilidad en caso de infracción.",
    ),
    (
        "¿Cuánto toma adecuarse?",
        "Depende de cuántos datos trate la empresa y de cómo los gestione hoy. Un diagnóstico inicial permite "
        "priorizar lo urgente y armar un plan realista antes de la entrada en vigencia.",
    ),
]

CHECKLIST = [
    (
        "Inventario",
        [
            "Identificamos qué datos personales tratamos: clientes, trabajadores, proveedores, postulantes y contactos.",
            "Sabemos dónde están guardados: sistemas, planillas, correos, papel y proveedores en la nube.",
            "Distinguimos los datos sensibles (salud, biometría, origen, creencias) y los de niños, niñas y adolescentes.",
            "Llevamos un registro de las actividades de tratamiento con su finalidad y plazo de conservación.",
        ],
    ),
    (
        "Licitud e información",
        [
            "Cada tratamiento tiene una base de licitud identificada (consentimiento, contrato, obligación legal u otra).",
            "Los consentimientos que pedimos son libres, informados, específicos y podemos demostrarlos.",
            "Nuestra política de privacidad está actualizada y es fácil de encontrar en el sitio web.",
            "Los formularios, el sitio web y las cookies informan qué datos se recogen y para qué.",
        ],
    ),
    (
        "Derechos de los titulares",
        [
            "Tenemos un canal para recibir solicitudes de acceso, rectificación, supresión, oposición, portabilidad y bloqueo.",
            "Hay una persona responsable de responderlas y un procedimiento con plazos.",
        ],
    ),
    (
        "Seguridad y proveedores",
        [
            "Los accesos a los datos están limitados a quienes los necesitan para su trabajo.",
            "Contamos con un protocolo para detectar, registrar y notificar vulneraciones de seguridad.",
            "Los contratos con proveedores que tratan datos por nosotros incluyen cláusulas de protección de datos.",
            "Sabemos si transferimos datos fuera de Chile y bajo qué resguardos.",
        ],
    ),
    (
        "Gobierno",
        [
            "Designamos a una persona o equipo a cargo del cumplimiento en protección de datos.",
            "Capacitamos a quienes manejan datos personales en la empresa.",
            "Evaluamos si nos conviene adoptar un modelo de prevención de infracciones.",
        ],
    ),
]


def days_left(today=None):
    today = today or datetime.date.today()
    return max((ENTRY_INTO_FORCE - today).days, 0)

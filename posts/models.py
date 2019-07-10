from django.db import models
from django.contrib.auth.models import User


STATUS_CHOICES = (
    ('draft', 'draft'),
    ('review', 'review'),
    ('rejected', 'rejected'),
    ('need_changes', 'need changes'),
    ('published', 'published')
)

REVIEW_STATUS_CHOICES = (
    ('pending', 'Pending'),
    ('completed', 'Completed')
)

POST_TYPE_CHOICES = (
    ('embeded', 'embeded'),
    ('youtube', 'youtube')
)


class Post(models.Model):
    """
    Post Model

    Post has some properties related to a post on a web, a generic container for content in Afinidata.

    Args:
        name: Nombre del post.
        status: Puede ser: draft, review, rejected, need_changes, published. Donde “draft” representa que aún está en borrador, “review” que se encuentra en revisión, “rejected” que ha sido rechazado, “need_changes” que hay cambios por realizar y “published”, que representa que el servicio que distribuye los posts lo tomará en cuenta.
        type: Puede ser: embeded, youtube. Donde embeded muestra en un iframe que ocupa toda la pantalla el contenido de un link, y youtube muestra un vídeo de youtube a través de su ID. (Próximo paso, un editor WYSIWYG y un type extra llamado “content”).
        content: Dependiendo del type, debería ser un link en el type “embeded”, y el ID del vídeo de Youtube en el type “youtube”. (Próximo paso, contenido resultante del editor WYSIWYG en el type “content”).
        content_activity: Contenido que es enviado al usuario del bot cuando este por problemas de conexión no puede ver el enlace o el vídeo del post. Se utiliza este signo “|” para delimitar el contenido de cada mensaje a través del chatbot.
        user: Usuario creador del post.
        min_range: El servicio que devuelve actividades se basa en un value para devolver un post dentro del rango, si value es mayor a este atributo el post es candidato para ser enviado.
        max_range: El servicio que devuelve actividades se basa en un value para devolver un post dentro del rango, si value es menor a este atributo el post es candidato para ser enviado.
        preview: El servicio que devuelve actividades, devuelve un pequeño resumen de qué trata esta actividad para llamar la atención del usuario, es este atributo.
        new (Por eliminar): Delimitaba en cierta fecha si el servicio debía de tomar en cuenta el post para enviarse a usuarios.
        thumbnail: El servicio que devuelve actividades, devuelve una imagen relacionada a la actividad. La url de la imagen debe guardarse en este atributo.
        area_id (Para uso próximo): En idea, guarda el id del área al que pertenecen (Áreas basadas en el proyecto Core (cognitivo, motor, emocional)). Para que el servicio basado en el área solicitada devuelva únicamente posts de esa área. Por defecto se están solicitando a través del chatbot únicamente posts con área 1, mismo valor que se está guardando automáticamente en el modelo.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    name = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS_CHOICES, max_length=255, default='draft')
    type = models.CharField(max_length=255, default='embeded', choices=POST_TYPE_CHOICES)
    content = models.TextField()
    content_activity = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    min_range = models.IntegerField(null=True, default=0)
    max_range = models.IntegerField(null=True, default=72)
    preview = models.TextField()
    new = models.BooleanField(default=False)
    thumbnail = models.TextField()
    area_id = models.IntegerField(null=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Interaction(models.Model):
    """
    Interaction

    Tracking the user interaction with content (or general interaction with the system).

    Args:
        post: Post asociado a la interacción. (Puede ser nulo, acciones como “iniciar sesión” no van asociadas a ningún post. Acciones como calificar si).
        user_id: ID del usuario del bot asociado a la interaction.
        username: Username del usuario del bot asociado a la interaction (Redundancia que se utiliza para ciertos reportes).
        channel_id: channel id del usuario del bot.
        bot_id: Bot al cual está conectado el usuario.
        type: String que guarda el tipo de interaction que ejecutó el usuario, estas pueden ser de cualquier tipo. De uso cotidiano en la plataforma en ciertas cosas se encuentran ‘session’ y ‘opened’, su uso puede ser muy variado.
        value: Valor de tipo Entero que puede almacenarse en las interacciones. (Formato de Entero posiblemente temporal, guardado así por alguna necesidad, por revisar)
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)
    user_id = models.IntegerField(default=0)
    username = models.CharField(max_length=255, null=True)
    channel_id = models.CharField(default="", max_length=50)
    bot_id = models.IntegerField(default=1)
    type = models.CharField(max_length=255, default='open')
    value = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.channel_id


class Feedback(models.Model):
    """
    Feedback

    Args:
        post: Post que recibe la calificación del usuario.
        user_id: ID del usuario del bot asociado a la interaction.
        username: Username del usuario del bot asociado a la interaction (Redundancia que se utiliza para ciertos reportes).
        channel_id: channel id del usuario del bot.
        bot_id: Bot al cual está conectado el usuario.
        Value: Valor de tipo entero que el usuario del bot le dio al post.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).

    """

    post = models.ForeignKey('Post', on_delete=models.CASCADE)
    user_id = models.IntegerField(default=0)
    username = models.CharField(max_length=255, null=True)
    channel_id = models.CharField(default="", max_length=50)
    bot_id = models.IntegerField(default=1)
    value = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.channel_id


class Label(models.Model):
    """
    Label

    Args:
        name: Nombre de la categoría
        posts: Referencia de muchos a muchos con el modelo Posts.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
        Question:
        name: Texto de pregunta que le llega al usuario (si se solicita a través de un servicio).
        Post: Referencia al post que pertenece esa pregunta.
        Replies (Por eliminar): Casilla de texto que guardaba las posibles respuestas a una pregunta.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posts = models.ManyToManyField(Post)

    def __str__(self):
        return self.name


class Question(models.Model):
    """
    Question:

    Args:
        name: Texto de pregunta que le llega al usuario (si se solicita a través de un servicio).
        Post: Referencia al post que pertenece esa pregunta.
        Replies (Por eliminar): Casilla de texto que guardaba las posibles respuestas a una pregunta.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    name = models.CharField(max_length=255, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    replies = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Response(models.Model):
    """
    Response:

    Args:
        question: Referencia a la question respondida.
        user_id: ID del usuario del bot que respondió a la pregunta.
        username: Username del usuario del bot que respondió la pregunta.
        response: Respuesta del usuario a la pregunta.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_id = models.IntegerField()
    username = models.CharField(max_length=255)
    response = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.pk)


# https://anthonyfox.io/posts/choices-for-choices-in-django-charfields
# https://docs.djangoproject.com/en/2.2/ref/models/instances/#django.db.models.Model.get_FOO_display

AREA = [
    ('cogni', 'Cognitivo & Lenguaje'),
    ('motor', 'Motor'),
    ('socio', 'Socioemocional'),
]

SUBAREA = [
    ('lang', "Lenguaje"),
    ('soc', "Socioemocional"),
    ('premath', "Prematemática"),
    ('sensor', "Sensorial"),
    ('motof', "Motricidad Fina"),
    ('motol', "Motricidad Gruesa"),
    ('sci', "Ciencias"),
    ('art', "Arte & Cultura"),
]

COMPONENTS = [
    ("vocabulario", "Vocabulario"),
    ("articulacionfonetica", "Articulación y Fonética"),
    ("sintaxiscomunicacion", "Sintaxis/Comunicación"),
    ("lectoescritura", "Lectoescritura"),
    ("literatura", "Literatura"),
    ("autoconocimiento", "Autoconocimiento"),
    ("autonomia", "Autonomía y Vida Práctica"),
    ("autocontrol", "Autocontrol"),
    ("empatia", "Empatía"),
    ("hsocial", "Habilidades Sociales"),
    ("plogico", "Pensamiento Lógico"),
    ("numconteo", "Números y Conteo"),
    ("problemasOperacionesRazonamiento", "Resolución de Problemas y Operaciones / Razonamiento"),
    ("pVisual", "Percepción Visual"),
    ("pAuditiva", "Percepción Auditiva"),
    ("pHaptica", "Percepción háptica"),
    ("pGustativa", "Percepción Gustativa"),
    ("pOlfativa", "Percepción Olfativa"),
    ("egnostico", "Estereognóstico"),
    ("om", "Coordinación Ojo-Mano"),
    ("pinza", "Movimiento de Pinza"),
    ("desplaza", "Desplazamiento"),
    ("balance", "Balance-Equilibrio"),
    ("tono", "Fuerza-Tonicidad Muscular"),
    ("coordinacion", "Coordinación"),
    ("experimentos", "Experimentos"),
    ("botanica", "Botánica"),
    ("zoologia", "Zoología"),
    ("astronomia", "Astronomía"),
    ("cuidadomh", "Cuidado del Medio Ambiente"),
    ("medionatural", "Medio Natural"),
    ("tech", "Tecnología"),
    ("geo", "Geografía"),
    ("plasticas", "Artes Plásticas"),
    ("musik", "Música"),
    ("danzaTeatro", "Danza y Teatro"),
    ("culturas", "Culturas del Mundo"),
]


class Taxonomy(models.Model):
    post = models.OneToOneField(Post,
                                on_delete=models.CASCADE,
                                primary_key=False,
                                )
    area = models.CharField(choices=AREA, max_length=250)
    subarea = models.CharField(choices=SUBAREA, max_length=250)
    component = models.CharField(choices=COMPONENTS, max_length=250)


class Review(models.Model):
    """
    Review:

    Args:
        post: Post por revisar
        status: Estado del review. Puede ser: pending, completed.
        comment: Casilla que permite que el creador del post deje un comentario para el revisor sobre su post.
        users: Usuarios vinculados a esta Revisión. (Author y Revisor) a través del modelo UserReviewRole.
        created_at, updated_at: (Uso general, fecha de creación, fecha de última actualización).
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    status = models.CharField(choices=REVIEW_STATUS_CHOICES, default='pending', max_length=20)
    comment = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, through='UserReviewRole')

    def __str__(self):
        return "%s__%s__%s" % (self.pk, self.status, self.post.pk)


REVIEW_ROLE_CHOICES = (('author', 'author'), ('reviser', 'reviser'))


class UserReviewRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(choices=REVIEW_ROLE_CHOICES, default='author', max_length=20)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pk)


class Approbation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)

    def __str__(self):
        return "%s__%s__%s" % (self.pk, self.user.first_name, self.review.pk)


class Rejection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    comment = models.TextField(null=True)

    def __str__(self):
        return "%s__%s__%s" % (self.pk, self.user.first_name, self.review.pk)


class ReviewComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    comment = models.TextField()

    def __str__(self):
        return "%s" % self.comment


RESPONSE_VALUE_CHOICES = ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4))


class QuestionResponse(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.CharField(max_length=255)
    value = models.IntegerField(choices=RESPONSE_VALUE_CHOICES)

    def __str__(self):
        return "%s__%s__%s__%s" % (self.pk, self.question.pk, self.response, self.value)

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Заголовок',
        max_length=200,
        help_text='Дайте короткое название',
    )
    slug = models.SlugField(
        'Слаг',
        unique=True,
        null=True,
        help_text=('Укажите адрес для страницы задачи. Используйте только '
                   'латиницу, цифры, дефисы и знаки подчёркивания'),
    )
    description = models.TextField(
        'Описание',
        null=True,
        help_text=('Укажите о чём будут посты'),
    )
    verbose_name = "группа"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        'Публикация',
        max_length=200,
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Группа",
        help_text='Выберите группу',
        blank=True,
        null=True,
    )
    # поле для картинки
    image = models.ImageField(
        verbose_name="Изображение",
        upload_to='posts/',
        blank=True,
        null=True,
        help_text='Добавьте изображение')

    class Meta:
        ordering = ['-pub_date']
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name="comments",
                             verbose_name="Комментарий",
                             help_text='Напишите комментарий',)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments", verbose_name="Автор")
    text = models.TextField("Текст", help_text='Напишите текст')
    created = models.DateTimeField("Дата публикации", auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.text[:10]


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name="following")

def get_followed_authors(user):
    user_subscriptions = user.follower.all()
    followed_authors = [subscription.author for subscription
                        in user_subscriptions]
    return followed_authors

import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse


from posts.models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Петя')
        cls.post = Post.objects.create(text='А' * 100, author=cls.user)
        cls.group = Group.objects.create(title='Группа', slug='group',
                                         description='описание группы')

    settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x02\x00'
        b'\x01\x00\x80\x00\x00\x00\x00\x00'
        b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
        b'\x00\x00\x00\x2C\x00\x00\x00\x00'
        b'\x02\x00\x01\x00\x00\x02\x02\x0C'
        b'\x0A\x00\x3B'
    )
    cls.uploaded = SimpleUploadedFile(
        name='small.gif',
        content=small_gif,
        content_type='image/gif'
    )

    @classmethod
    def tearDownClass(cls):
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # создаем авторизованного клиента
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        # посчитаем текущее количество постов в БД
        self.posts_count = Post.objects.count()

    def test_form(self):
        """
        Проверка формы создания нового поста: редирект, запись в БД, текст,
        картинка. Создается новая запись в БД.
        """
        form_data = {
            'author': self.user,
            'text': 'тестовый текст',
            'slug': self.group,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), self.posts_count + 1)
        self.assertTrue(Post.objects.filter(
            author__username='Петя', text='тестовый текст').exists())
        self.assertTrue(Group.objects.filter(
            title='Группа', slug='group',
            description='описание группы').exists())

    def test_form_edit(self):
        """
        Проверка редактирования поста в шаблоне post_edit. Изменяется
        соответствующая запись а базе данных. Кол-во постов не увеличивается.
        """
        form_data = {
            'author': self.user,
            'text': 'тестовый текст'
        }
        self.authorized_client.post(
            reverse('post_edit',
                    kwargs={'username': self.user, 'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.text, 'тестовый текст')
        self.assertEqual(Post.objects.count(), self.posts_count)

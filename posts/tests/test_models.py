from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create(
                username='testuser',
            )
        )
        cls.post = Post.objects.get()

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым в Post."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Публикация',
            'pub_date': 'Дата публикации',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-task',
        )
        cls.group = Group.objects.get(slug='test-task')

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым в Group."""
        group = GroupModelTest.group
        field_verboses = {
            'title': 'Заголовок',
            'slug': 'Слаг',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым в Group."""
        group = GroupModelTest.group
        field_help_texts = {
            'description': 'Укажите о чём будут посты',
            'title': 'Дайте короткое название',
            'slug': 'Укажите адрес для страницы задачи. Используйте только '
                    'латиницу, цифры, дефисы и знаки подчёркивания',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).help_text, expected)
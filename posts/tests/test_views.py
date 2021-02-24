import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, Comment, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug',
                                         description='Тестовое описание группы'
                                         )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(author=cls.user, text='Тестовый текст',
                                       group=cls.group, image=uploaded)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('index'): 'index.html',
            reverse('new_post'): 'new.html',
            reverse('group_posts',
                    kwargs={'slug': self.group.slug}): 'group.html',
            reverse('follow_index'): 'follow.html',
            'profile.html': reverse('profile',
                                    args=[self.user.username]),
            reverse('post',
                    args=[self.user.username, self.post.id]): 'post.html',
            reverse('post_edit',
                    args=[self.user.username, self.post.id]): 'new.html',
            reverse('add_comment',
                    args=[self.user.username, self.post.id]): 'post.html',
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('index'))
        first_post = response.context.get('page')[0]
        self.assertEqual(first_post.id, self.post.id)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author.username, self.user.username)
        self.assertEqual(first_post.author.get_full_name(),
                         self.user.get_full_name())

    def test_group_page_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': self.group.slug}))
        first_post = response.context.get('page')[0]
        self.assertEqual(first_post.id, self.post.id)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group.title, self.group.title)
        self.assertEqual(first_post.group.description, self.group.description)
        self.assertEqual(first_post, self.post)

    def test_new_post_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_shows_post_on_index_page_if_post_has_group(self):
        """Главная страница содержит пост, если при его создании
            указать группу"""
        response = self.guest_client.get(reverse('index'))

        self.assertContains(response, self.post.text)
        self.assertContains(response, self.post.author.username)

    def test_shows_post_on_group_page_if_post_has_group(self):
        """Страница группы содержит пост, если при его создании
            указать группу"""
        response = self.guest_client.get(
            reverse('group_posts', kwargs={'slug': self.post.group.slug}))

        self.assertContains(response, self.post.text)
        self.assertContains(response, self.post.author.get_full_name())

    def test_post_has_correct_group(self):
        """Проверка, что пост не попал в группу, для которой не был
            предназначен"""
        group_new = Group.objects.create()
        self.assertIn(self.post, self.group.posts.all())
        self.assertNotIn(self.post, group_new.posts.all())

    def test_username_page_show_correct_context(self):
        """Шаблон username сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('profile',
                                                 args=[self.user.username]))
        first_post = response.context.get('page')[0]
        self.assertEqual(first_post.id, self.post.id)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author.username, self.user.username)

    def test_username_post_id_page_show_correct_context(self):
        """Шаблон username/post_id сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('post',
                                                 args=[self.user.username,
                                                       self.post.id]))
        first_post = response.context.get('post')
        self.assertEqual(first_post.id, self.post.id)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author.username, self.user.username)

    def test_username_post_id_edit_page_show_correct_context(self):
        """Шаблон username/post_id/edit сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('post_edit',
                                                      args=[self.user.username,
                                                            self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_posts_on_index_page_cache(self):
        response_1 = self.guest_client.get(reverse('index'))
        first_post_1 = response_1.context.get('page')[0]
        self.assertContains(response_1, first_post_1.text)

        Post.objects.create(author=self.user, text='Новый тестовый текст')
        response_2 = self.guest_client.get(reverse('index'))
        first_post_2 = response_2.context.get('page')[0]
        self.assertNotContains(response_2, first_post_2.text)

        cache.clear()
        response_3 = self.guest_client.get(reverse('index'))
        self.assertContains(response_3, first_post_2.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = get_user_model().objects.create(username='User')
        for i in range(13):
            Post.objects.create(author=cls.user, text=f'Текст{i}')

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')

        self.assertEqual(len(response.context.get('page').object_list), 3)


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(author=cls.user, text='Тестовый текст')
        cls.comment = Comment.objects.create(author=cls.user,
                                             post=cls.post,
                                             text='Текст комментария')

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_authorized_client_can_comments_post(self):
        response = self.authorized_client.get(reverse(
            'add_comment', args=[self.user.username, self.post.id]))

        self.assertContains(response, self.comment)

    def test_guest_client_cant_comments_post(self):
        response = self.guest_client.get(reverse(
            'add_comment', args=[self.user.username, self.post.id]))

        self.assertRedirects(
            response, f'/auth/login/?next=/{self.user.username}/'
                      f'{self.post.id}/comment/')


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(
            username='TestUser_follower')
        cls.user_author = User.objects.create_user(
            username='TestUser_author')
        cls.post = Post.objects.create(author=cls.user_author,
                                       text='Тестовый текст', )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_follower)

    def test_authorized_client_can_follow(self):
        response = self.authorized_client.get(
            reverse(
                'profile_follow', args=[self.user_author.username]))

        self.assertRedirects(response, reverse(
            'profile', args=[self.user_author.username]))
        self.assertTrue(Follow.objects.filter(
            user=self.user_follower).exists())

    def test_authorized_client_can_unfollow(self):
        self.user_author.following.create(user=self.user_follower)
        self.user_author.following.filter(user=self.user_follower).delete()
        response = self.authorized_client.get(
            reverse('profile_unfollow',
                    args=[self.user_author.username]))

        self.assertRedirects(response, reverse(
            'profile', args=[self.user_author.username]))
        self.assertFalse(Follow.objects.filter(
            user=self.user_follower).exists())

    def test_post_appears_for_followers(self):
        self.user_author.following.create(user=self.user_follower)
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertContains(response, self.post)

    def test_post_not_appears_for_not_followers(self):
        user_another_author = User.objects.create_user(
            username='TestUser_another_author')
        post_of_another_author = Post.objects.create(
            author=user_another_author, text='Text of another author')

        response = self.authorized_client.get(reverse('follow_index'))

        self.assertNotContains(response, post_of_another_author)

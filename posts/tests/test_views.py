from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django import forms

from posts.models import Group, Post

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
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (reverse('group_posts',
                                   kwargs={'slug': self.group.slug})),
            'follow.html': reverse('follow_index'),
            'profile.html': reverse('profile',
                                    args=[self.user.username]),
            'post.html': reverse('post',
                                 args=[self.user.username, self.post.id]),
            'new.html': reverse('post_edit',
                                args=[self.user.username, self.post.id]),
            'post.html': reverse('add_comment',
                                 args=[self.user.username, self.post.id]),
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
            'group': forms.fields.ChoiceField
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
        response_1 = self.guest_client.get(reverse('posts:index'))
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
            Post.objects.create(author=cls.user, text='Текст' + str(i))

    def test_first_page_containse_ten_records(self):
        response = self.client.get(reverse('index'))

        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')

        self.assertEqual(len(response.context.get('page').object_list), 3)


class CommentViewTest(TestCase):

    def test_create_comment(self):
        user = User.objects.create_user(username='test_username')
        guest_client = Client()
        authorized_client = Client()
        self.client.force_login(user)
        post = Post.objects.create(author=user, text='Some random post text')
        # comment = Comment.odjects.create()
        comments = {'comment_1': 'Some random text first',
                    'comment_2': 'Some random text second',
                    }
        url = reverse('posts:add_comment', args=[user.username, post.id])

        response_1 = authorized_client.post(url, comments)
        #response_2 = guest_client.post(url, comments)

        self.assertRedirects(response_1, reverse('posts:post',
                                                 args=[user.username,
                                                       post.id]))
        comment_1 = Comment.objects.filter(author=user, post=post,
                                           text=comments['comment_1']).first()
        comment_2 = Comment.objects.filter(author=user, post=post,
                                           text=comments['comment_2']).first()
        self.assertIsNotNone(comment_1)
        self.assertIsNone(comment_2)

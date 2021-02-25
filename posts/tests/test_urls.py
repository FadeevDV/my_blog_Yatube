from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(author=cls.user, text='Тестовый текст')
        cls.group = Group.objects.create(title='Тестовая группа',
                                         slug='test-slug',
                                         description='Тестовое описание группы'
                                         )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_index_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_url_exists_at_desired_location(self):
        """Страница /group/group/ доступна любому пользователю."""
        response = self.guest_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, 200)

    def test_username_url_exists_at_desired_location(self):
        """Страница /username/ доступна любому пользователю."""
        response = self.guest_client.get(f'/{self.user.username}/')
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_url_exists_at_desired_location(self):
        """Страница /username/post_id/ доступна любому пользователю."""
        response = self.guest_client.get(f'/{self.user.username}/'
                                         f'{self.post.id}/')
        self.assertEqual(response.status_code, 200)

    def test_new_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_url_redirect_anonymous_on_admin_login(self):
        """Страница /new/ перенаправит анонимного пользователя
        на страницу логина."""
        response = self.guest_client.get('/new/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_username_post_id_edit_author_url_exists_at_desired_location(
            self):
        """Страница /username/post_id/edit доступна только автору поста."""
        response = \
            self.authorized_client.get(f'/{self.user.username}/'
                                       f'{self.post.id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_username_post_id_edit_guest_url_exists_at_desired_location(self):
        """Страница /username/post_id/edit доступна только автору поста.
        Неавторизированного пользователя перенаправит на страницу входа"""
        response = self.guest_client.get(f'/{self.user.username}/'
                                         f'{self.post.id}/edit/')
        self.assertRedirects(response, f'/auth/login/?next=/'
                                       f'{self.user.username}/'
                                       f'{self.post.id}/edit/')

    def test_username_post_id_edit_not_author_url_exists_at_desired_location(
            self):
        """Страница /username/post_id/edit доступна только автору поста.
        Авторизированного пользователя, но не автора поста, перенаправит на
        страницу просмотра этой записи"""
        user_not_author = User.objects.create(username='not_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(user_not_author)
        response = self.authorized_client.get(
            f'/{PostURLTests.user.username}/{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/{self.user.username}/'
                                       f'{self.post.id}/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': '/',
            'new.html': '/new/',
            'group.html': '/group/test-slug/',
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_wrong_uri_returns_404(self):
        """возвращает ли сервер код 404, если страница не найдена."""
        response = self.client.get(f'/{self.user.username}/'
                                   f'{self.post.id} *1000/')
        self.assertEqual(response.status_code, 404)

    def test_returns_404_status_code_if_url_doesnt_exist(self):
        url = f'/{get_random_string(10)}/'
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

    @override_settings(DEBUG=False)
    def test_renders_custom_template_on_404(self):
        url = f'/{get_random_string(10)}/'
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'misc/404.html')

    def test_username_post_id_followers_guest(self):
        """Страница /follow/ доступна только автору поста.
        Неавторизированного пользователя перенаправит на страницу 302"""
        response = self.guest_client.get('/follow/')
        self.assertEqual(response.status_code, 302)

    def test_username_follower_guest(self):
        urls_and_redirects = {reverse('follow_index'): 'follow.html',
                              reverse('add_comment',
                                      args=[self.user.username,
                                            self.post.id]): 'comments.html',
                              }
        for template, reverse_name in urls_and_redirects.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse_name)
                self.assertEqual(response.status_code, 404)

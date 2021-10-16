from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = StaticURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_homepage(self):
        response = self.authorized_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_followpage(self):
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, 200)

    def test_group(self):
        group_slug = StaticURLTests.group.slug
        response = self.authorized_client.get(f'/group/{group_slug}/')
        self.assertEqual(response.status_code, 200)

    def test_profile(self):
        username = StaticURLTests.user.username
        response = self.authorized_client.get(f'/profile/{username}/')
        self.assertEqual(response.status_code, 200)

    def test_post_detail(self):
        post_id = StaticURLTests.post.pk
        response = self.authorized_client.get(f'/posts/{post_id}/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        post_id = StaticURLTests.post.pk
        response = self.authorized_client.get(f'/posts/{post_id}/edit/')
        self.assertEqual(response.status_code, 200)

    def test_create(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_about_author(self):
        response = self.authorized_client.get('/about/author/')
        self.assertEqual(response.status_code, 200)

    def test_about_tech(self):
        response = self.authorized_client.get('/about/tech/')
        self.assertEqual(response.status_code, 200)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = PostURLTests.post
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            f'/posts/{post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create.html',
            f'/posts/{post.pk}/edit/': 'posts/create.html',
        }

        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

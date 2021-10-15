import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Comment, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = PostFormTests.user
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Форма создает запись в Post."""
        user = PostFormTests.user
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый пост 2',
            'author': user,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', args=(user.username,)
        ))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что создалась запись
        self.assertTrue(
            Post.objects.filter(
                author=user,
                text=form_data['text'],
            ).exists()
        )

    def test_edit_post(self):
        """Форма изменяет запись в Post."""
        user = PostFormTests.user
        post = PostFormTests.post
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост [edited]'
        }

        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                args=(post.pk,)
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(post.pk,)
        ))
        # Проверяем, сохранилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что выбранный пост был изменен
        self.assertTrue(
            Post.objects.filter(
                author=user,
                text=form_data['text'],
            ).exists()
        )

    def test_create_post_authorized_only(self):
        """Перенаправление неавторизированного пользователя."""
        user = PostFormTests.user
        posts_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый пост 2',
            'author': user,
        }

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        url_to_login = reverse('users:login')
        url_back_to_create = reverse('posts:post_create')
        self.assertRedirects(
            response,
            f'{url_to_login}?next={url_back_to_create}'
        )

        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверяем, что не создалась запись
        self.assertFalse(
            Post.objects.filter(
                author=user,
                text=form_data['text'],
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = CommentFormTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_comment_posting(self):
        user = CommentFormTests.user
        post = CommentFormTests.post
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }

        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                args=(post.pk,)
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                args=(post.pk,)
            )
        )
        # Проверяем, увеличилось ли число комментариев
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        # Проверяем, что создался комментарий
        self.assertTrue(
            Comment.objects.filter(
                author=user,
                text=form_data['text'],
            ).exists()
        )

    def test_comment_posting_authorized_only(self):
        user = CommentFormTests.user
        post = CommentFormTests.post
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий',
        }

        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                args=(post.pk,)
            ),
            data=form_data,
            follow=True
        )

        url_to_login = reverse('users:login')
        url_back_to_post = reverse('posts:add_comment', args=(post.pk,))
        self.assertRedirects(
            response,
            f'{url_to_login}?next={url_back_to_post}'
        )
        # Проверяем, не увеличилось ли число комментариев
        self.assertEqual(Comment.objects.count(), comments_count)
        # Проверяем, что не создался комментарий
        self.assertFalse(
            Comment.objects.filter(
                author=user,
                text=form_data['text'],
            ).exists()
        )

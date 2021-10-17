import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.user = User.objects.create_user(username='test_user')
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

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )

        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = TaskPagesTests.user
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = TaskPagesTests.post
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'group_name': 'test-slug'})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': 'test_user'})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post.pk})
            ),
            'posts/create.html': reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post.pk})
        )
        self.assertTemplateUsed(response, 'posts/create.html')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        user = TaskPagesTests.user
        post = TaskPagesTests.post
        response = self.authorized_client.get(reverse('posts:index'))

        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_image = first_object.image

        self.assertEqual(post_text, post.text)
        self.assertEqual(post_image, post.image)
        self.assertEqual(post_author, user)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        user = TaskPagesTests.user
        post = TaskPagesTests.post
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'group_name': 'test-slug'}
        ))

        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_image = first_object.image

        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, user)
        self.assertEqual(post_image, post.image)

        # Пост не попал в другую группу
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'group_name': 'test-slug-2'}
        ))

        amount_object = len(response.context['page_obj'])

        self.assertEqual(amount_object, 0)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        user = TaskPagesTests.user
        post = TaskPagesTests.post
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': post.pk}
        ))

        posts_amount = response.context['posts_amount']

        post_taked = response.context['post']
        post_text = post_taked.text
        post_author = post_taked.author
        post_image = post_taked.image

        self.assertEqual(posts_amount, 1)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, user)
        self.assertEqual(post_image, post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        user = TaskPagesTests.user
        post = TaskPagesTests.post
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'test_user'}
        ))

        posts_amount = response.context['posts_amount']

        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author
        post_image = first_object.image

        self.assertEqual(posts_amount, 1)
        self.assertEqual(post_text, post.text)
        self.assertEqual(post_author, user)
        self.assertEqual(post_image, post.image)

    def test_create_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        post = TaskPagesTests.post
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': post.pk},
        ))
        form_fields = {
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_following(self):
        """Пользователь может подписываться"""
        user = TaskPagesTests.user
        user2 = TaskPagesTests.user2

        response = self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': user2.username},
        ))
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': user2.username},
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=user,
                author=user2,
            ).exists()
        )

    def test_unfollowing(self):
        """Пользователь может отписываться"""
        user = TaskPagesTests.user
        user2 = TaskPagesTests.user2

        Follow.objects.create(user=user, author=user2)

        response = self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': user2.username},
        ))
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': user2.username},
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=user,
                author=user2,
            ).exists()
        )

    def test_follow_index_follower(self):
        """Проверка содержимого избранного у подписчика"""
        user = TaskPagesTests.user
        user2 = TaskPagesTests.user2

        Follow.objects.create(user=user, author=user2)

        response = self.authorized_client.get(reverse(
            'posts:follow_index',
        ))
        posts_list = response.context['page_obj']
        self.assertTrue(
            len(posts_list) == 1
        )

    def test_follow_index_guest(self):
        """Проверка содержимого избранного у пользователя без подписок"""
        response = self.authorized_client.get(reverse(
            'posts:follow_index',
        ))

        posts_list = response.context['page_obj']
        self.assertTrue(
            len(posts_list) == 0
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        for post_number in range(13):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {post_number}',
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()

    def test_index_paginator(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_paginator(self):
        response = self.client.get(reverse(
            'posts:group_list',
            kwargs={'group_name': 'test-slug'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_paginator(self):
        response = self.client.get(reverse(
            'posts:profile',
            kwargs={'username': 'test_user'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

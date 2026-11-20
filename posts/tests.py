from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from profiles.models import UserProfile

from .models import Comment, Post


class PostTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='test-password')
        UserProfile.objects.create(user=self.user)
        self.post = Post.objects.create(
            user=self.user,
            image='posts_images/test.jpg',
            caption='Publicación de prueba',
        )

    def test_anonymous_user_can_view_but_not_comment(self):
        url = reverse('post_detail', args=[self.post.pk])

        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, {'text': 'Comentario'})

        self.assertRedirects(response, f'{reverse("login")}?next={url}')
        self.assertFalse(Comment.objects.exists())

    def test_like_requires_post_and_toggles_like(self):
        self.client.force_login(self.user)
        url = reverse('post_like_ajax', args=[self.post.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['liked'])
        self.assertTrue(self.post.likes.filter(pk=self.user.pk).exists())

        response = self.client.post(url)
        self.assertFalse(response.json()['liked'])
        self.assertFalse(self.post.likes.filter(pk=self.user.pk).exists())

    def test_invalid_comment_keeps_post_visible(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('post_detail', args=[self.post.pk]), {'text': ' '})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.caption)
        self.assertIn('text', response.context['form'].errors)
        self.assertFalse(self.post.comments.exists())

    def test_non_numeric_post_id_returns_404(self):
        response = self.client.get('/posts/not-a-number/')

        self.assertEqual(response.status_code, 404)

    def test_home_includes_authenticated_users_own_posts(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertIn(self.post, response.context['last_posts'])

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import Follow, UserProfile


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana', password='test-password')
        self.profile = UserProfile.objects.create(user=self.user)
        self.other_user = User.objects.create_user('bea', password='test-password')
        self.other_profile = UserProfile.objects.create(user=self.other_user)
        self.client.force_login(self.user)

    def test_follow_button_toggles_relationship(self):
        url = reverse('profile_detail', args=[self.other_profile.pk])

        self.client.post(url)
        self.assertTrue(Follow.objects.filter(
            follower=self.profile,
            following=self.other_profile,
        ).exists())

        self.client.post(url)
        self.assertFalse(Follow.objects.filter(
            follower=self.profile,
            following=self.other_profile,
        ).exists())

    def test_user_cannot_follow_themselves(self):
        response = self.client.post(
            reverse('profile_detail', args=[self.profile.pk]),
        )

        self.assertRedirects(
            response,
            reverse('profile_detail', args=[self.profile.pk]),
        )
        self.assertFalse(Follow.objects.exists())

    def test_database_rejects_duplicate_and_self_follows(self):
        Follow.objects.create(
            follower=self.profile,
            following=self.other_profile,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(
                follower=self.profile,
                following=self.other_profile,
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Follow.objects.create(
                follower=self.profile,
                following=self.profile,
            )

    def test_non_numeric_profile_id_returns_404(self):
        response = self.client.get('/profile/not-a-number/')

        self.assertEqual(response.status_code, 404)

    def test_profile_displays_follower_and_following_counts(self):
        Follow.objects.create(
            follower=self.profile,
            following=self.other_profile,
        )

        response = self.client.get(
            reverse('profile_detail', args=[self.other_profile.pk]),
        )

        self.assertContains(response, 'Seguidores: 1')
        self.assertContains(response, 'Seguidos: 0')

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Profile, Contact


@override_settings(STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage')
class AccountTests(TestCase):

    def test_user_registration(self):
        """
        Test user registration with valid data.
        """
        response = self.client.post(
            reverse('register'), # No namespace
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'testpassword123',
                'password2': 'testpassword123',
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/register_done.html')
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Profile.objects.filter(user__username='testuser').exists())

    def test_user_login_valid_credentials(self):
        """
        Test user login with valid credentials.
        """
        # Create a user first
        User.objects.create_user(username='loginuser', password='loginpassword123')
        response = self.client.post(
            reverse('login'),
            {'username': 'loginuser', 'password': 'loginpassword123'}
        )
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_user_login_invalid_credentials(self):
        """
        Test user login with invalid credentials.
        """
        response = self.client.post(
            reverse('login'),
            {'username': 'wronguser', 'password': 'wrongpassword'}
        )
        self.assertEqual(response.status_code, 200) # Should re-render login page
        self.assertFormError(response, 'form', None, 'Please enter a correct username and password. Note that both fields may be case-sensitive.')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_profile_creation_signal(self):
        """
        Test that a Profile is created automatically when a User is created.
        """
        user = User.objects.create_user(username='profileuser', password='profilepassword')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertEqual(user.profile.user, user) # Check the reverse relation

    def test_profile_edit(self):
        """
        Test editing a user's profile.
        """
        user = User.objects.create_user(username='edituser', password='editpassword')
        # Profile should have been created by the signal
        self.client.login(username='edituser', password='editpassword')

        new_dob = '1990-01-01'
        new_photo_path = 'users/default.png' # Assuming a default image or need to handle file uploads

        response = self.client.post(
            reverse('edit'),
            {
                'first_name': 'Edited',
                'last_name': 'User',
                'email': 'edited@example.com',
                'date_of_birth': new_dob,
                # 'photo': new_photo_path # File uploads in tests can be tricky, might need to use SimpleUploadedFile
            },
            follow=True # Follow redirect to see the updated page or success message
        )
        self.assertEqual(response.status_code, 200) # Should render the edit page again, possibly with a success message

        user.refresh_from_db()
        user.profile.refresh_from_db()

        self.assertEqual(user.first_name, 'Edited')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.email, 'edited@example.com')
        self.assertEqual(str(user.profile.date_of_birth), new_dob)
        # self.assertTrue(user.profile.photo.url.endswith(new_photo_path))

    def test_contact_model(self):
        """
        Test creating a Contact object and its fields.
        """
        user_from = User.objects.create_user(username='contactfrom', password='password')
        user_to = User.objects.create_user(username='contactto', password='password')

        contact = Contact.objects.create(user_from=user_from, user_to=user_to)

        self.assertEqual(contact.user_from, user_from)
        self.assertEqual(contact.user_to, user_to)
        self.assertIsNotNone(contact.created)
        self.assertEqual(str(contact), f'{user_from} follows {user_to}')

    def test_user_follow_view(self):
        """
        Test the user_follow view for following and unfollowing users.
        """
        user1 = User.objects.create_user(username='user1', password='password1')
        user2 = User.objects.create_user(username='user2', password='password2')

        self.client.login(username='user1', password='password1')

        # Follow user2
        response_follow = self.client.post(
            reverse('user_follow'),
            {'id': user2.id, 'action': 'follow'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' # Simulate AJAX request
        )
        self.assertEqual(response_follow.status_code, 200)
        self.assertEqual(response_follow.json()['status'], 'ok')
        self.assertTrue(Contact.objects.filter(user_from=user1, user_to=user2).exists())

        # Unfollow user2
        response_unfollow = self.client.post(
            reverse('user_follow'),
            {'id': user2.id, 'action': 'unfollow'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest' # Simulate AJAX request
        )
        self.assertEqual(response_unfollow.status_code, 200)
        self.assertEqual(response_unfollow.json()['status'], 'ok')
        self.assertFalse(Contact.objects.filter(user_from=user1, user_to=user2).exists())

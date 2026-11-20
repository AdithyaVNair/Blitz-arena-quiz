from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='tester',
            email='tester@example.com',
            password='Password123!',
            avatar='fox',
            xp=100
        )

    def test_user_attributes(self):
        self.assertEqual(self.user.avatar, 'fox')
        self.assertEqual(self.user.xp, 100)
        self.assertEqual(str(self.user), 'tester')

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Log In')
        self.assertContains(response, 'Username')
        self.assertContains(response, 'Password')

    def test_signup_page_renders(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Avatar')

    def test_user_login_and_profile(self):
        login_success = self.client.login(username='tester', password='Password123!')
        self.assertTrue(login_success)
        
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tester')
        self.assertContains(response, '100')

    def test_user_logout(self):
        self.client.login(username='tester', password='Password123!')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_google_login_dev_mode(self):
        response = self.client.get(reverse('google_login'))
        self.assertRedirects(response, reverse('profile'))

    def test_password_validator_rules(self):
        from .validators import SimplePasswordValidator
        from django.core.exceptions import ValidationError
        v = SimplePasswordValidator()
        
        # Too short
        with self.assertRaises(ValidationError):
            v.validate("Short1!")
            
        # No uppercase
        with self.assertRaises(ValidationError):
            v.validate("lowercase1!")
            
        # No special char
        with self.assertRaises(ValidationError):
            v.validate("Uppercase12")
            
        # Valid
        v.validate("ValidPass1!")


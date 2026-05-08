from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Client, Account


class BankingModelTests(TestCase):
    def test_client_and_account_creation(self):
        user = User.objects.create_user(username='mehdi', password='pass12345')
        client = Client.objects.create(user=user, phone='0600000000')
        account = Account.objects.create(client=client, account_number='ACC-TEST-001', balance=500)

        self.assertEqual(str(client), 'mehdi')
        self.assertEqual(account.client, client)
        self.assertEqual(account.balance, 500)


class BankingViewTests(TestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)

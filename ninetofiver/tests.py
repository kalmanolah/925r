from rest_framework.test import APITestCase
from rest_assured import testcases
from ninetofiver import factories


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = factories.UserFactory()
        self.client.force_authenticate(self.user)

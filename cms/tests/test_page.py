from django.test import TestCase, Client
from wagtail.models import Page
from cms.models import HomePage

class WagtailPageTests(TestCase):
    def test_homepage_creation(self):
        root = Page.get_root_nodes()[0]
        homepage = HomePage(title="Test Home", slug="test-home")
        root.add_child(instance=homepage)
        self.assertEqual(HomePage.objects.count(), 1)
        
        client = Client()
        response = client.get('/test-home/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Home")
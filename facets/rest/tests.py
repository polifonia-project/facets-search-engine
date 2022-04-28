from django.test import TestCase

#from django.test import Client

from django_test_curl import CurlClient

class File_Load_Test(TestCase):

    def setUp(self):
        self.client = CurlClient()

    def test_details(self):
        response = self.client.curl("""
          curl http://localhost:8000/customer/details/
        """)

        self.assertEqual(response.status_code, 200)


	def zip_test(self):
		#To finish
		c = Client()
		response = c.put(path = '/index/ziptest/', data = 'data/test_zip.zip', content_type = 'application/zip')

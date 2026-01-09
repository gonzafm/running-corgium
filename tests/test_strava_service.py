import unittest
from unittest.mock import patch
from src.strava.strava_client import StravaService
from src.config import settings

class TestStravaService(unittest.TestCase):

    def setUp(self):
        self.patcher = patch('src.strava.strava_client.Client')
        self.MockClient = self.patcher.start()
        self.service = StravaService()

    def tearDown(self):
        self.patcher.stop()

    def test_get_basic_info(self):
        expected_url = "http://mock-url"
        self.service.client.authorization_url.return_value = expected_url
        
        url = self.service.get_basic_info()
        
        self.service.client.authorization_url.assert_called_once_with(
            client_id=settings.strava_client_id,
            redirect_uri=settings.strava_redirect_uri,
        )
        self.assertEqual(url, expected_url)

    def test_authenticate_and_store(self):
        mock_code = "mock_code"
        expected_token = "mock_access_token"
        self.service.client.exchange_code_for_token.return_value = {"access_token": expected_token}
        
        self.service.authenticate_and_store(mock_code)
        
        self.service.client.exchange_code_for_token.assert_called_once_with(
            client_id=settings.strava_client_id,
            client_secret=settings.strava_client_secret,
            code=mock_code
        )
        self.assertEqual(self.service.tokens["Gonzalo"], expected_token)

    def test_get_athlete(self):
        mock_athlete = {"name": "Gonzalo"}
        self.service.client.get_athlete.return_value = mock_athlete
        
        result = self.service.get_athlete()
        
        self.service.client.get_athlete.assert_called_once()
        self.assertEqual(result, mock_athlete)

if __name__ == '__main__':
    unittest.main()
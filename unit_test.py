from aiounittest.case import AsyncTestCase

from config import DefaultConfig

from botbuilder.ai.luis import LuisRecognizer

from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient
from msrest.authentication import CognitiveServicesCredentials

class LuisRecognizerTest(AsyncTestCase):
    """
    This set of 3 tests will:
    - Check the endpoint construction of the LUIs recognizer.
    - check no arg for the LuisRecognizer.
    - Try to recognize intent and entities to the Luis app, assertions for intent and entities are checked.
    """
    CONFIG = DefaultConfig()
    _luisAppId: str = CONFIG.LUIS_APP_ID
    _subscriptionKey: str = CONFIG.LUIS_API_KEY
    _endpoint: str = "https://" + CONFIG.LUIS_API_HOST_NAME


    def test_luis_recognizer_construction(self):
        # Arrange
        endpoint = (
            LuisRecognizerTest._endpoint + "/luis/v2.0/apps/"
            + LuisRecognizerTest._luisAppId + "?verbose=true&timezoneOffset=-360"
            "&subscription-key=" + LuisRecognizerTest._subscriptionKey + "&q="
        )

        # Act
        recognizer = LuisRecognizer(endpoint)

        # Assert
        app = recognizer._application
        self.assertEqual(LuisRecognizerTest._luisAppId, app.application_id)
        self.assertEqual(LuisRecognizerTest._subscriptionKey, app.endpoint_key)
        self.assertEqual("https://westeurope.api.cognitive.microsoft.com", app.endpoint)

    def test_luis_recognizer_none_luis_app_arg(self):
        with self.assertRaises(TypeError):
            LuisRecognizer(application=None)
            
    async def test_multiple_intents_list_entity_with_single_value(self):
        utterance: str = "I need to book a plane from Paris to Toronto on april 12th and return on april 21st. I have a budget of 2100$."

        client = LUISRuntimeClient(LuisRecognizerTest._endpoint, 
                                   CognitiveServicesCredentials(LuisRecognizerTest._subscriptionKey))
        
        result = client.prediction.resolve(LuisRecognizerTest._luisAppId, query=utterance)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.query)
        self.assertEqual(utterance, result.query)
        self.assertIsNotNone(result.top_scoring_intent.intent)
        self.assertEqual("book", result.top_scoring_intent.intent)
        self.assertIsNotNone(result.entities)
        self.assertEqual("budget", result.entities[0].type)
        self.assertEqual("2100 $ .", result.entities[0].entity)
        self.assertEqual("dst_city", result.entities[1].type)
        self.assertEqual("toronto", result.entities[1].entity)
        self.assertEqual("end_date", result.entities[2].type)
        self.assertEqual("april 21st .", result.entities[2].entity)
        self.assertEqual("or_city", result.entities[3].type)
        self.assertEqual("paris", result.entities[3].entity)
        self.assertEqual("str_date", result.entities[4].type)
        self.assertEqual("april 12th", result.entities[4].entity)
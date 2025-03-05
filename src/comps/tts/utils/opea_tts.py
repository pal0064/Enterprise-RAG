from fastapi import Request, HTTPException
from fastapi.responses import Response, StreamingResponse
import soundfile as sf
import uuid
from comps import get_opea_logger
import json
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEATTS:
    """
    Singleton class for managing TTS with different frameworks as a connector and model servers.
    This class ensures that only one instance is created and reused across the application.
    """

    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str):

        if cls._instance is None:
            cls._instance = super(OPEATTS, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing OPEATTS instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server} "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str) -> None:
        """
        Initializes the OPEATTS instance.

        Args:
            model_name (str): The full name of the model, which may include the repository ID (e.g., 'microsoft/speecht5_tts'). 
                      Internally, only the short name (the last part after the final '/') will be used. For instance, 
                      'speecht5_tts' will be extracted from 'microsoft/speecht5_tts'.

            model_server (str): The URL of the model server.
            endpoint (str): The endpoint for the model server.
            connector (str): The name of the connector framework to be used.
        """
        self._model_name = model_name.split('/')[-1].lower()    # Extract the last part of the model name
        self._model_server = model_server.lower()
        self._endpoint = endpoint
        self._APIs = []

    async def tts(self, input_data, voice,response_format):
        logger.info("reached tts")
        self._endpoint = self._endpoint.rstrip('/')
        url = self._endpoint + f"/predictions/{self._model_name.split('/')[-1]}"
        logger.info(url)
        try:
            from huggingface_hub import (
                    AsyncInferenceClient,
                )
            self.async_client = AsyncInferenceClient(
                    model=f"{url}",
                )
        except ImportError as e:
            error_message =  "Could not import huggingface_hub python package.\n" \
                             "Please install it with `pip install huggingface_hub`.\n"  \
                             f"Error: {e}"
            logger.exception(error_message)
            raise
        try:
            responses = await self.async_client.post(
                json={"inputs": input_data, "voice": voice}
            )
            logger.info(f"Received response: {responses}")
            speech = json.loads(responses.decode())
            logger.info(f"Received speech: {speech}")
            tmp_path = f"tmp_{uuid.uuid4()}.wav"
            sf.write(tmp_path, speech, samplerate=16000)

            def audio_gen():
                with open(tmp_path, "rb") as f:
                    yield from f

            return StreamingResponse(audio_gen(), media_type=f"audio/{response_format}")
        except Exception as e:
            logger.exception(f"Error embedding documents: {e}")
            raise

    async def run(self, request_data) -> StreamingResponse:
        """
        Processes the input document using the OPEATTS.

        Args:
            input: The input document to be processed.

        Returns:
            StreamingResponse.
        """
        logger.info(f"Received request data: {request_data}")
        print(request_data)
        if request_data['model'] not in ["microsoft/speecht5_tts"]:
            raise Exception("TTS model mismatch! Currently only support model: microsoft/speecht5_tts")
        if request_data['voice'] not in ["default", "male"]:
            logger.warning("Currently parameter 'voice' can only be default or male!")

        try:
            response = await self.tts(request_data['input_data'], request_data['voice'], request_data['format'])
            return response
        except Exception as e:
            logger.exception(f"Error processing TTS request: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

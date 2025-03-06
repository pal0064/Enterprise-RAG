import httpx
import asyncio

async def fetch_audio():
    url = "http://localhost:8200/v1/audio/speech"
    headers = {"Content-Type": "application/json"}
    body = {
        "input_data": ["Hi team rag 3?"],
        "voice": "default",
        "format": "mp3",
        "model": "microsoft/speecht5_tts",
    }

    async with httpx.AsyncClient() as client:
        # Use the stream method to handle streaming responses
        async with client.stream("POST", url, json=body, headers=headers) as response:
            # Check if the request was successful
            if response.status_code == 200:
                # Open a file to write the streaming response
                with open("output.mp3", "wb") as mp3_file:
                    async for chunk in response.aiter_bytes():
                        mp3_file.write(chunk)
                print("Audio saved to output.mp3")
            else:
                # Read the response content to get the error message
                error_content = await response.aread()
                print(f"Request failed with status code: {response.status_code}")
                print(response.text)
                print(f"Error content: {error_content.decode('utf-8')}")

# Run the async function
asyncio.run(fetch_audio())
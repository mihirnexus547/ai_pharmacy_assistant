"""
Speech-to-text provider.
"""
"""
Deepgram Speech-to-Text Provider.
"""

from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

from app.config import settings


class DeepgramSTT:
    """
    Wrapper around Deepgram Live Speech-to-Text.
    """

    def __init__(self):

        self.client = DeepgramClient(
            settings.DEEPGRAM_API_KEY
        )

    def listen(self):
        """
        Start listening from microphone.

        Yields:
            transcript (str)
        """

        connection = self.client.listen.live.v("1")

        def on_message(
            self,
            result,
            **kwargs,
        ):

            sentence = (
                result.channel.alternatives[0].transcript
            )

            if sentence:

                print(f"\nUser: {sentence}")

        connection.on(
            LiveTranscriptionEvents.Transcript,
            on_message,
        )

        options = LiveOptions(
            model="nova-3",
            language="en",
            smart_format=True,
            interim_results=False,
            punctuate=True,
        )

        connection.start(options)

        microphone = Microphone(
            connection.send
        )

        microphone.start()

        print("Listening...")
        print("Press ENTER to stop.\n")

        input()

        microphone.finish()
        connection.finish()


stt = DeepgramSTT()


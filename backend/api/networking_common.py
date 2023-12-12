from common import ASRConfig
from text_handlers import CurrentASRTextContainer
from buffer_common import OnlineASRProcessor, create_tokenizer
from typing import Dict, List, Union
import json
import time
import os


class TranscribePacket:
    def __init__(
        self,
        session_id: str,
        timestamp: int,
        source_language: str,
        transcript_language: str,
        prompt: str,
        audio: List,
    ) -> None:
        """
        TranscribePacket is a container for audio and metadata in `processing_queue`.
        It keeps track of language which has yet to recieve transcription of the audio
        and provides audio data for processing.

        Args:
            session_id (str): The ID of the session.
            timestamp (int): The numerical timestamp of the audio chunk.
            source_language (str): The language of the audio chunk.
            transcript_languages (List[str]): The language of the transcript.
            audio (list): The audio data as a byte string.
        """
        self.session_id: str = session_id
        self.timestamp: int = timestamp
        self.source_language: str = source_language
        self.transcript_language: str = transcript_language
        self.audio: List = audio
        self.sent_out_time: float = 0.0
        self.transcript: Union[None, str] = None
        self.prompt: str = prompt

    def is_completely_processed(self) -> bool:
        """
        Checks if audio has been completely transcribed.
        """
        return self.transcript is not None

    def get_data_to_offload(self) -> Union[Dict[str, Union[str, int, List]], None]:
        """
        Returns data to offload to ASR services.
        If no data is ready to be offloaded, returns None.
        """
        print(type(self.audio))
        print(len(self.audio))
        
        if self.transcript is None:
            if time.time() - self.sent_out_time > 15:
                self.sent_out_time = time.time()
                return {
                    "session_id": self.session_id,
                    "timestamp": self.timestamp,
                    "source_language": self.source_language,
                    "transcript_language": self.transcript_language,
                    "prompt": self.prompt,
                    "audio": self.audio,
                }
        return None


class TranslatePacket:
    # FIXME: implement
    def __init__(self):
        raise NotImplementedError

    # def got_offloaded_data(self, ASR_result: str, transcript_language: str):
    #     """
    #     Save the transcript of the audio chunk in the specified language.
    #     """
    #     self.transcript = ASR_result

    # def get_data_to_offload(self) -> Union[Dict[str, Union[str, int, List]], None]:
    #     """
    #     Returns data to offload to ASR services.
    #     If no data is ready to be offloaded, returns None.
    #     """
    #     for i, transcript in enumerate(self.transcripts):
    #         if transcript is None:
    #             if time.time() - self.sent_out_times[i] > 15:
    #                 self.sent_out_times[i] = time.time()
    #                 return {
    #                     "session_id": self.session_id,
    #                     "timestamp": self.timestamp,
    #                     "source_language": self.source_language,
    #                     "transcript_language": self.transcript_languages[i],
    #                     "audio": self.audio,
    #                 }
    #     return None


class Session:
    def __init__(self, session_id: str, config: ASRConfig) -> None:
        self.session_id: str = session_id
        # DONE: Fix uselsess of these two after initialization
        self.source_language: str = "en"  # default audio language
        self.transcript_language: str = "en"  # default transcript language

        self.save_path: str = self.get_save_folder(config.supported_languages)
        self.texts: CurrentASRTextContainer = CurrentASRTextContainer(
            self.save_path + "/text_chunks", config.supported_languages
        )
        # DONE: Check functionality of OnlineASRProcessor
        self.online_asr_processor: OnlineASRProcessor = OnlineASRProcessor(
            create_tokenizer(self.transcript_language)
        )

        self.untranscribed_timestamps: List[int] = [0]
        self.transcribed_timestamps: List[int] = []

    def switch_transcript_language(self, language: str):
        self.transcript_language = language
        self.online_asr_processor.tokenizer = create_tokenizer(self.transcript_language)

    def switch_source_language(self, language: str):
        self.source_language = language

    # DONE
    def end_session(self):
        for text in self.texts.current_texts.values():
            with open(
                self.save_path + f"/final_transcripts/{text.language}/transcript.srt", "w", encoding="utf-8"
            ) as file:
                print(str(text), file=file)

            with open(
                self.save_path + f"/final_transcripts/{text.language}/all_text_chunks.json", "w", encoding="utf-8"
            ) as file:
                print(text.to_json(), file=file)

    # DONE
    def get_save_folder(self, supported_languages: List[str]):
        if not os.path.isdir("recordings"):
            os.mkdir("recordings")
        recordings = os.listdir("recordings")
        # filter out files that are not directories
        # NOTE: This can crash if there is file with name of session_id
        recordings = [x for x in recordings if os.path.isdir("recordings/" + x)]
        if self.session_id not in recordings:
            os.mkdir("recordings/" + self.session_id)

        # list recordings/self.session_id
        recordings = os.listdir("recordings/" + self.session_id)
        # filter out files that are not directories
        # NOTE: This can crash if there is file with name of recordings_index
        recordings = [
            x for x in recordings if os.path.isdir("recordings/" + self.session_id + "/" + x)
        ]
        recordings_index = 0
        while str(recordings_index) in recordings:
            recordings_index += 1

        os.mkdir("recordings/" + self.session_id + "/" + str(recordings_index))
        recordings_folder = "recordings/" + self.session_id + "/" + str(recordings_index)
        os.mkdir(recordings_folder + "/audio")
        os.mkdir(recordings_folder + "/text_chunks")
        for language in supported_languages:
            os.mkdir(recordings_folder + "/text_chunks/" + language)
        os.mkdir(recordings_folder + "/final_transcripts")
        for language in supported_languages:
            os.mkdir(recordings_folder + "/final_transcripts/" + language)
        return recordings_folder

    # DONE
    def save_audio_chunk(self, chunk: Dict[str, float], timestamp: int):
        with open(
            self.save_path + "/audio/" + str(timestamp) + "_" + str(time.time()) + ".json",
            mode="w",
        ) as f:
            print(json.dumps(chunk), file=f)

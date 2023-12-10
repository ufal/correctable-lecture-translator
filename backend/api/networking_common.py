from common import ASRConfig, format_timestamp
from audio_handler import AudioBuffer
from text_handlers import CurrentASRTextContainer, break_line
from typing import Dict, List, TextIO, Union, Set
import json
import time
import re
import os


class Session:
    def __init__(self, session_id: str, config: ASRConfig) -> None:
        self.session_id: str = session_id
        self.source_language: str = "Czech"  # default audio language
        # TODO: change this to list of languages
        self.transcript_language: str = "Czech"  # default transcript language
        self.buffer: AudioBuffer = AudioBuffer(
            SNIPPET_SIZE=config.AUDIO_SNIPPET_SIZE,
            SHIFT_LENGTH=config.SHIFT_SIZE,
        )
        self.last_chunk_time: float = time.time()
        self.save_path: str = self.get_save_folder()
        self.texts: CurrentASRTextContainer = CurrentASRTextContainer(
            self.save_path + "/text_chunks", config.supported_languages
        )
        self.last_sent_timestamp: int = -1
        self.unprocessed_timestamps: List[int] = [0]
        self.sent_out_for_processing: Dict[int, float] = dict()
        self.processed_timestamps: Set[int] = {-1}

    def switch_transcript_language(self, language: str):
        self.transcript_language = language

    def switch_source_language(self, language: str):
        self.source_language = language

    def end_session(self):
        def process_segment(segment: dict, line_length: int = 0):
            segment["text"] = re.sub(r"\s+", " ", segment["text"])
            segment["text"] = segment["text"].strip()

            if line_length > 0 and len(segment["text"]) > line_length:
                # break at N characters as per Netflix guidelines
                segment["text"] = break_line(segment["text"], line_length)

            return segment

        def write_srt(transcript: List[dict], file: TextIO, line_length: int = 0):
            for i, segment in enumerate(transcript, start=1):
                segment = process_segment(segment, line_length=line_length)

                print(
                    f"{i}\n"
                    f"{format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')} --> "  # noqa: E501
                    f"{format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')}\n"  # noqa: E501
                    f"{segment['text'].strip().replace('-->', ' ->')}\n",
                    file=file,
                    flush=True,
                )

        latest_text_chunks = self.text.get_latest_text_chunks(versions={})
        transcript = []

        transcript = [
            {
                "start": 30.0 * chunk["timestamp"],
                "end": 30.0 * (chunk["timestamp"] + 1),
                "text": chunk["text"],
            }
            for chunk in latest_text_chunks
        ]

        with open(self.save_path + "/transcript.srt", "w", encoding="utf-8") as file:
            write_srt(transcript, file, line_length=0)

        with open(self.save_path + "/all_text_chunks.json", "w", encoding="utf-8") as file:
            json.dump(self.text.text_chunks, file, indent=4)

        with open(
            self.save_path + "/all_text_chunks_no_spans.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(self.text.text_chunks_no_spans, file, indent=4)

    def get_save_folder(self):
        recordings = os.listdir("recordings")
        # filter out files that are not directories
        recordings = [x for x in recordings if os.path.isdir("recordings/" + x)]
        if self.session_id not in recordings:
            os.mkdir("recordings/" + self.session_id)

        # list recordings/self.session_id
        recordings = os.listdir("recordings/" + self.session_id)
        # filter out files that are not directories
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
        return recordings_folder

    def save_audio_chunk(self, chunk, timestamp: int):
        with open(
            self.save_path + "/audio/" + str(timestamp) + "_" + str(time.time()) + ".json",
            mode="w",
        ) as f:
            print(json.dumps(chunk), file=f)


class TranscriptDataUnit:
    def __init__(
        self,
        session_id: str,
        timestamp: int,
        source_language: str,
        transcript_language: str,
        audio: List[bytes],
    ) -> None:
        """
        ProcessingDataUnit is a container for audio and metadata.
        It keeps track of languages which have yet to recieve transcription of the audio
        and provides audio data for processing.

        Args:
            session_id (str): The session ID of the session.
            timestamp (int): The timestamp of the audio chunk in seconds.
            source_language (str): The language of the audio chunk.
            transcript_languages (List[str]): The languages of the transcripts.
            audio (list[bytes]): The audio data as a byte string.
        """
        self.session_id: str = session_id
        self.timestamp: int = timestamp
        self.source_language: str = source_language
        self.transcript_language: str = transcript_language
        self.audio: List[bytes] = audio
        self.sent_out_time: float = 0.0
        self.transcript: Union[None, str] = None

    # FIXME: Transcript takes only one language as of now
    def is_completely_processed(self) -> bool:
        """
        Checks if audio has been completely transcribed.
        """
        for transcript in self.transcripts:
            if transcript is None:
                return False
        return True

    def get_data_to_offload(self) -> Union[Dict[str, Union[str, int, List[bytes]]], None]:
        """
        Returns data to offload to ASR services.
        If no data is ready to be offloaded, returns None.
        """
        for i, transcript in enumerate(self.transcripts):
            if transcript is None:
                if time.time() - self.sent_out_times[i] > 15:
                    self.sent_out_times[i] = time.time()
                    return {
                        "session_id": self.session_id,
                        "timestamp": self.timestamp,
                        "source_language": self.source_language,
                        "transcript_language": self.transcript_languages[i],
                        "audio": self.audio,
                    }
        return None

    def got_offloaded_data(self, ASR_result: str, transcript_language: str):
        """
        Save the transcript of the audio chunk in the specified language.
        """
        self.transcripts[self.transcript_languages.index(transcript_language)] = ASR_result


class TranslateDataUnit:
    pass

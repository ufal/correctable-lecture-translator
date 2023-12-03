import json
import time

import numpy as np
import requests
import torch
import whisper


class ASRConfig:
    def __init__(self):
        self.original_language = "Czech"
        self.decode_options = dict(
            language=self.original_language, beam_size=5, best_of=5, without_timestamps=True
        )
        self.transcribe_options = dict(
            task="transcribe",
            fp16=torch.cuda.is_available(),
            no_speech_threshold=0.6,
            temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            verbose=True,
            condition_on_previous_text=True,
            **self.decode_options
        )
        self.translate_options = dict(
            task="translate",
            fp16=torch.cuda.is_available(),
            no_speech_threshold=0.6,
            temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
            verbose=True,
            condition_on_previous_text=True,
            **self.decode_options
        )
        self.model = whisper.load_model("tiny")

        self.SAMPLING_RATE = 16000  # Hz
        self.AUDIO_SNIPPET_SECONDS = 30  # seconds
        self.AUDIO_SNIPPET_SIZE = self.SAMPLING_RATE * self.AUDIO_SNIPPET_SECONDS  # samples


def main():
    config = ASRConfig()

    while True:
        try:
            r = requests.get("https://slt.ufal.mff.cuni.cz:5003/offload_ASR", verify=False)
            json_data = json.loads(r.text)
            timestamp = json_data["timestamp"]
            audio = json_data["audio"]

            if len(audio) == 0:
                print("No audio data")
                time.sleep(5)
                continue

            print("timestamp:", timestamp)
            print("session_id", json_data["session_id"])
            print(type(audio[0]))
            session_id = json_data["session_id"]
            source_language = json_data["source_language"]
            transcript_language = json_data["transcript_language"]

            if isinstance(audio[0], int):
                audio = np.array(audio, dtype=np.float32) / 32768.0
            audio = np.array(audio, dtype=np.float32)
            result = None

            starting_ASR_time = time.time()
            if source_language == transcript_language:
                config.transcribe_options["language"] = source_language
                result = config.model.transcribe(audio, **config.transcribe_options)
            else:
                if transcript_language != "English":
                    continue
                config.translate_options["language"] = source_language
                result = config.model.transcribe(audio, **config.translate_options)
            print("ASR time:", time.time() - starting_ASR_time)
            print(result["text"])

            r = requests.post(
                "https://slt.ufal.mff.cuni.cz:5003/offload_ASR",
                json={"session_id": session_id, "timestamp": timestamp, "ASR_result": result},
                verify=False,
            )
            # print(r.text)
        except Exception as e:
            print("cannot connect to server" + str(e))
            time.sleep(5)


if __name__ == "__main__":
    main()

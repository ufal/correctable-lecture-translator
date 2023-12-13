#!/usr/bin/env python3
import json
import sys
import time

import numpy as np
import requests  # type: ignore
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Whisper backend
class ASRBase:
    # join transcribe words with this character (" " for whisper_timestamped, "" for faster-whisper
    #  because it emits the spaces when neeeded)
    sep = " "

    def __init__(self, lan, modelsize=None, cache_dir=None, model_dir=None):
        self.transcribe_kargs = {}
        self.original_language = lan

        self.model = self.load_model(modelsize, cache_dir, model_dir) # type: ignore

    def load_model(self, modelsize, cache_dir):
        raise NotImplementedError("must be implemented in the child class")

    def transcribe(self, audio, init_prompt=""):
        raise NotImplementedError("must be implemented in the child class")

    def use_vad(self):
        raise NotImplementedError("must be implemented in the child class")


class FasterWhisperASR(ASRBase):
    """Uses faster-whisper library as the backend. Works much faster, appx 4-times
    (in offline mode). For GPU, it requires installation with a specific CUDNN version.

    Requires imports, if used:
        import faster_whisper
    """

    sep = ""

    def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
        from faster_whisper import WhisperModel  # type: ignore

        if model_dir is not None:
            model_size_or_path = model_dir
        elif modelsize is not None:
            model_size_or_path = modelsize
        else:
            raise ValueError("modelsize or model_dir parameter must be set")

        # this worked fast and reliably on NVIDIA L40
        model = WhisperModel(
            model_size_or_path, device="cuda", compute_type="float16", download_root=cache_dir
        )

        # or run on GPU with INT8
        # tested: the transcripts were different, probably worse than with FP16, and it was
        # slightly (appx 20%) slower
        # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

        # or run on CPU with INT8
        # tested: works, but slow, appx 10-times than cuda FP16
        #        model = WhisperModel(modelsize, device="cpu", compute_type="int8") #,
        # download_root="faster-disk-cache-dir/")
        return model

    def transcribe(self, audio, init_prompt=""):
        # tested: beam_size=5 is faster and better than 1 (on one 200 second document from En ESIC,
        # min chunk 0.01)
        segments, info = self.model.transcribe(
            audio,
            language=self.original_language,
            initial_prompt=init_prompt,
            beam_size=5,
            word_timestamps=True,
            condition_on_previous_text=True,
            **self.transcribe_kargs,
        )
        return list(segments)

    def ts_words(self, segments):
        o = []
        for segment in segments:
            for word in segment.words:
                # not stripping the spaces -- should not be merged with them!
                w = word.word
                t = (word.start, word.end, w)
                o.append(t)
        return o

    def segments_end_ts(self, res):
        return [s.end for s in res]

    def use_vad(self):
        self.transcribe_kargs["vad_filter"] = True

    def set_translate_task(self):
        self.transcribe_kargs["task"] = "translate"


class ComputationNode:
    sep = ""

    def __init__(self, asr_model):
        self.asr_model = asr_model

    def transcribe(self, audio, init_prompt=""):
        return self.asr_model.transcribe(audio, init_prompt=init_prompt)

    def ts_words(self, segments):
        return self.asr_model.ts_words(segments)

    def segments_end_ts(self, res):
        return self.asr_model.segments_end_ts(res)


class ASRConfig:
    def __init__(self):
        self.min_chunk_size = 1.0  # Minimum audio chunk size in seconds. It waits up to this time
        # to do processing. If the processing takes shorter time, it waits, otherwise it processes
        # the whole segment that was received by this time.
        self.model = "large-v2"  # Name size of the Whisper model to use (default: large-v2). The
        # model is automatically downloaded from the model hub if not present in model cache dir.
        # tiny.en,tiny,base.en,base,small.en,small,medium.en,medium,large-v1,large-v2,large
        self.language = "en"  # Language code for transcription, e.g. en,de,cs.
        self.start_at = 0.0  # Start processing audio at this time.
        self.backend = "faster-whisper"  # Load only this backend for Whisper processing.
        self.vad = False  # Use VAD = voice activity detection, with the default parameters.
        self.SAMPLING_RATE = 16000
        self.model_cache_dir = None
        self.model_dir = None


def main() -> None:
    config = ASRConfig()

    size = config.model
    language = config.language

    if config.backend == "faster-whisper":
        asr_cls = FasterWhisperASR
    else:
        raise ValueError("unknown backend: " + config.backend)

    asr = asr_cls(
        modelsize=size, lan=language, cache_dir=config.model_cache_dir, model_dir=config.model_dir
    )

    if config.vad:
        asr.use_vad()

    # min_chunk = config.min_chunk_size
    comp_node = ComputationNode(asr)

    while True:
        try:
            r = requests.get("https://slt.ufal.mff.cuni.cz:5003/offload_ASR", verify=False)
            json_data = json.loads(r.text)
            timestamp = json_data["timestamp"]
            audio = json_data["audio"]

            print("audio: ", len(audio), file=sys.stderr)
            
            if len(audio) == 0:
                print("No audio data")
                time.sleep(5)
                continue

            prompt = json_data["prompt"]
            session_id = json_data["session_id"]
            source_language = json_data["source_language"]
            transcript_language = json_data["transcript_language"]

            if isinstance(audio[0], int):
                audio = np.array(audio, dtype=np.float32) / 32768.0
            audio = np.array(audio, dtype=np.float32)
            
            print(source_language, transcript_language, file=sys.stderr)
            comp_node.asr_model.original_language = source_language
            # starting_ASR_time = time.time()
            if source_language == transcript_language:
                comp_node.asr_model.transcribe_kargs["task"] = "transcribe"
            else:
                comp_node.asr_model.transcribe_kargs["task"] = "translate"

            try:
                # Should send prompt along with audio
                # prompt, non_prompt = self.prompt()
                # res = self.asr.transcribe(self.audio_buffer, init_prompt=prompt)
                # # print("RES:", res, file=sys.stdout, flush=True)

                # # transform to [(beg,end,"word1"), ...]
                # tsw = self.asr.ts_words(res)
                # ends = self.asr.segments_end_ts(res)
                res = comp_node.transcribe(audio, init_prompt=prompt)
                tsw = comp_node.ts_words(res)
                ends = comp_node.segments_end_ts(res)
                print("transcript: ", tsw, file=sys.stderr)

                r = requests.post(
                    "https://slt.ufal.mff.cuni.cz:5003/offload_ASR",
                    json={
                        "session_id": session_id,
                        "timestamp": timestamp,
                        "tsw": tsw,
                        "ends": ends,
                        "language": transcript_language,
                    },
                    verify=False,
                )

            except AssertionError:
                print("assertion error", file=sys.stderr)
                pass

            # print("ASR time: ", time.time() - starting_ASR_time, file=sys.stderr)
        except Exception as e:
            print("cannot connect to server " + str(e), file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    main()

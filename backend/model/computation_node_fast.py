#!/usr/bin/env python3
import sys
import numpy as np
import librosa
from functools import lru_cache
import time
import requests
import json


@lru_cache
def load_audio(fname):
    a, _ = librosa.load(fname, sr=16000)
    return a


def load_audio_chunk(fname, beg, end):
    audio = load_audio(fname)
    beg_s = int(beg * 16000)
    end_s = int(end * 16000)
    return audio[beg_s:end_s]


# Whisper backend
class ASRBase:
    # join transcribe words with this character (" " for whisper_timestamped, "" for faster-whisper because it emits the spaces when neeeded)
    sep = " "

    def __init__(self, lan, modelsize=None, cache_dir=None, model_dir=None):
        self.transcribe_kargs = {}
        self.original_language = lan

        self.model = self.load_model(modelsize, cache_dir, model_dir)

    def load_model(self, modelsize, cache_dir):
        raise NotImplementedError("must be implemented in the child class")

    def transcribe(self, audio, init_prompt=""):
        raise NotImplementedError("must be implemented in the child class")

    def use_vad(self):
        raise NotImplementedError("must be implemented in the child class")


class FasterWhisperASR(ASRBase):
    """Uses faster-whisper library as the backend. Works much faster, appx 4-times (in offline mode). For GPU, it requires installation with a specific CUDNN version.

    Requires imports, if used:
        import faster_whisper
    """

    sep = ""

    def load_model(self, modelsize=None, cache_dir=None, model_dir=None):
        from faster_whisper import WhisperModel

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
        # tested: the transcripts were different, probably worse than with FP16, and it was slightly (appx 20%) slower
        # model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

        # or run on CPU with INT8
        # tested: works, but slow, appx 10-times than cuda FP16
        #        model = WhisperModel(modelsize, device="cpu", compute_type="int8") #, download_root="faster-disk-cache-dir/")
        return model

    def transcribe(self, audio, init_prompt=""):
        # tested: beam_size=5 is faster and better than 1 (on one 200 second document from En ESIC, min chunk 0.01)
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


class HypothesisBuffer:
    def __init__(self):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []

        self.last_commited_time = 0
        self.last_commited_word = None

    def insert(self, new, offset):
        # compare self.commited_in_buffer and new. It inserts only the words in new that extend the commited_in_buffer, it means they are roughly behind last_commited_time and new in content
        # the new tail is added to self.new

        new = [(a + offset, b + offset, t) for a, b, t in new]
        self.new = [(a, b, t) for a, b, t in new if a > self.last_commited_time - 0.1]

        if len(self.new) >= 1:
            a, b, t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams) that are identical in commited and new. If they are, they're dropped.
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1, min(min(cn, nn), 5) + 1):  # 5 is the maximum
                        c = " ".join(
                            [self.commited_in_buffer[-j][2] for j in range(1, i + 1)][::-1]
                        )
                        tail = " ".join(self.new[j - 1][2] for j in range(1, i + 1))
                        if c == tail:
                            for j in range(i):
                                self.new.pop(0)
                            break

    def flush(self):
        # returns commited chunk = the longest common prefix of 2 last inserts.

        commit = []
        while self.new:
            na, nb, nt = self.new[0]

            if len(self.buffer) == 0:
                break

            if nt == self.buffer[0][2]:
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
                self.buffer.pop(0)
                self.new.pop(0)
            else:
                break
        self.buffer = self.new
        self.new = []
        self.commited_in_buffer.extend(commit)
        return commit

    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)

    def complete(self):
        return self.buffer


class OnlineASRProcessor:
    SAMPLING_RATE = 16000

    def __init__(self, asr, tokenizer):
        """asr: WhisperASR object
        tokenizer: sentence tokenizer object for the target language. Must have a method *split* that behaves like the one of MosesTokenizer.
        """
        self.asr = asr
        self.tokenizer = tokenizer

        self.init()

    def init(self):
        """run this when starting or restarting processing"""
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_time_offset = 0

        self.transcript_buffer = HypothesisBuffer()
        self.commited = []
        self.last_chunked_at = 0

        self.silence_iters = 0

    def insert_audio_chunk(self, audio):
        self.audio_buffer = np.append(self.audio_buffer, audio)

    def prompt(self):
        """Returns a tuple: (prompt, context), where "prompt" is a 200-character suffix of commited text that is inside of the scrolled away part of audio buffer.
        "context" is the commited text that is inside the audio buffer. It is transcribed again and skipped. It is returned only for debugging and logging reasons.
        """
        k = max(0, len(self.commited) - 1)
        while k > 0 and self.commited[k - 1][1] > self.last_chunked_at:
            k -= 1

        p = self.commited[:k]
        p = [t for _, _, t in p]
        prompt = []
        llllll = 0
        while p and llllll < 200:  # 200 characters prompt size
            x = p.pop(-1)
            llllll += len(x) + 1
            prompt.append(x)
        non_prompt = self.commited[k:]
        return self.asr.sep.join(prompt[::-1]), self.asr.sep.join(t for _, _, t in non_prompt)

    def process_iter(self):
        """Runs on the current audio buffer.
        Returns: a tuple (beg_timestamp, end_timestamp, "text"), or (None, None, "").
        The non-emty text is confirmed (commited) partial transcript.
        """

        prompt, non_prompt = self.prompt()
        res = self.asr.transcribe(self.audio_buffer, init_prompt=prompt)
        # print("RES:", res, file=sys.stdout, flush=True)

        # transform to [(beg,end,"word1"), ...]
        tsw = self.asr.ts_words(res)

        self.transcript_buffer.insert(tsw, self.buffer_time_offset)
        o = self.transcript_buffer.flush()
        self.commited.extend(o)
        # there is a newly confirmed text
        if o:
            # we trim all the completed sentences from the audio buffer
            self.chunk_completed_sentence()

        # if the audio buffer is longer than 30s, trim it...
        if len(self.audio_buffer) / self.SAMPLING_RATE > 30:
            # ...on the last completed segment (labeled by Whisper)
            self.chunk_completed_segment(res)

        return self.to_flush(o)

    def chunk_completed_sentence(self):
        if self.commited == []:
            return
        sents = self.words_to_sentences(self.commited)
        if len(sents) < 2:
            return
        while len(sents) > 2:
            sents.pop(0)
        # we will continue with audio processing at this timestamp
        chunk_at = sents[-2][1]

        self.chunk_at(chunk_at)

    def chunk_completed_segment(self, res):
        if self.commited == []:
            return

        ends = self.asr.segments_end_ts(res)

        t = self.commited[-1][1]

        if len(ends) > 1:
            e = ends[-2] + self.buffer_time_offset
            while len(ends) > 2 and e > t:
                ends.pop(-1)
                e = ends[-2] + self.buffer_time_offset
            if e <= t:
                self.chunk_at(e)

    def chunk_at(self, time):
        """trims the hypothesis and audio buffer at "time" """
        self.transcript_buffer.pop_commited(time)
        cut_seconds = time - self.buffer_time_offset
        self.audio_buffer = self.audio_buffer[int(cut_seconds) * self.SAMPLING_RATE :]
        self.buffer_time_offset = time
        self.last_chunked_at = time

    def words_to_sentences(self, words):
        """Uses self.tokenizer for sentence segmentation of words.
        Returns: [(beg,end,"sentence 1"),...]
        """

        cwords = [w for w in words]
        t = " ".join(o[2] for o in cwords)
        s = self.tokenizer.split(t)
        out = []
        while s:
            beg = None
            end = None
            sent = s.pop(0).strip()
            fsent = sent
            while cwords:
                b, e, w = cwords.pop(0)
                if beg is None and sent.startswith(w):
                    beg = b
                elif end is None and sent == w:
                    end = e
                    out.append((beg, end, fsent))
                    break
                sent = sent[len(w) :].strip()
        return out

    def finish(self):
        """Flush the incomplete text when the whole processing ends.
        Returns: the same format as self.process_iter()
        """
        o = self.transcript_buffer.complete()
        f = self.to_flush(o)
        return f

    def to_flush(
        self,
        sents,
        sep=None,
        offset=0,
    ):
        # concatenates the timestamped words or sentences into one sequence that is flushed in one line
        # sents: [(beg1, end1, "sentence1"), ...] or [] if empty
        # return: (beg1,end-of-last-sentence,"concatenation of sentences") or (None, None, "") if empty
        if sep is None:
            sep = self.asr.sep
        t = sep.join(s[2] for s in sents)
        if len(sents) == 0:
            b = None
            e = None
        else:
            b = offset + sents[0][0]
            e = offset + sents[-1][1]
        return (b, e, t)


WHISPER_LANG_CODES = "af,am,ar,as,az,ba,be,bg,bn,bo,br,bs,ca,cs,cy,da,de,el,en,es,et,eu,fa,fi,fo,fr,gl,gu,ha,haw,he,hi,hr,ht,hu,hy,id,is,it,ja,jw,ka,kk,km,kn,ko,la,lb,ln,lo,lt,lv,mg,mi,mk,ml,mn,mr,ms,mt,my,ne,nl,nn,no,oc,pa,pl,ps,pt,ro,ru,sa,sd,si,sk,sl,sn,so,sq,sr,su,sv,sw,ta,te,tg,th,tk,tl,tr,tt,uk,ur,uz,vi,yi,yo,zh".split(
    ","
)


def create_tokenizer(lan):
    """returns an object that has split function that works like the one of MosesTokenizer"""

    assert (
        lan in WHISPER_LANG_CODES
    ), "language must be Whisper's supported lang code: " + " ".join(WHISPER_LANG_CODES)

    if lan == "uk":
        import tokenize_uk

        class UkrainianTokenizer:
            def split(self, text):
                return tokenize_uk.tokenize_sents(text)

        return UkrainianTokenizer()

    # supported by fast-mosestokenizer
    if (
        lan
        in "as bn ca cs de el en es et fi fr ga gu hi hu is it kn lt lv ml mni mr nl or pa pl pt ro ru sk sl sv ta te yue zh".split()
    ):
        from mosestokenizer import MosesTokenizer

        return MosesTokenizer(lan)

    raise ValueError("language not supported by Current Tokenizers: " + lan)


class ASRConfig:
    def __init__(self):
        # self.original_language = "Czech"
        # self.decode_options = dict(language=self.original_language, beam_size=5, best_of=5, without_timestamps=True)
        # self.transcribe_options = dict(task="transcribe", fp16=torch.cuda.is_available(), no_speech_threshold=0.6, temperature=(
        #     0.0, 0.2, 0.4, 0.6, 0.8, 1.0), verbose=True, condition_on_previous_text=True, **self.decode_options)
        # self.translate_options = dict(task="translate", fp16=torch.cuda.is_available(), no_speech_threshold=0.6, temperature=(
        #     0.0, 0.2, 0.4, 0.6, 0.8, 1.0), verbose=True, condition_on_previous_text=True, **self.decode_options)
        # self.model = whisper.load_model("large")

        # self.SAMPLING_RATE = 16000  # Hz
        # self.AUDIO_SNIPPET_SECONDS = 30  # seconds
        # self.AUDIO_SNIPPET_SIZE = self.SAMPLING_RATE * self.AUDIO_SNIPPET_SECONDS  # samples

        self.min_chunk_size = 1.0  # Minimum audio chunk size in seconds. It waits up to this time to do processing. If the processing takes shorter time, it waits, otherwise it processes the whole segment that was received by this time.
        self.model = "large-v2"  # Name size of the Whisper model to use (default: large-v2). The model is automatically downloaded from the model hub if not present in model cache dir.
        # tiny.en,tiny,base.en,base,small.en,small,medium.en,medium,large-v1,large-v2,large
        self.language = "en"  # Language code for transcription, e.g. en,de,cs.
        self.task = "transcribe"  # "transcribe" or "translate"
        self.start_at = 0.0  # Start processing audio at this time.
        self.backend = "faster-whisper"  # Load only this backend for Whisper processing.
        self.vad = False  # Use VAD = voice activity detection, with the default parameters.
        self.SAMPLING_RATE = 16000
        self.model_cache_dir = None
        self.model_dir = None


if __name__ == "__main__":
    config = ASRConfig()

    size = config.model
    language = config.language

    t = time.time()

    if config.backend == "faster-whisper":
        asr_cls = FasterWhisperASR

    asr = asr_cls(
        modelsize=size, lan=language, cache_dir=config.model_cache_dir, model_dir=config.model_dir
    )

    if config.task == "translate":
        asr.set_translate_task()
        tgt_language = "en"  # Whisper translates into English
    else:
        tgt_language = language  # Whisper transcribes in this language

    e = time.time()

    if config.vad:
        asr.use_vad()

    min_chunk = config.min_chunk_size
    comp_node = ComputationNode(asr)
    online1 = OnlineASRProcessor(comp_node, create_tokenizer(tgt_language))

    while True:
        try:
            r = requests.get("http://slt.ufal.mff.cuni.cz:5003/offload_ASR", verify=False)
            json_data = json.loads(r.text)
            timestamp = json_data["timestamp"]
            audio = json_data["audio"]

            if len(audio) == 0:
                print("No audio data")
                time.sleep(5)
                continue

            session_id = json_data["session_id"]
            source_language = json_data["source_language"]
            transcript_language = json_data["transcript_language"]

            if isinstance(audio[0], int):
                audio = np.array(audio, dtype=np.float32) / 32768.0
            audio = np.array(audio, dtype=np.float32)

            starting_ASR_time = time.time()
            if source_language == transcript_language:
                config.language = source_language
                end = 0

                online1.insert_audio_chunk(audio)

                try:
                    o1 = online1.process_iter()
                except AssertionError:
                    print("assertion error", file=sys.stderr)
                    pass
                else:
                    # output_transcript("Pheonix: ", o1)
                    if o1[0] is not None:
                        result = o1[2]
                        print(result)

                        r = requests.post(
                            "http://slt.ufal.mff.cuni.cz:5003/offload_ASR",
                            json={
                                "session_id": session_id,
                                "timestamp": timestamp,
                                "ASR_result": result,
                            },
                            verify=False,
                        )

            # print("ASR time:", time.time() - starting_ASR_time)

        except Exception as e:
            print("cannot connect to server " + str(e))
            time.sleep(5)

        # time.sleep(1)

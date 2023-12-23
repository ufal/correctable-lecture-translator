# from typing import List
import numpy as np
import tokenize_uk # type: ignore
from mosestokenizer import MosesTokenizer # type: ignore
from typing import List, Tuple

# # DONE?: rework this according to computation_node_fast
# class AudioBuffer:
#     def __init__(self, SNIPPET_SIZE: int, SHIFT_LENGTH: int):
#         # config
#         self.SNIPPET_SIZE = SNIPPET_SIZE
#         self.SHIFT_LENGTH = SHIFT_LENGTH

#         # data
#         self.buffer: List[bytes] = []
#         self.smallest_available_timestamp = 0

#     def extend(self, chunk):
#         self.buffer.extend(chunk)

#     def get_snippet(self, timestamp: int) -> List[bytes]:
#         actuall_timestamp = timestamp - self.smallest_available_timestamp
#         return self.buffer[
#             actuall_timestamp * self.SHIFT_LENGTH : actuall_timestamp * self.SHIFT_LENGTH
#             + self.SNIPPET_SIZE
#         ]

#     def can_get_snippet(self, timestamp: int):
#         actuall_timestamp = timestamp - self.smallest_available_timestamp
#         return actuall_timestamp * self.SHIFT_LENGTH + self.SNIPPET_SIZE <= len(self.buffer)

#     def shift(self):
#         if len(self.buffer) > self.SNIPPET_SIZE:
#             self.smallest_available_timestamp += 1
#             self.buffer = self.buffer[self.SHIFT_LENGTH :]

#     def clear(self):
#         self.buffer = []
#         self.smallest_available_timestamp = 0

#     def __len__(self):
#         return len(self.buffer)


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

    def __init__(self, tokenizer):
        """asr: WhisperASR object
        tokenizer: sentence tokenizer object for the target language. Must have a method *split* that behaves like the one of MosesTokenizer.
        """
        self.tokenizer = tokenizer
        # NOTE: when using something else than FasterWhisperASR, change the separator to the one used by the ASR
        self.asr_sep = ""
        self.init()

    def init(self) -> None:
        """run this when starting or restarting processing"""
        self.audio_buffer = np.array([], dtype=np.float32)
        self.buffer_time_offset = 0

        self.transcript_buffer = HypothesisBuffer()
        self.commited:List[Tuple[float, float, str]] = []
        self.last_chunked_at = 0

        self.silence_iters = 0
        self.buffer_updated: bool= False
        self.last_timestamp: int = 0

    def insert_audio_chunk(self, audio):
        self.audio_buffer = np.append(self.audio_buffer, audio)
        self.buffer_updated = True

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
        return self.asr_sep.join(prompt[::-1]), self.asr_sep.join(t for _, _, t in non_prompt)

    def process_iter(self, tsw, ends):
        """Runs on the current audio buffer.
        Returns: a tuple (beg_timestamp, end_timestamp, "text"), or (None, None, "").
        The non-emty text is confirmed (commited) partial transcript.
        """
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
            self.chunk_completed_segment(ends)
            


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

    def chunk_completed_segment(self, ends):
        if self.commited == []:
            return

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
            sep = self.asr_sep
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

        class UkrainianTokenizer:
            def split(self, text):
                return tokenize_uk.tokenize_sents(text)

        return UkrainianTokenizer()

    # supported by fast-mosestokenizer
    if (
        lan
        in "as bn ca cs de el en es et fi fr ga gu hi hu is it kn lt lv ml mni mr nl or pa pl pt ro ru sk sl sv ta te yue zh".split()
    ):
        return MosesTokenizer(lan)

    raise ValueError("language not supported by Current Tokenizers: " + lan)

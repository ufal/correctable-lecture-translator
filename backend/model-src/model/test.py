import librosa
from functools import lru_cache

@lru_cache
def load_audio(fname):
    a, _ = librosa.load(fname, sr=16000)
    return a


def load_audio_chunk(fname, beg, end):
    audio = load_audio(fname)
    beg_s = int(beg * 16000)
    end_s = int(end * 16000)
    return audio[beg_s:end_s]

audio = load_audio_chunk('../whisper_streaming/TheCOOL121NetherPortalchangenooneistalkingabout.wav', 0, 10)
print(audio.shape)

audio = load_audio('../whisper_streaming/TheCOOL121NetherPortalchangenooneistalkingabout.wav')
print(audio.shape)

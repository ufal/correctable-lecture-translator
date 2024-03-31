import jsonpickle


class ASRConfig:
    def __init__(self):
        self.SAMPLING_RATE = 16000  # Hz
        self.AUDIO_SNIPPET_SECONDS = 30  # seconds
        self.AUDIO_SNIPPET_SIZE = self.SAMPLING_RATE * self.AUDIO_SNIPPET_SECONDS  # samples
        self.SHIFT_SECONDS = 28  # seconds
        self.SHIFT_SIZE = (
            self.SHIFT_SECONDS * self.SAMPLING_RATE
        )  # seconds * samples/second = samples
        # FIXME: Write language codes for all supported languages
        self.supported_languages = ["cs", "en"]


class Timespan:
    def __init__(self, start: float, end: float):
        """Timespan in seconds"""
        self.start = start
        self.end = end

    def to_json(self):
        res = jsonpickle.encode(self, unpicklable=True, indent=4)
        assert isinstance(res, str)
        return res

    def from_json(self, json_str: str):
        res = jsonpickle.decode(json_str)
        assert isinstance(res, Timespan)
        return res


def format_timestamp(
    seconds: float,
    always_include_hours: bool = False,
    decimal_marker: str = ".",
):
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds -= hours * 3_600_000

    minutes = milliseconds // 60_000
    milliseconds -= minutes * 60_000

    seconds = milliseconds // 1_000
    milliseconds -= seconds * 1_000

    hours_marker = f"{hours:02d}:" if always_include_hours or hours > 0 else ""
    return f"{hours_marker}{minutes:02d}:{seconds:02d}{decimal_marker}{milliseconds:03d}"

from typing import Dict, List, TextIO, Tuple, Union
import json
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


def break_line(line: str, length: int):
    break_index = min(len(line) // 2, length)  # split evenly or at maximum length

    # work backwards from that guess to split between words
    # if break_index <= 1, we've hit the beginning of the string and can't split
    while break_index > 1:
        if line[break_index - 1] == " ":
            break  # break at space
        else:
            break_index -= 1
    if break_index > 1:
        # split the line, not including the space at break_index
        return line[: break_index - 1] + "\n" + line[break_index:]
    else:
        return line

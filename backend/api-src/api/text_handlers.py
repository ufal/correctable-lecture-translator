import difflib
from typing import Dict, List, Tuple, Union

import jsonpickle

from api.common import format_timestamp


class Timespan:
    def __init__(self, start: float, end: float):
        self.start = start
        self.end = end

    def to_json(self):
        res = jsonpickle.encode(self, unpicklable=True, indent=4)
        assert isinstance(res, str)
        return res

    def from_json(self, json_str: str):
        res = jsonpickle.decode(json_str)
        assert type(res) == Timespan
        return res


class ASRTextUnit:
    def __init__(self, text: str, srt_line_num: int, timespan: Timespan, version: int) -> None:
        self.text = text
        self.srt_line_num = srt_line_num
        self.timespan = timespan
        # @Qwedux: I am not sure if TextUnit has to know it's version
        self.version = version

    def __str__(self) -> str:
        """Returns .srt format of the text unit

        Example:
        >>> asr_text_unit = ASRTextUnit(text="This is some transcribed text.", srt_line_num=0, timespan=Timespan(2, 3), version=0)
        >>> print(asr_text_unit)

        ```txt
        0
        00:00:02,000 --> 00:00:03,000
        This is some transcribed text.
        ```
        """
        return (
            f"{self.srt_line_num}\n"
            + f"{format_timestamp(self.timespan.start, always_include_hours=True, decimal_marker=',')} --> "
            + f"{format_timestamp(self.timespan.end, always_include_hours=True, decimal_marker=',')}\n"
            + f"{self.text.strip().replace('-->', ' ->')}\n"
        )

    def to_json(self):
        res = jsonpickle.encode(self, unpicklable=True, indent=4)
        assert isinstance(res, str)
        return res

    def from_json(self, json_str: str):
        res = jsonpickle.decode(json_str)
        assert isinstance(res, ASRTextUnit)
        return res


class CurrentASRText:
    def __init__(self, save_path: str):
        self.text_chunks: Dict[int, Dict[int, ASRTextUnit]] = dict()
        self.text_chunks_no_spans: Dict[int, Dict[int, ASRTextUnit]] = dict()
        self.save_path = save_path

    def append(self, text: str, timestamp: int):
        # FIXME: Propagate timespans for subtitles
        self.text_chunks[timestamp] = {
            0: ASRTextUnit(
                text=text, srt_line_num=timestamp, timespan=Timespan(0.0, 10.0), version=0
            )
        }
        self.text_chunks_no_spans[timestamp] = {
            0: ASRTextUnit(
                text=text, srt_line_num=timestamp, timespan=Timespan(0.0, 10.0), version=0
            )
        }
        with open(self.save_path + "/" + str(timestamp) + "_0" + ".txt", "w") as f:
            print(text, file=f)

    def clear(self):
        self.text_chunks = dict()
        self.text_chunks_no_spans = dict()

    def get_latest_versions(self):
        return {
            timestamp: max(self.text_chunks[timestamp].keys())
            for timestamp in self.text_chunks.keys()
        }

    def get_latest_text_chunks(self, versions: Dict[int, int]):
        ret_value: List[Dict[str, Union[int, str]]] = []
        for timestamp in self.text_chunks.keys():
            newest_version = max(self.text_chunks[timestamp].keys())
            if timestamp in versions:
                if versions[timestamp] < newest_version:
                    ret_value.append(
                        {
                            "timestamp": timestamp,
                            "version": newest_version,
                            "text": self.text_chunks[timestamp][newest_version].text,
                        }
                    )
            else:
                ret_value.append(
                    {
                        "timestamp": timestamp,
                        "version": newest_version,
                        "text": self.text_chunks[timestamp][newest_version].text,
                    }
                )
        return ret_value

    def edit_text_chunk(self, timestamp: int, version: int, text: str) -> Tuple[str, int]:
        if (
            text
            == self.text_chunks_no_spans[timestamp][
                max(self.text_chunks_no_spans[timestamp].keys())
            ]
        ):
            # if the text is the same as the newest version, discard the edit
            return self.text_chunks_no_spans[timestamp][
                max(self.text_chunks_no_spans[timestamp].keys())
            ].text, max(self.text_chunks_no_spans[timestamp].keys())
        # if version < max(self.text_chunks_no_spans[timestamp].keys()):
        #     # if the version of sender is older than the newest version, discard the edit
        #     return self.text_chunks_no_spans[timestamp][
        #         max(self.text_chunks_no_spans[timestamp].keys())
        #     ].text, max(self.text_chunks_no_spans[timestamp].keys())

        diff = difflib.ndiff(
            self.text_chunks_no_spans[timestamp][
                max(self.text_chunks_no_spans[timestamp].keys())
            ].text,
            text,
        )
        new_text = []
        in_edited = False
        for i, line in enumerate(diff):
            if line[0] == " ":
                if in_edited:
                    # new_text.append("</span>")
                    new_text.append("</highlighted>")
                    in_edited = False
                new_text.append(line[2:])
            if line[0] == "-":
                continue
            if line[0] == "+":
                if not in_edited:
                    # new_text.append("<span class='edited'>")
                    new_text.append("<highlighted>")
                    in_edited = True
                new_text.append(line[2:])

        version_num = max(self.text_chunks[timestamp].keys()) + 1
        with open(
            self.save_path + "/" + str(timestamp) + "_" + str(version_num) + ".txt",
            "w",
        ) as f:
            print(text, file=f)
        self.text_chunks[timestamp][version_num].text = "".join(new_text)
        self.text_chunks_no_spans[timestamp][version_num].text = text
        return self.text_chunks_no_spans[timestamp][version_num].text, version_num

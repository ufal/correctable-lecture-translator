import jsonpickle
from typing import Dict, List, Tuple, Union
from common import format_timestamp, Timespan
import time


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


class ASRTextUnit:
    def __init__(self, text: str, timestamp: int, timespan: Timespan, version: int) -> None:
        self.text = text
        self.timestamp = timestamp
        self.timespan = timespan
        # @Qwedux: I am not sure if TextUnit has to know it's version
        self.version = version
        self.rating = 0

    def __str__(self) -> str:
        """Returns .srt format of the text unit

        Example:
        >>> asr_text_unit = ASRTextUnit(text="This is some transcribed text.", id_num=0, timespan=\
            Timespan(2, 3), version=0)
        >>> print(asr_text_unit)

        ```txt
        0
        00:00:02,000 --> 00:00:03,000
        This is some transcribed text.
        ```
        """
        return (
            f"{self.timestamp}\n"
            + format_timestamp(self.timespan.start, always_include_hours=True, decimal_marker=",")
            + "--> "
            + format_timestamp(self.timespan.end, always_include_hours=True, decimal_marker=",")
            + "\n"
            + self.text.strip().replace("-->", " ->")
            + "\n"
        )

    def raw_text(self) -> str:
        return self.text

    def to_json(self):
        res = jsonpickle.encode(self, unpicklable=True, indent=4)
        assert isinstance(res, str)
        return res

    def from_json(self, json_str: str):
        res = jsonpickle.decode(json_str)
        assert isinstance(res, ASRTextUnit)
        return res


class CurrentASRText:
    def __init__(self, save_path: str, language: str) -> None:
        self.text_chunks: Dict[int, List[ASRTextUnit]] = dict()
        """dict of timestamp -> version -> ASRTextUnit"""
        self.save_path = save_path
        self.language = language
        # TODO: Abstract correction rule into a class
        self.correction_rules: List[Dict[str, Union[str, int, Dict[str, Union[str, bool]]]]] = []
        """Corrrection rules have the following general structure:
        ```
        [
            {
                "from": [
                    {
                        "string": str,
                        "active": bool
                    },
                    ...
                ],
                "to": str,
                "version": int,
            },
            ...
        ]
        ```
        """

    def edit_correction_rules(
        self, correction_rules: List[Dict[str, Union[str, int, Dict[str, Union[str, bool]]]]]
    ) -> None:
        # TODO: Versioning of correction rules? Right now we just overwrite the old ones
        self.correction_rules = correction_rules
        # remove empty correction rules
        for rule in self.correction_rules:
            rule["from"] = [
                source_string for source_string in rule["from"] if source_string["string"] != ""
            ]
        self.correction_rules = [
            rule for rule in self.correction_rules if len(rule["from"]) > 0 and rule["to"] != ""
        ]

        current_time = str(time.time()).replace(".", "_")
        with open(
            self.save_path + "/" + self.language + "/" + f"correction_rules_{current_time}.json",
            "w",
        ) as f:
            print(self.correction_rules, file=f)

    def longest_correction_rule_source(self) -> int:
        longest_rule = 0
        for rule in self.correction_rules:
            for source_string in rule["from"]:
                if source_string["active"] and len(source_string["string"]) > longest_rule:
                    longest_rule = len(source_string["string"])
        return longest_rule

    def apply_correction_rules(self, text: str) -> str:
        new_text = []
        text_buffer = ""

        for char in text:
            text_buffer += char
            rules_skipped = 0
            for rule in self.correction_rules:
                rule_skipped = True
                for source_string in rule["from"]:
                    if source_string["active"] and source_string["string"] in text_buffer:
                        rule_skipped = False
                        # remove source_string["string"] from the end of text_buffer
                        text_buffer = text_buffer[: -len(source_string["string"])]
                        new_text.append(text_buffer + rule["to"])
                        text_buffer = ""
                        break
                if not rule_skipped:
                    break
                rules_skipped += rule_skipped

            if rules_skipped == len(self.correction_rules):
                # we skipped all rules, keep only longest_correction_rule_source()-1 characters
                # in text_buffer
                remove_chars_num = len(text_buffer) - self.longest_correction_rule_source() + 1
                remove_chars_num = min(remove_chars_num, len(text_buffer))
                new_text.append(text_buffer[:remove_chars_num])
                text_buffer = text_buffer[remove_chars_num:]

        new_text.append(text_buffer)
        return "".join(new_text)

    def append(self, text: str, timestamp: int, timespan: Timespan) -> None:
        """Creates a new text chunk at the given timestamp with the given text"""
        corrected_text = self.apply_correction_rules(text)
        new_text_unit = ASRTextUnit(text=corrected_text, timestamp=0, timespan=timespan, version=0)
        self.text_chunks[timestamp] = [new_text_unit]
        with open(
            self.save_path + "/" + self.language + "/" + str(timestamp) + "_0" + ".json", "w"
        ) as f:
            print(new_text_unit.to_json(), file=f)

    def clear(self) -> None:
        """Clears all text chunk data"""
        self.text_chunks = dict()

    def get_latest_versions(self) -> Dict[int, int]:
        """Returns a dict of timestamp -> version of the latest version of each text chunk"""
        return {
            timestamp: self.text_chunks[timestamp][-1].version
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
                            "text": self.text_chunks[timestamp][newest_version],
                        }
                    )
            else:
                ret_value.append(
                    {
                        "timestamp": timestamp,
                        "version": newest_version,
                        "text": self.text_chunks[timestamp][newest_version],
                    }
                )
        return ret_value

    def edit_text_chunk(
        self, timestamp: int, _version: int, text: str
    ) -> Tuple[str, int]:  # noqa: ARG002
        """Edits the text chunk at the given timestamp and version to the given text"""
        if self.apply_correction_rules(text) == self.text_chunks[timestamp][-1].text:
            # if the text is the same as the newest version, discard the edit
            return self.text_chunks[timestamp][-1], self.text_chunks[timestamp][-1].version

        # TODO: Maybe do something smarter with the version, not just discarding it

        new_text_unit = ASRTextUnit(
            text=self.apply_correction_rules(text),
            timestamp=timestamp,
            # The timespan is the same for all versions of a text chunk
            timespan=self.text_chunks[timestamp][0].timespan,
            version=len(self.text_chunks[timestamp]),
        )
        self.text_chunks[timestamp].append(new_text_unit)

        with open(
            self.save_path + "/" + self.language + "/" + str(timestamp) + "_0" + ".json", "w"
        ) as f:
            print(new_text_unit.to_json(), file=f)

        return new_text_unit.text, self.text_chunks[timestamp][-1].version

    def rate_text_chunk(self, timestamp: int, version: int, d_rating: int) -> None:
        """Rates the text chunk at the given timestamp and version with the given rating"""
        self.text_chunks[timestamp][version].rating += d_rating


class CurrentASRTextContainer:
    def __init__(self, save_path: str, supported_languages: List[str]) -> None:
        self.current_texts = {
            lang_id: CurrentASRText(save_path, lang_id) for lang_id in supported_languages
        }
    
    def get_latest_versions(self) -> Dict[str, Dict[int, int]]:
        return {
            lang_id: self.current_texts[lang_id].get_latest_versions()
            for lang_id in self.current_texts.keys()
        }

    def get_latest_text_chunks(self, versions: Dict[str, Dict[int, int]]):
        return {
            lang_id: self.current_texts[lang_id].get_latest_text_chunks(versions[lang_id])
            for lang_id in self.current_texts.keys()
        }

    def clear(self) -> None:
        for lang_id in self.current_texts.keys():
            self.current_texts[lang_id].clear()
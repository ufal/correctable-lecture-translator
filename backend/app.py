from flask import Flask, request, make_response, Response
import json
import time
import os
from flask_cors import CORS
from typing import Tuple, Dict, List, Union, TextIO
import re
import difflib


class ASRConfig:
    def __init__(self):
        self.SAMPLING_RATE = 16000  # Hz
        self.AUDIO_SNIPPET_SECONDS = 30  # seconds
        self.AUDIO_SNIPPET_SIZE = self.SAMPLING_RATE * self.AUDIO_SNIPPET_SECONDS  # samples
        self.SHIFT_SECONDS = 28  # seconds
        self.SHIFT_SIZE = self.SHIFT_SECONDS * self.SAMPLING_RATE  # seconds * samples/second = samples


class Session:
    def __init__(self, session_id: str) -> None:
        global CONFIG

        self.session_id: str = session_id
        self.source_language: str = "Czech"  # default audio language
        self.transcript_language: str = "English"  # default transcript language
        self.buffer: AudioBuffer = AudioBuffer(SNIPPET_SIZE=CONFIG.AUDIO_SNIPPET_SIZE, SHIFT_LENGTH=CONFIG.SHIFT_SIZE)
        self.last_chunk_time: float = time.time()
        self.save_path: str = self.get_save_folder()
        self.text: CurrentASRText = CurrentASRText(self.save_path + "/text_chunks")
        self.last_sent_timestamp: int = -1
        self.unprocessed_timestamps: list[int] = [0]
        self.sent_out_for_processing: Dict[int, float] = dict()
        self.processed_timestamps: set[int] = {-1}

    def switch_transcript_language(self, language: str):
        self.transcript_language = language

    def switch_source_language(self, language: str):
        self.source_language = language

    def end_session(self):
        def format_timestamp(seconds: float, always_include_hours: bool = False, decimal_marker: str = '.'):
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
            break_index = min(len(line)//2, length)  # split evenly or at maximum length

            # work backwards from that guess to split between words
            # if break_index <= 1, we've hit the beginning of the string and can't split
            while break_index > 1:
                if line[break_index - 1] == " ":
                    break  # break at space
                else:
                    break_index -= 1
            if break_index > 1:
                # split the line, not including the space at break_index
                return line[:break_index - 1] + "\n" + line[break_index:]
            else:
                return line

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
                    f"{format_timestamp(segment['start'], always_include_hours=True, decimal_marker=',')} --> "
                    f"{format_timestamp(segment['end'], always_include_hours=True, decimal_marker=',')}\n"
                    f"{segment['text'].strip().replace('-->', '->')}\n",
                    file=file,
                    flush=True,
                )

        latest_text_chunks = self.text.get_latest_text_chunks(versions={})
        transcript = []
        for chunk in latest_text_chunks:
            transcript.append({"start": 30.0 * chunk["timestamp"], "end": 30.0 * # type: ignore
                              (chunk["timestamp"] + 1), "text": chunk["text"]}) # type: ignore

        with open(self.save_path + "/transcript.srt", "w", encoding="utf-8") as file:
            write_srt(transcript, file, line_length=0)

        with open(self.save_path + "/all_text_chunks.json", "w", encoding="utf-8") as file:
            json.dump(self.text.text_chunks, file, indent=4)

        with open(self.save_path + "/all_text_chunks_no_spans.json", "w", encoding="utf-8") as file:
            json.dump(self.text.text_chunks_no_spans, file, indent=4)

        # throw away everything from processing queue that belongs to this session
        global processing_queue
        processing_queue = [x for x in processing_queue if x["session_id"] != self.session_id]

    def get_save_folder(self):
        recordings = os.listdir("recordings")
        # filter out files that are not directories
        recordings = [x for x in recordings if os.path.isdir("recordings/" + x)]
        if self.session_id not in recordings:
            os.mkdir("recordings/" + self.session_id)

        # list recordings/self.session_id
        recordings = os.listdir("recordings/" + self.session_id)
        # filter out files that are not directories
        recordings = [x for x in recordings if os.path.isdir("recordings/" + self.session_id + "/" + x)]
        recordings_index = 0
        while str(recordings_index) in recordings:
            recordings_index += 1

        os.mkdir("recordings/" + self.session_id + "/" + str(recordings_index))
        recordings_folder = "recordings/" + self.session_id + "/" + str(recordings_index)
        os.mkdir(recordings_folder + "/audio")
        os.mkdir(recordings_folder + "/text_chunks")
        return recordings_folder

    def save_audio_chunk(self, chunk, timestamp: int):
        with open(self.save_path + "/audio/" + str(timestamp) + "_" + str(time.time()) + ".json", mode="w") as f:
            print(json.dumps(chunk), file=f)


class CurrentASRText:
    def __init__(self, save_path: Union[str,None] = None):
        self.text_chunks: dict[int, dict[int, str]] = dict()
        self.text_chunks_no_spans: dict[int, dict[int, str]] = dict()
        self.save_path = save_path

    def append(self, text: str, timestamp: int):
        self.text_chunks[timestamp] = {0: text}
        self.text_chunks_no_spans[timestamp] = {0: text}
        with open(self.save_path + "/" + str(timestamp) + "_0" + ".txt", "w") as f:
            print(text, file=f)

    def clear(self):
        self.text_chunks = dict()
        self.text_chunks_no_spans = dict()

    def get_latest_versions(self):
        return {timestamp: max(self.text_chunks[timestamp].keys()) for timestamp in self.text_chunks.keys()}

    def get_latest_text_chunks(self, versions: Dict[int, int]):
        ret_value: List[Dict[str, Union[int, str]]] = []
        for timestamp in self.text_chunks.keys():
            newest_version = max(self.text_chunks[timestamp].keys())
            if timestamp in versions:
                if versions[timestamp] < newest_version:
                    ret_value.append({"timestamp": timestamp, "version": newest_version,
                                     "text": self.text_chunks[timestamp][newest_version]})
            else:
                ret_value.append({"timestamp": timestamp, "version": newest_version,
                                 "text": self.text_chunks[timestamp][newest_version]})
        return ret_value

    def edit_text_chunk(self, timestamp: int, version: int, text: str) -> Tuple[str, int]:
        if text == self.text_chunks_no_spans[timestamp][max(self.text_chunks_no_spans[timestamp].keys())]:
            # if the text is the same as the newest version, discard the edit
            return self.text_chunks_no_spans[timestamp][max(self.text_chunks_no_spans[timestamp].keys())], max(self.text_chunks_no_spans[timestamp].keys())
        if version < max(self.text_chunks_no_spans[timestamp].keys()):
            # if the version of sender is older than the newest version, discard the edit
            return self.text_chunks_no_spans[timestamp][max(self.text_chunks_no_spans[timestamp].keys())], max(self.text_chunks_no_spans[timestamp].keys())

        diff = difflib.ndiff(self.text_chunks_no_spans[timestamp]
                             [max(self.text_chunks_no_spans[timestamp].keys())], text)
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
        with open(self.save_path + "/" + str(timestamp) + "_" + str(version_num) + ".txt", "w") as f:
            print(text, file=f)
        self.text_chunks[timestamp][version_num] = "".join(new_text)
        self.text_chunks_no_spans[timestamp][version_num] = text
        return self.text_chunks[timestamp][version_num], version_num


class AudioBuffer:
    def __init__(self, SNIPPET_SIZE, SHIFT_LENGTH):
        # config
        self.SNIPPET_SIZE: int = SNIPPET_SIZE
        self.SHIFT_LENGTH: int = SHIFT_LENGTH

        # data
        self.buffer = []
        self.smallest_available_timestamp = 0

    def extend(self, chunk):
        self.buffer.extend(chunk)

    def get_snippet(self, timestamp: int):
        actuall_timestamp = timestamp - self.smallest_available_timestamp
        return self.buffer[actuall_timestamp * self.SHIFT_LENGTH: actuall_timestamp * self.SHIFT_LENGTH + self.SNIPPET_SIZE]

    def can_get_snippet(self, timestamp: int):
        actuall_timestamp = timestamp - self.smallest_available_timestamp
        return actuall_timestamp * self.SHIFT_LENGTH + self.SNIPPET_SIZE <= len(self.buffer)

    def shift(self):
        if len(self.buffer) > self.SNIPPET_SIZE:
            self.smallest_available_timestamp += 1
            self.buffer = self.buffer[self.SHIFT_LENGTH:]

    def clear(self):
        self.buffer = []
        self.smallest_available_timestamp = 0

    def __len__(self):
        return len(self.buffer)


app = Flask(__name__)
CORS(app)
CONFIG = ASRConfig()
sessions: Dict[str, Session] = dict()
processing_queue: List[Dict[str, Union[str, int, List]]] = []
# sessions["straka-mic-test"] = Session("straka-mic-test")

def make_dummy_data():
    global sessions
    session = Session("default")

    session.text.append("Hello, my name is John.", 0)
    session.text.append("I am a student at the University of Applied Sciences in Munich.", 1)
    session.text.append("It is not a nice place to live", 2)
    session.text.append("but it is a nice place to study.", 3)
    session.text.append("Lorem Ipsum is simply dummy text of the printing and typesetting industry.", 4)
    session.text.append(
        "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.", 5)
    session.text.append(
        "It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.", 6)
    session.text.append("It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.", 7)

    sessions[session.session_id] = session

# make_dummy_data()


def add_cors_headers(response: Response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


def session_not_found(session_id: str):
    response_data = {
        "success": False,
        "session_id": session_id,
        "message": "Session not found"
    }
    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response


def get_data_to_offload():
    global processing_queue

    for item in processing_queue:
        session_id = item["session_id"]
        timestamp = item["timestamp"]
        audio = item["audio"]
        source_language = item["source_language"]
        transcript_language = item["transcript_language"]

        if timestamp in sessions[session_id].sent_out_for_processing and time.time() - sessions[session_id].sent_out_for_processing[timestamp] < 15:
            # don't send the same request too soon if it was already sent
            continue

        sessions[session_id].sent_out_for_processing[timestamp] = time.time()

        response_data = {
            "success": True,
            "session_id": session_id,
            "timestamp": timestamp,
            "source_language": source_language,
            "transcript_language": transcript_language,
            "audio": audio
        }
        return response_data

    response_data = {
        "success": True,
        "timestamp": None,
        "audio": []
    }
    return response_data


def got_offloaded_data(session_id: str, timestamp: int, ASR_result: str):
    global processing_queue

    if timestamp in sessions[session_id].text.text_chunks:
        # data already received
        return

    sessions[session_id].text.append(ASR_result, timestamp)
    sessions[session_id].processed_timestamps.add(timestamp)
    sessions[session_id].unprocessed_timestamps.remove(timestamp)
    sessions[session_id].sent_out_for_processing.pop(timestamp, None)
    processing_queue = [x for x in processing_queue if not (
        x["session_id"] == session_id and x["timestamp"] == timestamp)]


@app.route("/submit_audio_chunk", methods=['POST'])
def submit_audio_chunk():
    """Submit an audio chunk for processing.

    This route accepts a JSON payload with the following fields:
    - timestamp (`int`): The timestamp of the audio chunk in seconds.
    - chunk (`Union[Dict[str, int], Dict[str, float]]`): The audio data as a byte string.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
        {"success": true, "session_id": "default"}
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1.0, "1": 0.5}})
        {"success": true, "session_id": "default"}
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=UNKNOWN_SESSION", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
        {"success": false, "session_id": "UNKNOWN_SESSION", "message": "Session not found"}
    """

    global CONFIG, sessions, processing_queue

    session_id = request.args.get("session_id", default=None, type=str)
    request_data = request.get_json()
    timestamp = request_data["timestamp"]
    chunk = request_data["chunk"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    try:
        session = sessions[session_id]
    except KeyError:
        return session_not_found(session_id=session_id), 404

    session.save_audio_chunk(chunk=chunk, timestamp=timestamp)
    chunk: List = [chunk[x] for x in chunk]
    session.buffer.extend(chunk)
    session.last_chunk_time = time.time()

    if session.buffer.can_get_snippet(max(session.unprocessed_timestamps)):
        processing_queue.append({"session_id": session_id, "timestamp": max(session.unprocessed_timestamps), "source_language": session.source_language,
                                "transcript_language": session.transcript_language, "audio": session.buffer.get_snippet(max(session.unprocessed_timestamps))})
        session.unprocessed_timestamps.append(max(session.unprocessed_timestamps) + 1)
        session.buffer.shift()

    response_data = {
        "success": True,
        "session_id": session.session_id
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/get_latest_text_chunks", methods=['POST'])
def get_latest_text_chunks():
    """ Get the latest text chunks.

    This route accepts a JSON payload with the following fields:
    - versions (`Dict[str, int]`): A dictionary mapping timestamps to the version of the text chunks that the client already has.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.
        - text_chunks (`list[Dict[str, int | str]]`): A list of text chunks with newer versions. Each text chunk is a dictionary with the following fields:
            - timestamp (`int`): The timestamp of the text chunk.
            - version (`int`): The version of the text chunk.
            - text (`str`): The text of the text chunk.
        - versions (`Dict[str, int]`): A dictionary mapping timestamps to the latest version of the text chunks.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunks?session_id=default", json={"versions": {"0": 0, "1": 0}})
        {"success": true, "session_id": "default", "text_chunks": [{"timestamp": 0, "version": 1, "text": "Hello world!"}, {"timestamp": 2, "version": 0, "text": "This is a new text!"}], "versions": {"0": 1, "1": 0, "2": 0}}
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunks?session_id=UNKNOWN_SESSION", json={"versions": {"0": 0, "1": 0}})
        {"success": false, "session_id": "UNKNOWN_SESSION", "message": "Session not found"}
    """

    global sessions
    session_id = request.args.get("session_id", default=None, type=str)
    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    request_data = request.get_json()
    versions = request_data["versions"]
    versions = {int(x): versions[x] for x in versions}

    session = sessions[session_id]
    text_chunks = session.text.get_latest_text_chunks(versions)
    new_versions = session.text.get_latest_versions()

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "text_chunks": text_chunks,
        "versions": new_versions
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/get_latest_text_chunk_versions", methods=['GET'])
def get_latest_text_chunk_versions():
    """Get the latest versions of the text chunks.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.
        - versions (`Dict[str, int]`): A dictionary mapping timestamps to the latest version of the text chunks.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunk_versions?session_id=default")
        {"success": true, "session_id": "default", "versions": {"0": 1, "1": 1, "2": 0}}
    """

    global sessions
    session_id = request.args.get("session_id", default=None, type=str)
    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    session = sessions[session_id]
    versions = session.text.get_latest_versions()

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "versions": versions
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/edit_asr_chunk", methods=['POST'])
def edit_asr_chunk():
    """Edit an ASR chunk.

    This route accepts a JSON payload with the following fields:
    - timestamp (`int`): The timestamp of the ASR chunk.
    - version (`int`): The version of the ASR chunk.
    - text (`str`): The text of the ASR chunk.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.
        - text (`str`): The text of the ASR chunk.
        - timestamp (`int`): The timestamp of the ASR chunk.
        - version (`int`): The version of the ASR chunk.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/edit_asr_chunk?session_id=default", json={"timestamp": 0, "version": 1, "text": "Hello there, my name is John Wick."})
        {"success": true, "session_id": "default", "text": "Hello<span class='edited'> there</span>, my name is John<span class='edited'> Wick</span>.", "timestamp": 0, "version": 2}
    """
    global sessions
    request_data = request.get_json()
    session_id = request.args.get("session_id", default=None, type=str)
    timestamp = request_data["timestamp"]
    version = request_data["version"]
    text = request_data["text"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    session = sessions[session_id]
    text, version_num = session.text.edit_text_chunk(timestamp, version, text)

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "text": text,
        "timestamp": timestamp,
        "version": version_num
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/switch_source_language", methods=['POST'])
def switch_source_language():
    """Switch the source language of the session.

    This route accepts a JSON payload with the following fields:
    - language (`str`): The language to switch to.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/switch_source_language?session_id=default", json={"language": "English"})
        {"success": true, "session_id": "default"}
    """
    global sessions
    request_data = request.get_json()
    session_id = request.args.get("session_id", default=None, type=str)
    language = request_data["language"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    session = sessions[session_id]
    session.switch_source_language(language)

    response_data = {
        "success": True,
        "session_id": session.session_id,
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/switch_transcript_language", methods=['POST'])
def switch_transcript_language():
    """Switch the transcript language of the session.

    This route accepts a JSON payload with the following fields:
    - language (`str`): The language to switch to.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/switch_transcript_language?session_id=default", json={"language": "English"})
        {"success": true, "session_id": "default"}
    """

    global sessions
    request_data = request.get_json()
    session_id = request.args.get("session_id", default=None, type=str)
    language = request_data["language"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    session = sessions[session_id]
    session.switch_transcript_language(language)

    response_data = {
        "success": True,
        "session_id": session.session_id,
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/offload_ASR", methods=['POST', 'GET'])
def offload_computation():
    """Offload ASR computation to the server.

    On a POST request, this route accepts a JSON payload with the following fields:
    - session_id (`str`): The session ID of the session.
    - timestamp (`int`): The timestamp of the audio chunk.
    - ASR_result (`dict`): The ASR result of the audio chunk.

    On a POST request, this route returns a JSON payload with the following fields:
    - success (`bool`): Whether the request was successful.

    On a GET request, this route returns a JSON payload with the following fields:
    - session_id (`str`): The session ID of the session.
    - timestamp (`int`): The timestamp of the audio chunk.
    - audio_chunk (`list`): The audio chunk to be processed.

    Example:
        >>> requests.post("http://slt.ufal.mff.cuni.cz:5003/offload_ASR", json={"session_id": "default", "timestamp": 0, "ASR_result": {"text": "Hello world"}})
        {"success": true}
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/offload_ASR")
        {"session_id": "default", "timestamp": 0, "audio_chunk": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, ...]}
    """

    global CONFIG, sessions, processing_queue
    if request.method == "POST":
        request_data = request.get_json()
        got_offloaded_data(session_id=request_data["session_id"], timestamp=int(
            request_data["timestamp"]), ASR_result=request_data["ASR_result"]["text"])

        response_data = {
            "success": True,
        }

        response = make_response(json.dumps(response_data))
        response.headers['Content-Type'] = 'application/json'
        response = add_cors_headers(response)
        return response, 200

    elif request.method == "GET":
        response_data = get_data_to_offload()
        response = make_response(json.dumps(response_data))
        response.headers['Content-Type'] = 'application/json'
        response = add_cors_headers(response)
        return response, 200

    else:
        response_data = {
            "success": False,
            "message": "Method not allowed"
        }
        response = make_response(json.dumps(response_data))
        response.headers['Content-Type'] = 'application/json'
        response = add_cors_headers(response)
        return response, 405


@app.route("/get_active_sessions", methods=['GET'])
def get_active_sessions():
    """Get the active sessions.

    This route returns a JSON payload with the following fields:
    - active_sessions (`list`): A list of active sessions.

    Example:
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/get_active_sessions")
        {"active_sessions": ["default"]}
    """

    global sessions
    response_data = {
        "active_sessions": list(sessions.keys()),
    }

    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/create_session", methods=['GET'])
def create_session():
    """Create a new session.

    Args:
        session_id (`str`): The session ID of the session.

    Returns:
        A JSON response with the following fields:
        - success (`bool=True`): The request was successful.
        - message (`str`): A message describing what happened.

    Example:
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/create_session?session_id=default")
        {"success": true, "message": "Successfully created session default"}
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/create_session?session_id=session_already_exists")
        {"success": false, "message": "Session already exists"}
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/create_session")
        {"success": false, "message": "Session ID not provided"}
    """

    global sessions
    session_id = request.args.get("session_id", default=None, type=str)

    if session_id is None or len(session_id) == 0:

        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "Session ID not provided"
        del response_data["session_id"]
        response.data = json.dumps(response_data)
        return response, 404

    if session_id in sessions:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "Session already exists"
        del response_data["session_id"]
        response.data = json.dumps(response_data)
        return response, 404

    sessions[session_id] = Session(session_id=session_id)
    response_data = {
        "success": True,
        "message": f"Successfully created session {session_id}"
    }
    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


@app.route("/end_session", methods=['GET'])
def end_session():
    """End a session.

    Args:
        session_id (`str`): The session ID of the session.

    Returns:
        A JSON response with the following fields:
        - success (`bool=True`): The request was successful.
        - message (`str`): A message describing what happened.

        - success (`bool=False`): The request was not successful.
        - message (`str`): A message describing what happened.
        - session_id (`str`): The session ID of the session.

    Example:
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/end_session?session_id=default")
        {"success": true, "message": "Successfully ended session default"}
        >>> requests.get("http://slt.ufal.mff.cuni.cz:5003/end_session?session_id=session_not_found")
        {"success": false, "message": "Session not found", "session_id": "session_not_found"}
    """
    global sessions
    session_id = request.args.get("session_id", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        response = session_not_found(session_id=session_id)
        return response, 404

    sessions[session_id].end_session()
    del sessions[session_id]
    response_data = {
        "success": True,
        "message": f"Successfully ended session {session_id}"
    }
    response = make_response(json.dumps(response_data))
    response.headers['Content-Type'] = 'application/json'
    response = add_cors_headers(response)
    return response, 200


if __name__ == "__main__":
    try:
        servercert = os.environ["SERVERCERT"]
        serverkey = os.environ["SERVERKEY"]
    except KeyError:
        servercert = None
        serverkey = None

    if servercert is None or serverkey is None:
        app.run(port=5003, host="slt.ufal.mff.cuni.cz")
    else:
        app.run(port=5003, host="slt.ufal.mff.cuni.cz", ssl_context=(servercert, serverkey))

import io
import json
import os

# create random session_id
import random
import string
from typing import Dict, List, Tuple, Union

import jsonpickle

# for file upload
import soundfile
from flask import Flask, Response, make_response, request
from flask_cors import CORS

from .buffer_common import OnlineASRProcessor, create_tokenizer
from .common import ASRConfig, Timespan

# modules for ASR manipulation
from .networking_common import Session, TranscribePacket, TranslatePacket
from .text_handlers import CorrectionRule

app = Flask(__name__)
CORS(app)
CONFIG = ASRConfig()
sessions: Dict[str, Session] = dict()
processing_queue: List[TranscribePacket] = []
processing_queue_translate: List[TranslatePacket] = []

# TODO: subtitles to ~37 characters per chunk
# TODO: edit chunks ~50 characters per chunk
# TODO: chunk editable or not flag


def add_cors_headers(response: Response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


def session_not_found(session_id: Union[str, None]
 = None):
    response_data = {
        "success": False,
        "session_id": session_id,
        "message": "Session not found",
    }
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response


def plain_response(message: str):
    response = make_response(message)
    response.headers["Content-Type"] = "text/plain"
    response = add_cors_headers(response)
    return response


def json_response(json_data):
    response = make_response(json.dumps(json_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response


def get_data_to_offload():
    global processing_queue

    # create items in processing queue from sessins with enough audio data
    for session_id in sessions:
        session = sessions[session_id]
        if session.online_asr_processor.buffer_updated:
            session.online_asr_processor.buffer_updated = False
            processing_queue.append(
                TranscribePacket(
                    session_id=session_id,
                    timestamp=session.online_asr_processor.last_timestamp,
                    source_language=session.source_language,
                    transcript_language=session.transcript_language,
                    prompt=session.online_asr_processor.prompt()[0],
                    audio=session.online_asr_processor.audio_buffer.tolist(),
                )
            )
            session.untranscribed_timestamps.append(
                session.online_asr_processor.last_timestamp
            )
            session.online_asr_processor.last_timestamp += 1

    for item in processing_queue:
        response_data = item.get_data_to_offload()
        if response_data is not None:
            return response_data

    response_data = {"success": True, "timestamp": None, "audio": []}
    return response_data


def got_offloaded_data(session_id: str, timestamp: int, tsw, ends, language: str):
    global processing_queue, processing_queue_translate

    packet = None
    # search for the TranscribePacket in the processing queue by session_id and timestamp
    for item in processing_queue:
        if item.session_id == session_id and item.timestamp == timestamp:
            packet = item
            break

    if packet is None:
        # no such packet found
        return
    assert isinstance(packet, TranscribePacket)

    if packet.transcript is not None:
        # data already received
        return
    packet.transcript = "Recieved data"

    session = sessions[session_id]
    session.untranscribed_timestamps.remove(timestamp)
    session.transcribed_timestamps.append(timestamp)

    processing_queue = [
        x
        for x in processing_queue
        if not (x.session_id == session_id and x.timestamp == timestamp)
    ]
    commited = session.online_asr_processor.process_iter(tsw, ends)
    if len(session.online_asr_processor.audio_buffer) / 16000 > 45:
        session.online_asr_processor = OnlineASRProcessor(
            create_tokenizer(session.transcript_language)
        )

    if commited[0] is not None:
        assert isinstance(commited[0], float)
        assert isinstance(commited[1], float)
        session.texts.current_texts[language].append(
            commited[2], Timespan(commited[0], commited[1])
        )
        processing_queue_translate.append(
            TranslatePacket(
                session_id=session_id,
                timestamp=timestamp,
                source_language=session.source_language,
                target_languages=session.supported_languages,
                source_text=commited[2],
                timespan=Timespan(commited[0], commited[1]),
            )
        )


def got_offloaded_file(session_id: str, timestamp: int, tsw, ends, language: str):
    global processing_queue, processing_queue_translate

    packet = None
    # search for the TranscribePacket in the processing queue by session_id and timestamp
    for item in processing_queue:
        if item.session_id == session_id and item.timestamp == timestamp:
            packet = item
            break

    if packet is None:
        # no such packet found
        return
    assert isinstance(packet, TranscribePacket)

    if packet.transcript is not None:
        # data already received
        return
    packet.transcript = "Recieved data"

    session = sessions[session_id]
    session.transcribed_timestamps.append(timestamp)

    processing_queue = [
        x
        for x in processing_queue
        if not (x.session_id == session_id and x.timestamp == timestamp)
    ]

    # tsw has format [(beg,end,"word1"), ...]
    # we need to split it to text chunks with length ~40 characters
    for i in range(len(tsw)):
        session.texts.current_texts[language].append(
            tsw[i][2], Timespan(tsw[i][0], tsw[i][1])
        )


@app.route("/submit_audio_chunk", methods=["POST"])
def submit_audio_chunk() -> Tuple[Response, int]:
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
        >>> requests.post("https://API_URL/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
        {"success": true, "session_id": "default"}
        >>> requests.post("https://API_URL/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1.0, "1": 0.5}})
        {"success": true, "session_id": "default"}
        >>> requests.post("https://API_URL/submit_audio_chunk?session_id=UNKNOWN_SESSION", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
        {"success": false, "session_id": "UNKNOWN_SESSION", "message": "Session not found"}
    """

    global CONFIG, sessions, processing_queue

    session_id = request.args.get("session_id", default=None, type=str)
    request_data = request.get_json()
    assert isinstance(request_data, dict)
    assert isinstance(request_data["timestamp"], int)
    assert isinstance(request_data["chunk"], dict)

    timestamp: int = request_data["timestamp"]
    chunk: Dict[str, float] = request_data["chunk"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404

    try:
        session = sessions[session_id]
    except KeyError:
        return session_not_found(session_id=session_id), 404

    session.save_audio_chunk(chunk=chunk, timestamp=timestamp)
    chunk_bytes: List[float] = [chunk[x] for x in chunk]
    session.online_asr_processor.insert_audio_chunk(chunk_bytes)

    response_data = {"success": True, "session_id": session.session_id}
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/get_latest_text_chunks", methods=["POST"])
def get_latest_text_chunks():
    """Get the latest text chunks.

    This route accepts a JSON payload with the following fields:
    - versions (`Dict[str, int]`): A dictionary mapping timestamps to the version of the text chunks that the client already has.

    Args:
        session_id (str): The session ID of the session.

    Returns:
        json: A JSON response with the following fields:
        - success (`bool`): Whether the request was successful.
        - session_id (`str`): The session ID of the session.
        - text_chunks (`list[Dict[str, Union[int. str]]]`): A list of text chunks with newer versions. Each text chunk is a dictionary with the following fields:
            - timestamp (`int`): The timestamp of the text chunk.
            - version (`int`): The version of the text chunk.
            - text (`str`): The text of the text chunk.
        - versions (`Dict[str, int]`): A dictionary mapping timestamps to the latest version of the text chunks.

        or a JSON response with the following fields:
        - success (`bool=False`): The request was not successful.
        - session_id (`str`): The session ID of the session.
        - message (`str`): A message describing what went wrong if the request was not successful.

    Example:
        >>> requests.post("https://API_URL/get_latest_text_chunks?session_id=default", json={"versions": {"0": 0, "1": 0}})
        {"success": true, "session_id": "default", "text_chunks": [{"timestamp": 0, "version": 1, "text": "Hello world!"}, {"timestamp": 2, "version": 0, "text": "This is a new text!"}], "versions": {"0": 1, "1": 0, "2": 0}}
        >>> requests.post("https://API_URL/get_latest_text_chunks?session_id=UNKNOWN_SESSION", json={"versions": {"0": 0, "1": 0}})
        {"success": false, "session_id": "UNKNOWN_SESSION", "message": "Session not found"}
    """

    global sessions
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    request_data = request.get_json()
    assert isinstance(request_data, dict)
    versions = request_data["versions"]
    versions = {int(x): versions[x] for x in versions}

    session = sessions[session_id]
    text_chunks = session.texts.current_texts[language].get_latest_text_chunks(versions)
    new_versions = session.texts.current_texts[language].get_latest_versions()

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "text_chunks": text_chunks,
        "versions": new_versions,
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/get_latest_text_chunk_versions", methods=["GET"])
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
        >>> requests.get("https://API_URL/get_latest_text_chunk_versions?session_id=default")
        {"success": true, "session_id": "default", "versions": {"0": 1, "1": 1, "2": 0}}
    """

    global sessions
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    session = sessions[session_id]
    versions = session.texts.current_texts[language].get_latest_versions()

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "versions": versions,
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/edit_asr_chunk", methods=["POST"])
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
        >>> requests.post("https://API_URL/edit_asr_chunk?session_id=default", json={"timestamp": 0, "version": 1, "text": "Hello there, my name is John Wick."})
        {"success": true, "session_id": "default", "text": "Hello<span class='edited'> there</span>, my name is John<span class='edited'> Wick</span>.", "timestamp": 0, "version": 2}
    """

    global sessions
    request_data = request.get_json()
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)
    timestamp = request_data["timestamp"]
    version = request_data["version"]
    text = request_data["text"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    session = sessions[session_id]
    text, version = session.texts.current_texts[language].edit_text_chunk(
        timestamp, version, text
    )

    response_data = {
        "success": True,
        "session_id": session.session_id,
        "text": text,
        "timestamp": timestamp,
        "version": version,
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/switch_source_language", methods=["POST"])
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
        >>> requests.post("https://API_URL/switch_source_language?session_id=default", json={"language": "English"})
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
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/switch_transcript_language", methods=["POST"])
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
        >>> requests.post("https://API_URL/switch_transcript_language?session_id=default", json={"language": "English"})
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
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/offload_ASR", methods=["POST", "GET"])
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
        >>> requests.post("https://API_URL/offload_ASR", json={"session_id": "default", "timestamp": 0, "ASR_result": {"text": "Hello world"}})
        {"success": true}
        >>> requests.get("https://API_URL/offload_ASR")
        {"session_id": "default", "timestamp": 0, "audio_chunk": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, ...]}
    """

    global CONFIG, sessions, processing_queue
    if request.method == "POST":
        request_data = request.get_json()
        assert isinstance(request_data, dict)

        if request_data["is_file"]:
            got_offloaded_file(
                session_id=request_data["session_id"],
                timestamp=int(request_data["timestamp"]),
                tsw=request_data["tsw"],
                ends=request_data["ends"],
                language=request_data["language"],
            )
        else:
            got_offloaded_data(
                session_id=request_data["session_id"],
                timestamp=int(request_data["timestamp"]),
                tsw=request_data["tsw"],
                ends=request_data["ends"],
                language=request_data["language"],
            )

        response_data = {
            "success": True,
        }

        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    elif request.method == "GET":
        response_data = get_data_to_offload()
        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    else:
        response_data = {"success": False, "message": "Method not allowed"}
        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 405


@app.route("/get_active_sessions", methods=["GET"])
def get_active_sessions():
    """Get the active sessions.

    This route returns a JSON payload with the following fields:
    - active_sessions (`list`): A list of active sessions.

    Example:
        >>> requests.get("https://API_URL/get_active_sessions")
        {"active_sessions": ["default"]}
    """

    global sessions
    response_data = {
        "active_sessions": list(sessions.keys()),
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/create_session", methods=["GET"])
def create_session():
    """Create a new session.

    Args:
        session_id (`str`): The session ID of the session.

    Returns:
        A JSON response with the following fields:
        - success (`bool=True`): The request was successful.
        - message (`str`): A message describing what happened.

    Example:
        >>> requests.get("https://API_URL/create_session?session_id=default")
        {"success": true, "message": "Successfully created session default"}
        >>> requests.get("https://API_URL/create_session?session_id=session_already_exists")
        {"success": false, "message": "Session already exists"}
        >>> requests.get("https://API_URL/create_session")
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

    sessions[session_id] = Session(session_id=session_id, config=CONFIG)
    response_data = {
        "success": True,
        "message": f"Successfully created session {session_id}",
    }
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/end_session", methods=["GET"])
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
        >>> requests.get("https://API_URL/end_session?session_id=default")
        {"success": true, "message": "Successfully ended session default"}
        >>> requests.get("https://API_URL/end_session?session_id=session_not_found")
        {"success": false, "message": "Session not found", "session_id": "session_not_found"}
    """
    global sessions
    session_id = request.args.get("session_id", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        response = session_not_found(session_id=session_id)
        return response, 404

    sessions[session_id].end_session()
    del sessions[session_id]

    # throw away everything from processing queue that belongs to this session
    global processing_queue
    processing_queue = [x for x in processing_queue if x.session_id != session_id]

    response_data = {
        "success": True,
        "message": f"Successfully ended session {session_id}",
    }
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/rate_text_chunk", methods=["POST"])
def rate_text_chunk() -> Tuple[Response, int]:
    global sessions
    request_data = request.get_json()
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)

    timestamp = request_data["timestamp"]
    version = request_data["version"]
    rating_update = request_data["rating_update"]

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    session = sessions[session_id]
    session.texts.current_texts[language].rate_text_chunk(
        timestamp, version, rating_update
    )
    new_rating: int = (
        session.texts.current_texts[language].text_chunks[timestamp][version].rating
    )

    response_data = {
        "success": True,
        "message": f"Successfully updated rating for {session_id}, language {language}, chunk_id {timestamp}, chunk_version {version}, rating_update {rating_update}, new_rating {new_rating}",
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/submit_correction_rules", methods=["POST"])
def submit_correction_rules():
    global sessions
    request_data = request.get_json()["entries"]
    """Request data has following structure:
    ```
    [
        {
            "source_strings": [
                {
                    "string": "str",
                    "active": "bool"
                },
            ],
            "to": "str",
            "version": "int",
        },
    ]
    ```
    """
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    session = sessions[session_id]
    session.texts.current_texts[language].correction_rules = []

    for rule in request_data:
        session.texts.current_texts[language].correction_rules.append(CorrectionRule())
        session.texts.current_texts[language].correction_rules[-1].decode_from_dict(
            rule
        )

    # clear empty rules
    session.texts.current_texts[language].clear_empty_correction_rules()
    response_data = {
        "success": True,
        "message": f"Successfully uploaded rules for session {session_id}, language {language}",
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/get_correction_rules", methods=["GET"])
def get_correction_rules():
    global sessions
    session_id = request.args.get("session_id", default=None, type=str)
    language = request.args.get("language", default=None, type=str)

    if session_id is None or session_id not in sessions or len(session_id) == 0:
        return session_not_found(session_id=session_id), 404
    if language is None or language not in sessions[session_id].texts.current_texts:
        response = session_not_found(session_id=session_id)
        response_data = json.loads(response.data)
        response_data["message"] = "language not found"
        response.data = json.dumps(response_data)
        return response, 404

    session = sessions[session_id]
    response_data = []
    for rule in session.texts.current_texts[language].correction_rules:
        response_data.append(rule.encode_to_dict())

    response_data = {
        "locked": True,
        "entries": response_data,
    }
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


@app.route("/", methods=["GET"])
def landing_page():
    return plain_response("I work uwu"), 200


@app.route("/submit_audio_file", methods=["POST"])
def submit_audio_file():
    if "file" not in request.files:
        return plain_response("No file part"), 400

    # get the file
    audio_file = request.files["file"]
    if audio_file.filename == "":
        return plain_response("No selected file"), 400

    audio_data = audio_file.read()
    audio_data, sr = soundfile.read(io.BytesIO(audio_data))

    if sr != 16000:
        return plain_response(f"Wrong sample rate: {sr} instead of 16000"), 400

    # get a random session_id
    session_id = "".join(random.choice(string.ascii_letters) for i in range(32))
    while session_id in sessions:
        session_id = "".join(random.choice(string.ascii_letters) for i in range(32))

    sessions[session_id] = Session(session_id=session_id, config=CONFIG)
    session = sessions[session_id]
    processing_queue.append(
        TranscribePacket(
            session_id=session_id,
            timestamp=0,
            source_language=session.source_language,
            transcript_language=session.transcript_language,
            prompt="",
            audio=audio_data.tolist(),
            is_file=True,
        )
    )

    return (
        json_response(
            json_data={
                "success": True,
                "session_id": session.session_id,
            }
        ),
        200,
    )


def got_translated_data(session_id, timestamp, timespan, translated_text):
    global processing_queue_translate

    packet = None
    # search for the TranscribePacket in the processing queue by session_id and timestamp
    for item in processing_queue_translate:
        if item.session_id == session_id and item.timestamp == timestamp:
            packet = item
            break

    if packet is None:
        # no such packet found
        return

    assert isinstance(packet, TranslatePacket)

    if packet.recieved:
        # data already received
        return
    packet.recieved = True

    session = sessions[session_id]

    processing_queue_translate = [
        x for x in processing_queue_translate if not x == packet
    ]

    timespan = jsonpickle.decode(timespan)
    assert isinstance(timespan, Timespan)

    for language in translated_text:
        if language != session.transcript_language:
            session.texts.current_texts[language].append(
                translated_text[language], timespan
            )


def get_translate_data():
    for item in processing_queue_translate:
        response_data = item.get_data_to_offload()
        if response_data is not None:
            return response_data

    response_data = None
    return response_data


@app.route("/offload_translation", methods=["GET", "POST"])
def offload_translation():
    if request.method == "POST":
        request_data = request.get_json()
        assert isinstance(request_data, dict)

        got_translated_data(
            session_id=request_data["session_id"],
            timestamp=int(request_data["timestamp"]),
            translated_text=request_data["translated_text"],
            timespan=request_data["timespan"],
        )

        response_data = {
            "success": True,
        }

        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    elif request.method == "GET":
        response_data = get_translate_data()
        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    else:
        response_data = {"success": False, "message": "Method not allowed"}
        response = make_response(
            jsonpickle.encode(response_data, unpicklable=True, indent=4)
        )
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 405


def main() -> None:
    servercert: Union[str, None]
 = os.environ.get("SERVERCERT")
    serverkey: Union[str, None]
 = os.environ.get("SERVERKEY")

    host = os.environ.get("COLETRA_API_HOST", "localhost")
    port = int(os.environ.get("COLETRA_API_PORT", 5000))

    if servercert is None or serverkey is None:
        app.run(port=port, host=host)
    else:
        app.run(
            port=port,
            host=host,
            ssl_context=(servercert, serverkey),
        )


if __name__ == "__main__":
    main()

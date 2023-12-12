import json
import os  # type: ignore

# import time
import jsonpickle  # type: ignore

from typing import Dict, List, Union, Tuple
from flask import Flask, Response, make_response, request
from flask_cors import CORS  # type: ignore

# modules for ASR manipulation
# from common import format_timestamp, break_line
# from text_handlers import CurrentASRText
# from audio_handler import AudioBuffer
from networking_common import Session, TranscribePacket
from common import ASRConfig, Timespan
from text_handlers import CorrectionRule


app = Flask(__name__)
CORS(app)
CONFIG = ASRConfig()
sessions: Dict[str, Session] = dict()
processing_queue: List[TranscribePacket] = []
# sessions["straka-mic-test"] = Session("straka-mic-test")

"""
def make_dummy_data():
    global sessions
    session = Session("default", CONFIG)

    session.text.append("Hello, my name is John.", 0)
    session.text.append("I am a student at the University of Applied Sciences in Munich.", 1)
    session.text.append("It is not a nice place to live", 2)
    session.text.append("but it is a nice place to study.", 3)
    session.text.append(
        "Lorem Ipsum is simply dummy text of the printing and typesetting industry.",
        4,
    )
    session.text.append(
        "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s,\
         when an unknown printer took a galley of type and scrambled it to make a type\
         specimen book.",
        5,
    )
    session.text.append(
        "It has survived not only five centuries, but also the leap into electronic\
         typesetting, remaining essentially unchanged.",
        6,
    )
    session.text.append(
        "It was popularised in the 1960s with the release of Letraset sheets containing\
         Lorem Ipsum passages, and more recently with desktop publishing software like\
         Aldus PageMaker including versions of Lorem Ipsum.",
        7,
    )

    sessions[session.session_id] = session
"""

# make_dummy_data()


# DONE
def add_cors_headers(response: Response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response


# DONE
def session_not_found(session_id: Union[str, None] = None):
    response_data = {
        "success": False,
        "session_id": session_id,
        "message": "Session not found",
    }
    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response


# DONE
def get_data_to_offload():
    global processing_queue

    # DONE: create items in processing queue from sessins with enough audio data
    for sessin_id in sessions:
        session = sessions[sessin_id]
        if session.online_asr_processor.buffer_updated:
            session.online_asr_processor.buffer_updated = False
            processing_queue.append(
                TranscribePacket(
                    session_id=sessin_id,
                    timestamp=session.online_asr_processor.last_timestamp,
                    source_language=session.source_language,
                    transcript_language=session.transcript_language,
                    prompt=session.online_asr_processor.prompt()[0],
                    audio=session.online_asr_processor.audio_buffer.tolist(),
                )
            )
            session.untranscribed_timestamps.append(session.online_asr_processor.last_timestamp)
            session.online_asr_processor.last_timestamp += 1

    for item in processing_queue:
        response_data = item.get_data_to_offload()
        if response_data is not None:
            tmp = response_data["audio"]
            assert isinstance(tmp, list)
            print(len(tmp))
            return response_data

    response_data = {"success": True, "timestamp": None, "audio": []}
    return response_data


# DONE
def got_offloaded_data(session_id: str, timestamp: int, tsw, ends, language: str):
    global processing_queue

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

    if commited[0] is not None:
        assert isinstance(commited[0], float)
        assert isinstance(commited[1], float)
        session.texts.current_texts[language].append(
            commited[2], Timespan(commited[0], commited[1])
        )


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
        {"success": true, "session_id": "default"}
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=default", json={"timestamp": 0, "chunk": {"0": 1.0, "1": 0.5}})
        {"success": true, "session_id": "default"}
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/submit_audio_chunk?session_id=UNKNOWN_SESSION", json={"timestamp": 0, "chunk": {"0": 1, "1": 2}})
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


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunks?session_id=default", json={"versions": {"0": 0, "1": 0}})
        {"success": true, "session_id": "default", "text_chunks": [{"timestamp": 0, "version": 1, "text": "Hello world!"}, {"timestamp": 2, "version": 0, "text": "This is a new text!"}], "versions": {"0": 1, "1": 0, "2": 0}}
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunks?session_id=UNKNOWN_SESSION", json={"versions": {"0": 0, "1": 0}})
        {"success": false, "session_id": "UNKNOWN_SESSION", "message": "Session not found"}
    """  # noqa: E501

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


# DONE
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
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/get_latest_text_chunk_versions?session_id=default")
        {"success": true, "session_id": "default", "versions": {"0": 1, "1": 1, "2": 0}}
    """  # noqa: E501

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


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/edit_asr_chunk?session_id=default", json={"timestamp": 0, "version": 1, "text": "Hello there, my name is John Wick."})
        {"success": true, "session_id": "default", "text": "Hello<span class='edited'> there</span>, my name is John<span class='edited'> Wick</span>.", "timestamp": 0, "version": 2}
    """  # noqa: E501

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
    text, version = session.texts.current_texts[language].edit_text_chunk(timestamp, version, text)

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


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/switch_source_language?session_id=default", json={"language": "English"})
        {"success": true, "session_id": "default"}
    """  # noqa: E501

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


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/switch_transcript_language?session_id=default", json={"language": "English"})
        {"success": true, "session_id": "default"}
    """  # noqa: E501

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


# DONE
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
        >>> requests.post("https://slt.ufal.mff.cuni.cz:5003/offload_ASR", json={"session_id": "default", "timestamp": 0, "ASR_result": {"text": "Hello world"}})
        {"success": true}
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/offload_ASR")
        {"session_id": "default", "timestamp": 0, "audio_chunk": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, ...]}
    """  # noqa: E501

    global CONFIG, sessions, processing_queue
    if request.method == "POST":
        request_data = request.get_json()
        assert isinstance(request_data, dict)

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

        response = make_response(jsonpickle.encode(response_data, unpicklable=True, indent=4))
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    elif request.method == "GET":
        response_data = get_data_to_offload()
        response = make_response(jsonpickle.encode(response_data, unpicklable=True, indent=4))
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 200

    else:
        response_data = {"success": False, "message": "Method not allowed"}
        response = make_response(jsonpickle.encode(response_data, unpicklable=True, indent=4))
        response.headers["Content-Type"] = "application/json"
        response = add_cors_headers(response)
        return response, 405


# DONE
@app.route("/get_active_sessions", methods=["GET"])
def get_active_sessions():
    """Get the active sessions.

    This route returns a JSON payload with the following fields:
    - active_sessions (`list`): A list of active sessions.

    Example:
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/get_active_sessions")
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


# DONE
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
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/create_session?session_id=default")
        {"success": true, "message": "Successfully created session default"}
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/create_session?session_id=session_already_exists")
        {"success": false, "message": "Session already exists"}
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/create_session")
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


# DONE
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
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/end_session?session_id=default")
        {"success": true, "message": "Successfully ended session default"}
        >>> requests.get("https://slt.ufal.mff.cuni.cz:5003/end_session?session_id=session_not_found")
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


# DONE
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
    session.texts.current_texts[language].rate_text_chunk(timestamp, version, rating_update)
    new_rating: int = session.texts.current_texts[language].text_chunks[timestamp][version].rating

    response_data = {
        "success": True,
        "message": f"Successfully updated rating for {session_id}, language {language}, chunk_id {timestamp}, chunk_version {version}, rating_update {rating_update}, new_rating {new_rating}",
    }

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


# DONE
@app.route("/submit_correction_rules", methods=["POST"])
def submit_correction_rules():
    global sessions
    request_data = request.get_json()
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
        session.texts.current_texts[language].correction_rules[-1].decode_from_dict(rule)

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


# DONE
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

    response = make_response(json.dumps(response_data))
    response.headers["Content-Type"] = "application/json"
    response = add_cors_headers(response)
    return response, 200


# DONE
@app.route("/", methods=["GET"])
def landing_page():
    response = make_response("I work uwu")
    response.headers["Content-Type"] = "text/plain"
    response = add_cors_headers(response)
    return response, 200


# DONE
def main() -> None:
    try:
        servercert: Union[str, None] = os.environ["SERVERCERT"]
        serverkey: Union[str, None] = os.environ["SERVERKEY"]
    except KeyError:
        servercert = None
        serverkey = None

    if servercert is None or serverkey is None:
        app.run(port=5003, host="slt.ufal.mff.cuni.cz")
    else:
        app.run(
            port=5003,
            host="slt.ufal.mff.cuni.cz",
            ssl_context=(servercert, serverkey),
        )


if __name__ == "__main__":
    main()

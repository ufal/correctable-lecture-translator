import requests  # type: ignore
import urllib3
import json
import time
import sys

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

while True:
    try:
        r = requests.get("https://slt.ufal.mff.cuni.cz:5003/offload_translation", verify=False)
        json_data = json.loads(r.text)

        print(json_data)
        if json_data is None:
            time.sleep(5)
            continue

        session_id = json_data["session_id"]
        timestamp = json_data["timestamp"]
        source_text = json_data["source_text"]
        source_language = json_data["source_language"]
        target_languages = json_data["target_languages"]
        timespan = json_data["timespan"]

        
        translated_text = {}
        for target_language in target_languages:
            translated_text[target_language] = target_language + " " + source_text
        
        r = requests.post(
            "https://slt.ufal.mff.cuni.cz:5003/offload_translation",
            json={
                "session_id": session_id,
                "timestamp": timestamp,
                "translated_text": translated_text,
                "timespan": timespan,
            },
            verify=False,
        )

        # print("ASR time: ", time.time() - starting_ASR_time, file=sys.stderr)
    except Exception as e:
        print("cannot connect to server " + str(e), file=sys.stderr)
        time.sleep(5)
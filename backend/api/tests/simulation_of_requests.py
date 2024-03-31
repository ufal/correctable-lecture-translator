import os
import json
import requests
import time

# I want to simulate sending one request evert second to localhost:5000

API_URL = os.environ.get("COLETRA_API_URL")


def list_dir_sorted(path):
    files = os.listdir(path)
    files.sort(key=lambda x: int(x.split("_")[0]))
    return files


# class for reading recording data from files:
class Recording:
    def __init__(self, foldername):
        self.foldername = foldername
        self.data = self.read_data()

    def read_data(self):
        data = []
        for filename in list_dir_sorted(self.foldername):
            with open(self.foldername + "/" + filename, "r") as f:
                data.append({"timestamp": filename.split("_")[0], "chunk": json.load(f)})
        return data


recordings_folder = "recordings/0/"

for file in os.listdir(recordings_folder):
    # open the file and replace all single quotes with double quotes
    data = ""
    with open(recordings_folder + file, "r") as f:
        data = f.read()
        data = data.replace("'", '"')
    with open(recordings_folder + file, "w") as f:
        f.write(data)

recordings = Recording(recordings_folder)

# now every second send a json encoded request to localhost:5000
# with the data from the recordings


stable = ""
unstable = ""

for chunk in recordings.data:
    r = requests.post(f"{API_URL}/submit_audio_chunk", json=chunk)
    # print(r.text)
    # r.text is a json which I want to decode
    decoded = json.loads(r.text)
    print(chunk["timestamp"], decoded)
    time.sleep(1)

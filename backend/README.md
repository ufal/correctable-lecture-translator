# Coletra Backend

## Project setup and run

- SSL certificate is needed to successfully run the frontend, without it the browser won't be able
to record and send audio (although this can be forced by adding the frontend host domain to a
list using this chromium flag `unsafely-treat-insecure-origin-as-secure`). The paths to the
cert and key files should be passed as environment variables `SERVERCERT` and `SERVERKEY`.

- Setup also requires a backend server to be running, the path to which must be specified as
`COLETRA_API_URL` environment variable. Note that this URL needs to be the same as `API_URL` for the frontend.

- The backend consist of two parts, API and Model. The API is a Flask server that handles audio processing and other functionalities provided by frontend. The Model is a script that is polling API for new audio, running the Whisper model and returning transcriptions to API.

- API requires `Python3.8` and `poetry` package manager installed, because of the fast-mosestokenizer.
- (Model requires - if not run in docker - from `Python3.8` to `Python3.11` and `poetry` package manager installed.)

- To run the backend:
1. Run the API with `poetry shell`, `poetry install` and `COLETRA_API_HOST=my.api.url COLETRA_API_PORT=1234 SERVERCERT=servercert.pem SERVERKEY=serverkey.pem poetry run api` in the `backend/api` folder. The API requires the `COLETRA_API_HOST`, `COLETRA_API_PORT`, `SERVERCERT` and `SERVERKEY` environment variables to be set.

2. Run the MODEL with `poetry shell`, `poetry install` and `COLETRA_API_URL=my.api.url:1234 poetry run model` in the `backend/model` folder. The MODEL requires the `COLETRA_API_URL` environment variable to be set.

If you don't want to use poetry shell, but are used to conda (e.g. because you want to switch between python versions easily), you can run them like this:
```shell
pip install pipx
pipx install poetry

# creating the env for api
conda create -n coletra-backend -y python=3.8
conda activate coletra-backend
conda install libgcc=5.2.0 -y
cd backend/api
poetry install

# running the api to be accessible from everywhere
COLETRA_API_HOST=0.0.0.0 COLETRA_API_PORT=1234 poetry run api
# running it in background
COLETRA_API_HOST=0.0.0.0 COLETRA_API_PORT=1234 nohup poetry run api >> run_api.log 2>&1 &
# getting logs
tail backend/api/run_api.log

# creating env for model
conda create -n coletra-backend-model -y python=3.11
conda activate coletra-backend-model
cd backend/model
poetry install
# if you don't have cuda drivers by default
pip install "nvidia-cudnn-cu11<9"
pip install nvidia-cublas-cu12
# find the location of libcublas.so.12 etc by running the following code and use it in your path
find <path of your conda> -name libcublas.so.12
find <path of your conda> -name libcudnn.so.8
# use the path without the filename, you want to point it to the directory
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:path1:path2
# run it on the same machine as the api
COLETRA_API_URL=http://localhost:1234 poetry run model
# running it in background
COLETRA_API_URL=http://localhost:1234 nohup poetry run model >> run_model.log 2>&1 &
# getting logs
tail backend/model/run_model.log
```

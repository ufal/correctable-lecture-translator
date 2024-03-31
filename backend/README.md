# Coletra Backend

## Project setup and run

- SSL certificate is needed to succesfully run the frontend, without it the browser won't be able
to record and send audio (although this can be forced by adding the frontend host domain to a
list using this chromium flag `unsafely-treat-insecure-origin-as-secure`). The paths to the
cert and key files should be passed as environment variables `SERVERCERT` and `SERVERKEY`.

- Setup also requires a backend server to be running, the path to which must be specified as
`COLETRA_API_URL` environment variable. Note that this URL needs to be the same as `API_URL` for the frontend.

- The backend consist of two parts, API and Model. The API is a Flask server that handles audio processing and other functionalities provided by frontend. The Model is a script that is polling API for new audio, running the Whisper model and returning transcriptions to API.

- API requires `Python3.11` and `poetry` package manager installed.
- (Model requires - if not run in docker - from `Python3.8` to `Python3.11` and `poetry` package manager installed.)

- To run the backend:
1. Run the API with `poetry shell`, `poetry install` and `COLETRA_API_HOST=my.api.url COLETRA_API_PORT=1234 SERVERCERT=servercert.pem SERVERKEY=serverkey.pem poetry run api` in the `backend/api` folder. The API requires the `COLETRA_API_HOST`, `COLETRA_API_PORT`, `SERVERCERT` and `SERVERKEY` environment variables to be set.

2. Run the MODEL with `poetry shell`, `poetry install` and `COLETRA_API_URL=my.api.url:1234 poetry run model` in the `backend/model` folder. The MODEL requires the `COLETRA_API_URL` environment variable to be set.

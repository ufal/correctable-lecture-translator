# Coletra Frontend

## Usage

- The frontend is available at the base url which for the ufal deployment is [coletra.ufal.mff.cuni.cz](https://coletra.ufal.mff.cuni.cz). Mind that our system is ran on demand so it might not be available to check out at all times.
- At the base url `/` there is the main viewing UI which allows the user to view the lecture video and the transcript. The transcript can be edited in the editing UI which can be accessed in the main menu.
- Recording UI is available at `/record` and allows the user to record audio and send it to the backend for processing.

## Project setup and run

- SSL certificate is needed to succesfully run the frontend, without it the browser won't be able
to record and send audio (although this can be forced by adding the frontend host domain to a
list using this chromium flag `unsafely-treat-insecure-origin-as-secure`). The paths to the
cert and key files should be passed as environment variables `SERVERCERT` and `SERVERKEY`.

- Setup also requires a backend server to be running, the path to which must be specified as
`API_URL` environment variable.

- Frontend folder contains two "Dockerfiles". One (`BaseDockerfile`) is for dependency installation
and the other (`Dockerfile`) is for running the frontend. First the base image must be built:
`docker build -t coletra-frontend-base:latest -f BaseDockerfile .`. Then the main image can be built
like so: `docker build --build-arg SERVERCERT=path/to/servercert --build-arg SERVERKEY=path/to/serverkey --build-arg API_URL=https://your.api.url.com:1234 -t coletra-frontend .`.

- The frontend can then be run with `docker run -p 443:3000 --rm coletra-frontend`.

Then, the page which is recording will be available on `https://your.api.url.com/record`.

### running on http

If you want to run it on http without SSL, you can run it like this:
```shell
sudo docker build --network host --build-arg API_URL=http://<server domain>:1234 -t coletra-frontend .
sudo docker run -d --name coletra-frontend -p 80:3000 --rm coletra-frontend
```
then see the logs by
```shell
docker logs coletra-frontend
```

In order to have the recording working, you need to allow non-encrypted page to use the microphone

#### on MS Edge

Visit ` edge://flags/#unsafely-treat-insecure-origin-as-secure` and set there `http://<your url>` without the port or `/recording`.

#### on Chrome

Start the chrome with `google-chrome --unsafely-treat-insecure-origin-as-secure=http://<your url>`.

## Compatibility notes

The frontend does not work in firefox right now. Chromium-based browser is recommended.

## Development

- Install dependencies with `npm install`.
- Run the development server with `npm run serve` (don't forget to set the `API_URL` environment variable, `SERVERCERT` and `SERVERKEY` environment variables are optional for development).

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin).

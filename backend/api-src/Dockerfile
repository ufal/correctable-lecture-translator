## BASE DOCKER IMAGE FOR FASTER BUILDS ###

# FROM python:3.11.6-alpine3.18

# # install package manager
# RUN pip install poetry


# # make the 'app' folder the current working directory
# WORKDIR /app

# # copy the project files to the working directory
# COPY . .

# # install project dependencies
# RUN poetry install --only main


### PRODUCTION BUILD ###

FROM crt-api-base:latest

# copy just the implementation files
COPY api .

# install without dependencies since we already installed them in the base image
RUN poetry install --only-root

ENV POETRY_SERVERKEY=serverkey.pem
ENV POETRY_SERVERCERT=servercert.pem

EXPOSE 5003
RUN poetry run start-api
CMD [ ""]

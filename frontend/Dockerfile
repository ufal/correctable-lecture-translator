### PRODUCTION BUILD ###
FROM coletra-frontend-base:latest

COPY  . .

ARG SERVERCERT
ARG SERVERKEY
ARG API_URL

ENV SERVERCERT=$SERVERCERT
ENV SERVERKEY=$SERVERKEY
ENV API_URL=$API_URL

RUN npm run build

EXPOSE 3000
ENTRYPOINT serve -s --cors --ssl-cert $SERVERCERT --ssl-key $SERVERKEY dist
# for http
# ENTRYPOINT serve -s --cors dist

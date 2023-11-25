### BASE DOCKER IMAGE FOR FASTER BUILDS ###

# FROM node:lts-alpine

# RUN apk add --no-cache python3 g++ make

# # install simple http server for serving static content
# RUN npm install -g serve

# # make the 'app' folder the current working directory
# WORKDIR /app

# # copy both 'package.json' and 'package-lock.json' (if available)
# COPY package*.json ./

# # install project dependencies
# RUN npm install --loglevel=error


### PRODUCTION BUILD ###

FROM crt-fe-base:latest

COPY  . .
RUN npm run build

EXPOSE 3000
CMD [ "serve", "-s", "--cors", "--ssl-cert", "servercert.pem", "--ssl-key", "serverkey.pem", "dist"]

FROM node:12-slim


COPY cert /cert

COPY package.json /
COPY package-lock.json /
RUN npm install

COPY app.js /
COPY modules /modules

CMD ['node', 'app.js']
const fs = require('fs');
const http = require('http');
const https = require('https');
const WebSocketServer = require('websocket').server;

const privateKey  = fs.readFileSync('./cert/server.key', 'utf8');
const certificate = fs.readFileSync('./cert/server.cert', 'utf8');

const websocketRouter = require('./modules/websocketRouter.js');
const cliArguments = require('./modules/argParser.js').cliArguments;

const credentials = { key: privateKey, cert: certificate };
const express = require('express');
const bodyParser = require('body-parser');
const log = console.log;

process.on('uncaughtException', function(err) {
	log(`Exception: ${err}`);
	throw err;
});

function gracefulShutdown() {
	console.info('Shutting down...');
	process.exit(0);
}

process.on('SIGTERM', () => {
  console.info('SIGTERM signal received.');
  gracefulShutdown();
});

process.on('SIGINT', () => {
	console.info('SIGINT signal received.');
	gracefulShutdown();
});

app = express();

app.set('cliArguments', cliArguments);

app.use(bodyParser.json())
app.use(function(error, req, res, next) {
	log(`API Request ${req.method} ${req.originalUrl}`);
});

// Routers
const httpRouter = require('./modules/apiRouter.js');
const simControlRouter = require('./modules/simControlRouter.js');

app.use('/', httpRouter);
app.use('/simControl', simControlRouter);


app.use(function(req, res, next) {
	var errMessage = `Not Found: ${req.originalUrl}`;
	log(errMessage);
    res.status(404);
    res.send(errMessage);
});

function startHTTPServer(port) {
	var httpsServer = https.createServer(credentials, app);

	httpsServer.listen(port);
	console.log(`HTTP(s) Server Listening on ${port}`)
}

function statWebSocketServer(ws_port) {
	const httpsServerForWS = https.createServer(credentials);

	httpsServerForWS.listen(ws_port);
	const wsServer = new WebSocketServer({
		httpServer: httpsServerForWS
	});

	wsServer.on('request', function(request) {
		const connection = request.accept(null, request.origin);

		connection.on('message', function(message) {
			new websocketRouter.WebSocketMessageHandler(connection, message);
		});

		connection.on('close', function(reasonCode, description) {
			console.log(`Client has disconnected. code=${reasonCode} description=${description}`);
		});
	});

	console.log(`WebSocket Server Listening on ${ws_port}`)
}


const port = app.get('cliArguments').httpPort;
const ws_port = app.get('cliArguments').wsPort;

startHTTPServer(port);
statWebSocketServer(ws_port);



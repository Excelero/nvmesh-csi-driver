

simLogic = require('./simLogic.js');
exports.WebSocketMessageHandler = class WebSocketMessageHandler {
	constructor(connection, raw_message) {
		this.connection = connection;
		this.message = this.parseJSON(raw_message);
		this.route();
	}

	parseJSON(raw_message) {
		try {
			var msg = JSON.parse(raw_message.utf8Data);
			return msg;
		} catch(err) {
			var wrapError = new Error(`Failed top parse JSON from message data: ${raw_message.utf8Data}. Error: ${err}`)
			throw wrapError;
		}
	}

	route() {
		console.log(`Received WebSocket message route: ${this.message.route}`);
		switch (this.message.route) {
			case '/login':
				this.handleLogin();
				break;
			case '/registerToEvents':
				this.doNothing();
				break;
			case '/registerStatsEvents':
				this.doNothing();
				break;
			default:
				var err = `Management Simulator - message Not Implemented for route: ${this.message.route}`;
				this.sendResponse({ success: false, error: err });
				throw new Error(err);
		}
	}

	doNothing() {}

	handleLogin() {
		var success = simLogic.isUserAuthenticated(this.message.email, this.message.password);
		this.sendResponse({ success: success, error: success ? '' : 'wrong credentials' });
	}

	sendResponse(response) {
		var response_msg = JSON.stringify(response);
		this.connection.sendUTF(response_msg);
	}
}

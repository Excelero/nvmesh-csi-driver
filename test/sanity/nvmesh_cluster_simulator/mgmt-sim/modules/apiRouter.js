const { simulateAttachOnNode, simulateDetachOnNode } = require('./simLogic.js');

express = require('express');
simLogic = require('./simLogic.js');

var router = express.Router();

router.get('/', function(req,res) {
    res.send('Management Simulator for CSI Driver');
});

router.post('/login', function(req,res) {
    var credentials = req.body;
    var success = simLogic.isUserAuthenticated(credentials.username, credentials.password);
    res.json({ success: success, error: success ? '' : 'wrong credentials' });
});

router.get('/isAlive', function(req, res) {
	res.json('Of course I\'m alive..');
});

router.get('/version', function(req, res) {
	res.json("version=\"2.0.2-mgmt-sim\"\ncommit=\"mgmt-sim\"\nchangeID=\"mgmt-sim\"\nbranch=\"HEAD\"\n");
});

router.get('/volumes/all/0/0', function(req,res) {
    var volumes = app.get('sim-data').volumes;
    var listOfVolumes = Object.values(volumes);
    res.json(listOfVolumes);
});

router.post('/volumes/save', function(req,res) {
    var data = app.get('sim-data');
    var volumes = data.volumes;
	var response = [];

    var totalTimeout = 0;
	req.body.forEach(volume => {
        var existingIDs = volumes.map(v => v._id);

        if (existingIDs.indexOf(volume._id) > -1) {
            console.log(`Failed to add volume ${volume._id} - Name already Exists`);
		    response.push({ _id: volume.name, success: false, error: 'Name already Exists' });
        } else if (data.options.availableStorageGB < volume.capacity) {
            console.log(`Failed to add volume ${volume._id} - Not enough space`);
		    response.push({ _id: volume.name, success: false, error: '' });
        } else {
            data.options.availableStorageGB -= volume.capacity;
            console.log(`Adding volume ${volume._id}`);
            volumes[volume._id] = volume;
		    response.push({ _id: volume.name, success: true});

            // simulate allocation duration
            totalTimeout += data.options.volumeCreationDelayMS;
        }
	});

    if (data.options.customResponse && data.options.customResponse.route == '/volumes/save') {
        console.log(`Volume creation - customResponse: ${JSON.stringify(data.options.customResponse)}`);
        return res.status(data.options.customResponse.httpCode).send(data.options.customResponse.response);
    }

    if (totalTimeout > 1000)
        console.log(`Volume creation - waiting ${totalTimeout} before responding`, response);

    return setTimeout(() => {
        console.log(`Volume creation - sending response`, response);
        res.json(response)
    }, totalTimeout);
});

router.post('/volumes/update', function(req,res) {
    var volumes = app.get('sim-data').volumes;
	var response = [];
	req.body.forEach(volume => {
        console.log(`Updating volume ${volume._id}`);
        volumes[volume._id] = volume;
		response.push(successResponse(volume.name));
	});

    res.json(response);
});

router.post('/volumes/delete', function(req,res) {
    var volumes = app.get('sim-data').volumes;
	var response = [];
	req.body.forEach(volume => {
        console.log(`Deleting volume ${volume._id}`);
        delete volumes[volume._id];
		response.push(successResponse(volume.name));
	});

    res.json(response);
});

router.get('/clients/all/0/0', function(req,res) {
    var clients = app.get('sim-data').clients;
    console.log(`request to /clients/all/0/0 returning: ${JSON.stringify(clients)}`);
    res.json(clients);
});

router.post('/clients/attach', async function(req, res) {
    var clients = app.get('sim-data').clients;
    var simVolumes = app.get('sim-data').volumes;

    let payload = req.body;

    console.log(`request to /clients/attach: ${JSON.stringify(payload)}`);

	let { volumes, client: clientID } = payload;
    let responses = [];

    if (!clients[clientID]) {
        responses.push(errorResponse(clientID, `There is no such client ${clientID}`));
        return res.json(responses);
    }

    var asyncCalls = volumes.map(async v => {
        try {
            await simulateAttachOnNode(clientID, v.name);
            responses.push(successResponse(v.name));
        } catch (err) {
            responses.push(errorResponse(v.name, err));
        }
    });

    await Promise.all(asyncCalls);

    console.log(`request to /clients/attach returning: ${JSON.stringify(responses)}`);
    res.json(responses);
});

router.post('/clients/detach', async function(req,res) {
    var clients = app.get('sim-data').clients;
    var simVolumes = app.get('sim-data').volumes;

    let payload = req.body;
	let { volumes, client: clientID } = payload;
    let responses = [];

    if (!clients[clientID]) {
        responses.push(errorResponse(clientID, `There is no such client ${clientID}`));
        return res.json(responses);
    }

    var asyncCalls = volumes.map(async v => {
        try {
            await simulateDetachOnNode(clientID, v.name);
            responses.push(successResponse(v.name));
        } catch (err) {
            responses.push(errorResponse(v.name, err.toString(), err));
        }
    });

    await Promise.all(asyncCalls);
    
    console.log(`request to /clients/detach returning: ${JSON.stringify(responses)}`);
    res.json(responses);
});

router.get('/dbUUID', function(req,res) {
    const dbUUID = app.get('sim-data').dbUUID;
    console.log(`request to /dbUUID returning: ${dbUUID}`);
    res.json({ success: true, dbUUID: dbUUID });
});

router.get('/isAlive', function(req,res) {
    res.send('I\'m still here');
});

function successResponse(id) {
    return { _id: id, success: true, error: null, payload: null };
}

function errorResponse(id, error, payload) {
    return { _id: id, success: false, error: error, payload, payload };
}

module.exports = router;

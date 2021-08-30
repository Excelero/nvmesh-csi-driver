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
		response.push({ _id: volume.name, success: true});
	});

    res.json(response);
});

router.post('/volumes/delete', function(req,res) {
    var volumes = app.get('sim-data').volumes;
	var response = [];
	req.body.forEach(volume => {
        console.log(`Deleting volume ${volume._id}`);
        delete volumes[volume._id];
		response.push({ _id: volume.name, success: true});
	});

    res.json(response);
});

router.get('/clients/all/0/0', function(req,res) {
    var clients = app.get('sim-data').clients;
    res.json(clients);
});

router.get('/dbUUID', function(req,res) {
    const dbUUID = app.get('sim-data').dbUUID;
    console.log(`request to /dbUUID returning: ${dbUUID}`);
    res.json({ success: true, dbUUID: dbUUID });
});

router.get('/isAlive', function(req,res) {
    res.send('I\'m still here');
});

module.exports = router;

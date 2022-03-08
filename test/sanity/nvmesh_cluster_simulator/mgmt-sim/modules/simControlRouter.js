
express = require('express');
var uuid = require('node-uuid');
const { parse } = require('yargs');

var router = express.Router();

const GB = Math.pow(1024, 3);
const TB = Math.pow(1024, 4);

const simData = {
    dbUUID: uuid.v1(),
    targets: [],
    clients: [],
    volumes: [],
    users: [
        { email: 'admin@excelero.com', password: 'admin' },
        { email: 'app@excelero.com', password: 'admin' },
    ],
    options: {
        availableStorageGB: 1 * TB,
        volumeCreationDelayMS: 50,
        customResponse: null
    },
};

function initialize() {
    var args = app.get('cliArguments');
    if (args.clients) {
        args.clients.forEach(clientID => {
            console.log(`Initialization - Adding client ${clientID}`);
            simData.clients.push({ client_id: clientID });
        });
    }

    if (args.options) {
        try{
            var parsedOptions = JSON.parse(args.options);
            updateOptions(parsedOptions);
        } catch (err) {
            console.log(`Failed to parse argument --options with value: '${args.options}' as JSON.  `);
            process.exit(1);
        }

    }

    console.log(`dbUUID: ${simData.dbUUID}`);
}

function updateOptions(newOptions) {
    const options = simData.options;

    // override specific fields
    for (var key in newOptions) {
        console.log(`updating option ${key}=${JSON.stringify(newOptions[key])}`);
        options[key] = newOptions[key];
    }

    return options;
}

initialize();

app.set('sim-data', simData);

router.get('/status', function(req,res) {
    res.json(simData);
});

router.post('/set-options', function(req,res) {
    const newOptions = req.body;
    console.log(`/set-options called with: ${JSON.stringify(newOptions)}`);

    const options = updateOptions(newOptions);
    res.json({ success: true, updatedOptions: options });
});

router.post('/set-storage-gb', function(req,res) {
    var newStorageGB = req.body;
    console.log(`Setting availableStorageGB to ${newStorageGB}`);
    simData.availableStorageGB = newStorageGB;

    res.json(simData);
});


module.exports = router;

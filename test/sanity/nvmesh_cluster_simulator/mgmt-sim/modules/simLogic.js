const path = require('path');
const fs = require('fs');

const GB = 1024 * 1024 * 1024;

exports.isUserAuthenticated = function(email, password) {
	console.log(`isUserAuthenticated called with username=${email} password=${password}`);
    var users = app.get('sim-data').users;
    var user = users.find(u => u.email == email);
    if (!user || user.password != password) {
        console.log(`isUserAuthenticated failed with username=${email} password=${password}`);
        return false
    } else
        return true
};

exports.simulateAttachOnNode = async function(clientID, volumeID) {
  try {
    await createNVMeshDeviceOnNode(clientID, volumeID);
    await createVolumeStatusProcFileOnNode(clientID, volumeID);
  } catch (err){
    console.log(`Error while trying to simulate attach on client: ${clientID} volume: ${volumeID} Error: ${err}`);
    return err
  }
};

async function createFile(dir, fileName, data) {
  await fs.promises.mkdir(dir, { recursive: true });

  const filePath = path.join(dir, fileName);
  await fs.promises.writeFile(filePath, data);

  console.log('file ' + filePath + ' is created successfully.');
}

async function createNVMeshDeviceOnNode(clientID, volumeID) {
  const devPath = '/tmp/csi_sanity/' + clientID + '/dev/nvmesh/';
  await fs.promises.mkdir(devPath, { recursive: true });

  const filePath = path.join(devPath, volumeID);
  await createEmptyFileOfSize(filePath, 1*GB);
}

async function createVolumeStatusProcFileOnNode(clientID, volumeID) {
  const volumeProcDir = '/tmp/csi_sanity/' + clientID + '/proc/nvmeibc/volumes/' + volumeID;

  var volStatus = {
    'dbg': '0x200', // IO Enabled
    'status': 'IO Enabled'
  };

  const customStatus = app.get('sim-data').options.volumeStatusProcContent;

  if (customStatus) {
    console.log('Setting custom volume status.json content of', customStatus);
    volStatus = customStatus;
  }

  await createFile(volumeProcDir, 'status.json', JSON.stringify(volStatus));
}

exports.simulateDetachOnNode = async function(clientID, volumeID) {
  return new Promise((resolve, reject) => {
    const devicePath = path.join('/tmp/csi_sanity/', clientID,'dev/nvmesh/', volumeID);
    fs.unlink(devicePath, err => {
      if (err) return reject(err);
      const volumeProcDir =  path.join('/tmp/csi_sanity/', clientID, 'proc/nvmeibc/volumes', volumeID, 'status.json');
      fs.unlink(volumeProcDir, err => {
        if (err) return reject(err);
        resolve();
      });
    });
  });
};

const createEmptyFileOfSize = (fileName, size) => {
  return new Promise((resolve, reject) => {
      fs.open(fileName, 'w', (err, fd) => {
          if (err) return reject(err);
          fs.write(fd, 'ok', Math.max(0, size - 2), err => {
              fs.close(fd, closeErr => {
                if (err) return reject(err);
                resolve(true);
              });
          });
      });
  });
};

exports.registerToEvents = function(events, callback) {
  const emitter = app.get('eventEmitter')
  events.forEach(e => {
    emitter.on(e, callback);
  });
};
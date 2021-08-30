const yargs = require('yargs/yargs')
const { hideBin } = require('yargs/helpers')

const argv = yargs(hideBin(process.argv))
  .option('http-port', {
    type: 'int',
    description: 'HTTP API server port',
    default: 4000
  })
  .option('ws-port', {
    type: 'int',
    description: 'WebSocket server port',
    default: 4001
  })
  .option('clients', {
    type: 'array',
    description: 'A list of clientIDs',
  })
  .option('options', {
    type: 'string',
    description: 'additional options as Json',
  })
  .argv

exports.cliArguments = argv;

const Validator = require('jsonschema').Validator;
var v = new Validator();



var obj = {
    "client":"node-1",
    "volumes":[
        {
            "name":"vol_1",
            "reservation":{
                "preempt":false,
                "mode":"SHARED_READ_ONLY"
            }
        }
    ]
};

var schema = {
    'type': 'object',
    required: ['volumes'],
    properties: {
        volumes: {
            type: 'array',
            items: {
                type: 'object',
                required: ['reservation'],
                properties: {
                    reservation: {
                        type: 'object',
                        properties: {
                            preempt: { 
                                enum: [ true ]
                            }
                        }
                    }
                },
            }
        },
    }
};


console.log(v.validate(obj, schema));
const Validator = require('jsonschema').Validator;

exports.schemaValidatorMiddleware = function(req, res, next) {
    const url = req.url;
    const schemas = app.get('sim-data').options.schemas;

    if (!(url in schemas))
        return next();

    const schema = schemas[url];
    console.log(`found schema for url ${url}. typeof(schema) == ${typeof(schema)} schema: ${JSON.stringify(schema)}`);
    var v = new Validator();
    console.log(`schema validation for obj: ${JSON.stringify(req.body)}`);

    const result = v.validate(req.body, schema);
    console.log(`schema validation result: ${JSON.stringify(result.errors)}`);
    
    if (result.errors.length)
        return res.json({'error': 'Schema errors', schemaResult: result});

    next();
};

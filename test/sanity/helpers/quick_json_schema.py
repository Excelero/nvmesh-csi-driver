import json


class JSONSchemaBuilder(object):
    def __init__(self):
        self.schema = {}

    def validate_obj_value(self, field, value):
        '''
        nested fields can be noted as 'volumes[].reservation.preempt' where volume is an array, reservation is an object and preempt is the field to validate
        value is expected in JSON schema format such as: { 'type': 'string' }  or { enum: [ true ] }

        This will not handle json keys with dots (.) in them
        '''
        schema = {
            'type': 'object'
        }
        JSONSchemaBuilder._from_dot_notation(schema, field, value)
        self.merge_to_schema(self.schema, schema)

    @staticmethod
    def _from_dot_notation(schema, field, value):
        if not '.' in field:
            # we have a simple rule
            schema[field] = value
            return

        field_parts = field.split('.')

        key = field_parts[0]
        if 'properties' not in schema:
            schema['properties'] = {}

        properties = schema['properties']
        if '[]' in key:
            key = key[:-2]
            properties[key] = {
                'type': 'array',
                'items': {}
            }
            child_schema = properties[key]['items']
        else:
            properties[key] = {
                'type': 'object',
                'properties': {}
            }
            child_schema = properties[key]['properties']

        schema['required'] = [key]
        JSONSchemaBuilder._from_dot_notation(child_schema, '.'.join(field_parts[1:]), value)

    def merge_to_schema(self, base, schema):
        try:
            for key in schema.keys():
                field = schema[key]
                if key not in base:
                    base[key] = schema[key]
                    continue

                if type(field) == list:
                    for item in field:
                        if item not in base[key]:
                            base[key].append(item)
                elif type(field) == dict:
                    self.merge_to_schema(base[key], schema[key])
                else:
                    print('overriding value for %s' % key)
                    base[key] = schema[key]

        except Exception as ex:
            print('{}: {} base: {}  schema: {}'.format(ex.__class__.__name__, str(ex), base, schema))
            raise


    def __str__(self):
        return json.dumps(self.get_schema())

    def get_schema(self):
        return self.schema


if __name__ == '__main__':
    b = JSONSchemaBuilder()

    b.validate_obj_value('volumes[].reservation.preempt', {'enum': True})
    b.validate_obj_value('volumes[].name', {'enum': 'vol1'})
    b.validate_obj_value('success', {'enum': True})

    res = b.get_schema()
    print(res)

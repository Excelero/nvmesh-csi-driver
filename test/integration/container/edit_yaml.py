import argparse
import yaml

parser = argparse.ArgumentParser()
parser.add_argument('-u','--update', help='inplace update', required=True)
parser.add_argument('-f','--file', help='file name', required=True)
args = parser.parse_args()

with open(args.file) as fp:
    data = yaml.safe_load(fp.read())

field_path, value = args.update.split('=')
fields = field_path.split('.')

data_path = data
print(data_path)
for f in fields[1:-1]:
    data_path = data_path[f.strip()]

key = fields[-1].strip()
data_path[key] = value.strip()

with open(args.file, 'w') as fp:
    yaml.dump(data, fp, sort_keys=True)
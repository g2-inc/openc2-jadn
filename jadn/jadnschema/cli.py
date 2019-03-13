import argparse
import cbor2
import json
import os
import sys

from .codec.codec import Codec
from . import (
    jadn
)

instance_exts = {
    'cbor': lambda f: cbor2.load(f),
    'json': lambda f: json.load(f)
}


def schema_file(path):
    fname, ext = os.path.splitext(path)
    if ext == '.jadn':
        try:
            with open(path, 'r') as f:
                return dict(
                    path=path,
                    schema=json.load(f)
                )
        except Exception as e:
            pass
    raise TypeError("Invalid instance given")


def instance_file(path):
    fname, ext = os.path.splitext(path)
    ext = ext[1:]

    if ext in instance_exts:
        try:
            with open(path, 'rb') as f:
                return dict(
                    path=path,
                    instance=instance_exts[ext](f)
                )
        except Exception as e:
            pass

    raise TypeError("Invalid schema given")


parser = argparse.ArgumentParser(description="JADN Schema Validation CLI")

parser.add_argument(
    "-i", "--instance",
    action="append",
    dest="instance",
    type=instance_file,
    help=f"JSON instance to validate (i.e. filename.[{','.join(instance_exts.keys())}])(may be specified multiple times)",
)

parser.add_argument(
    "schema",
    help="JADN Schema to validate with (i.e. filename.jadn)",
    type=schema_file,
)


def validate_msg(codec, _types, msg):
    valid = {}
    for t in _types:
        try:
            codec.decode(t, msg)
            valid[t] = True
        except (ValueError, TypeError) as e:
            # print(f'{e}\n')
            valid[t] = False
    return valid


def main(args=sys.argv[1:]):
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    sys.exit(run(args=arguments))


def run(args, stdout=sys.stdout, stderr=sys.stderr):
    jadn_analysis = jadn.jadn_analyze(args['schema']['schema'])

    if len(jadn_analysis['undefined']):
        stderr.write(f"Invalid Schema, {len(jadn_analysis['undefined'])} undefined types:\n")
        stderr.write(', '.join(jadn_analysis['undefined']) + '\n')
        exit(1)
    else:
        stdout.write(f"Valid schema at {args['schema']['path']}\n")

    codec = None
    try:
        codec = Codec(args['schema']['schema'], True, True)
    except Exception as e:
        stderr.write(f"Schema Error: {e}\n")
        exit(1)

    if len(args['instance']) > 0:
        stdout.write(f"\nValidating using schema at {args['schema']['path']}\n")
        exports = args['schema']['schema'].get('meta', {}).get('exports', [])

        for instance in args['instance']:
            path = instance['path']
            valid = validate_msg(codec, exports, instance['instance'])

            if any(valid.values()):
                val_types = ', '.join({k: v for k, v in valid.items() if v}.keys())
                stdout.write(f"Instance '{path}' is valid as {val_types}\n")
            else:
                stderr.write(f"Instance '{path}' is invalid\n")

    return ''

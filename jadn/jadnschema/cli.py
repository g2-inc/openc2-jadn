import argparse
import os
import sys

from . import (
    base,
    enums,
    jadn
)
from .convert.message import Message


def schema_file(path):
    fname, ext = os.path.splitext(path)
    schema = None

    if ext == '.jadn':
        try:
            schema = jadn.jadn_load(path)
        except (IOError, TypeError, ValueError) as e:
            raise TypeError("Invalid instance given")

    return dict(
        path=path,
        schema=schema
    )


def instance_file(path):
    fname, ext = os.path.splitext(path)
    ext = ext[1:]

    if ext in enums.MessageFormats.values():
        try:
            return dict(
                path=path,
                instance=Message(path, ext)
            )
        except (IOError, TypeError, ValueError) as e:
            pass

    raise TypeError("Invalid schema given")


parser = argparse.ArgumentParser(description="JADN Schema Validation CLI")

parser.add_argument(
    "-i", "--instance",
    action="append",
    dest="instance",
    type=instance_file,
    help=f"instance to validate (i.e. filename.[{','.join(enums.MessageFormats.values())}])(may be specified multiple times)",
)

parser.add_argument(
    "schema",
    help="JADN Schema to validate with (i.e. filename.jadn)",
    type=schema_file,
)


def main(args=sys.argv[1:]):
    arguments = vars(parser.parse_args(args=args or ["--help"]))
    sys.exit(run(args=arguments))


def run(args, stdout=sys.stdout, stderr=sys.stderr):
    schema = base.validate_schema(args.get('schema', {}).get('schema', {}))

    if schema and isinstance(schema, list):
        for err in schema:
            stderr.write(f'{err}\n')
        exit(1)
    elif schema:
        stdout.write(f"Valid schema at {args.get('schema', {}).get('path', '')}\n")

    if len(args['instance']) > 0:
        for instance in args['instance']:
            stdout.write(f"\nValidating instance at {instance.get('path', '')} using schema at {args.get('schema', {}).get('path', '')}\n")
            val_msg = base.validate_instance(schema, instance.get('instance', {}))
            if isinstance(val_msg, list):
                for err in val_msg:
                    stdout.write(f"{err}\n")
            elif isinstance(val_msg, tuple):
                stdout.write(f"Instance '{instance.get('path', '')}' is valid as {val_msg[1]}\n")

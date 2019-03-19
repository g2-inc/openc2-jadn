import os

from jadnschema import jadn_load, MessageFormats, validate_schema, validate_instance
from jadnschema.convert import Message

msgs = {}
dir = './message/'

print("Load Messages")
for msg_file in os.listdir(dir):
    if msg_file.startswith(('.', '_')): continue

    n, t = msg_file.split('.')
    k = "{}-{}".format(t, n)
    msgs[k] = t, Message(os.path.join(dir, msg_file), MessageFormats.get(t.upper()))

print("Load Schema")
schema = jadn_load('schema/oc2ls-csdpr02.jadn')

print("Validate Messages\n")
for n, tup in msgs.items():
    t, o = tup
    print(n)

    print("{}_dumps -> {}\n".format(t, getattr(o, f"{t}_dumps", lambda: 'N/A')()))
    if t != 'json':
        print("json_dumps -> {}\n".format(o.json_dumps()))

    msg = validate_instance(schema, o.json_dumps())
    print("Decoded Msg -> {}\n\n".format(msg))

# JADN Schema
JSON Abstract Data Notation (JADN) is a language-neutral, platform-neutral,
and format-neutral mechanism for serializing structured data.  See [docs](docs/jadn-overview.md) for
information about the JADN language.

## Examples
- Python
```python
# EDIT ME FOR PROPER USAGE
from jadnschema import validate

# A sample schema, like what we'd get from json.load()
schema = {
    "type" : "object",
    "properties" : {
        "price" : {"type" : "number"},
        "name" : {"type" : "string"},
    },
}

# If no exception is raised by validate(), the instance is valid.
validate(
    schema=schema,
    instance={"name" : "Eggs", "price" : 34.99}
)

validate(
    schema=schema,
    instance={"name" : "Eggs", "price" : "Invalid"}
)
```

- Console    
```bash
jadnschema sample.jadn -i sample.json -i sample_1.json
```

## Features
- Supporting Python version 3.6+
- Console support
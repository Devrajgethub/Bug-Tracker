import pydantic
print(f"Pydantic Version: {pydantic.VERSION}")
try:
    from pydantic import field_validator
    print("field_validator imported successfully")
except ImportError:
    print("field_validator NOT found in pydantic")

try:
    from pydantic import ConfigDict
    print("ConfigDict imported successfully")
except ImportError:
    print("ConfigDict NOT found in pydantic")

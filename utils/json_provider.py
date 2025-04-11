# utils/json_provider.py
import json
from datetime import datetime
from pydantic import BaseModel
from pydantic_core import Url
from flask.json.provider import JSONProvider # Correct import for Flask >= 2.3

class CustomJSONProvider(JSONProvider):
    """
    Custom JSON Provider for Flask that knows how to serialize
    Pydantic models, HttpUrl, and datetime objects.
    """
    def default(self, obj):
        """Define custom serialization logic."""
        if isinstance(obj, BaseModel):
            # Use Pydantic's method to get JSON-serializable dict/list
            return obj.model_dump(mode='json')
        if isinstance(obj, Url):
            # Convert pydantic_core.Url (used by HttpUrl) to string
            return str(obj)
        if isinstance(obj, datetime):
            # Format datetime objects as ISO 8601 strings
            return obj.isoformat()
        # --- No need for super().default(obj) here ---
        # If none of the above match, the encoder's default will handle it.
        # We just need to ensure the encoder uses this logic first.

    def dumps(self, obj, **kwargs):
        """Serialize object to JSON string, ensuring correct encoding and defaults."""
        kwargs.setdefault('ensure_ascii', False)
        # Pass our custom default function directly to json.dumps
        kwargs.setdefault('default', self.default)
        return json.dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        """Deserialize JSON string to Python object."""
        return json.loads(s, **kwargs)

    # --- Removed the problematic _get_encoder_cls() method ---
    # We pass self.default directly to json.dumps now.
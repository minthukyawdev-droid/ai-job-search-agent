import json
import re
from collections.abc import Iterable


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}")


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def list_to_csv(values: Iterable[str]) -> str:
    return ", ".join(dict.fromkeys(v.strip() for v in values if v and v.strip()))


def tags_from_storage(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return split_csv(value)


def tags_to_storage(values: Iterable[str]) -> str:
    return json.dumps(list(dict.fromkeys(v.strip() for v in values if v and v.strip())))


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text or "")]


def normalize_text(*parts: str | None) -> str:
    return " ".join(part for part in parts if part)

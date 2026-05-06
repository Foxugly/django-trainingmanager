"""JSON formatter for the prod log handler.

Hand-rolled to avoid pulling in python-json-logger for what amounts to
30 lines. Matches the field names that most observability stacks
(Datadog / GCP Cloud Logging / ELK) auto-detect: `timestamp`, `level`,
`logger`, `message`, plus `exc_info` and `stack_info` when relevant.
"""

import json
import logging


class JsonFormatter(logging.Formatter):
    """Serialise a LogRecord as a single-line JSON object.

    No batching, no buffering — one record = one line, which is what
    every line-oriented log shipper expects.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(payload, ensure_ascii=False)

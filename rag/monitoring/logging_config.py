import os
import json
import logging
import logging.config
from datetime import datetime

def setup_logging(log_level: str = None, log_to_file: bool = True, log_dir: str = "logs") -> logging.Logger:
    """
    Configures structured JSON logging for the application.
    Returns the root logger.
    """
    level = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    numeric_level = getattr(logging, level, logging.INFO)

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        }
    }

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)
        log_filename = os.path.join(log_dir, f"compliance_copilot_{datetime.now().strftime('%Y%m%d')}.log")
        handlers["file"] = {
            "class": "logging.FileHandler",
            "filename": log_filename,
            "formatter": "json",
            "encoding": "utf-8",
        }

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "json": {
                "()": "logging.Formatter",
                "fmt": '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
            }
        },
        "handlers": handlers,
        "root": {
            "level": numeric_level,
            "handlers": list(handlers.keys()),
        },
    }

    logging.config.dictConfig(config)
    logger = logging.getLogger("compliance_copilot")
    logger.info(f"Logging initialized. Level={level}, log_to_file={log_to_file}")
    return logger


class QueryMetricsLogger:
    """
    Records per-query metrics: latency, number of chunks retrieved, sources, and whether a violation was detected.
    """
    def __init__(self):
        self.logger = logging.getLogger("compliance_copilot.metrics")

    def log_query(
        self,
        query: str,
        latency_ms: float,
        num_chunks: int,
        sources: list,
        is_violation: bool,
        llm_provider: str = "unknown"
    ):
        record = {
            "event": "query",
            "query": query[:200],  # truncate for safety
            "latency_ms": round(latency_ms, 2),
            "chunks_retrieved": num_chunks,
            "sources": [s.get("source", "?") for s in sources],
            "violation_detected": is_violation,
            "llm_provider": llm_provider,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.logger.info(json.dumps(record))

    def log_ingestion(self, num_files: int, num_chunks: int, duration_ms: float):
        record = {
            "event": "ingestion",
            "files_processed": num_files,
            "chunks_generated": num_chunks,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        self.logger.info(json.dumps(record))

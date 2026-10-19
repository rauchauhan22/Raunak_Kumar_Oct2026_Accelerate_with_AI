import logging
import os

os.makedirs("traces", exist_ok=True)

logger = logging.getLogger("pipeline")
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler("traces/pipeline.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def log_event(run_id, phase, status, message=""):
    """Record a pipeline phase event to traces/pipeline.log and the console."""
    logger.info(f"run_id={run_id} phase={phase} status={status} {message}".strip())

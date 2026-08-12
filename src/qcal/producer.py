"""Bounded deterministic Event Hubs telemetry producer."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from azure.eventhub import EventData, EventHubProducerClient


class Producer(Protocol):
    def create_batch(self) -> Any: ...

    def send_batch(self, batch: Any) -> None: ...

    def close(self) -> None: ...


def _default_factory(connection_string: str, event_hub_name: str) -> Producer:
    return EventHubProducerClient.from_connection_string(
        conn_str=connection_string, eventhub_name=event_hub_name
    )


def emit_bounded_telemetry(
    *,
    connection_string: str,
    event_hub_name: str,
    source_path: Path,
    message_limit: int,
    receipt_path: Path,
    producer_factory: Callable[[str, str], Producer] = _default_factory,
) -> dict[str, Any]:
    """Emit exactly ``message_limit`` valid JSON lines and write a sanitized receipt."""

    if not connection_string.strip():
        raise ValueError("connection_string is required")
    if not event_hub_name.strip():
        raise ValueError("event_hub_name is required")
    if message_limit <= 0:
        raise ValueError("message_limit must be positive")
    source_bytes = source_path.read_bytes()
    lines = source_bytes.splitlines()
    if len(lines) < message_limit:
        raise ValueError(
            f"source contains {len(lines)} messages but {message_limit} were requested"
        )

    started_at = datetime.now(UTC)
    producer = producer_factory(connection_string, event_hub_name)
    attempted = 0
    emitted = 0
    batch = producer.create_batch()
    pending_count = 0
    try:
        for raw_line in lines[:message_limit]:
            parsed = json.loads(raw_line)
            if not isinstance(parsed, dict) or "event_id" not in parsed:
                raise ValueError("each telemetry message must be a JSON object with event_id")
            event = EventData(raw_line.decode("utf-8"))
            attempted += 1
            try:
                batch.add(event)
                pending_count += 1
            except ValueError:
                if pending_count == 0:
                    raise
                producer.send_batch(batch)
                emitted += pending_count
                batch = producer.create_batch()
                batch.add(event)
                pending_count = 1
        if pending_count:
            producer.send_batch(batch)
            emitted += pending_count
    finally:
        producer.close()

    if emitted != message_limit:
        raise RuntimeError(f"expected to emit {message_limit} events; emitted {emitted}")
    completed_at = datetime.now(UTC)
    receipt = {
        "schema": "part4-event-hubs-producer-receipt/v1",
        "seed": 20260812,
        "event_hub_name": event_hub_name,
        "source_file": source_path.name,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "events_attempted": attempted,
        "events_emitted": emitted,
        "started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at_utc": completed_at.isoformat().replace("+00:00", "Z"),
        "bounded": True,
        "connection_material_included": False,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt

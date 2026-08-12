import json
from pathlib import Path

from qcal.producer import emit_bounded_telemetry


class FakeBatch:
    def __init__(self, capacity: int = 3) -> None:
        self.capacity = capacity
        self.events = []

    def add(self, event) -> None:
        if len(self.events) >= self.capacity:
            raise ValueError("batch full")
        self.events.append(event)


class FakeProducer:
    def __init__(self) -> None:
        self.sent = []
        self.closed = False

    def create_batch(self) -> FakeBatch:
        return FakeBatch()

    def send_batch(self, batch: FakeBatch) -> None:
        self.sent.extend(batch.events)

    def close(self) -> None:
        self.closed = True


def test_producer_emits_exact_bound_and_never_writes_connection_material(tmp_path: Path) -> None:
    source = tmp_path / "events.jsonl"
    source.write_text(
        "".join(json.dumps({"event_id": f"EVT-{index:03d}"}) + "\n" for index in range(10)),
        encoding="utf-8",
    )
    receipt_path = tmp_path / "receipt.json"
    producer = FakeProducer()

    receipt = emit_bounded_telemetry(
        connection_string="Endpoint=sb://private-value/;SharedAccessKey=private-value",
        event_hub_name="quality-telemetry",
        source_path=source,
        message_limit=7,
        receipt_path=receipt_path,
        producer_factory=lambda _connection, _event_hub: producer,
    )
    public_text = receipt_path.read_text(encoding="utf-8")

    assert receipt["events_attempted"] == 7
    assert receipt["events_emitted"] == 7
    assert len(producer.sent) == 7
    assert producer.closed is True
    assert "private-value" not in public_text
    assert "SharedAccessKey" not in public_text

import json
from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "localhost:19092",
    "group.id": "debug-reader",
    "auto.offset.reset": "latest",
})
c.subscribe(["upi.public.transactions"])
print("Listening... press Ctrl+C to stop")

try:
    while True:
        msg = c.poll(1.0)
        if msg is None or msg.error():
            continue
        e = json.loads(msg.value())
        row = e["after"]
        print(f"op={e['op']} user={row['user_id']} "
              f"amount={row['amount']} device={row['device_id']}")
finally:
    c.close()
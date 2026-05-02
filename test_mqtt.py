#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import json

received_count = 0
messages = []

def on_message(client, userdata, msg):
    global received_count, messages
    received_count += 1
    try:
        payload = json.loads(msg.payload.decode())
        messages.append({"topic": msg.topic, "payload": payload})
        print(f"[{received_count}] {msg.topic}: precision={payload.get('precision_pct', '?')}")
    except:
        print(f"[{received_count}] {msg.topic}")

def on_connect(client, userdata, flags, rc, properties=None):
    print(f'Connected')
    client.subscribe("pixartek/#")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect('192.168.86.243', 1883, 60)
client.loop_start()

print("Listening for MQTT messages from vision node (15 seconds)...")
time.sleep(15)
client.loop_stop()
print(f"Total messages received: {received_count}")

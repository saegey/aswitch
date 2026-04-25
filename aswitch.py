import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import os


AUDIO_PIN = 17
TRIGGER_PIN = 27

MQTT_HOST = os.environ.get('MQTT_HOST', 'localhost')
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60
MQTT_USERNAME = os.environ.get('MQTT_USER')
MQTT_PASSWORD = os.environ.get('MQTT_PASS')

AUDIO_COMMAND_TOPIC = "aswitch/audio"
AUDIO_STATE_TOPIC = "aswitch/audio/state"
TRIGGER_COMMAND_TOPIC = "aswitch/trigger"
TRIGGER_STATE_TOPIC = "aswitch/trigger/state"

# Relay boards are active opposite from the original assumption.
AUDIO_DAC = GPIO.HIGH
AUDIO_MIXER = GPIO.LOW

TRIGGER_ON = GPIO.HIGH
TRIGGER_OFF = GPIO.LOW


def normalize_payload(payload):
    return payload.decode(errors="ignore").strip().lower()


def publish_state(client, topic, state):
    info = client.publish(topic, state, retain=True)
    print(f"Published {topic} -> {state} (mid={info.mid})", flush=True)


def current_audio_state():
    return "dac" if GPIO.input(AUDIO_PIN) == AUDIO_DAC else "mixer"


def current_trigger_state():
    return "on" if GPIO.input(TRIGGER_PIN) == TRIGGER_ON else "off"


def set_audio(client, source, publish=True):
    if source not in {"dac", "mixer"}:
        print(f"Ignoring invalid audio command: {source}", flush=True)
        return

    current = current_audio_state()
    if current == source:
        print(f"Audio already {source}", flush=True)
        if publish:
            publish_state(client, AUDIO_STATE_TOPIC, current)
        return

    target = AUDIO_DAC if source == "dac" else AUDIO_MIXER
    GPIO.output(AUDIO_PIN, target)
    new_state = current_audio_state()
    print(f"Audio changed: {current} -> {new_state}", flush=True)
    if publish:
        publish_state(client, AUDIO_STATE_TOPIC, new_state)


def set_trigger(client, state, publish=True):
    if state not in {"on", "off"}:
        print(f"Ignoring invalid trigger command: {state}", flush=True)
        return

    current = current_trigger_state()
    if current == state:
        print(f"Trigger already {state}", flush=True)
        if publish:
            publish_state(client, TRIGGER_STATE_TOPIC, current)
        return

    target = TRIGGER_ON if state == "on" else TRIGGER_OFF
    GPIO.output(TRIGGER_PIN, target)
    new_state = current_trigger_state()
    print(f"Trigger changed: {current} -> {new_state}", flush=True)
    if publish:
        publish_state(client, TRIGGER_STATE_TOPIC, new_state)


def apply_safe_defaults(client=None, publish=False):
    GPIO.output(AUDIO_PIN, AUDIO_MIXER)
    GPIO.output(TRIGGER_PIN, TRIGGER_OFF)
    print("Applied safe defaults: audio=mixer, trigger=off", flush=True)

    if client is not None and publish:
        publish_state(client, AUDIO_STATE_TOPIC, current_audio_state())
        publish_state(client, TRIGGER_STATE_TOPIC, current_trigger_state())


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected to MQTT: reason_code={reason_code}", flush=True)
    client.subscribe(AUDIO_COMMAND_TOPIC)
    client.subscribe(TRIGGER_COMMAND_TOPIC)
    publish_state(client, AUDIO_STATE_TOPIC, current_audio_state())
    publish_state(client, TRIGGER_STATE_TOPIC, current_trigger_state())


def on_message(client, userdata, msg):
    payload = normalize_payload(msg.payload)
    print(f"Incoming {msg.topic} -> {payload}", flush=True)

    if msg.topic == AUDIO_COMMAND_TOPIC:
        set_audio(client, payload)
    elif msg.topic == TRIGGER_COMMAND_TOPIC:
        set_trigger(client, payload)


def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(AUDIO_PIN, GPIO.OUT, initial=AUDIO_MIXER)
    GPIO.setup(TRIGGER_PIN, GPIO.OUT, initial=TRIGGER_OFF)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Shutting down", flush=True)
    finally:
        apply_safe_defaults(client, publish=False)
        GPIO.cleanup()


if __name__ == "__main__":
    main()

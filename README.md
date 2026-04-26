# Audio Switch Deploy

This repo contains the Raspberry Pi MQTT relay listener, a USB audio activity detector with optional WAV recording, and a simple SSH deploy flow.

## Files

- `aswitch.py`: relay control service
- `audio_activity.py`: USB audio RMS detector that publishes MQTT state and can record WAV files
- `deploy/aswitch.service`: `systemd` unit for relay control
- `deploy/audio_activity.service`: `systemd` unit for audio activity detection
- `deploy/deploy.sh`: pushes files over SSH, installs Python deps, and restarts the service

The deploy script creates or reuses a virtual environment at `/home/<user>/aswitch/.venv` on the Pi and installs dependencies there, avoiding Raspberry Pi OS's externally managed system Python restriction.

## Assumptions

- The Pi is reachable as `aswitch.local`
- SSH works for `saegey@aswitch.local`
- The remote user can run `sudo systemctl ...`
- Python 3 with `venv` support is installed on the Pi

## Deploy

```bash
chmod +x deploy/deploy.sh
./deploy/deploy.sh
```

Deploy the audio activity service:

```bash
ASWITCH_SERVICE=audio_activity.service \
ASWITCH_SERVICE_TEMPLATE=audio_activity.service \
./deploy/deploy.sh
```

You can override defaults with environment variables:

```bash
ASWITCH_HOST=aswitch.local \
ASWITCH_USER=saegey \
ASWITCH_REMOTE_DIR=/home/saegey/aswitch \
ASWITCH_SERVICE=aswitch.service \
./deploy/deploy.sh
```

## Audio Activity Detector

The detector listens to `plughw:CARD=CODEC,DEV=0`, computes RMS across stereo input, and publishes:

- Retained state topic: `aswitch/audio_activity/state`
- Debug RMS topic: `aswitch/audio_activity/rms`
- Recording command topic: `aswitch/audio_recording/set`
- Retained recording state topic: `aswitch/audio_recording/state`
- Retained current file topic: `aswitch/audio_recording/file`
- Recording error topic: `aswitch/audio_recording/error`

Current defaults in [audio_activity.py](/Users/saegey/Projects/aswitch/audio_activity.py):

- `RMS_THRESHOLD = 0.01`
- `ACTIVE_HOLD_SECONDS = 2.0`
- `INACTIVE_HOLD_SECONDS = 300.0`

Tune those constants on the Pi if needed for your mixer output level.

Recording defaults in [audio_activity.py](/Users/saegey/Projects/aswitch/audio_activity.py):

- `RECORDINGS_DIR = /home/saegey/aswitch/recordings`
- `RECORDING_ATTENUATION_DB = 0.0`
- `BLOCKSIZE = 8192`
- `STREAM_LATENCY = "high"`

## Install Notes

System packages on Raspberry Pi OS:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev libportaudio2 portaudio19-dev libasound2-dev
```

Python packages:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create `/home/saegey/aswitch/.env` on the Pi:

```bash
cat > /home/saegey/aswitch/.env <<'EOF'
MQTT_HOST=homeassistant.local
MQTT_USER=your-user
MQTT_PASS=your-password
AUDIO_DEVICE=plughw:CARD=CODEC,DEV=0
RECORDINGS_DIR=/home/saegey/aswitch/recordings
RECORDING_ATTENUATION_DB=-6.0
EOF
```

## Home Assistant Example

```yaml
mqtt:
  binary_sensor:
    - name: "Mixer Audio Activity"
      unique_id: "aswitch_mixer_audio_activity"
      state_topic: "aswitch/audio_activity/state"
      payload_on: "active"
      payload_off: "inactive"
      device_class: sound
      availability_mode: latest

  sensor:
    - name: "Mixer Audio RMS"
      unique_id: "aswitch_mixer_audio_rms"
      state_topic: "aswitch/audio_activity/rms"
      state_class: measurement
      icon: "mdi:waveform"

    - name: "Mixer Recording File"
      unique_id: "aswitch_mixer_recording_file"
      state_topic: "aswitch/audio_recording/file"
      icon: "mdi:file-wave"

  switch:
    - name: "Mixer Recording"
      unique_id: "aswitch_mixer_recording"
      command_topic: "aswitch/audio_recording/set"
      state_topic: "aswitch/audio_recording/state"
      payload_on: "on"
      payload_off: "off"
      icon: "mdi:record-rec"
```

Tracked automation example for amp auto-power:

- [home_assistant/amp_automation.yaml](/Users/saegey/Projects/aswitch/home_assistant/amp_automation.yaml)
- [home_assistant/shairport_sync_example.yaml](/Users/saegey/Projects/aswitch/home_assistant/shairport_sync_example.yaml)

Replace `media_player.your_streaming_box` with your actual Home Assistant media player entity before importing it.

## Check Status On The Pi

```bash
ssh saegey@aswitch.local
sudo systemctl status aswitch.service
sudo systemctl status audio_activity.service
journalctl -u aswitch.service -f
journalctl -u audio_activity.service -f
```

# Audio Switch Deploy

This repo contains the Raspberry Pi MQTT relay listener plus a simple SSH deploy flow.

## Files

- `aswitch.py`: the service script
- `deploy/aswitch.service`: the `systemd` unit installed on the Pi
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

You can override defaults with environment variables:

```bash
ASWITCH_HOST=aswitch.local \
ASWITCH_USER=saegey \
ASWITCH_REMOTE_DIR=/home/saegey/aswitch \
ASWITCH_SERVICE=aswitch.service \
./deploy/deploy.sh
```

## Check Status On The Pi

```bash
ssh saegey@aswitch.local
sudo systemctl status aswitch.service
journalctl -u aswitch.service -f
```

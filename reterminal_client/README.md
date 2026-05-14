# Reterminal E1002 transit display client

Polls the Flask map server every 60 s and shows the resulting 800×480
PNG fullscreen.

## What to copy to the device

You only need two files on the Reterminal:

- `display.py`           — the polling loop
- `transit-display.service` — systemd unit (optional, for autostart)

Suggested install path: `/opt/transit-display/display.py`.

## One-time setup on the Reterminal

```bash
sudo apt update
sudo apt install -y python3-requests feh  # or: fbi, if you don't have X
sudo mkdir -p /opt/transit-display
sudo cp display.py /opt/transit-display/
```

Find the IP of the machine running the Flask server (e.g. `192.168.1.42`),
then test the network path:

```bash
curl -o /tmp/test.png "http://192.168.1.42:5000/image?mode=full"
```

## Two ways to display the image

### Option A — `feh` (you have a desktop / X server)

`feh` can watch a file and reload it automatically. Easiest setup:

```bash
# Terminal 1: keep feh up, watching the file
feh --fullscreen --hide-pointer --reload 60 /tmp/transit.png

# Terminal 2: run the poller
SERVER_URL=http://192.168.1.42:5000 MODE=random \
    VIEWER=feh python3 /opt/transit-display/display.py
```

The poller just keeps overwriting `/tmp/transit.png`; feh notices.

### Option B — `fbi` (no X, framebuffer console)

```bash
SERVER_URL=http://192.168.1.42:5000 MODE=full \
    VIEWER=fbi python3 /opt/transit-display/display.py
```

The poller will respawn `fbi` after each fresh image.

## Modes

| `MODE`   | Notes                                              |
|----------|----------------------------------------------------|
| `full`   | Entire Capital Metro system                        |
| `line`   | Single route — also set `ROUTE_ID` (int)           |
| `random` | Random ~4 km × 2.6 km slice, centered on a vehicle |

Useful `ROUTE_ID`s (check the shapefile for the full list):
- `550` — MetroRail Red Line
- `1`, `7`, `10`, `20`, `300`, `801`, `803` — high-frequency local / rapid routes

## Autostart with systemd

```bash
sudo cp transit-display.service /etc/systemd/system/
# Edit SERVER_URL/MODE/ROUTE_ID in the unit file:
sudoedit /etc/systemd/system/transit-display.service
sudo systemctl daemon-reload
sudo systemctl enable --now transit-display.service
journalctl -u transit-display.service -f   # watch logs
```

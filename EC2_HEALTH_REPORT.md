# EC2 Production Health Report
**Instance:** ec2-18-224-69-106.us-east-2.compute.amazonaws.com
**Generated:** 2026-02-27
**Uptime:** 88 days

---

## Summary

| Area | Status | Severity |
|------|--------|----------|
| Disk usage | 60% (4.8G / 8G) | WARN |
| Memory headroom | ~320MB available, no swap | CRITICAL |
| Journald log size | 834MB uncapped | CRITICAL |
| Docker log limits | None configured | HIGH |
| Bot scanning activity | Heavy (1,600+ req/6h) | HIGH |
| Backend runtime errors | Active 500s and AttributeErrors | HIGH |
| Reclaimable space | ~302MB (volume + build cache) | MEDIUM |

---

## 1. CRITICAL — No Swap Space

The instance has **0 bytes of swap** on a 1 vCPU / ~949MB RAM machine. If any process spikes (bot scan flood, memory leak in Python workers), the kernel OOM killer will silently terminate Docker containers with no warning or graceful shutdown.

**Fix:** Add a swap file.
```bash
sudo dd if=/dev/zero of=/swapfile bs=128M count=8   # creates 1GB swap
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

---

## 2. CRITICAL — Journald Consuming 834MB (Uncapped)

`/var/log/journal` is **834MB** and growing. The `/etc/systemd/journald.conf` has all limits commented out (compile-time defaults), meaning journald can grow to fill the disk.

**Fix:** Cap journald in `/etc/systemd/journald.conf`:
```ini
[Journal]
SystemMaxUse=200M
SystemMaxFileSize=50M
MaxRetentionSec=2weeks
```
Then apply:
```bash
sudo systemctl restart systemd-journald
sudo journalctl --vacuum-size=200M
```
This alone will reclaim ~630MB of disk immediately.

---

## 3. HIGH — Docker Logs Have No Size Limits

No `/etc/docker/daemon.json` exists, so Docker uses the default `json-file` log driver with **no max-size or max-file limits**. Logs will grow unbounded.

Current Docker log sizes:
- `base-nginx-1`: **34MB** (and growing — heavy bot traffic)
- `base-backend-1`: **3.8MB**
- `base-frontend-1`: **30KB**

**Fix:** Create `/etc/docker/daemon.json`:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "20m",
    "max-file": "3"
  }
}
```
Then restart Docker: `sudo systemctl restart docker` (will restart all containers — schedule a maintenance window).

Alternatively, set per-container in `docker-compose.prod.yml`:
```yaml
services:
  nginx:
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "20m"
        max-file: "3"
```

---

## 4. HIGH — Heavy Bot/Scanner Activity Generating Log Noise

The nginx container is receiving **~270 requests/hour from bots** scanning for:
- WordPress paths (`/wp-admin`, `/wp-content`, `/wp-includes`)
- Upload endpoints (`/upload`, `/files`, `/media`, `/blob`, `/s3/upload`, etc.) — **68 hits reached the backend** in 24h
- Config file probes (`/.env`, `/error.log`, `/config.php`) — **190 `.env` probes in 24h**
- PHP files (`/admin.php`, `/css.php`, `/x.php`)

**Concerning:** Nginx is returning `200 1055` for all these paths (the React SPA catch-all serving `index.html`). Bots interpret `200` as success and escalate scanning intensity. You want 404s for non-SPA paths.

**Fix — nginx:** Return 404 for common scanner paths explicitly:
```nginx
# In your nginx.conf server block:
location ~* \.(php|asp|aspx|jsp)$ { return 404; }
location ~ ^/(wp-|\.env|\.git|admin\.php|config\.) { return 404; }
```

**Fix — rate limiting in nginx:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
location /api/ {
    limit_req zone=api burst=10 nodelay;
}
```

---

## 5. HIGH — Active Backend Runtime Errors (500s)

Two distinct crash patterns in the backend logs:

**a) AttributeError on flight data endpoints:**
```
AttributeError: 'str' object has no attribute 'get'
```
Affects at least one endpoint — likely a FlightAware or AviationStack response that returns a string on error instead of a dict, and the code calls `.get()` on it without checking type first.

**b) UnboundLocalError on /flightAware/UA4342:**
```
UnboundLocalError: cannot access local variable 'rh' where it is not associated with a value
GET /flightAware/UA4342 → 500 Internal Server Error
```
A variable `rh` is used in a code path that is reached before assignment (likely inside a conditional branch that doesn't always execute).

**c) FlightStats delay extraction:**
```
Delay status error in FlightStatsExtractor.tc, list index out of range
```
Accessing a list index that doesn't exist — likely an empty response from FlightStats.

These should be wrapped in try/except with graceful fallbacks so they return structured errors instead of 500s.

---

## 6. MEDIUM — Reclaimable Disk Space (~302MB)

| Resource | Size | Action |
|----------|------|--------|
| `base_node_modules` Docker volume | 272MB | **Safe to delete** — 0 active containers using it (dangling) |
| Docker build cache | 29.75MB | Safe to prune |
| **Total reclaimable** | **~302MB** | |

Commands:
```bash
docker volume rm base_node_modules     # 272MB back
docker builder prune -f                # 29.75MB back
```

---

## 7. MEDIUM — Memory is Tight (No Headroom for Spikes)

Current memory breakdown:
- **Total:** 949MB
- **Used:** 470MB
- **Available:** ~320MB
- **Swap:** 0MB

Largest consumers:
- `systemd-journald`: 88MB (9%) — inflated by uncapped log retention (fixes with item #2)
- Python Celery workers: ~165MB combined (17.5%)
- Docker daemon: 58MB
- Vite preview node process: 39MB
- uvicorn: 23MB

With 320MB available and zero swap, a traffic spike or memory leak leaves no safety net. Adding swap (item #1) is the immediate mitigation. Longer term, consider upgrading from t2/t3.micro to t3.small (2GB RAM).

---

## 8. LOW — Orphaned `base_node_modules` Volume

The `base_node_modules` Docker volume (272MB) has 0 active container links. It was created 2025-02-06 and appears to be a leftover from a previous deployment. It's taking up 272MB of the 8GB disk for no benefit.

---

## Recommended Action Order

1. **Now (no downtime):**
   - Add swap file (item #1)
   - Cap journald and vacuum (item #2) — reclaims ~630MB
   - Remove orphaned volume + prune build cache (item #6) — reclaims ~302MB
   - Total immediate disk recovery: ~930MB, bringing disk to ~35% used

2. **Next deployment:**
   - Add Docker log limits to `docker-compose.prod.yml` (item #3)
   - Add nginx 404 rules for scanner paths (item #4)

3. **Code fixes (backend):**
   - Fix `AttributeError` on flight data endpoint — add type check before `.get()` calls
   - Fix `UnboundLocalError` for variable `rh` in flightAware route
   - Fix list index out of range in `FlightStatsExtractor.tc`

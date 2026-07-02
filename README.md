## Run it locally

**Prereqs:** Node.js + Yarn, Python 3.8+, and MongoDB (local or MongoDB Atlas).

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate   |   Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
# install the AI image library used by this app:
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/
sudo supervisorctl restart backend   # or locally:  uvicorn server:app --reload --port 8001
```

**`backend/.env`** must contain:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="storyboarder"
CORS_ORIGINS="*"
EMERGENT_LLM_KEY=...   # get it from: Profile → Universal Key
```

**Frontend (React):**
```bash
cd frontend
yarn install
yarn start
```
**`frontend/.env`**:
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

**MongoDB:** start it locally (`mongod` / `brew services start mongodb-community`) or use an Atlas connection string in `MONGO_URL`.

---

## Admin operations & pool rotation

The seed-image URL pool (the default art every new project's scenes / characters / locations inherit) is sourced from `backend/sp_image_pool.py` and exposed at runtime via `GET /api/seed-image-pool`. There are two admin endpoints that let you swap or repaint the pool without redeploying. Both share a single auth secret.

### Required env var

Add this to `backend/.env` (and restart uvicorn):

```
ADMIN_ROTATION_TOKEN="your_long_random_secret_here"
```

If unset, both admin endpoints fail-closed with `401 ADMIN_ROTATION_TOKEN not configured on server`.

### `POST /api/admin/rotate-pool`

Atomically swap the in-memory CHAR / LOC / FRAMES URL pool. Validates every URL via `HEAD` (5 s timeout) before mutating, so a typo never ships. Concurrency-safe via a process-wide `asyncio.Lock`.

```bash
curl -X POST http://localhost:8001/api/admin/rotate-pool \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: $ADMIN_ROTATION_TOKEN" \
  -d '{
    "pools": {
      "CHAR_IMAGES":  ["https://images.unsplash.com/photo-...?...", ...],
      "LOC_IMAGES":   ["https://images.pexels.com/photos/...?...", ...],
      "FRAME_IMAGES": ["https://images.unsplash.com/photo-...?...", ...]
    },
    "sha": "optional-version-tag-e.g.-git-sha"
  }'
```

Response (200):

```json
{
  "version": "optional-version-tag-e.g.-git-sha",
  "replaced": {"CHAR_IMAGES": 10, "LOC_IMAGES": 8, "FRAME_IMAGES": 12}
}
```

Failure modes:
- `401` — admin token missing or mismatched.
- `400` — empty arrays, non-`http` URLs, duplicate URLs (within or across pools), missing/extra pool keys. Error body always names the offending field.
- `422` — at least one URL failed `HEAD` (404 / 5xx / timeout). The first failing URL is in `detail` for triage.

### `POST /api/admin/refresh-all-projects`

Re-parse every project's stored `screenplay` against the currently-active pool and write the fresh URLs to MongoDB. Returns `202 {"status": "started"}` immediately; runs in a background task. **Call this after a `rotate-pool` so existing projects' scenes / characters / locations visually update.**

```bash
curl -X POST http://localhost:8001/api/admin/refresh-all-projects \
  -H "X-Admin-Token: $ADMIN_ROTATION_TOKEN"
```

The refresh preserves user-uploaded or AI-rendered `/api/...` URLs (smart-merge rule in `scripts/refresh_project_images.py`). Only seed URLs are replaced.

### Cron automation

`backend/scripts/scheduled_refresh.sh` is a cron-friendly wrapper around the refresh script:

```bash
# Make it executable once:
chmod +x backend/scripts/scheduled_refresh.sh

# Run nightly at 03:00 UTC (after any rotation admin might have done earlier):
0 3 * * * /opt/storyboard/backend/scripts/scheduled_refresh.sh
```

The script logs to `backend/refresh_cron.log` (override with `LOG_FILE=...`). Honours `MONGO_URL` / `DB_NAME` from `.env` and exits non-zero on failure so cron can alert.

### Manual single-project refresh

If you only want to repaint one project's seed URLs (without doing the whole fleet):

```bash
cd backend
source venv/bin/activate
python scripts/refresh_project_images.py p-c1284788cc06            # real
python scripts/refresh_project_images.py p-c1284788cc06 --dry-run  # diff only
```

---

## Prometheus metrics (admin rotation surface)

`GET /metrics` (public, no auth) exposes four series for the admin pool-rotation surface. Scrape with the standard 15–60 s interval.

| Series | Type | Labels | Meaning |
| --- | --- | --- | --- |
| `storyboard_pool_rotation_total` | Counter | `result={success,failure}` | Every `POST /api/admin/rotate-pool`. Auth failures are included. |
| `storyboard_pool_rotation_failures_total` | Counter | `kind={schema,auth,head_failure,duplicate}` | Failure buckets. Sum across all `kind` values ≈ `..._total{result="failure"}` (matches by construction — the auth bucket increments both counters in lockstep). |
| `storyboard_pool_rotation_duration_seconds` | Histogram | – | Wall-clock for the rotate handler (HEAD-verify + swap + audit-insert). Buckets: 0.05 / 0.1 / 0.25 / 0.5 / 1 / 2.5 / 5 / 10 / 30 s. |
| `storyboard_admin_audit_writes_total` | Counter | `result={success,failure}` | MongoDB audit-log insert outcomes. `failure` usually means Mongo was unreachable after a successful rotation. |

### Useful PromQL

```promql
# Rotation error rate (auth is counted as a failure)
rate(storyboard_pool_rotation_total{result="failure"}[5m])
  / rate(storyboard_pool_rotation_total[5m])

# Failure breakdown — which bucket is dominating?
sum by (kind) (rate(storyboard_pool_rotation_failures_total[5m]))

# p95 rotation latency (HEADs + swap)
histogram_quantile(0.95,
  sum by (le) (rate(storyboard_pool_rotation_duration_seconds_bucket[5m])))

# Alert: audit-write failures (Mongo blip after a successful rotation)
rate(storyboard_admin_audit_writes_total{result="failure"}[5m]) > 0
```

### Grafana dashboard

`grafana/storyboard_rotation.json` is a minimal 4-panel dashboard that ships those queries pre-wired:

1. **Rotation rate** — stacked counters of `success` vs `failure`.
2. **Failure breakdown** — line per `kind` (schema / auth / head_failure / duplicate) over the last 1 h.
3. **Rotation latency** — p50 / p95 / p99 lines derived from the histogram.
4. **Audit write failures** (alert row) — fires when the per-second rate goes above 0.

Grafana → Dashboards → Import, paste the file path or upload the JSON. Set the data source variable `$DS` to your Prometheus instance.

### Prometheus scrape config snippet

```yaml
scrape_configs:
  - job_name: storyboard
    metrics_path: /metrics
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
```

---

## Theme tokens ("Neon Flux" cyberpunk)

The SPA ships a single dark cyberpunk visual identity. Tokens live in `frontend/src/index.css` under `:root` and in `frontend/tailwind.config.js` under `theme.extend`. When touching any visual surface, honour these rules unless you have an explicit reason otherwise.

### Palette (HSL channel triplets)

| Token | HSL | Hex | Use |
| --- | --- | --- | --- |
| `--background` | `260 33% 3%` | `#05050A` | Page / app shell base |
| `--card` | `260 20% 9%` | `#13131A` | Elevated surface (cards, dialogs) |
| `--primary` | `184 100% 50%` | `#00F0FF` | Cyan main accent (links, CTAs, focus rings) |
| `--secondary` | `300 100% 50%` | `#FF00FF` | Magenta accent (active counters, connectors) |
| `--accent` | `271 90% 60%` | `#9B30FF` | Purple tertiary (badges, highlights) |
| `--destructive` | `345 100% 50%` | `#FF0040` | Hot pink for destructive CTAs |
| `--success` | `144 100% 50%` | `#00FF66` | Matrix green for healthy states |
| `--border` | `260 28% 18%` | `#212130` | Hairline grid lines |
| `--radius` | `0px` | n/a | Brutalist sharp corners globally |

The `:root[data-theme="light"]` block re-maps these to legible light equivalents so users who explicitly flip the Style switcher (in the project header) get a softer treatment. The light theme uses round-2xl on the radius and softer neon alpha so it doesn't read as a hostile light-mode cyberpunk.

### Fonts

* **Display** (`font-display`): **Orbitron** — loaded via the `Orbitron:wght@400;600;700;900` Google Fonts query in `src/index.css`. Use for page H1/H2 and any display-type label that needs to read as a "console heading".
* **Mono** (`font-mono`): **JetBrains Mono** — loaded via `@import url('...JetBrains+Mono...')`. Use for telemetry / metadata / chips / terminal-style captions like `// SCN-01`, `[OK]`, `▌`.
* **Sans body**: Inter — unchanged from the pre-cyberpunk baseline; the readable workhorse for paragraphs and form labels.

### Tailwind utility additions

Don't reach for raw Tailwind utilities alone when building a new surface; use these cyberpunk-flavoured wrappers:

| Utility | Effect |
| --- | --- |
| `shadow-neon-primary` | Soft cyan halo (cyan + 0.55 alpha) — apply to primary CTA hover, focused inputs |
| `shadow-neon-secondary` | Magenta halo — destructive button hover |
| `shadow-neon-accent` | Purple halo — accent-level highlights |
| `shadow-aberration` | Chromatic-aberration ring (2-px cyan + 2-px magenta offsets) — focus-visible state |
| `animate-pulse-neon` | 2s cyan halo breathing — primary buttons, dashboard hero, empty-state icons |
| `animate-scanline` | 8s vertical scanline scroll — only used inside `body::before`'s CRT overlays |
| `animate-blink` | 1.1s stepped terminal caret blink — caret + active-route pip |

### Layout patterns

* **Sidebar rail** (`frontend/src/components/Sidebar.jsx`): logo is `> S.BOARD.OS_<animate-blink>_</span>` mono JetBrains-Mono. Active nav item gets `border-l-2 border-primary shadow-[inset_4px_0_18px_-2px_hsl(var(--primary)/0.35)]`. Status row at the bottom reads `> SYS ONLINE <span>v2.0</span>`.
* **Tab rail** (project workspace, NewProject tab strip, ObjectsPanel filter strip): top-border + inset cyan glow on the active tab. Inactive tab is `border-transparent` and gets `hover:bg-primary/5` so the rail reads as a "circuit" instead of a pill set.
* **Corner-bracket reticle**: four small L-bracket spans (`border-t-2 border-l-2 border-primary` etc.) sit at the four corners of dropzones and empty states. Used for Dashboard empty state, NewProject dropzone, and the StoryboardPanel's outer wrapper. Don't replace with a soft dashed border.
* **Card chrome**: cyberpunk cards have `rounded-none` + `border-b-1 border-primary` (or `border-b-4` on hex-grid cards) instead of soft shadows + rounded-xl.
* **Headings**: take `font-display` (Orbitron) + `font-extrabold tracking-tight`. Don't italicise.
* **Telemetric captions**: `font-mono uppercase tracking-[0.18em] text-[10-11px] text-muted-foreground` on `[OK]`, `//` prefixed notes, count badges, etc.

### Accessibility

* `prefers-reduced-motion: reduce` (in `src/index.css`) disables the `animate-pulse-neon`, `animate-blink`, and CRT scanline overlays. Any new animation must respect this fallback.
* Focus-visible uses `shadow-aberration` (cyan/magenta offsets) so keyboard nav reads as a deliberate "channel-shifted" ring without falling back to a soft shadcn outline.
* Body color contrast: cyan `#00F0FF` on obsidian `#05050A` yields ~14:1 (well past WCAG AAA). Off-white text (~#E2E2EE) on obsidian yields ~15:1. Don't use cyan for body paragraphs; reserve it for accent labels only.


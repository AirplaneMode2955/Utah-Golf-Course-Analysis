# UGA Handicap Scraper & Dashboard

Scrapes USGA course rating data (Rating, Bogey Rating, Slope) for Utah Golf Association facilities and visualizes them in a local HTML dashboard.

---

## Directory Structure

```
uga handicaps/
├── courses.json              # Input — list of UGA facilities to scrape (FacilityId, FacilityName, etc.)
├── scrape_it.py              # Scraper — fetches course/tee data from the UGA API
├── generate_dashboard.py     # Dashboard generator — flattens data and builds dashboard.html
├── dashboard.html            # Generated — open this in a browser to view the dashboard
├── outputs/
│   ├── output.json           # Raw scrape output: { "Course Name - ID": [ { tee: {Rating, Bogey, Slope} } ] }
│   └── output_claude.json    # Flattened tee records used by the dashboard
└── individual_course_data/
    └── course_XXXXX.json     # One file per course (keyed by CourseId), same tee structure
```

---

## Setup

Install the one dependency (handles Cloudflare's TLS fingerprint check):

```bash
pip install curl_cffi
```

---

## Workflow

### 1. Scrape

```bash
python scrape_it.py
```

Reads `courses.json`, hits the UGA facility API for each facility, and writes:
- `outputs/output.json` — combined output across all facilities
- `individual_course_data/course_XXXXX.json` — one file per course

Facilities that return an error or fail to parse are skipped and reported at the end.

### 2. Generate Dashboard

```bash
python generate_dashboard.py
```

Reads `outputs/output.json`, flattens it into `outputs/output_claude.json`, and generates `dashboard.html` with all data embedded.

### 3. View Dashboard

Open `dashboard.html` in any browser (no server needed — data is embedded).

---

## Dashboard Features

- **Scatter chart** — Course Rating (x) vs Slope (y) for every tee. Male tees in blue, female tees in pink.
- **Bar chart** — Average slope by course (top 30). Sortable by slope, rating, or name.
- **Course detail table** — Click any course in the sidebar or any scatter point to see all its tees with Rating, Bogey, and Slope (color-coded: green < 120, orange 120–139, red ≥ 140).
- **Gender filter** — Toggle between Both / Male / Female across all views simultaneously.
- **Course search** — Filter the sidebar list by name.

---

## Refreshing Cookies

The UGA site is protected by Cloudflare. The cookies in `scrape_it.py` expire periodically. When you start getting 403 errors:

1. Open [uga.org](https://www.uga.org) in Chrome and navigate to any facility page.
2. Open DevTools → Network tab → click any `gn-api` request.
3. Right-click the request → **Copy as cURL**.
4. Extract the cookie values from the curl command and paste them into the `COOKIES` dict at the top of `scrape_it.py`.

The critical cookie is `cf_clearance` — it's the Cloudflare challenge token. The others (session, analytics) are less time-sensitive but should be refreshed at the same time.

---

## Data Format

### `outputs/output.json`
```json
{
  "Bloomington CC - 7176": [
    {
      "male - Red":   { "Rating": "72.70", "Bogey": "96.90", "Slope": 130 },
      "female - Red": { "Rating": "79.20", "Bogey": "112.60", "Slope": 142 }
    }
  ]
}
```

### `outputs/output_claude.json` (flattened)
```json
[
  {
    "course": "Bloomington CC",
    "courseId": "7176",
    "tee": "Red",
    "gender": "male",
    "rating": 72.70,
    "bogey": 96.90,
    "slope": 130
  }
]
```

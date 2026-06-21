import json
import os

OUTPUTS_DIR = "outputs"

def load_and_flatten():
    with open(os.path.join(OUTPUTS_DIR, 'output.json'), 'r') as f:
        raw = json.load(f)

    flat = []
    for course_key, course_list in raw.items():
        parts = course_key.rsplit(' - ', 1)
        course_name = parts[0]
        course_id = parts[1] if len(parts) > 1 else ''

        if not course_list:
            continue

        tees = course_list[0]
        for tee_key, tee_data in tees.items():
            gender_part, tee_name = tee_key.split(' - ', 1)
            flat.append({
                'course': course_name,
                'courseId': course_id,
                'tee': tee_name,
                'gender': gender_part,
                'rating': float(tee_data['Rating']),
                'bogey': float(tee_data['Bogey']),
                'slope': int(tee_data['Slope']),
            })

    with open(os.path.join(OUTPUTS_DIR, 'output_claude.json'), 'w') as f:
        json.dump(flat, f, indent=2)

    return flat


def generate_html(data):
    data_json = json.dumps(data)

    courses = sorted(set(d['course'] for d in data))
    courses_json = json.dumps(courses)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UGA Course Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e2e8f0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}

  header {{ background: #1a1d2e; border-bottom: 1px solid #2d3148; padding: 12px 20px; display: flex; align-items: center; gap: 16px; flex-shrink: 0; }}
  header h1 {{ font-size: 18px; font-weight: 700; color: #fff; }}
  .stat-pills {{ display: flex; gap: 12px; margin-left: auto; }}
  .pill {{ background: #252840; border: 1px solid #3d4166; border-radius: 20px; padding: 4px 12px; font-size: 12px; color: #a0aec0; }}
  .pill span {{ color: #7c8cf8; font-weight: 600; }}

  .layout {{ display: flex; flex: 1; overflow: hidden; }}

  aside {{ width: 240px; background: #13151f; border-right: 1px solid #2d3148; display: flex; flex-direction: column; flex-shrink: 0; }}
  .sidebar-header {{ padding: 12px; border-bottom: 1px solid #2d3148; }}
  .sidebar-header input {{ width: 100%; background: #1e2130; border: 1px solid #3d4166; border-radius: 6px; padding: 7px 10px; color: #e2e8f0; font-size: 13px; outline: none; }}
  .sidebar-header input:focus {{ border-color: #7c8cf8; }}
  .course-list {{ flex: 1; overflow-y: auto; padding: 6px 0; }}
  .course-list::-webkit-scrollbar {{ width: 4px; }}
  .course-list::-webkit-scrollbar-track {{ background: transparent; }}
  .course-list::-webkit-scrollbar-thumb {{ background: #3d4166; border-radius: 4px; }}
  .course-item {{ padding: 8px 14px; cursor: pointer; font-size: 12.5px; color: #94a3b8; border-left: 3px solid transparent; transition: all 0.15s; }}
  .course-item:hover {{ background: #1e2130; color: #e2e8f0; }}
  .course-item.active {{ background: #1e2130; color: #7c8cf8; border-left-color: #7c8cf8; }}

  main {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 16px; gap: 14px; }}

  .controls {{ display: flex; gap: 10px; align-items: center; flex-shrink: 0; }}
  .toggle-group {{ display: flex; background: #1e2130; border: 1px solid #3d4166; border-radius: 6px; overflow: hidden; }}
  .toggle-btn {{ padding: 6px 14px; font-size: 12px; cursor: pointer; border: none; background: transparent; color: #94a3b8; transition: all 0.15s; }}
  .toggle-btn.active {{ background: #7c8cf8; color: #fff; }}
  .sort-label {{ font-size: 12px; color: #64748b; margin-left: 12px; }}
  .sort-select {{ background: #1e2130; border: 1px solid #3d4166; border-radius: 6px; color: #e2e8f0; padding: 5px 10px; font-size: 12px; outline: none; cursor: pointer; }}

  .charts-row {{ display: flex; gap: 14px; flex: 1; min-height: 0; }}
  .chart-card {{ background: #1a1d2e; border: 1px solid #2d3148; border-radius: 10px; padding: 14px; display: flex; flex-direction: column; }}
  .chart-card h2 {{ font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 10px; flex-shrink: 0; }}
  .chart-card canvas {{ flex: 1; min-height: 0; }}
  .scatter-card {{ flex: 1.3; }}
  .bar-card {{ flex: 1; overflow: hidden; }}

  .detail-panel {{ background: #1a1d2e; border: 1px solid #2d3148; border-radius: 10px; padding: 14px; flex-shrink: 0; }}
  .detail-panel h2 {{ font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 10px; }}
  .detail-empty {{ color: #4a5568; font-size: 13px; font-style: italic; }}
  .tee-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .tee-table th {{ color: #64748b; text-align: left; padding: 4px 10px; border-bottom: 1px solid #2d3148; font-weight: 500; }}
  .tee-table td {{ padding: 5px 10px; border-bottom: 1px solid #1e2130; }}
  .tee-table tr:last-child td {{ border-bottom: none; }}
  .tee-table tr:hover td {{ background: #252840; }}
  .gender-m {{ color: #7c8cf8; }}
  .gender-f {{ color: #f687b3; }}
  .slope-high {{ color: #fc8181; }}
  .slope-med {{ color: #f6ad55; }}
  .slope-low {{ color: #68d391; }}
</style>
</head>
<body>

<header>
  <h1>UGA Course Dashboard</h1>
  <div class="stat-pills" id="statPills"></div>
</header>

<div class="layout">
  <aside>
    <div class="sidebar-header">
      <input type="text" id="searchInput" placeholder="Search courses..." oninput="filterCourses()">
    </div>
    <div class="course-list" id="courseList"></div>
  </aside>

  <main>
    <div class="controls">
      <div class="toggle-group">
        <button class="toggle-btn active" id="btn-both" onclick="setGender('both')">Both</button>
        <button class="toggle-btn" id="btn-male" onclick="setGender('male')">Male</button>
        <button class="toggle-btn" id="btn-female" onclick="setGender('female')">Female</button>
      </div>
      <span class="sort-label">Bar chart sort:</span>
      <select class="sort-select" onchange="setSortMode(this.value)">
        <option value="slope_desc">Highest Slope</option>
        <option value="slope_asc">Lowest Slope</option>
        <option value="rating_desc">Highest Rating</option>
        <option value="name">Course Name</option>
      </select>
    </div>

    <div class="charts-row">
      <div class="chart-card scatter-card">
        <h2>Rating vs Slope — all tees <span id="scatterCount" style="color:#4a5568"></span></h2>
        <canvas id="scatterChart"></canvas>
      </div>
      <div class="chart-card bar-card">
        <h2>Avg Slope by Course (top 30)</h2>
        <canvas id="barChart"></canvas>
      </div>
    </div>

    <div class="detail-panel">
      <h2 id="detailTitle">Course Detail</h2>
      <div id="detailContent"><p class="detail-empty">Click a course in the sidebar or a point on the scatter chart to see tee details.</p></div>
    </div>
  </main>
</div>

<script>
const ALL_DATA = {data_json};
const ALL_COURSES = {courses_json};

let genderFilter = 'both';
let selectedCourse = null;
let sortMode = 'slope_desc';
let scatterChart, barChart;

// ── Stats ──────────────────────────────────────────────────────────────
function buildStats() {{
  const slopes = ALL_DATA.map(d => d.slope);
  const ratings = ALL_DATA.map(d => d.rating);
  document.getElementById('statPills').innerHTML = `
    <div class="pill"><span>${{ALL_COURSES.length}}</span> courses</div>
    <div class="pill"><span>${{ALL_DATA.length}}</span> tees</div>
    <div class="pill">Slope <span>${{Math.min(...slopes)}}–${{Math.max(...slopes)}}</span></div>
    <div class="pill">Rating <span>${{Math.min(...ratings).toFixed(1)}}–${{Math.max(...ratings).toFixed(1)}}</span></div>
  `;
}}

// ── Sidebar ────────────────────────────────────────────────────────────
function buildSidebar() {{
  renderCourseList(ALL_COURSES);
}}

function filterCourses() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  const filtered = ALL_COURSES.filter(c => c.toLowerCase().includes(q));
  renderCourseList(filtered);
}}

function renderCourseList(courses) {{
  const el = document.getElementById('courseList');
  el.innerHTML = courses.map(c => `
    <div class="course-item ${{selectedCourse === c ? 'active' : ''}}" onclick="selectCourse('${{c.replace(/'/g, "\\\\'")}}')">
      ${{c}}
    </div>
  `).join('');
}}

function selectCourse(name) {{
  selectedCourse = selectedCourse === name ? null : name;
  renderCourseList(
    document.getElementById('searchInput').value
      ? ALL_COURSES.filter(c => c.toLowerCase().includes(document.getElementById('searchInput').value.toLowerCase()))
      : ALL_COURSES
  );
  updateScatter();
  updateDetail();
}}

// ── Gender toggle ──────────────────────────────────────────────────────
function setGender(g) {{
  genderFilter = g;
  ['both','male','female'].forEach(x => document.getElementById('btn-'+x).classList.remove('active'));
  document.getElementById('btn-'+g).classList.add('active');
  updateScatter();
  updateBar();
  updateDetail();
}}

function setSortMode(v) {{
  sortMode = v;
  updateBar();
}}

// ── Filtered data helper ───────────────────────────────────────────────
function filtered(data) {{
  let d = data;
  if (genderFilter !== 'both') d = d.filter(x => x.gender === genderFilter);
  return d;
}}

// ── Scatter chart ──────────────────────────────────────────────────────
function buildScatter() {{
  const ctx = document.getElementById('scatterChart').getContext('2d');
  scatterChart = new Chart(ctx, {{
    type: 'scatter',
    data: {{ datasets: [] }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      animation: {{ duration: 200 }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label(ctx) {{
              const p = ctx.raw;
              return [p.course + ' — ' + p.tee, 'Rating: ' + p.x + '  Slope: ' + p.y + '  Bogey: ' + p.bogey];
            }}
          }},
          backgroundColor: '#1a1d2e',
          borderColor: '#3d4166',
          borderWidth: 1,
          titleColor: '#e2e8f0',
          bodyColor: '#94a3b8',
          padding: 10,
        }},
      }},
      scales: {{
        x: {{
          title: {{ display: true, text: 'Course Rating', color: '#64748b', font: {{ size: 11 }} }},
          grid: {{ color: '#1e2130' }},
          ticks: {{ color: '#64748b', font: {{ size: 10 }} }},
        }},
        y: {{
          title: {{ display: true, text: 'Slope', color: '#64748b', font: {{ size: 11 }} }},
          grid: {{ color: '#1e2130' }},
          ticks: {{ color: '#64748b', font: {{ size: 10 }} }},
        }},
      }},
      onClick(e, elements) {{
        if (elements.length) {{
          const pt = scatterChart.data.datasets[elements[0].datasetIndex].data[elements[0].index];
          selectCourse(pt.course);
        }}
      }},
    }},
  }});
  updateScatter();
}}

function updateScatter() {{
  let data = filtered(ALL_DATA);
  const isSel = selectedCourse !== null;

  const make = (pts, color, label) => ({{
    label,
    data: pts,
    backgroundColor: pts.map(p => isSel && p.course === selectedCourse ? color.replace('0.45','0.9') : (isSel ? color.replace('0.45','0.08') : color)),
    pointRadius: pts.map(p => isSel && p.course === selectedCourse ? 6 : 4),
    pointHoverRadius: 7,
  }});

  const mPts = data.filter(d => d.gender==='male').map(d => ({{ x:d.rating, y:d.slope, bogey:d.bogey, course:d.course, tee:d.tee }}));
  const fPts = data.filter(d => d.gender==='female').map(d => ({{ x:d.rating, y:d.slope, bogey:d.bogey, course:d.course, tee:d.tee }}));

  scatterChart.data.datasets = [
    make(mPts, 'rgba(124,140,248,0.45)', 'Male'),
    make(fPts, 'rgba(246,135,179,0.45)', 'Female'),
  ];
  scatterChart.update();
  document.getElementById('scatterCount').textContent = `(${{data.length}} tees)`;
}}

// ── Bar chart ──────────────────────────────────────────────────────────
function buildBar() {{
  const ctx = document.getElementById('barChart').getContext('2d');
  barChart = new Chart(ctx, {{
    type: 'bar',
    data: {{ labels: [], datasets: [] }},
    options: {{
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      animation: {{ duration: 200 }},
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label(ctx) {{ return ' Avg Slope: ' + ctx.raw.toFixed(1); }}
          }},
          backgroundColor: '#1a1d2e',
          borderColor: '#3d4166',
          borderWidth: 1,
          bodyColor: '#94a3b8',
        }},
      }},
      scales: {{
        x: {{
          grid: {{ color: '#1e2130' }},
          ticks: {{ color: '#64748b', font: {{ size: 10 }} }},
        }},
        y: {{
          grid: {{ color: 'transparent' }},
          ticks: {{ color: '#94a3b8', font: {{ size: 10 }}, padding: 4 }},
        }},
      }},
      onClick(e, elements) {{
        if (elements.length) {{
          const label = barChart.data.labels[elements[0].index];
          selectCourse(label);
        }}
      }},
    }},
  }});
  updateBar();
}}

function updateBar() {{
  const data = filtered(ALL_DATA);
  const byC = {{}};
  data.forEach(d => {{
    if (!byC[d.course]) byC[d.course] = [];
    byC[d.course].push(d.slope);
  }});
  const rows = Object.entries(byC).map(([c, slopes]) => ({{
    course: c,
    avgSlope: slopes.reduce((a,b)=>a+b,0)/slopes.length,
    maxSlope: Math.max(...slopes),
    avgRating: data.filter(d=>d.course===c).reduce((a,b)=>a+b.rating,0) / data.filter(d=>d.course===c).length,
  }}));

  if (sortMode === 'slope_desc') rows.sort((a,b) => b.avgSlope - a.avgSlope);
  else if (sortMode === 'slope_asc') rows.sort((a,b) => a.avgSlope - b.avgSlope);
  else if (sortMode === 'rating_desc') rows.sort((a,b) => b.avgRating - a.avgRating);
  else rows.sort((a,b) => a.course.localeCompare(b.course));

  const top = rows.slice(0, 30);
  barChart.data.labels = top.map(r => r.course);
  barChart.data.datasets = [{{
    data: top.map(r => +r.avgSlope.toFixed(1)),
    backgroundColor: top.map(r => selectedCourse === r.course ? '#7c8cf8' : 'rgba(124,140,248,0.4)'),
    borderColor: top.map(r => selectedCourse === r.course ? '#7c8cf8' : 'rgba(124,140,248,0.6)'),
    borderWidth: 1,
    borderRadius: 3,
  }}];
  barChart.update();
}}

// ── Detail panel ───────────────────────────────────────────────────────
function slopeClass(s) {{
  if (s >= 140) return 'slope-high';
  if (s >= 120) return 'slope-med';
  return 'slope-low';
}}

function updateDetail() {{
  const titleEl = document.getElementById('detailTitle');
  const contentEl = document.getElementById('detailContent');
  if (!selectedCourse) {{
    titleEl.textContent = 'Course Detail';
    contentEl.innerHTML = '<p class="detail-empty">Click a course in the sidebar or a point on the scatter chart to see tee details.</p>';
    return;
  }}
  let tees = ALL_DATA.filter(d => d.course === selectedCourse);
  if (genderFilter !== 'both') tees = tees.filter(d => d.gender === genderFilter);
  tees.sort((a,b) => b.slope - a.slope);

  titleEl.textContent = selectedCourse + ' (' + tees.length + ' tees shown)';
  contentEl.innerHTML = `
    <table class="tee-table">
      <thead>
        <tr>
          <th>Gender</th><th>Tee</th>
          <th>Rating</th><th>Bogey</th><th>Slope</th>
        </tr>
      </thead>
      <tbody>
        ${{tees.map(t => `
          <tr>
            <td class="${{t.gender === 'male' ? 'gender-m' : 'gender-f'}}">${{t.gender}}</td>
            <td>${{t.tee}}</td>
            <td>${{t.rating.toFixed(1)}}</td>
            <td>${{t.bogey.toFixed(1)}}</td>
            <td class="${{slopeClass(t.slope)}}">${{t.slope}}</td>
          </tr>
        `).join('')}}
      </tbody>
    </table>
  `;
}}

// ── Init ───────────────────────────────────────────────────────────────
buildStats();
buildSidebar();
buildScatter();
buildBar();
</script>
</body>
</html>"""


if __name__ == '__main__':
    flat = load_and_flatten()
    html = generate_html(flat)
    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Done — {len(flat)} tees across {len(set(d['course'] for d in flat))} courses.")
    print("Open dashboard.html in your browser.")

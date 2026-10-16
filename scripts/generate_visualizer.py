import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
JSON_PATH = BASE_DIR / "outputs" / "benchmark_summary.json"
OUTPUT_HTML = BASE_DIR / "outputs" / "benchmark_visualizer.html"

def load_data():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_html():
    raw_data = load_data()
    data_json_str = json.dumps(raw_data)

    html_template = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Microservice DAG Task Scheduling Benchmark</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #151d30;
      --card-border: #23304d;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --proposed-color: #10b981;
      --t1: #3b82f6;
      --t2: #ec4899;
      --t3: #8b5cf6;
      --t4: #f59e0b;
      --unassigned: #475569;
    }}

    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      font-family: 'Inter', -apple-system, sans-serif;
    }}

    body {{
      background-color: var(--bg);
      color: var(--text-main);
      padding: 12px 16px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      padding: 12px 20px;
      border-radius: 10px;
      border: 1px solid var(--card-border);
      flex-wrap: wrap;
      gap: 12px;
    }}

    .title-area h1 {{
      font-size: 18px;
      font-weight: 800;
      background: linear-gradient(135deg, #38bdf8, #818cf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}

    .title-area p {{
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 2px;
    }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 16px;
      flex-wrap: wrap;
    }}

    .control-group {{
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
    }}

    select, button {{
      background: #0b0f19;
      color: #fff;
      border: 1px solid var(--card-border);
      padding: 7px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      outline: none;
      transition: all 0.2s;
    }}

    select:focus, button:hover {{
      border-color: var(--accent);
    }}

    .toggle-label {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      color: #cbd5e1;
      font-weight: 500;
      user-select: none;
    }}

    .toggle-label input {{
      accent-color: #38bdf8;
      width: 15px;
      height: 15px;
      cursor: pointer;
    }}

    /* Compact Legend Bar */
    .legend-bar {{
      display: flex;
      gap: 16px;
      align-items: center;
      font-size: 12px;
      background: rgba(21, 29, 48, 0.8);
      padding: 7px 16px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      flex-wrap: wrap;
    }}

    .legend-item {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      color: #cbd5e1;
    }}

    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      display: inline-block;
    }}

    .line-legend {{
      width: 22px;
      height: 2px;
      display: inline-block;
    }}

    /* 3-Col Layout */
    .compare-container {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      flex: 1;
      min-height: 640px;
    }}

    .algo-card {{
      background: var(--card-bg);
      border-radius: 10px;
      border: 1px solid var(--card-border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }}

    .algo-card.is-proposed {{
      border: 2px solid var(--proposed-color);
      box-shadow: 0 0 16px rgba(16, 185, 129, 0.12);
    }}

    .algo-header {{
      padding: 10px 14px;
      background: rgba(11, 15, 25, 0.65);
      border-bottom: 1px solid var(--card-border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .algo-title {{
      font-size: 14px;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .tag-proposed {{
      font-size: 9px;
      padding: 2px 7px;
      background: rgba(16, 185, 129, 0.2);
      color: #34d399;
      border: 1px solid #10b981;
      border-radius: 20px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }}

    .metrics-summary {{
      padding: 8px 12px;
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      background: rgba(11, 15, 25, 0.35);
      border-bottom: 1px solid var(--card-border);
    }}

    .metric-item {{
      background: #0b0f19;
      padding: 5px 6px;
      border-radius: 6px;
      text-align: center;
      border: 1px solid #1b253b;
    }}

    .metric-label {{
      font-size: 9px;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 600;
    }}

    .metric-val {{
      font-size: 13px;
      font-weight: 700;
      color: #fff;
      margin-top: 1px;
    }}

    .metric-val.highlight {{
      color: #34d399;
    }}

    .metric-val.warning {{
      color: #f87171;
    }}

    .graph-wrapper {{
      flex: 1;
      position: relative;
      min-height: 520px;
      background: #080c16;
    }}

    .graph-canvas {{
      width: 100%;
      height: 100%;
      position: absolute;
      top: 0;
      left: 0;
    }}

    /* Custom Floating Tooltip (Plain text, clean HTML) */
    #custom-tooltip {{
      position: fixed;
      pointer-events: none;
      background: #1e293b;
      border: 1px solid var(--accent);
      padding: 8px 12px;
      border-radius: 6px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6);
      font-size: 12px;
      line-height: 1.5;
      display: none;
      z-index: 999;
      color: #f8fafc;
    }}

    #custom-tooltip strong {{
      color: #38bdf8;
    }}
  </style>
</head>
<body>

  <header>
    <div class="title-area">
      <h1>Microservice Task Scheduling — Flow & Dependency Visualizer</h1>
      <p>Trực quan hóa luồng công việc từng Team (Flow mui tên liền) & Phụ thuộc DAG (Mũi tên nét đứt)</p>
    </div>

    <div class="controls">
      <div class="control-group">
        <label for="scenarioSelect">Kịch bản:</label>
        <select id="scenarioSelect" onchange="renderAll()">
          <option value="demo-1.json">demo-1 (2 Teams, 20 Tasks)</option>
          <option value="demo-2.json">demo-2 (3 Teams, 40 Tasks)</option>
          <option value="demo-3.json">demo-3 (4 Teams, 60 Tasks)</option>
        </select>
      </div>

      <label class="toggle-label">
        <input type="checkbox" id="chkShowDeps" checked onchange="renderAll()">
        <span>Hiện ràng buộc DAG (Nét đứt)</span>
      </label>

      <button onclick="resetViews()">⟲ Căn giữa góc nhìn</button>
    </div>
  </header>

  <div class="legend-bar">
    <span style="font-weight: 700; color: #fff;">Chú thích:</span>
    <span class="legend-item"><span class="dot" style="background: #3b82f6;"></span> Team 1 (t1)</span>
    <span class="legend-item"><span class="dot" style="background: #ec4899;"></span> Team 2 (t2)</span>
    <span class="legend-item"><span class="dot" style="background: #8b5cf6;"></span> Team 3 (t3)</span>
    <span class="legend-item"><span class="dot" style="background: #f59e0b;"></span> Team 4 (t4)</span>
    <span class="legend-item"><span class="dot" style="background: #475569;"></span> Bỏ qua / Cắt tỉa</span>
    <span class="legend-item"><span class="line-legend" style="background: #38bdf8;"></span> Luồng làm việc Team (Team Flow)</span>
    <span class="legend-item"><span class="line-legend" style="border-top: 2px dashed #94a3b8; background: transparent;"></span> Ràng buộc tiền đề (DAG Preds)</span>
  </div>

  <div class="compare-container">
    <!-- Proposed -->
    <div class="algo-card is-proposed">
      <div class="algo-header">
        <div class="algo-title">
          <span>Proposed Algorithm</span>
          <span class="tag-proposed">ĐỀ XUẤT</span>
        </div>
      </div>
      <div class="metrics-summary" id="metrics-proposed"></div>
      <div class="graph-wrapper">
        <div id="graph-proposed" class="graph-canvas"></div>
      </div>
    </div>

    <!-- Greedy CVSS -->
    <div class="algo-card">
      <div class="algo-header">
        <div class="algo-title">
          <span>Greedy CVSS</span>
        </div>
      </div>
      <div class="metrics-summary" id="metrics-greedy_cvss"></div>
      <div class="graph-wrapper">
        <div id="graph-greedy_cvss" class="graph-canvas"></div>
      </div>
    </div>

    <!-- Google OR-Tools CP-SAT -->
    <div class="algo-card">
      <div class="algo-header">
        <div class="algo-title">
          <span>OR-Tools CP-SAT</span>
          <span style="font-size: 10px; background: #3b82f6; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: 700;">EXACT BASELINE</span>
        </div>
      </div>
      <div class="metrics-summary" id="metrics-exact"></div>
      <div class="graph-wrapper">
        <div id="graph-exact" class="graph-canvas"></div>
      </div>
    </div>
  </div>

  <div id="custom-tooltip"></div>

  <script>
    const benchmarkData = {data_json_str};
    const networks = {{}};

    const teamStyles = {{
      "t1": {{ bg: "#1e3a8a", border: "#3b82f6", text: "#bfdbfe", edge: "#3b82f6" }},
      "t2": {{ bg: "#831843", border: "#ec4899", text: "#fbcfe8", edge: "#ec4899" }},
      "t3": {{ bg: "#4c1d95", border: "#8b5cf6", text: "#ddd6fe", edge: "#8b5cf6" }},
      "t4": {{ bg: "#78350f", border: "#f59e0b", text: "#fde68a", edge: "#f59e0b" }},
      "unassigned": {{ bg: "#1e293b", border: "#475569", text: "#94a3b8", edge: "#475569" }}
    }};

    function shortenModule(mod) {{
      return mod.replace('ts-', '').replace('-service', '');
    }}

    function renderAlgoCard(algoKey, scenarioData) {{
      const algoData = scenarioData[algoKey];
      const tasks = scenarioData.tasks;
      const showDeps = document.getElementById('chkShowDeps').checked;

      // Map task info
      const taskMap = {{}};
      tasks.forEach(t => {{ taskMap[t.id] = t; }});

      // Map team sequence
      const nodeTeamMap = {{}};
      algoData.team_schedules.forEach(ts => {{
        ts.tasks_sequence.forEach((taskId, idx) => {{
          nodeTeamMap[taskId] = {{ teamId: ts.team_id, order: idx }};
        }});
      }});

      // Render Metrics
      const totalTasks = tasks.length;
      const assignedCount = Object.keys(nodeTeamMap).length;
      const unassignedCount = totalTasks - assignedCount;

      document.getElementById(`metrics-${{algoKey}}`).innerHTML = `
        <div class="metric-item">
          <div class="metric-label">Risk Resolved</div>
          <div class="metric-val">${{algoData.risk_resolved}}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">Switch Cost</div>
          <div class="metric-val ${{algoKey === 'proposed' ? 'highlight' : 'warning'}}">${{algoData.switch_cost.toFixed(1)}}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">SMS Score</div>
          <div class="metric-val">${{algoData.sms.toFixed(3)}}</div>
        </div>
        <div class="metric-item">
          <div class="metric-label">Bỏ qua</div>
          <div class="metric-val" style="color: ${{unassignedCount > 0 ? '#f59e0b' : '#94a3b8'}}">${{unassignedCount}} / ${{totalTasks}}</div>
        </div>
      `;

      // Build Horizontal Coordinates for Team Lanes
      // Row spacing & Column spacing
      const X_START = 80;
      const X_STEP = 110;
      const Y_STEP = 110;

      const teamRowIndex = {{}};
      algoData.team_schedules.forEach((ts, idx) => {{
        teamRowIndex[ts.team_id] = idx;
      }});
      const unassignedRow = algoData.team_schedules.length;

      const visNodes = [];
      const visEdges = [];

      // 1. Add Team Start Nodes (Header Node for each lane)
      algoData.team_schedules.forEach((ts, tIdx) => {{
        const tColor = teamStyles[ts.team_id] || teamStyles.t1;
        const startNodeId = `start_${{ts.team_id}}`;
        visNodes.push({{
          id: startNodeId,
          label: ts.team_id.toUpperCase(),
          x: 0,
          y: tIdx * Y_STEP,
          fixed: true,
          shape: 'circle',
          font: {{ color: '#fff', size: 12, face: 'Inter', bold: true }},
          color: {{ background: tColor.border, border: '#ffffff' }},
          borderWidth: 2,
          margin: 6,
          isMeta: true
        }});

        // Team sequence flow edges
        let prevId = startNodeId;
        ts.tasks_sequence.forEach((taskId, seqIdx) => {{
          const t = taskMap[taskId];
          if (!t) return;

          const label = `${{t.id}}\\n${{shortenModule(t.module)}}`;
          visNodes.push({{
            id: taskId,
            label: label,
            x: X_START + seqIdx * X_STEP,
            y: tIdx * Y_STEP,
            fixed: true,
            shape: 'box',
            font: {{ color: tColor.text, size: 10, face: 'Inter', bold: true }},
            color: {{ background: tColor.bg, border: tColor.border }},
            borderWidth: 2,
            margin: 6,
            taskRaw: t,
            assignedInfo: `${{ts.team_id.toUpperCase()}} (#${{seqIdx + 1}})`
          }});

          // Solid job flow edge
          visEdges.push({{
            from: prevId,
            to: taskId,
            arrows: 'to',
            color: {{ color: tColor.border, highlight: '#ffffff' }},
            width: 2.5,
            smooth: false
          }});
          prevId = taskId;
        }});
      }});

      // 2. Add Unassigned Nodes in the bottom lane
      let unassignedXIdx = 0;
      tasks.forEach(t => {{
        if (!nodeTeamMap[t.id]) {{
          const uColor = teamStyles.unassigned;
          const label = `${{t.id}}\\n${{shortenModule(t.module)}}`;
          visNodes.push({{
            id: t.id,
            label: label,
            x: X_START + (unassignedXIdx++) * X_STEP,
            y: unassignedRow * Y_STEP,
            fixed: true,
            shape: 'box',
            font: {{ color: uColor.text, size: 10, face: 'Inter' }},
            color: {{ background: uColor.bg, border: uColor.border }},
            borderWidth: 1,
            shapeProperties: {{ borderDashes: [4, 4] }},
            margin: 6,
            taskRaw: t,
            assignedInfo: 'Không được chọn (Cắt tỉa)'
          }});
        }}
      }});

      // Add label node for Unassigned row if there are unassigned tasks
      if (unassignedCount > 0) {{
        visNodes.push({{
          id: 'start_unassigned',
          label: 'SKIP',
          x: 0,
          y: unassignedRow * Y_STEP,
          fixed: true,
          shape: 'circle',
          font: {{ color: '#94a3b8', size: 10, face: 'Inter', bold: true }},
          color: {{ background: '#1e293b', border: '#475569' }},
          borderWidth: 1,
          shapeProperties: {{ borderDashes: [3, 3] }},
          margin: 6,
          isMeta: true
        }});
      }}

      // 3. Add Dependency Edges (Dashed) if enabled
      if (showDeps) {{
        tasks.forEach(t => {{
          if (t.preds && t.preds.length > 0) {{
            t.preds.forEach(predId => {{
              visEdges.push({{
                from: predId,
                to: t.id,
                arrows: {{ to: {{ enabled: true, scaleFactor: 0.6 }} }},
                dashes: [4, 5],
                color: {{ color: 'rgba(148, 163, 184, 0.4)', highlight: '#38bdf8' }},
                width: 1,
                smooth: {{ type: 'curvedCW', roundness: 0.2 }}
              }});
            }});
          }}
        }});
      }}

      const container = document.getElementById(`graph-${{algoKey}}`);
      const data = {{
        nodes: new vis.DataSet(visNodes),
        edges: new vis.DataSet(visEdges)
      }};

      const options = {{
        physics: false,
        interaction: {{
          dragNodes: true,
          hover: true,
          zoomView: true,
          dragView: true
        }}
      }};

      if (networks[algoKey]) {{
        networks[algoKey].destroy();
      }}

      const net = new vis.Network(container, data, options);
      networks[algoKey] = net;

      // Custom Clean Tooltip handling (No HTML escape errors)
      const tooltip = document.getElementById('custom-tooltip');
      net.on('hoverNode', function (params) {{
        const node = data.nodes.get(params.node);
        if (!node || node.isMeta || !node.taskRaw) return;

        const t = node.taskRaw;
        tooltip.innerHTML = `
          <div><strong>Task ID:</strong> ${{t.id}}</div>
          <div><strong>Module:</strong> ${{t.module}}</div>
          <div><strong>Xử lý bởi:</strong> ${{node.assignedInfo}}</div>
          <div><strong>Risk / Effort:</strong> ${{t.risk}} / ${{t.effort}}</div>
          <div><strong>Phụ thuộc (Preds):</strong> ${{t.preds.length ? t.preds.join(', ') : 'Gốc (None)'}}</div>
        `;
        tooltip.style.display = 'block';
      }});

      net.on('blurNode', function () {{
        tooltip.style.display = 'none';
      }});

      container.addEventListener('mousemove', (e) => {{
        if (tooltip.style.display === 'block') {{
          tooltip.style.left = (e.clientX + 14) + 'px';
          tooltip.style.top = (e.clientY + 14) + 'px';
        }}
      }});

      // Auto fit after small delay
      setTimeout(() => {{
        net.fit({{ animation: false }});
      }}, 50);
    }}

    function renderAll() {{
      const scenarioKey = document.getElementById('scenarioSelect').value;
      const scenarioData = benchmarkData[scenarioKey];
      if (!scenarioData) return;

      renderAlgoCard('exact', scenarioData);
      renderAlgoCard('proposed', scenarioData);
      renderAlgoCard('greedy_cvss', scenarioData);
    }}

    function resetViews() {{
      Object.values(networks).forEach(net => {{
        net.fit({{ animation: true }});
      }});
    }}

    window.onload = () => {{
      renderAll();
    }};
  </script>
</body>
</html>
"""
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated visualizer HTML at: {OUTPUT_HTML}")

if __name__ == "__main__":
    generate_html()

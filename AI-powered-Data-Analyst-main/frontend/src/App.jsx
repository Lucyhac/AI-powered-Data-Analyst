import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area,
} from "recharts";

const API_BASE = "";

const COLORS = [
  "#2563eb",
  "#0ea5e9",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
];

const styles = `
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root{
  --bg:#0f172a;
  --card:#111827;
  --text:#f8fafc;
  --muted:#94a3b8;
  --border:#1e293b;
  --accent:#2563eb;
}

*{
  box-sizing:border-box;
}

body,#root{
  margin:0;
  font-family:'Inter',sans-serif;
  background:var(--bg);
  color:var(--text);
}

.layout{
  display:grid;
  grid-template-columns:260px 1fr;
  min-height:100vh;
}

.sidebar{
  background:#020617;
  border-right:1px solid var(--border);
  padding:20px;
}

.logo{
  font-size:24px;
  font-weight:700;
  margin-bottom:30px;
  color:#60a5fa;
}

.nav-btn{
  width:100%;
  padding:12px;
  margin-bottom:10px;
  border:none;
  border-radius:10px;
  background:#111827;
  color:white;
  cursor:pointer;
  text-align:left;
  font-weight:600;
  transition:0.3s;
}

.nav-btn:hover{
  background:#1e293b;
}

.main{
  padding:24px;
}

.topbar{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:20px;
}

.title{
  font-size:32px;
  font-weight:700;
}

.subtitle{
  color:var(--muted);
  margin-top:4px;
}

.card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:18px;
  padding:20px;
  margin-bottom:20px;
}

.grid{
  display:grid;
  gap:20px;
}

.kpi-grid{
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
}

.kpi-card{
  border-radius:18px;
  padding:20px;
  color:white;
}

.kpi-title{
  font-size:13px;
  text-transform:uppercase;
  opacity:0.9;
}

.kpi-value{
  font-size:32px;
  font-weight:700;
  margin-top:8px;
}

.btn{
  border:none;
  padding:12px 18px;
  border-radius:12px;
  font-weight:700;
  cursor:pointer;
}

.btn-primary{
  background:#2563eb;
  color:white;
}

.upload-box{
  border:2px dashed #334155;
  padding:20px;
  border-radius:16px;
}

.table-wrap{
  overflow:auto;
}

table{
  width:100%;
  border-collapse:collapse;
}

th,td{
  padding:10px;
  border-bottom:1px solid #1e293b;
  font-size:13px;
}

th{
  color:#94a3b8;
}

.insight-card{
  background:#1e293b;
  padding:16px;
  border-radius:14px;
  border-left:5px solid #2563eb;
  margin-bottom:12px;
}

.loading{
  color:#94a3b8;
  margin-top:10px;
}

.section-title{
  margin-bottom:14px;
  font-size:20px;
  font-weight:700;
}

@media(max-width:1000px){
  .layout{
    grid-template-columns:1fr;
  }

  .sidebar{
    display:none;
  }
}
`;

const KPI = ({ title, value, color }) => (
  <div
    className="kpi-card"
    style={{
      background:`linear-gradient(135deg, ${color}, #111827)`
    }}
  >
    <div className="kpi-title">{title}</div>
    <div className="kpi-value">{value ?? "-"}</div>
  </div>
);

export default function App() {
  const [files, setFiles] = useState([]);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "AI Powered Data Analyst";
  }, []);

  const postForm = async (url) => {
    const form = new FormData();

    files.forEach((f) => {
      form.append("files", f);
    });

    return axios.post(`${API_BASE}${url}`, form, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  };

  const runAnalysis = async () => {
    if (!files.length) {
      alert("Please upload dataset");
      return;
    }

    setLoading(true);

    try {
      const res = await postForm("/analyze");
      setData(res.data);
      console.log(res.data);
    } catch (err) {
      console.error(err);
      alert("Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const rows = useMemo(() => {
    return data?.preview || [];
  }, [data]);

  return (
    <>
      <style>{styles}</style>

      <div className="layout">

        <aside className="sidebar">
          <div className="logo">Insight360 AI</div>

          <button className="nav-btn">Dashboard</button>
          <button className="nav-btn">Analytics</button>
          <button className="nav-btn">AI Insights</button>
          <button className="nav-btn">Visualizations</button>
          <button className="nav-btn">Reports</button>
          <button className="nav-btn">Settings</button>
        </aside>

        <main className="main">

          <div className="topbar">
            <div>
              <div className="title">
                AI Powered Data Analyst
              </div>

              <div className="subtitle">
                Automated Business Intelligence Dashboard
              </div>
            </div>
          </div>

          <div className="card upload-box">
            <div className="section-title">
              Upload Dataset
            </div>

            <input
              type="file"
              multiple
              accept=".csv,.xlsx,.xls"
              onChange={(e) =>
                setFiles(Array.from(e.target.files))
              }
            />

            <div style={{ marginTop:16 }}>
              <button
                className="btn btn-primary"
                onClick={runAnalysis}
                disabled={loading}
              >
                {loading
                  ? "Analyzing..."
                  : "Run AI Analysis"}
              </button>
            </div>

            {loading && (
              <div className="loading">
                AI is analyzing your dataset...
              </div>
            )}
          </div>

          <div className="grid kpi-grid">

            <KPI
              title="Total Rows"
              value={data?.kpis?.rows}
              color="#2563eb"
            />

            <KPI
              title="Total Columns"
              value={data?.kpis?.columns}
              color="#10b981"
            />

            <KPI
              title="Missing Values"
              value={data?.kpis?.missing_count}
              color="#ef4444"
            />

            <KPI
              title="Numeric Columns"
              value={data?.numeric_cols?.length}
              color="#f59e0b"
            />

          </div>

          {data && (
            <>

              <div
                className="grid"
                style={{
                  gridTemplateColumns:"2fr 1fr"
                }}
              >

                <div className="card">
                  <div className="section-title">
                    Dataset Preview
                  </div>

                  <div className="table-wrap">

                    <table>

                      <thead>
                        <tr>
                          {Object.keys(rows[0] || {}).map((col) => (
                            <th key={col}>
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody>

                        {rows.slice(0,20).map((row, idx) => (
                          <tr key={idx}>

                            {Object.keys(row).map((col) => (
                              <td key={col}>
                                {String(row[col])}
                              </td>
                            ))}

                          </tr>
                        ))}

                      </tbody>

                    </table>

                  </div>
                </div>

                <div className="card">

                  <div className="section-title">
                    AI Insights
                  </div>

                  {(data.insights || []).map((insight, idx) => (
                    <div
                      key={idx}
                      className="insight-card"
                    >
                      {insight}
                    </div>
                  ))}

                </div>

              </div>

              <div
                className="grid"
                style={{
                  gridTemplateColumns:
                    "repeat(auto-fit,minmax(350px,1fr))"
                }}
              >

                <div className="card">

                  <div className="section-title">
                    Statistical Overview
                  </div>

                  <ResponsiveContainer width="100%" height={300}>

                    <BarChart data={data.summary || []}>

                      <CartesianGrid strokeDasharray="3 3" />

                      <XAxis dataKey="column" />

                      <YAxis />

                      <Tooltip />

                      <Legend />

                      <Bar
                        dataKey="mean"
                        fill="#2563eb"
                      />

                    </BarChart>

                  </ResponsiveContainer>

                </div>

                <div className="card">

                  <div className="section-title">
                    Trend Analysis
                  </div>

                  <ResponsiveContainer width="100%" height={300}>

                    <LineChart data={data.summary || []}>

                      <CartesianGrid strokeDasharray="3 3" />

                      <XAxis dataKey="column" />

                      <YAxis />

                      <Tooltip />

                      <Line
                        type="monotone"
                        dataKey="max"
                        stroke="#10b981"
                        strokeWidth={3}
                      />

                    </LineChart>

                  </ResponsiveContainer>

                </div>

                <div className="card">

                  <div className="section-title">
                    Distribution Analysis
                  </div>

                  <ResponsiveContainer width="100%" height={300}>

                    <PieChart>

                      <Pie
                        data={data.summary || []}
                        dataKey="mean"
                        nameKey="column"
                        outerRadius={100}
                        label
                      >

                        {(data.summary || []).map((_, index) => (
                          <Cell
                            key={index}
                            fill={
                              COLORS[index % COLORS.length]
                            }
                          />
                        ))}

                      </Pie>

                      <Tooltip />

                    </PieChart>

                  </ResponsiveContainer>

                </div>

                <div className="card">

                  <div className="section-title">
                    Area Analytics
                  </div>

                  <ResponsiveContainer width="100%" height={300}>

                    <AreaChart data={data.summary || []}>

                      <CartesianGrid strokeDasharray="3 3" />

                      <XAxis dataKey="column" />

                      <YAxis />

                      <Tooltip />

                      <Area
                        type="monotone"
                        dataKey="mean"
                        stroke="#8b5cf6"
                        fill="#8b5cf6"
                      />

                    </AreaChart>

                  </ResponsiveContainer>

                </div>

              </div>

            </>
          )}

        </main>

      </div>
    </>
  );
}

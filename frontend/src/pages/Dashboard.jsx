import { useState, useEffect } from "react";
import { api } from "../api/predictions";

const s = {
  page: { minHeight: "100vh", background: "var(--black)", display: "flex" },
  sidebar: {
    width: "220px", minHeight: "100vh", borderRight: "1px solid var(--border)",
    padding: "32px 24px", display: "flex", flexDirection: "column", flexShrink: 0,
  },
  logo: {
    fontFamily: "var(--font-serif)", fontSize: "22px",
    color: "var(--gold)", marginBottom: "4px",
  },
  shopName: {
    fontSize: "11px", fontFamily: "var(--font-mono)",
    color: "var(--text-muted)", marginBottom: "40px",
    letterSpacing: "0.05em", whiteSpace: "nowrap",
    overflow: "hidden", textOverflow: "ellipsis",
  },
  navItem: (active) => ({
    padding: "9px 12px", borderRadius: "5px", marginBottom: "2px",
    cursor: "pointer", fontSize: "13px", transition: "all 0.15s",
    background: active ? "var(--surface-2)" : "transparent",
    color: active ? "var(--text-primary)" : "var(--text-secondary)",
    border: active ? "1px solid var(--border)" : "1px solid transparent",
  }),
  main: { flex: 1, padding: "40px 48px", overflowY: "auto" },
  topBar: {
    display: "flex", justifyContent: "space-between",
    alignItems: "flex-start", marginBottom: "40px",
  },
  pageTitle: {
    fontFamily: "var(--font-serif)", fontSize: "30px",
    fontWeight: 400, color: "var(--text-primary)", marginBottom: "4px",
  },
  pageSubtitle: { color: "var(--text-muted)", fontSize: "12px", fontFamily: "var(--font-mono)" },
  grid: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px", marginBottom: "32px" },
  statCard: {
    background: "var(--surface)", border: "1px solid var(--border)",
    borderRadius: "8px", padding: "20px 24px",
  },
  statLabel: { fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "10px" },
  statValue: { fontFamily: "var(--font-mono)", fontSize: "28px", fontWeight: 300, color: "var(--text-primary)" },
  statAccent: (color) => ({ color }),
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    textAlign: "left", padding: "10px 16px",
    fontSize: "10px", fontFamily: "var(--font-mono)",
    color: "var(--text-muted)", letterSpacing: "0.1em",
    textTransform: "uppercase", borderBottom: "1px solid var(--border)",
  },
  td: {
    padding: "14px 16px", fontSize: "13px",
    borderBottom: "1px solid var(--border)",
    color: "var(--text-primary)",
  },
  badge: (type) => ({
    display: "inline-block", padding: "3px 8px", borderRadius: "4px",
    fontSize: "10px", fontFamily: "var(--font-mono)", letterSpacing: "0.05em",
    background: type === "critical" ? "rgba(224,82,82,0.12)" : type === "warning" ? "rgba(201,168,76,0.12)" : "rgba(82,168,130,0.12)",
    color: type === "critical" ? "var(--red)" : type === "warning" ? "var(--gold)" : "var(--green)",
    border: `1px solid ${type === "critical" ? "rgba(224,82,82,0.3)" : type === "warning" ? "rgba(201,168,76,0.3)" : "rgba(82,168,130,0.3)"}`,
  }),
  btn: {
    padding: "8px 16px", background: "var(--gold)", color: "var(--black)",
    border: "none", borderRadius: "5px", fontSize: "12px",
    fontFamily: "var(--font-mono)", cursor: "pointer", fontWeight: 500,
  },
  btnGhost: {
    padding: "8px 16px", background: "transparent",
    color: "var(--text-secondary)", border: "1px solid var(--border)",
    borderRadius: "5px", fontSize: "12px", fontFamily: "var(--font-mono)", cursor: "pointer",
  },
  alertCard: {
    background: "rgba(224,82,82,0.06)", border: "1px solid rgba(224,82,82,0.2)",
    borderRadius: "8px", padding: "14px 18px", marginBottom: "10px",
    display: "flex", justifyContent: "space-between", alignItems: "center",
  },
  section: {
    background: "var(--surface)", border: "1px solid var(--border)",
    borderRadius: "8px", marginBottom: "24px", overflow: "hidden",
  },
  sectionHeader: {
    padding: "16px 24px", borderBottom: "1px solid var(--border)",
    display: "flex", justifyContent: "space-between", alignItems: "center",
  },
  sectionTitle: { fontSize: "13px", fontWeight: 500, color: "var(--text-primary)" },
};

export default function Dashboard({ shop, onLogout }) {
  const [tab, setTab] = useState("overview");
  const [products, setProducts] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [runningPred, setRunningPred] = useState(null);
  const [manualForm, setManualForm] = useState({ product_name: "", category: "Groceries", units_sold: "", stock_remaining: "" });
  const [manualLoading, setManualLoading] = useState(false);
  const [manualMsg, setManualMsg] = useState("");
  const [csvFile, setCsvFile] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState("");

  const CATEGORIES = ["Groceries", "Cleaning", "Electronics", "Clothing", "Furniture", "Toys", "Other"];

  useEffect(() => { loadAll(); }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [prodRes, predRes, alertRes] = await Promise.all([
        api.get(`${BASE_URL}/inventory/products/${shop.id}`),
        api.get(`${BASE_URL}/predictions/shop/${shop.id}`),
        api.get(`${BASE_URL}/predictions/alerts/${shop.id}`),
      ]);
      setProducts(prodRes.data);
      setPredictions(predRes.data);
      setAlerts(alertRes.data);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const runPrediction = async (productId) => {
    setRunningPred(productId);
    try {
      await api.get(`${BASE_URL}/predictions/run/${productId}`);
      await loadAll();
    } catch (e) { console.error(e); }
    setRunningPred(null);
  };

  const runAllPredictions = async () => {
    for (const p of products) await runPrediction(p.id);
  };

  const resolveAlert = async (alertId) => {
    await api.patch(`${BASE_URL}/predictions/alerts/${alertId}/resolve`);
    await loadAll();
  };

  const logManualSale = async () => {
    if (!manualForm.product_name || !manualForm.units_sold) return;
    setManualLoading(true);
    setManualMsg("");
    try {
      let product = products.find(p => p.name.toLowerCase() === manualForm.product_name.toLowerCase());
      if (!product) {
        const res = await api.post(`${BASE_URL}/inventory/products`, {
          shop_id: shop.id, name: manualForm.product_name,
          category: manualForm.category, current_stock: parseInt(manualForm.stock_remaining) || 0,
        });
        product = res.data;
      }
      await api.post(`${BASE_URL}/inventory/sales`, {
        product_id: product.id, shop_id: shop.id,
        date: new Date().toISOString().split("T")[0],
        units_sold: parseInt(manualForm.units_sold),
        stock_remaining: manualForm.stock_remaining ? parseInt(manualForm.stock_remaining) : null,
      });
      setManualMsg("Sale logged successfully!");
      setManualForm({ product_name: "", category: "Groceries", units_sold: "", stock_remaining: "" });
      await loadAll();
    } catch { setManualMsg("Failed to log sale."); }
    setManualLoading(false);
  };

  const uploadCSV = async () => {
    if (!csvFile) return;
    setUploadLoading(true);
    setUploadMsg("");
    try {
      const form = new FormData();
      form.append("file", csvFile);
      const res = await api.post(`/inventory/upload-csv/${shop.id}`, form, { headers: { "Content-Type": "multipart/form-data" } });
      setUploadMsg(`✓ ${res.data.products_created} products, ${res.data.sales_logs_added} records imported`);
      setCsvFile(null);
      await loadAll();
    } catch { setUploadMsg("Upload failed. Check CSV format."); }
    setUploadLoading(false);
  };

  const getPredForProduct = (pid) => predictions.find(p => p.product_id === pid);

  const getRisk = (pred) => {
    if (!pred) return "unknown";
    if (pred.days_until_stockout <= 3) return "critical";
    if (pred.days_until_stockout <= 7) return "warning";
    return "ok";
  };

  const criticalCount = predictions.filter(p => p.days_until_stockout <= 3).length;
  const warningCount = predictions.filter(p => p.days_until_stockout > 3 && p.days_until_stockout <= 7).length;

  const inputS = {
    width: "100%", background: "var(--surface-2)", border: "1px solid var(--border)",
    borderRadius: "6px", padding: "10px 14px", color: "var(--text-primary)",
    fontSize: "13px", outline: "none",
  };
  const selectS = { ...inputS };
  const labelS = {
    fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-muted)",
    letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "6px", display: "block",
  };
  const fieldS = { display: "flex", flexDirection: "column", gap: "6px" };

  return (
    <div style={s.page}>
      <div style={s.sidebar}>
        <div style={s.logo}>ShelfWise</div>
        <div style={s.shopName}>{shop.name}</div>
        {["overview", "products", "alerts", "log-sale", "import"].map(t => (
          <div key={t} style={s.navItem(tab === t)} onClick={() => setTab(t)}>
            {t === "overview" && "Overview"}
            {t === "products" && "Products"}
            {t === "alerts" && `Alerts ${alerts.length > 0 ? `(${alerts.length})` : ""}`}
            {t === "log-sale" && "Log Sale"}
            {t === "import" && "Import CSV"}
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <div
          style={{ ...s.navItem(false), color: "var(--text-muted)", fontSize: "12px" }}
          onClick={onLogout}
        >
          Switch Shop
        </div>
      </div>

      <div style={s.main}>
        {tab === "overview" && (
          <>
            <div style={s.topBar}>
              <div>
                <div style={s.pageTitle}>Good day, {shop.owner_name || "there"}.</div>
                <div style={s.pageSubtitle}>// {new Date().toDateString().toLowerCase()}</div>
              </div>
              <button style={s.btn} onClick={runAllPredictions}>
                Run All Predictions
              </button>
            </div>

            <div style={s.grid}>
              <div style={s.statCard}>
                <div style={s.statLabel}>Total Products</div>
                <div style={s.statValue}>{products.length}</div>
              </div>
              <div style={s.statCard}>
                <div style={s.statLabel}>Critical Stock</div>
                <div style={{ ...s.statValue, ...s.statAccent(criticalCount > 0 ? "var(--red)" : "var(--text-primary)") }}>
                  {criticalCount}
                </div>
              </div>
              <div style={s.statCard}>
                <div style={s.statLabel}>Active Alerts</div>
                <div style={{ ...s.statValue, ...s.statAccent(alerts.length > 0 ? "var(--gold)" : "var(--text-primary)") }}>
                  {alerts.length}
                </div>
              </div>
            </div>

            {alerts.length > 0 && (
              <div style={{ marginBottom: "32px" }}>
                <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "12px" }}>
                  Active Alerts
                </div>
                {alerts.slice(0, 3).map(a => (
                  <div key={a.id} style={s.alertCard}>
                    <div>
                      <div style={{ fontSize: "13px", marginBottom: "2px" }}>{a.message}</div>
                      <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                        {new Date(a.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button style={s.btnGhost} onClick={() => resolveAlert(a.id)}>Resolve</button>
                  </div>
                ))}
              </div>
            )}

            <div style={s.section}>
              <div style={s.sectionHeader}>
                <div style={s.sectionTitle}>Stock Overview</div>
                <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                  {predictions.length} predictions available
                </div>
              </div>
              {loading ? (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
                  Loading...
                </div>
              ) : products.length === 0 ? (
                <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "12px" }}>
                  No products yet. Import a CSV or log a sale to get started.
                </div>
              ) : (
                <table style={s.table}>
                  <thead>
                    <tr>
                      {["Product", "Category", "Stock", "Days Left", "7d Forecast", "Confidence", "Status", ""].map(h => (
                        <th key={h} style={s.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {products.map(p => {
                      const pred = getPredForProduct(p.id);
                      const risk = getRisk(pred);
                      return (
                        <tr key={p.id} style={{ transition: "background 0.15s" }}>
                          <td style={s.td}>{p.name}</td>
                          <td style={{ ...s.td, color: "var(--text-secondary)" }}>{p.category}</td>
                          <td style={{ ...s.td, fontFamily: "var(--font-mono)" }}>{p.current_stock}</td>
                          <td style={{ ...s.td, fontFamily: "var(--font-mono)", color: risk === "critical" ? "var(--red)" : risk === "warning" ? "var(--gold)" : "var(--text-primary)" }}>
                            {pred ? `${pred.days_until_stockout}d` : "—"}
                          </td>
                          <td style={{ ...s.td, fontFamily: "var(--font-mono)" }}>
                            {pred ? pred.predicted_units_7d : "—"}
                          </td>
                          <td style={{ ...s.td, fontFamily: "var(--font-mono)", color: "var(--text-secondary)" }}>
                            {pred ? `${pred.confidence_score}%` : "—"}
                          </td>
                          <td style={s.td}>
                            {pred ? (
                              <span style={s.badge(risk)}>
                                {risk === "critical" ? "Critical" : risk === "warning" ? "Low Stock" : "Healthy"}
                              </span>
                            ) : "—"}
                          </td>
                          <td style={s.td}>
                            <button
                              style={{ ...s.btnGhost, padding: "5px 10px", fontSize: "11px" }}
                              onClick={() => runPrediction(p.id)}
                              disabled={runningPred === p.id}
                            >
                              {runningPred === p.id ? "..." : "Predict"}
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {tab === "products" && (
          <>
            <div style={s.topBar}>
              <div>
                <div style={s.pageTitle}>Products</div>
                <div style={s.pageSubtitle}>// {products.length} items tracked</div>
              </div>
            </div>
            <div style={s.section}>
              <table style={s.table}>
                <thead>
                  <tr>
                    {["Product", "Category", "Price", "Current Stock", "Reorder Point", "30d Forecast", "Restock Qty"].map(h => (
                      <th key={h} style={s.th}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {products.map(p => {
                    const pred = getPredForProduct(p.id);
                    return (
                      <tr key={p.id}>
                        <td style={s.td}>{p.name}</td>
                        <td style={{ ...s.td, color: "var(--text-secondary)" }}>{p.category}</td>
                        <td style={{ ...s.td, fontFamily: "var(--font-mono)" }}>{p.price ? `₹${p.price}` : "—"}</td>
                        <td style={{ ...s.td, fontFamily: "var(--font-mono)" }}>{p.current_stock}</td>
                        <td style={{ ...s.td, fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>{p.reorder_point}</td>
                        <td style={{ ...s.td, fontFamily: "var(--font-mono)" }}>{pred ? pred.predicted_units_30d : "—"}</td>
                        <td style={{ ...s.td, fontFamily: "var(--font-mono)", color: pred?.restock_recommended ? "var(--gold)" : "var(--text-muted)" }}>
                          {pred ? pred.restock_quantity : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}

        {tab === "alerts" && (
          <>
            <div style={s.topBar}>
              <div>
                <div style={s.pageTitle}>Alerts</div>
                <div style={s.pageSubtitle}>// {alerts.length} unresolved</div>
              </div>
            </div>
            {alerts.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "13px" }}>
                No active alerts. All products are healthy.
              </div>
            ) : (
              alerts.map(a => (
                <div key={a.id} style={s.alertCard}>
                  <div>
                    <div style={{ fontSize: "13px", marginBottom: "4px" }}>{a.message}</div>
                    <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>
                      {a.alert_type.toUpperCase()} · {new Date(a.created_at).toLocaleString()}
                    </div>
                  </div>
                  <button style={s.btnGhost} onClick={() => resolveAlert(a.id)}>Resolve</button>
                </div>
              ))
            )}
          </>
        )}

        {tab === "log-sale" && (
          <>
            <div style={s.topBar}>
              <div>
                <div style={s.pageTitle}>Log a Sale</div>
                <div style={s.pageSubtitle}>// quick daily entry</div>
              </div>
            </div>
            <div style={{ maxWidth: "480px" }}>
              <div style={{ display: "grid", gap: "16px", marginBottom: "20px" }}>
                <div style={fieldS}>
                  <label style={labelS}>Product Name</label>
                  <input
                    style={inputS} list="product-list"
                    value={manualForm.product_name}
                    onChange={e => setManualForm(p => ({ ...p, product_name: e.target.value }))}
                    placeholder="e.g. Basmati Rice"
                  />
                  <datalist id="product-list">
                    {products.map(p => <option key={p.id} value={p.name} />)}
                  </datalist>
                </div>
                <div style={fieldS}>
                  <label style={labelS}>Category</label>
                  <select style={selectS} value={manualForm.category} onChange={e => setManualForm(p => ({ ...p, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div style={fieldS}>
                  <label style={labelS}>Units Sold Today</label>
                  <input style={inputS} type="number" value={manualForm.units_sold} onChange={e => setManualForm(p => ({ ...p, units_sold: e.target.value }))} placeholder="0" />
                </div>
                <div style={fieldS}>
                  <label style={labelS}>Stock Remaining (optional)</label>
                  <input style={inputS} type="number" value={manualForm.stock_remaining} onChange={e => setManualForm(p => ({ ...p, stock_remaining: e.target.value }))} placeholder="0" />
                </div>
              </div>
              {manualMsg && (
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: manualMsg.includes("success") ? "var(--green)" : "var(--red)", marginBottom: "16px" }}>
                  {manualMsg}
                </div>
              )}
              <button style={{ ...s.btn, width: "100%", padding: "12px" }} onClick={logManualSale} disabled={manualLoading}>
                {manualLoading ? "Logging..." : "Log Sale"}
              </button>
            </div>
          </>
        )}

        {tab === "import" && (
          <>
            <div style={s.topBar}>
              <div>
                <div style={s.pageTitle}>Import CSV</div>
                <div style={s.pageSubtitle}>// bulk data upload</div>
              </div>
            </div>
            <div style={{ maxWidth: "520px" }}>
              <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: "8px", padding: "20px 24px", marginBottom: "24px" }}>
                <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-muted)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: "12px" }}>
                  Expected Format
                </div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: "var(--text-secondary)", lineHeight: 2 }}>
                  date, product_name, category, units_sold, stock_remaining<br />
                  2024-01-01, Basmati Rice, Groceries, 45, 200<br />
                  2024-01-02, Surf Excel, Cleaning, 12, 80
                </div>
              </div>

              <div
                style={{ border: `1px dashed ${csvFile ? "var(--gold)" : "var(--border-bright)"}`, borderRadius: "8px", padding: "40px", textAlign: "center", cursor: "pointer", marginBottom: "16px", transition: "border-color 0.2s" }}
                onClick={() => document.getElementById("csv-import").click()}
              >
                <input id="csv-import" type="file" accept=".csv" style={{ display: "none" }} onChange={e => setCsvFile(e.target.files[0])} />
                {csvFile ? (
                  <div>
                    <div style={{ color: "var(--gold)", marginBottom: "4px", fontFamily: "var(--font-mono)" }}>{csvFile.name}</div>
                    <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>{(csvFile.size / 1024).toFixed(1)} KB</div>
                  </div>
                ) : (
                  <div style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)", fontSize: "13px" }}>
                    Click to select CSV file
                  </div>
                )}
              </div>

              {uploadMsg && (
                <div style={{ fontFamily: "var(--font-mono)", fontSize: "12px", color: uploadMsg.includes("✓") ? "var(--green)" : "var(--red)", marginBottom: "16px" }}>
                  {uploadMsg}
                </div>
              )}

              <button
                style={{ ...s.btn, width: "100%", padding: "12px", background: !csvFile ? "var(--surface-3)" : "var(--gold)", color: !csvFile ? "var(--text-muted)" : "var(--black)" }}
                onClick={uploadCSV}
                disabled={!csvFile || uploadLoading}
              >
                {uploadLoading ? "Uploading..." : "Upload & Import"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
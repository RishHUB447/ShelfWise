import { useState } from "react";
import axios from "axios";

const BASE_URL = "http://localhost:8000";

export default function Onboarding({ onShopCreated }) {
  const [step, setStep] = useState(1);
  const [shopName, setShopName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [loading, setLoading] = useState(false);
  const [shop, setShop] = useState(null);
  const [csvFile, setCsvFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");

  const createShop = async () => {
    if (!shopName.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await axios.post(`${BASE_URL}/inventory/shops`, {
        name: shopName,
        owner_name: ownerName,
      });
      setShop(res.data);
      setStep(2);
    } catch {
      setError("Failed to create shop. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const uploadCSV = async () => {
    if (!csvFile) return;
    setLoading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("file", csvFile);
      const res = await axios.post(
        `${BASE_URL}/inventory/upload-csv/${shop.id}`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setUploadResult(res.data);
      setStep(3);
    } catch {
      setError("Upload failed. Check your CSV format.");
    } finally {
      setLoading(false);
    }
  };

  const s = {
    page: {
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "40px 20px",
      background: "var(--black)",
    },
    container: { width: "100%", maxWidth: "480px" },
    logo: {
      fontFamily: "var(--font-serif)",
      fontSize: "28px",
      color: "var(--gold)",
      marginBottom: "8px",
      letterSpacing: "-0.5px",
    },
    tagline: {
      color: "var(--text-muted)",
      fontSize: "13px",
      marginBottom: "48px",
      fontFamily: "var(--font-mono)",
      letterSpacing: "0.05em",
    },
    stepIndicator: {
      display: "flex",
      gap: "6px",
      marginBottom: "40px",
    },
    dot: (active, done) => ({
      height: "2px",
      flex: 1,
      background: done ? "var(--gold)" : active ? "var(--gold)" : "var(--border)",
      opacity: done ? 1 : active ? 0.6 : 1,
      transition: "all 0.3s",
    }),
    label: {
      fontSize: "11px",
      fontFamily: "var(--font-mono)",
      color: "var(--text-muted)",
      letterSpacing: "0.1em",
      textTransform: "uppercase",
      marginBottom: "8px",
      display: "block",
    },
    input: {
      width: "100%",
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "6px",
      padding: "12px 16px",
      color: "var(--text-primary)",
      fontSize: "15px",
      outline: "none",
      marginBottom: "20px",
      transition: "border-color 0.2s",
    },
    btn: (disabled) => ({
      width: "100%",
      padding: "13px",
      background: disabled ? "var(--surface-3)" : "var(--gold)",
      color: disabled ? "var(--text-muted)" : "var(--black)",
      border: "none",
      borderRadius: "6px",
      fontSize: "14px",
      fontWeight: 500,
      cursor: disabled ? "not-allowed" : "pointer",
      transition: "all 0.2s",
      fontFamily: "var(--font-mono)",
      letterSpacing: "0.05em",
    }),
    error: {
      color: "var(--red)",
      fontSize: "12px",
      fontFamily: "var(--font-mono)",
      marginBottom: "16px",
    },
    heading: {
      fontFamily: "var(--font-serif)",
      fontSize: "24px",
      fontWeight: 400,
      marginBottom: "8px",
      color: "var(--text-primary)",
    },
    sub: {
      color: "var(--text-secondary)",
      fontSize: "13px",
      marginBottom: "32px",
      lineHeight: 1.7,
    },
    csvBox: {
      border: "1px dashed var(--border-bright)",
      borderRadius: "8px",
      padding: "32px",
      textAlign: "center",
      marginBottom: "20px",
      cursor: "pointer",
      transition: "border-color 0.2s",
    },
    templateBox: {
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "6px",
      padding: "16px",
      marginBottom: "24px",
      fontFamily: "var(--font-mono)",
      fontSize: "11px",
      color: "var(--text-secondary)",
      lineHeight: 2,
    },
    successCard: {
      background: "var(--surface)",
      border: "1px solid var(--border)",
      borderRadius: "8px",
      padding: "24px",
      marginBottom: "24px",
    },
    statRow: {
      display: "flex",
      justifyContent: "space-between",
      marginBottom: "12px",
    },
    statLabel: { color: "var(--text-secondary)", fontSize: "13px" },
    statValue: {
      color: "var(--gold)",
      fontFamily: "var(--font-mono)",
      fontSize: "13px",
    },
  };

  return (
    <div style={s.page}>
      <div style={s.container}>
        <div style={s.logo}>ShelfWise</div>
        <div style={s.tagline}>// inventory intelligence</div>

        <div style={s.stepIndicator}>
          {[1, 2, 3].map((i) => (
            <div key={i} style={s.dot(step === i, step > i)} />
          ))}
        </div>

        {step === 1 && (
          <div>
            <div style={s.heading}>Set up your shop</div>
            <div style={s.sub}>
              Tell us about your store. This takes 30 seconds.
            </div>
            <label style={s.label}>Shop name</label>
            <input
              style={s.input}
              value={shopName}
              onChange={(e) => setShopName(e.target.value)}
              placeholder="e.g. Sharma General Store"
              onKeyDown={(e) => e.key === "Enter" && createShop()}
            />
            <label style={s.label}>Your name</label>
            <input
              style={s.input}
              value={ownerName}
              onChange={(e) => setOwnerName(e.target.value)}
              placeholder="e.g. Rahul Sharma"
              onKeyDown={(e) => e.key === "Enter" && createShop()}
            />
            {error && <div style={s.error}>{error}</div>}
            <button
              style={s.btn(!shopName.trim() || loading)}
              disabled={!shopName.trim() || loading}
              onClick={createShop}
            >
              {loading ? "Creating..." : "Continue →"}
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <div style={s.heading}>Upload your sales data</div>
            <div style={s.sub}>
              Upload a CSV with your past sales. The more history you provide,
              the smarter the predictions.
            </div>

            <div style={s.templateBox}>
              date, product_name, category, units_sold, stock_remaining{"\n"}
              2024-01-01, Basmati Rice, Groceries, 45, 200{"\n"}
              2024-01-01, Surf Excel, Cleaning, 12, 80
            </div>

            <div
              style={{
                ...s.csvBox,
                borderColor: csvFile ? "var(--gold)" : "var(--border-bright)",
              }}
              onClick={() => document.getElementById("csv-input").click()}
            >
              <input
                id="csv-input"
                type="file"
                accept=".csv"
                style={{ display: "none" }}
                onChange={(e) => setCsvFile(e.target.files[0])}
              />
              {csvFile ? (
                <div>
                  <div style={{ color: "var(--gold)", marginBottom: "4px" }}>
                    {csvFile.name}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                    {(csvFile.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              ) : (
                <div>
                  <div
                    style={{ color: "var(--text-secondary)", marginBottom: "4px" }}
                  >
                    Click to select CSV file
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "12px" }}>
                    or drag and drop
                  </div>
                </div>
              )}
            </div>

            {error && <div style={s.error}>{error}</div>}

            <button
              style={s.btn(!csvFile || loading)}
              disabled={!csvFile || loading}
              onClick={uploadCSV}
            >
              {loading ? "Uploading..." : "Upload & Continue →"}
            </button>

            <button
              style={{
                ...s.btn(false),
                background: "transparent",
                color: "var(--text-muted)",
                marginTop: "12px",
                border: "1px solid var(--border)",
              }}
              onClick={() => onShopCreated(shop)}
            >
              Skip for now
            </button>
          </div>
        )}

        {step === 3 && uploadResult && (
          <div>
            <div style={s.heading}>You're all set.</div>
            <div style={s.sub}>
              ShelfWise has loaded your data and is ready to predict.
            </div>

            <div style={s.successCard}>
              <div style={s.statRow}>
                <span style={s.statLabel}>Products imported</span>
                <span style={s.statValue}>{uploadResult.products_created}</span>
              </div>
              <div style={s.statRow}>
                <span style={s.statLabel}>Sales records loaded</span>
                <span style={s.statValue}>{uploadResult.sales_logs_added}</span>
              </div>
              <div style={{ ...s.statRow, marginBottom: 0 }}>
                <span style={s.statLabel}>Shop ID</span>
                <span
                  style={{
                    ...s.statValue,
                    fontSize: "10px",
                    color: "var(--text-muted)",
                  }}
                >
                  {shop.id.slice(0, 8)}...
                </span>
              </div>
            </div>

            <button style={s.btn(false)} onClick={() => onShopCreated(shop)}>
              Open Dashboard →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
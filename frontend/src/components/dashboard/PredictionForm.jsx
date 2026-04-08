import { useState } from "react";
import { predictDemand } from "../../api/predictions";

const CATEGORIES = ["Groceries", "Electronics", "Furniture", "Clothing", "Toys"];
const REGIONS = ["North", "South", "East", "West"];
const WEATHERS = ["Sunny", "Rainy", "Cloudy", "Snowy"];
const SEASONS = ["Spring", "Summer", "Autumn", "Winter"];

export default function PredictionForm({ onResult }) {
  const [form, setForm] = useState({
    product_id: "P0001", store_id: "S001",
    category: "Groceries", region: "North",
    discount: 10, weather_condition: "Sunny",
    holiday_promotion: false, competitor_pricing: 30,
    seasonality: "Autumn",
  });
  const [loading, setLoading] = useState(false);

  const handle = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((p) => ({ ...p, [name]: type === "checkbox" ? checked : type === "number" ? parseFloat(value) : value }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await predictDemand(form);
      onResult(result, form);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%", padding: "10px 14px",
    background: "#0a0a0f", border: "1px solid var(--border)",
    borderRadius: "8px", color: "var(--text-primary)",
    fontFamily: "var(--font-main)", fontSize: "14px",
    outline: "none",
  };

  const labelStyle = {
    fontSize: "11px", fontWeight: 600,
    color: "var(--text-secondary)", textTransform: "uppercase",
    letterSpacing: "0.08em", marginBottom: "6px", display: "block"
  };

  const fieldStyle = { display: "flex", flexDirection: "column", gap: "6px" };

  return (
    <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
        <div style={fieldStyle}>
          <label style={labelStyle}>Product ID</label>
          <input style={inputStyle} name="product_id" value={form.product_id} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Store ID</label>
          <input style={inputStyle} name="store_id" value={form.store_id} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Category</label>
          <select style={inputStyle} name="category" value={form.category} onChange={handle}>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Region</label>
          <select style={inputStyle} name="region" value={form.region} onChange={handle}>
            {REGIONS.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Inventory Level</label>
          <input style={inputStyle} type="number" name="inventory_level" value={form.inventory_level} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Price ($)</label>
          <input style={inputStyle} type="number" name="price" value={form.price} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Discount (%)</label>
          <input style={inputStyle} type="number" name="discount" value={form.discount} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Competitor Pricing ($)</label>
          <input style={inputStyle} type="number" name="competitor_pricing" value={form.competitor_pricing} onChange={handle} />
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Weather</label>
          <select style={inputStyle} name="weather_condition" value={form.weather_condition} onChange={handle}>
            {WEATHERS.map(w => <option key={w}>{w}</option>)}
          </select>
        </div>
        <div style={fieldStyle}>
          <label style={labelStyle}>Seasonality</label>
          <select style={inputStyle} name="seasonality" value={form.seasonality} onChange={handle}>
            {SEASONS.map(s => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <input type="checkbox" name="holiday_promotion" checked={form.holiday_promotion} onChange={handle} id="holiday" />
        <label htmlFor="holiday" style={{ ...labelStyle, margin: 0 }}>Holiday / Promotion Active</label>
      </div>
      <button type="submit" disabled={loading} style={{
        padding: "13px", background: loading ? "var(--border)" : "var(--accent-blue)",
        border: "none", borderRadius: "10px", color: "#fff",
        fontFamily: "var(--font-main)", fontWeight: 600, fontSize: "15px",
        cursor: loading ? "not-allowed" : "pointer", transition: "all 0.2s",
      }}>
        {loading ? "Predicting..." : "Run Prediction"}
      </button>
    </form>
  );
}
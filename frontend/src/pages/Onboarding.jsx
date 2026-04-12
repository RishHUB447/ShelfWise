import { useState } from "react";
import { register, login } from "../api/predictions";

export default function Onboarding({ onShopCreated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ shop_name: "", owner_name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handle = (e) => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  const submit = async () => {
    setLoading(true);
    setError("");
    try {
      const res = mode === "register"
        ? await register(form)
        : await login({ email: form.email, password: form.password });
      localStorage.setItem("shelfwise_token", res.data.token);
      onShopCreated(res.data.shop);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const s = {
    page: {
      minHeight: "100vh", display: "flex",
      alignItems: "center", justifyContent: "center",
      padding: "40px 20px", background: "var(--black)",
    },
    container: { width: "100%", maxWidth: "420px" },
    logo: {
      fontFamily: "var(--font-serif)", fontSize: "32px",
      color: "var(--gold)", marginBottom: "4px", letterSpacing: "-0.5px",
    },
    tagline: {
      color: "var(--text-muted)", fontSize: "12px",
      fontFamily: "var(--font-mono)", letterSpacing: "0.08em", marginBottom: "48px",
    },
    tabs: { display: "flex", marginBottom: "32px", borderBottom: "1px solid var(--border)" },
    tab: (active) => ({
      padding: "10px 20px", fontSize: "13px", cursor: "pointer",
      fontFamily: "var(--font-mono)", border: "none", background: "transparent",
      color: active ? "var(--text-primary)" : "var(--text-muted)",
      borderBottom: active ? "1px solid var(--gold)" : "1px solid transparent",
      marginBottom: "-1px", transition: "all 0.2s",
    }),
    label: {
      fontSize: "10px", fontFamily: "var(--font-mono)", color: "var(--text-muted)",
      letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: "6px", display: "block",
    },
    input: {
      width: "100%", background: "var(--surface)", border: "1px solid var(--border)",
      borderRadius: "6px", padding: "12px 16px", color: "var(--text-primary)",
      fontSize: "14px", outline: "none", marginBottom: "16px", transition: "border-color 0.2s",
    },
    btn: (disabled) => ({
      width: "100%", padding: "13px",
      background: disabled ? "var(--surface-3)" : "var(--gold)",
      color: disabled ? "var(--text-muted)" : "var(--black)",
      border: "none", borderRadius: "6px", fontSize: "13px",
      fontFamily: "var(--font-mono)", fontWeight: 500,
      cursor: disabled ? "not-allowed" : "pointer", transition: "all 0.2s",
      letterSpacing: "0.05em",
    }),
    error: {
      color: "var(--red)", fontSize: "12px",
      fontFamily: "var(--font-mono)", marginBottom: "16px",
    },
  };

  const isDisabled = loading || !form.email || !form.password || (mode === "register" && !form.shop_name);

  return (
    <div style={s.page}>
      <div style={s.container}>
        <div style={s.logo}>ShelfWise</div>
        <div style={s.tagline}>// inventory intelligence</div>

        <div style={s.tabs}>
          <button style={s.tab(mode === "login")} onClick={() => { setMode("login"); setError(""); }}>
            Login
          </button>
          <button style={s.tab(mode === "register")} onClick={() => { setMode("register"); setError(""); }}>
            Register
          </button>
        </div>

        {mode === "register" && (
          <>
            <label style={s.label}>Shop Name</label>
            <input style={s.input} name="shop_name" value={form.shop_name} onChange={handle} placeholder="e.g. Sharma General Store" />
            <label style={s.label}>Your Name</label>
            <input style={s.input} name="owner_name" value={form.owner_name} onChange={handle} placeholder="e.g. Rahul Sharma" />
          </>
        )}

        <label style={s.label}>Email</label>
        <input style={s.input} name="email" type="email" value={form.email} onChange={handle} placeholder="you@example.com" onKeyDown={e => e.key === "Enter" && submit()} />

        <label style={s.label}>Password</label>
        <input style={s.input} name="password" type="password" value={form.password} onChange={handle} placeholder="••••••••" onKeyDown={e => e.key === "Enter" && submit()} />

        {error && <div style={s.error}>{error}</div>}

        <button style={s.btn(isDisabled)} disabled={isDisabled} onClick={submit}>
          {loading ? "Please wait..." : mode === "login" ? "Login →" : "Create Shop →"}
        </button>
      </div>
    </div>
  );
}
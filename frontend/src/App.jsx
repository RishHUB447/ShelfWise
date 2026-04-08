import { useState } from "react";
import PredictionForm from "./components/dashboard/PredictionForm";
import { predictDemand, getPredictionHistory } from "./api/predictions";
import "./App.css";

function App() {
  const [currentResult, setCurrentResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [error, setError] = useState(null);

  const handlePredictionResult = async (result, formData) => {
    setCurrentResult(result);
    setError(null);
    // Automatically fetch updated history for this product
    await fetchHistory(result.product_id);
  };

  const fetchHistory = async (productId) => {
    if (!productId) return;
    setLoadingHistory(true);
    try {
      const historyData = await getPredictionHistory(productId);
      setHistory(historyData);
    } catch (err) {
      console.error("Failed to load history:", err);
      setError("Could not load prediction history.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="app-container">
      <header className="dashboard-header">
        <div className="header-content">
          <h1>
            <span className="gradient-text">StockPulse</span> Inventory AI
          </h1>
          <p className="subtitle">Demand prediction engine with XGBoost</p>
        </div>
        <div className="header-badge">
          <span className="badge">Real-time ML</span>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="form-section glass-card">
          <div className="section-title">
            <span className="title-icon">📊</span>
            <h2>Prediction Parameters</h2>
          </div>
          <PredictionForm onResult={handlePredictionResult} />
        </div>

        {currentResult && (
          <div className="result-section glass-card">
            <div className="section-title">
              <span className="title-icon">🔮</span>
              <h2>Live Forecast</h2>
            </div>
            <div className="result-grid">
              <div className="result-card">
                <div className="result-label">Product</div>
                <div className="result-value">{currentResult.product_id}</div>
                <div className="result-sub">Store: {currentResult.store_id}</div>
              </div>
              <div className="result-card highlight">
                <div className="result-label">Predicted Demand</div>
                <div className="result-value large">
                  {currentResult.predicted_units.toLocaleString()} units
                </div>
              </div>
              <div className="result-card">
                <div className="result-label">Confidence Score</div>
                <div className="result-value">
                  <div className="confidence-bar">
                    <div
                      className="confidence-fill"
                      style={{ width: `${currentResult.confidence_score}%` }}
                    ></div>
                  </div>
                  <span className="confidence-text">
                    {currentResult.confidence_score}%
                  </span>
                </div>
              </div>
              <div className="result-card">
                <div className="result-label">Restock Suggestion</div>
                <div
                  className={`result-value restock-badge ${
                    currentResult.restock_recommended ? "urgent" : "safe"
                  }`}
                >
                  {currentResult.restock_recommended
                    ? "⚠️ Restock Recommended"
                    : "✅ Stock Adequate"}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="history-section glass-card">
          <div className="section-title">
            <span className="title-icon">📜</span>
            <h2>Prediction History</h2>
            {currentResult && (
              <button
                className="refresh-btn"
                onClick={() => fetchHistory(currentResult.product_id)}
                disabled={loadingHistory}
              >
                ↻
              </button>
            )}
          </div>
          {loadingHistory ? (
            <div className="loading-history">Loading history...</div>
          ) : history.length === 0 ? (
            <div className="empty-history">
              {currentResult
                ? "No past predictions for this product yet."
                : "Submit a prediction to see history."}
            </div>
          ) : (
            <div className="history-table-wrapper">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Product ID</th>
                    <th>Store</th>
                    <th>Predicted Units</th>
                    <th>Confidence</th>
                    <th>Restock</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((pred, idx) => (
                    <tr key={idx}>
                      <td>{formatDate(pred.predicted_for_date)}</td>
                      <td>{pred.product_id}</td>
                      <td>{pred.store_id}</td>
                      <td>{Math.round(pred.predicted_units)}</td>
                      <td>
                        <span className="confidence-chip">
                          {pred.confidence_score}%
                        </span>
                      </td>
                      <td>
                        {pred.restock_recommended ? (
                          <span className="status-badge warn">Yes</span>
                        ) : (
                          <span className="status-badge success">No</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {error && <div className="error-message">{error}</div>}
        </div>
      </main>
    </div>
  );
}

export default App;
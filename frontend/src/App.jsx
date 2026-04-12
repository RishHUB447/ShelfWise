import { useState } from "react";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";

export default function App() {
  const [shop, setShop] = useState(() => {
    const token = localStorage.getItem("shelfwise_token");
    const saved = localStorage.getItem("shelfwise_shop");
    return token && saved ? JSON.parse(saved) : null;
  });

  const handleShopCreated = (shopData) => {
    localStorage.setItem("shelfwise_shop", JSON.stringify(shopData));
    setShop(shopData);
  };

  const handleLogout = () => {
    localStorage.removeItem("shelfwise_token");
    localStorage.removeItem("shelfwise_shop");
    setShop(null);
  };

  if (!shop) return <Onboarding onShopCreated={handleShopCreated} />;
  return <Dashboard shop={shop} onLogout={handleLogout} />;
}
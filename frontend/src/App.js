import React, { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import Marketplace from "./pages/Marketplace";
import BountyBoard from "./pages/BountyBoard";
import Scoreboard from "./pages/Scoreboard";
import HousesPage from "./pages/HousesPage";
import PaymentSuccess from "./pages/PaymentSuccess";
import AdminPanel from "./pages/AdminPanel";
import CurrencyExchange from "./pages/CurrencyExchange";
import TitleDeeds from "./pages/TitleDeeds";
import { Toaster } from "@/components/ui/sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export { API, BACKEND_URL };

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const token = localStorage.getItem("token");
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem("token");
      }
    }
    setLoading(false);
  };

  const login = (userData, token) => {
    localStorage.setItem("token", token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-emerald-400 text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster position="top-right" />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={user ? <Navigate to="/dashboard" /> : <LandingPage />} />
          <Route path="/auth" element={user ? <Navigate to="/dashboard" /> : <AuthPage onLogin={login} />} />
          <Route path="/dashboard" element={user ? <Dashboard user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/marketplace" element={user ? <Marketplace user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/bounties" element={user ? <BountyBoard user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/scoreboard" element={user ? <Scoreboard user={user} onLogout={logout} /> : <Navigate to="/auth" />} />
          <Route path="/houses" element={user ? <HousesPage user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/payment-success" element={user ? <PaymentSuccess user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/exchange" element={user ? <CurrencyExchange user={user} onLogout={logout} onUpdateUser={checkAuth} /> : <Navigate to="/auth" />} />
          <Route path="/admin" element={user && user.is_admin ? <AdminPanel user={user} onLogout={logout} /> : <Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;

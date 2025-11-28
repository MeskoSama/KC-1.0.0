import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Coins, Trophy, Home, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const Dashboard = ({ user, onLogout, onUpdateUser }) => {
  const [stats, setStats] = useState({
    totalBalance: 0,
    ranksOwned: 0,
    housesOwned: 0,
    transactions: 0
  });

  useEffect(() => {
    loadStats();
  }, [user]);

  const loadStats = () => {
    const totalBalance = Object.values(user.balances).reduce((sum, val) => sum + val, 0);
    setStats({
      totalBalance,
      ranksOwned: user.owned_ranks?.length || 0,
      housesOwned: user.owned_houses?.length || 0,
      transactions: user.total_transactions || 0
    });
  };

  const statCards = [
    {
      title: 'Primary Balance',
      value: `${user.balances[user.currency_type].toFixed(2)} ${user.currency_type}`,
      icon: Coins,
      color: 'emerald'
    },
    {
      title: 'Ranks Owned',
      value: stats.ranksOwned,
      icon: Trophy,
      color: 'amber'
    },
    {
      title: 'Houses Owned',
      value: stats.housesOwned,
      icon: Home,
      color: 'cyan'
    },
    {
      title: 'Total Transactions',
      value: stats.transactions,
      icon: TrendingUp,
      color: 'rose'
    }
  ];

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-slate-200">Welcome back, </span>
            <span className="text-purple-400 glow-text" data-testid="dashboard-username">{user.username}</span>
          </h1>
          <p className="text-slate-400 text-lg">Here's your trading overview</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {statCards.map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="stat-card" data-testid={`stat-${stat.title.toLowerCase().replace(' ', '-')}`}>
                <div className="flex items-center justify-between mb-4">
                  <Icon size={32} className={`text-${stat.color}-400`} />
                  <div className={`text-3xl font-black text-${stat.color}-400`}>{stat.value}</div>
                </div>
                <h3 className="text-slate-400 font-medium">{stat.title}</h3>
              </div>
            );
          })}
        </div>

        {/* All Balances */}
        <Card className="glass-card border-purple-600/20 mb-8">
          <CardHeader>
            <CardTitle className="text-2xl">All Currency Balances</CardTitle>
            <CardDescription>Your balances across all server currencies</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(user.balances).map(([currency, balance]) => (
                <div
                  key={currency}
                  className={`p-4 rounded-lg ${
                    currency === user.currency_type
                      ? 'bg-purple-600/20 border-2 border-purple-600'
                      : 'bg-slate-800/50 border border-slate-700'
                  }`}
                  data-testid={`balance-${currency.toLowerCase()}`}
                >
                  <div className="text-sm text-slate-400 mb-1">{currency}</div>
                  <div className="text-2xl font-bold text-purple-400">{balance.toFixed(2)}</div>
                  {currency === user.currency_type && (
                    <div className="text-xs text-purple-500 mt-1">Primary</div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Owned Ranks */}
        {user.owned_ranks && user.owned_ranks.length > 0 && (
          <Card className="glass-card border-amber-600/20 mb-8">
            <CardHeader>
              <CardTitle className="text-2xl">Your Ranks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                {user.owned_ranks.map((rank, index) => (
                  <div
                    key={index}
                    className="px-4 py-2 bg-amber-600/20 border border-amber-600 rounded-lg font-bold text-amber-400"
                    data-testid={`owned-rank-${index}`}
                  >
                    {rank}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <Card className="glass-card border-purple-600/20">
          <CardHeader>
            <CardTitle className="text-2xl">Quick Actions</CardTitle>
            <CardDescription>What would you like to do?</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <a
                href="/portfolio"
                className="p-6 bg-emerald-600/10 hover:bg-emerald-600/20 border border-emerald-600/30 rounded-lg transition-all"
                data-testid="quick-action-portfolio"
              >
                <h3 className="text-lg font-bold text-emerald-400 mb-2">📊 Portfolio</h3>
                <p className="text-slate-400 text-sm">View your complete wealth breakdown</p>
              </a>
              <a
                href="/marketplace"
                className="p-6 bg-purple-600/10 hover:bg-purple-600/20 border border-purple-600/30 rounded-lg transition-all"
                data-testid="quick-action-marketplace"
              >
                <h3 className="text-lg font-bold text-purple-400 mb-2">💳 Buy Currency</h3>
                <p className="text-slate-400 text-sm">Purchase in-game currency with VISA/MASTERCARD</p>
              </a>
              <a
                href="/houses"
                className="p-6 bg-cyan-600/10 hover:bg-cyan-600/20 border border-cyan-600/30 rounded-lg transition-all"
                data-testid="quick-action-houses"
              >
                <h3 className="text-lg font-bold text-cyan-400 mb-2">🏘️ Browse Houses</h3>
                <p className="text-slate-400 text-sm">Find your dream Minecraft property</p>
              </a>
              <a
                href="/transactions"
                className="p-6 bg-amber-600/10 hover:bg-amber-600/20 border border-amber-600/30 rounded-lg transition-all"
                data-testid="quick-action-transactions"
              >
                <h3 className="text-lg font-bold text-amber-400 mb-2">📜 History</h3>
                <p className="text-slate-400 text-sm">View all your transactions</p>
              </a>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

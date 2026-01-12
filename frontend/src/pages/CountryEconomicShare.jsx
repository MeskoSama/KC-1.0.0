import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Globe, Landmark, TrendingUp, Wallet, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const CountryEconomicShare = ({ user, onLogout }) => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEconomicShares();
  }, []);

  const loadEconomicShares = async () => {
    try {
      const response = await axios.get(`${API}/countries/economic-shares/all`);
      setCountries(response.data.countries || []);
    } catch (error) {
      console.error('Failed to load economic shares:', error);
    } finally {
      setLoading(false);
    }
  };

  const prepareChartData = (metric) => {
    return countries
      .filter(c => (c.economic_share?.[metric] || 0) > 0)
      .map(c => ({
        name: c.name,
        value: c.economic_share?.[metric] || 0,
        color: c.color || '#9333ea'
      }));
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-900 border border-purple-600/30 p-3 rounded-lg shadow-xl">
          <p className="text-white font-bold">{payload[0].name}</p>
          <p className="text-purple-400">{payload[0].value.toFixed(2)}%</p>
        </div>
      );
    }
    return null;
  };

  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, name }) => {
    if (percent < 0.05) return null; // Don't show label for small slices
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    
    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        className="text-xs font-bold"
      >
        {(percent * 100).toFixed(1)}%
      </text>
    );
  };

  const PieChartCard = ({ title, description, icon, metric, colorClass }) => {
    const data = prepareChartData(metric);
    const hasData = data.length > 0 && data.some(d => d.value > 0);

    return (
      <Card className={`glass-card border-${colorClass}-600/20`}>
        <CardHeader>
          <CardTitle className={`text-xl flex items-center gap-2 text-${colorClass}-400`}>
            {icon}
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          {hasData ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderCustomLabel}
                    outerRadius={120}
                    innerRadius={60}
                    fill="#8884d8"
                    dataKey="value"
                    animationDuration={800}
                  >
                    {data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(0,0,0,0.3)" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    formatter={(value, entry) => (
                      <span className="text-slate-300">{value}</span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center text-slate-500">
              No data available
            </div>
          )}
          
          {/* Data Table */}
          <div className="mt-4 space-y-2">
            {countries.map((country) => (
              <div
                key={country.id}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-800/30 hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: country.color || '#9333ea' }}
                  />
                  <span className="text-slate-300 text-sm">{country.name}</span>
                </div>
                <span className={`font-mono font-bold text-${colorClass}-400`}>
                  {(country.economic_share?.[metric] || 0).toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen kapitalist-bg">
        <Navbar user={user} onLogout={onLogout} />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <RefreshCw className="animate-spin text-purple-400" size={32} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen kapitalist-bg">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
            📊 Economic Share
          </h1>
          <p className="text-slate-400 mt-2">Countries' economic shares in the game world</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="glass-card border-blue-600/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Total Countries</p>
                  <p className="text-2xl font-bold text-blue-400">{countries.length}</p>
                </div>
                <Globe className="text-blue-400" size={32} />
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card border-green-600/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Active Traders</p>
                  <p className="text-2xl font-bold text-green-400">
                    {countries.filter(c => (c.economic_share?.trade || 0) > 0).length}
                  </p>
                </div>
                <TrendingUp className="text-green-400" size={32} />
              </div>
            </CardContent>
          </Card>
          <Card className="glass-card border-purple-600/20">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Reserve Holders</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {countries.filter(c => (c.economic_share?.global_reserves || 0) > 0).length}
                  </p>
                </div>
                <Landmark className="text-purple-400" size={32} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Country Color Legend */}
        <Card className="glass-card border-purple-600/20 mb-8">
          <CardHeader>
            <CardTitle className="text-lg">Country Colors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {countries.map((country) => (
                <div key={country.id} className="flex items-center gap-2">
                  <div
                    className="w-6 h-6 rounded-lg shadow-lg"
                    style={{ backgroundColor: country.color || '#9333ea' }}
                  />
                  <span className="text-slate-300">{country.name}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Pie Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <PieChartCard
            title="Bank Account Flow"
            description="Share of money flow through bank accounts"
            icon={<Wallet size={24} />}
            metric="bank_flow"
            colorClass="blue"
          />
          <PieChartCard
            title="Trade Share"
            description="Share in global trade activities"
            icon={<TrendingUp size={24} />}
            metric="trade"
            colorClass="green"
          />
          <PieChartCard
            title="Global Reserves"
            description="Share of global currency reserves"
            icon={<Landmark size={24} />}
            metric="global_reserves"
            colorClass="purple"
          />
        </div>

        {/* Note */}
        <p className="text-center text-slate-500 text-sm mt-8">
          Economic shares are updated by administrators and reflect the current state of the game economy.
        </p>
      </div>
    </div>
  );
};

export default CountryEconomicShare;

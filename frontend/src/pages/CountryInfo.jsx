import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Landmark, TrendingUp, TrendingDown, Coins, Building2, Factory, ShoppingCart, Users, Cog, Sparkles, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const CountryInfo = ({ user, onLogout }) => {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState(null);

  useEffect(() => {
    loadCountries();
  }, []);

  const loadCountries = async () => {
    try {
      const response = await axios.get(`${API}/countries`);
      setCountries(response.data.countries || []);
      if (response.data.countries?.length > 0) {
        setSelectedCountry(response.data.countries[0]);
      }
    } catch (error) {
      console.error('Failed to load countries:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toLocaleString();
  };

  const getIncomeIcon = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('factory')) return <Factory size={16} />;
    if (lower.includes('industrial')) return <Cog size={16} />;
    if (lower.includes('tax')) return <Coins size={16} />;
    if (lower.includes('customs')) return <ShoppingCart size={16} />;
    if (lower.includes('trade')) return <TrendingUp size={16} />;
    if (lower.includes('business')) return <Building2 size={16} />;
    if (lower.includes('guild')) return <Users size={16} />;
    if (lower.includes('infrastructure')) return <Landmark size={16} />;
    return <Coins size={16} />;
  };

  const getExpenseIcon = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('consumption')) return <ShoppingCart size={16} />;
    if (lower.includes('maintenance')) return <Cog size={16} />;
    if (lower.includes('salaries') || lower.includes('energy')) return <Users size={16} />;
    if (lower.includes('ministries') || lower.includes('council')) return <Building2 size={16} />;
    if (lower.includes('government')) return <Landmark size={16} />;
    if (lower.includes('artificial') || lower.includes('ai')) return <Sparkles size={16} />;
    return <TrendingDown size={16} />;
  };

  const getIndependenceColor = (status) => {
    switch (status) {
      case 'independent country': return 'bg-green-600/20 text-green-400 border-green-600/30';
      case 'independent region': return 'bg-blue-600/20 text-blue-400 border-blue-600/30';
      case 'independent area': return 'bg-cyan-600/20 text-cyan-400 border-cyan-600/30';
      case 'independent settlement': return 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30';
      case 'non-independent settlement': return 'bg-red-600/20 text-red-400 border-red-600/30';
      default: return 'bg-gray-600/20 text-gray-400 border-gray-600/30';
    }
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
            🏛️ Country Information
          </h1>
          <p className="text-slate-400 mt-2">Treasury status, income and expenses for all nations</p>
        </div>

        {/* Country Selector Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {countries.map((country) => (
            <button
              key={country.id}
              onClick={() => setSelectedCountry(country)}
              className={`px-4 py-2 rounded-lg transition-all font-medium ${
                selectedCountry?.id === country.id
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/30'
                  : 'bg-slate-800/50 text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'
              }`}
              style={{
                borderLeft: `4px solid ${country.color || '#9333ea'}`
              }}
            >
              {country.name} ({country.currency})
            </button>
          ))}
        </div>

        {selectedCountry && (
          <div className="space-y-6">
            {/* Country Header */}
            <Card className="glass-card border-purple-600/20" style={{ borderTopColor: selectedCountry.color, borderTopWidth: '4px' }}>
              <CardHeader>
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <CardTitle className="text-3xl flex items-center gap-3">
                      <Landmark className="text-purple-400" style={{ color: selectedCountry.color }} />
                      {selectedCountry.name}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2 mt-2">
                      <Badge className={getIndependenceColor(selectedCountry.independence_status)}>
                        {selectedCountry.independence_status}
                      </Badge>
                      <span className="text-slate-500">|</span>
                      <span className="font-mono text-purple-400">{selectedCountry.currency}</span>
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <p className="text-slate-400 text-sm">Treasury Balance</p>
                    <p className="text-3xl font-bold text-green-400">
                      {formatNumber(selectedCountry.treasury)} {selectedCountry.currency}
                    </p>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Income and Expenses Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Income */}
              <Card className="glass-card border-green-600/20">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2 text-green-400">
                    <TrendingUp />
                    Income
                  </CardTitle>
                  <CardDescription>Weekly revenue sources</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedCountry.income?.length > 0 ? (
                      selectedCountry.income.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-green-900/10 rounded-lg border border-green-600/20">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-green-600/20 rounded-lg text-green-400">
                              {getIncomeIcon(item.name)}
                            </div>
                            <span className="text-slate-200">{item.name}</span>
                          </div>
                          <span className="font-mono text-green-400 font-bold">
                            +{formatNumber(item.amount)} {selectedCountry.currency}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-center py-4">No income items</p>
                    )}
                    
                    {/* Total Income */}
                    <div className="flex items-center justify-between p-4 bg-green-600/20 rounded-lg border-2 border-green-500/30 mt-4">
                      <span className="text-lg font-bold text-green-400">Total Income</span>
                      <span className="text-xl font-mono font-bold text-green-400">
                        +{formatNumber(selectedCountry.total_income || 0)} {selectedCountry.currency}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Expenses */}
              <Card className="glass-card border-red-600/20">
                <CardHeader>
                  <CardTitle className="text-xl flex items-center gap-2 text-red-400">
                    <TrendingDown />
                    Expenses
                  </CardTitle>
                  <CardDescription>Weekly expenditures</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {selectedCountry.expenses?.length > 0 ? (
                      selectedCountry.expenses.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 bg-red-900/10 rounded-lg border border-red-600/20">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-red-600/20 rounded-lg text-red-400">
                              {getExpenseIcon(item.name)}
                            </div>
                            <span className="text-slate-200">{item.name}</span>
                          </div>
                          <span className="font-mono text-red-400 font-bold">
                            -{formatNumber(item.amount)} {selectedCountry.currency}
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-center py-4">No expense items</p>
                    )}
                    
                    {/* Total Expenses */}
                    <div className="flex items-center justify-between p-4 bg-red-600/20 rounded-lg border-2 border-red-500/30 mt-4">
                      <span className="text-lg font-bold text-red-400">Total Expenses</span>
                      <span className="text-xl font-mono font-bold text-red-400">
                        -{formatNumber(selectedCountry.total_expenses || 0)} {selectedCountry.currency}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Weekly Net Impact */}
            <Card className={`glass-card ${(selectedCountry.weekly_net || 0) >= 0 ? 'border-green-600/30' : 'border-red-600/30'}`}>
              <CardContent className="pt-6">
                <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className={`p-4 rounded-xl ${(selectedCountry.weekly_net || 0) >= 0 ? 'bg-green-600/20' : 'bg-red-600/20'}`}>
                      {(selectedCountry.weekly_net || 0) >= 0 ? (
                        <TrendingUp size={32} className="text-green-400" />
                      ) : (
                        <TrendingDown size={32} className="text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-slate-400">Weekly Net Impact on Treasury</p>
                      <p className="text-sm text-slate-500">Updates automatically every week</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-4xl font-bold font-mono ${(selectedCountry.weekly_net || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {(selectedCountry.weekly_net || 0) >= 0 ? '+' : ''}{formatNumber(selectedCountry.weekly_net || 0)} {selectedCountry.currency}
                    </p>
                    <p className="text-slate-500 text-sm mt-1">per week</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Last Update Info */}
            {selectedCountry.last_treasury_update && (
              <p className="text-center text-slate-500 text-sm">
                Last treasury update: {new Date(selectedCountry.last_treasury_update).toLocaleString()}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CountryInfo;

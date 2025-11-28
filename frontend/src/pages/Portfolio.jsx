import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { TrendingUp, Home, Coins, Wallet, PieChart, DollarSign } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const Portfolio = ({ user, onLogout }) => {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPortfolio();
  }, []);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/portfolio/summary`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPortfolioData(response.data);
    } catch (error) {
      console.error('Failed to load portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="kapitalist-bg min-h-screen pb-12">
        <Navbar user={user} onLogout={onLogout} />
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <p className="text-slate-400 text-lg">Loading portfolio...</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="kapitalist-bg min-h-screen pb-12">
        <Navbar user={user} onLogout={onLogout} />
        <div className="container mx-auto px-4">
          <div className="text-center py-12">
            <p className="text-slate-400 text-lg">Failed to load portfolio data</p>
          </div>
        </div>
      </div>
    );
  }

  const { net_worth, breakdown, stats } = portfolioData;

  const calculatePercentage = (value, total) => {
    if (total === 0) return 0;
    return ((value / total) * 100).toFixed(1);
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">Portfolio Overview</span>
          </h1>
          <p className="text-slate-400 text-lg">Your complete wealth breakdown</p>
        </div>

        {/* Net Worth Summary */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="glass-card border-purple-600/30 bg-gradient-to-br from-purple-900/30 to-purple-600/10">
            <CardHeader>
              <CardTitle className="text-sm text-purple-300 flex items-center gap-2">
                <Wallet size={18} />
                Total Net Worth
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-purple-400 mb-1">
                {net_worth.total_grp.toFixed(2)} GRP
              </div>
              <div className="text-sm text-slate-400">
                ≈ ${net_worth.total_usd.toFixed(2)} USD
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card border-emerald-600/30">
            <CardHeader>
              <CardTitle className="text-sm text-emerald-300 flex items-center gap-2">
                <Coins size={18} />
                Currency Value
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-emerald-400 mb-1">
                {net_worth.currency_value.toFixed(2)}
              </div>
              <div className="text-sm text-slate-400">
                {calculatePercentage(net_worth.currency_value, net_worth.total_grp)}% of portfolio
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card border-blue-600/30">
            <CardHeader>
              <CardTitle className="text-sm text-blue-300 flex items-center gap-2">
                <TrendingUp size={18} />
                Investments
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-blue-400 mb-1">
                {net_worth.investments_value.toFixed(2)}
              </div>
              <div className="text-sm text-slate-400">
                {calculatePercentage(net_worth.investments_value, net_worth.total_grp)}% of portfolio
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card border-cyan-600/30">
            <CardHeader>
              <CardTitle className="text-sm text-cyan-300 flex items-center gap-2">
                <Home size={18} />
                Properties
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-black text-cyan-400 mb-1">
                {net_worth.properties_value.toFixed(2)}
              </div>
              <div className="text-sm text-slate-400">
                {calculatePercentage(net_worth.properties_value, net_worth.total_grp)}% of portfolio
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Breakdown */}
        <Tabs defaultValue="currencies" className="mb-6">
          <TabsList className="bg-slate-800/50 border border-slate-700 mb-6">
            <TabsTrigger value="currencies" className="data-[state=active]:bg-purple-600">
              Currencies
            </TabsTrigger>
            <TabsTrigger value="investments" className="data-[state=active]:bg-purple-600">
              Investments
            </TabsTrigger>
            <TabsTrigger value="properties" className="data-[state=active]:bg-purple-600">
              Properties
            </TabsTrigger>
          </TabsList>

          {/* Currencies Tab */}
          <TabsContent value="currencies">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Coins className="text-emerald-400" />
                  Currency Holdings
                </CardTitle>
                <CardDescription>Your balances across all server currencies</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(breakdown.currencies).map(([currency, data]) => (
                    <div
                      key={currency}
                      className="flex items-center justify-between p-4 bg-slate-800/30 border border-slate-700 rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-lg flex items-center justify-center font-black text-lg ${
                          currency === user.currency_type 
                            ? 'bg-purple-600/30 text-purple-400 border-2 border-purple-600' 
                            : 'bg-slate-800 text-slate-400'
                        }`}>
                          {currency}
                        </div>
                        <div>
                          <h3 className="text-white font-semibold">{currency}</h3>
                          <p className="text-slate-400 text-sm">
                            {currency === user.currency_type && '⭐ Primary Currency'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-emerald-400">
                          {data.balance.toFixed(2)}
                        </div>
                        <div className="text-sm text-slate-400">
                          ≈ {data.grp_value.toFixed(2)} GRP
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Investments Tab */}
          <TabsContent value="investments">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <TrendingUp className="text-blue-400" />
                  Investment Portfolio
                </CardTitle>
                <CardDescription>
                  {stats.active_investments} active investment{stats.active_investments !== 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {breakdown.investments.length === 0 ? (
                  <div className="text-center py-12">
                    <TrendingUp size={48} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400 text-lg">No investments yet</p>
                    <p className="text-slate-500 text-sm mt-2">
                      Visit the Investments page to start trading
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {breakdown.investments.map((investment) => (
                      <div
                        key={investment.symbol}
                        className="flex items-center justify-between p-4 bg-slate-800/30 border border-slate-700 rounded-lg"
                      >
                        <div>
                          <h3 className="text-white font-bold text-lg">{investment.symbol}</h3>
                          <p className="text-slate-400 text-sm">{investment.name}</p>
                          <div className="flex gap-3 mt-2 text-sm">
                            <span className="text-slate-500">
                              Qty: <span className="text-slate-300">{investment.quantity}</span>
                            </span>
                            <span className="text-slate-500">
                              Price: <span className="text-slate-300">{investment.current_price} {investment.currency}</span>
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-blue-400">
                            {investment.total_value.toFixed(2)} {investment.currency}
                          </div>
                          <div className="text-sm text-slate-400">
                            ≈ {investment.grp_value.toFixed(2)} GRP
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Properties Tab */}
          <TabsContent value="properties">
            <Card className="glass-card border-purple-600/20">
              <CardHeader>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Home className="text-cyan-400" />
                  Real Estate Portfolio
                </CardTitle>
                <CardDescription>{stats.owned_houses} propert{stats.owned_houses !== 1 ? 'ies' : 'y'}</CardDescription>
              </CardHeader>
              <CardContent>
                {breakdown.properties.length === 0 ? (
                  <div className="text-center py-12">
                    <Home size={48} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400 text-lg">No properties owned</p>
                    <p className="text-slate-500 text-sm mt-2">
                      Visit the Houses page to purchase properties
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {breakdown.properties.map((property) => (
                      <div
                        key={property.id}
                        className="flex items-center justify-between p-4 bg-slate-800/30 border border-slate-700 rounded-lg"
                      >
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-white font-bold text-lg">{property.name}</h3>
                            <span className="text-xs px-2 py-1 bg-cyan-600/20 text-cyan-400 rounded border border-cyan-600">
                              {property.building_type}
                            </span>
                          </div>
                          <p className="text-slate-400 text-sm">📍 {property.location}</p>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-cyan-400">
                            {property.purchase_price.toFixed(2)} {property.currency}
                          </div>
                          <div className="text-sm text-slate-400">
                            ≈ {property.grp_value.toFixed(2)} GRP
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Stats Summary */}
        <Card className="glass-card border-purple-600/20">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <PieChart className="text-purple-400" />
              Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-800/30 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Total Spent</div>
                <div className="text-xl font-bold text-purple-400">${stats.total_spent.toFixed(2)}</div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Transactions</div>
                <div className="text-xl font-bold text-purple-400">{stats.total_transactions}</div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Ranks Owned</div>
                <div className="text-xl font-bold text-purple-400">{stats.owned_ranks}</div>
              </div>
              <div className="p-4 bg-slate-800/30 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Properties</div>
                <div className="text-xl font-bold text-purple-400">{stats.owned_houses}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Portfolio;

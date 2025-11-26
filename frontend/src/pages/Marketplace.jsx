import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Coins, Crown, CreditCard } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const Marketplace = ({ user, onLogout, onUpdateUser }) => {
  const [currencyRates, setCurrencyRates] = useState({});
  const [rankPrices, setRankPrices] = useState({});
  const [currencyAmount, setCurrencyAmount] = useState(10000);
  const [selectedCurrency, setSelectedCurrency] = useState('NIM');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadMarketplaceData();
  }, []);

  const loadMarketplaceData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [ratesRes, ranksRes] = await Promise.all([
        axios.get(`${API}/marketplace/currency-rates`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/marketplace/rank-prices`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setCurrencyRates(ratesRes.data.rates);
      setRankPrices(ranksRes.data.ranks);
    } catch (error) {
      toast.error('Failed to load marketplace data');
    }
  };

  const calculatePrice = (amount, currency) => {
    if (!currencyRates || !currencyRates.GRP_TO_USD) return '0.00';
    
    // Convert to GRP first
    let grpAmount = amount;
    if (currency !== 'GRP') {
      const rateKey = `GRP_TO_${currency}`;
      grpAmount = amount / currencyRates[rateKey];
    }
    
    // Convert GRP to USD
    const usdAmount = grpAmount * currencyRates.GRP_TO_USD;
    return usdAmount.toFixed(2);
  };

  const handleBuyCurrency = async () => {
    if (currencyAmount < 1000) {
      toast.error('Minimum purchase is 1,000 currency');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/checkout/session`,
        {
          package_type: 'currency',
          package_id: 'currency_purchase',
          currency_type: selectedCurrency,
          quantity: parseFloat(currencyAmount)
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create checkout session');
      setLoading(false);
    }
  };

  const handleBuyRank = async (rankName) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/checkout/session`,
        {
          package_type: 'rank',
          package_id: rankName,
          quantity: 1.0
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      window.location.href = response.data.url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create checkout session');
      setLoading(false);
    }
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">MARKETPLACE</span>
          </h1>
          <p className="text-slate-400 text-lg">Purchase currency and ranks with VISA/MASTERCARD</p>
        </div>

        <Tabs defaultValue="currency" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-800/50 max-w-md" data-testid="marketplace-tabs">
            <TabsTrigger value="currency" data-testid="tab-currency">
              <Coins className="mr-2" size={18} />
              Currency
            </TabsTrigger>
            <TabsTrigger value="ranks" data-testid="tab-ranks">
              <Crown className="mr-2" size={18} />
              Ranks
            </TabsTrigger>
          </TabsList>

          <TabsContent value="currency" className="mt-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass-card border-purple-600/20">
                <CardHeader>
                  <CardTitle className="text-2xl flex items-center gap-2">
                    <Coins className="text-purple-400" />
                    Buy Server Currency
                  </CardTitle>
                  <CardDescription>Purchase ANY server currency with VISA/MASTERCARD via Stripe</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="select-currency">Select Currency</Label>
                    <select
                      id="select-currency"
                      value={selectedCurrency}
                      onChange={(e) => setSelectedCurrency(e.target.value)}
                      className="w-full p-3 bg-slate-800 border border-slate-700 rounded-lg text-lg font-bold text-purple-400"
                      data-testid="currency-selector"
                    >
                      <option value="NIM">NIM</option>
                      <option value="GRP">GRP</option>
                      <option value="VDD">VDD</option>
                      <option value="KKD">KKD</option>
                    </select>
                    <p className="text-sm text-slate-500">You can buy any currency regardless of your server</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="currency-amount">Amount ({selectedCurrency})</Label>
                    <Input
                      id="currency-amount"
                      data-testid="currency-amount-input"
                      type="number"
                      min="1000"
                      step="1000"
                      value={currencyAmount}
                      onChange={(e) => setCurrencyAmount(e.target.value)}
                      className="bg-slate-800/50 border-slate-700 text-lg"
                    />
                    <p className="text-sm text-slate-500">Minimum: 1,000 {selectedCurrency}</p>
                  </div>

                  <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-slate-400">You get:</span>
                      <span className="text-2xl font-bold text-purple-400">
                        {parseFloat(currencyAmount).toLocaleString()} {selectedCurrency}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Price:</span>
                      <span className="text-2xl font-bold text-white">
                        ${calculatePrice(currencyAmount, selectedCurrency)} USD
                      </span>
                    </div>
                  </div>

                  <Button
                    onClick={handleBuyCurrency}
                    disabled={loading}
                    className="w-full btn-minecraft text-lg py-6"
                    data-testid="buy-currency-button"
                  >
                    <CreditCard className="mr-2" size={20} />
                    {loading ? 'Processing...' : 'Pay with VISA/MASTERCARD'}
                  </Button>
                </CardContent>
              </Card>

              <Card className="glass-card border-slate-700">
                <CardHeader>
                  <CardTitle className="text-2xl">Currency Rates</CardTitle>
                  <CardDescription>Exchange rates for all server currencies</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(currencyRates).map(([currency, rate]) => (
                      <div
                        key={currency}
                        className={`p-4 rounded-lg ${
                          currency === user.currency_type
                            ? 'bg-purple-600/20 border-2 border-purple-600'
                            : 'bg-slate-800/50 border border-slate-700'
                        }`}
                        data-testid={`rate-${currency.toLowerCase()}`}
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <div className="font-bold text-lg">{currency}</div>
                            <div className="text-sm text-slate-400">
                              {rate.toFixed(2)} {currency} = $1 USD
                            </div>
                          </div>
                          {currency === user.currency_type && (
                            <div className="text-xs font-bold text-purple-400 bg-purple-600/20 px-3 py-1 rounded">
                              YOUR CURRENCY
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="ranks" className="mt-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(rankPrices).map(([rankName, price]) => {
                const isOwned = user.owned_ranks?.includes(rankName);
                return (
                  <Card
                    key={rankName}
                    className={`glass-card ${
                      isOwned ? 'border-amber-600' : 'border-slate-700'
                    } hover:border-purple-600/50 transition-all`}
                    data-testid={`rank-${rankName.toLowerCase().replace(' ', '-')}`}
                  >
                    <CardHeader>
                      <Crown className={isOwned ? 'text-amber-400' : 'text-slate-400'} size={32} />
                      <CardTitle className="text-xl">{rankName}</CardTitle>
                      <CardDescription className="text-2xl font-bold text-purple-400">
                        ${price.toFixed(2)} USD
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {isOwned ? (
                        <div className="w-full py-3 bg-amber-600/20 border border-amber-600 rounded-lg text-center font-bold text-amber-400">
                          OWNED
                        </div>
                      ) : (
                        <Button
                          onClick={() => handleBuyRank(rankName)}
                          disabled={loading}
                          className="w-full btn-minecraft"
                          data-testid={`buy-rank-${rankName.toLowerCase().replace(' ', '-')}`}
                        >
                          <CreditCard className="mr-2" size={18} />
                          Buy Now
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default Marketplace;

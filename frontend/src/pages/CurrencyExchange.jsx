import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ArrowRightLeft, TrendingUp } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const CurrencyExchange = ({ user, onLogout, onUpdateUser }) => {
  const [rates, setRates] = useState({});
  const [fromCurrency, setFromCurrency] = useState('NIM');
  const [toCurrency, setToCurrency] = useState('GRP');
  const [amount, setAmount] = useState(1000);
  const [convertedAmount, setConvertedAmount] = useState(0);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRates();
  }, []);

  useEffect(() => {
    calculateConversion();
  }, [fromCurrency, toCurrency, amount, rates]);

  const loadRates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/exchange-rates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRates(response.data.rates);
    } catch (error) {
      toast.error('Failed to load exchange rates');
    }
  };

  const calculateConversion = () => {
    if (!rates || !amount) {
      setConvertedAmount(amount);
      return;
    }

    if (fromCurrency === toCurrency) {
      setConvertedAmount(amount);
      return;
    }

    // Use direct conversion from exchange matrix
    const rateKey = `${fromCurrency}_TO_${toCurrency}`;
    const rate = rates[rateKey] || 1.0;
    const targetAmount = parseFloat(amount) * rate;

    setConvertedAmount(targetAmount.toFixed(2));
  };

  const handleConvert = async () => {
    if (!amount || amount <= 0) {
      toast.error('Please enter a valid amount');
      return;
    }

    if (fromCurrency === toCurrency) {
      toast.error('Cannot convert to the same currency');
      return;
    }

    if (user.balances[fromCurrency] < amount) {
      toast.error('Insufficient balance');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API}/currency/convert`,
        {
          from_currency: fromCurrency,
          to_currency: toCurrency,
          amount: parseFloat(amount)
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(
        `Converted ${response.data.from_amount} ${response.data.from_currency} to ${response.data.to_amount.toFixed(2)} ${response.data.to_currency}`
      );
      onUpdateUser();
      setAmount(1000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Conversion failed');
    } finally {
      setLoading(false);
    }
  };

  const swapCurrencies = () => {
    setFromCurrency(toCurrency);
    setToCurrency(fromCurrency);
  };

  const currencies = ['NIM', 'GRP', 'VDD', 'KKD'];

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">CURRENCY EXCHANGE</span>
          </h1>
          <p className="text-slate-400 text-lg">Convert between server currencies</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Conversion Card */}
          <Card className="glass-card border-purple-600/20">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                <ArrowRightLeft className="text-purple-400" />
                Currency Converter
              </CardTitle>
              <CardDescription>Exchange your currencies at live rates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* From Currency */}
              <div className="space-y-2">
                <Label>From</Label>
                <div className="flex gap-2">
                  <Select value={fromCurrency} onValueChange={setFromCurrency}>
                    <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="from-currency-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map((curr) => (
                        <SelectItem key={curr} value={curr} disabled={curr === toCurrency}>
                          {curr}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="bg-slate-800 border-slate-700"
                    data-testid="amount-input"
                  />
                </div>
                <div className="text-sm text-slate-500">
                  Available: {user.balances[fromCurrency]?.toFixed(2)} {fromCurrency}
                </div>
              </div>

              {/* Swap Button */}
              <div className="flex justify-center">
                <Button
                  onClick={swapCurrencies}
                  variant="outline"
                  size="icon"
                  className="rounded-full border-purple-500 hover:bg-purple-950"
                  data-testid="swap-button"
                >
                  <ArrowRightLeft size={20} className="text-purple-400" />
                </Button>
              </div>

              {/* To Currency */}
              <div className="space-y-2">
                <Label>To</Label>
                <div className="flex gap-2">
                  <Select value={toCurrency} onValueChange={setToCurrency}>
                    <SelectTrigger className="bg-slate-800 border-slate-700" data-testid="to-currency-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {currencies.map((curr) => (
                        <SelectItem key={curr} value={curr} disabled={curr === fromCurrency}>
                          {curr}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    value={convertedAmount}
                    readOnly
                    className="bg-slate-800 border-slate-700 text-purple-400 font-bold"
                    data-testid="converted-amount"
                  />
                </div>
                <div className="text-sm text-slate-500">
                  Balance: {user.balances[toCurrency]?.toFixed(2)} {toCurrency}
                </div>
              </div>

              {/* Exchange Rate */}
              <div className="p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                <div className="text-sm text-slate-400 mb-1">Exchange Rate</div>
                <div className="text-lg font-bold text-purple-400">
                  1 {fromCurrency} = {(convertedAmount / amount || 0).toFixed(5)} {toCurrency}
                </div>
              </div>

              <Button
                onClick={handleConvert}
                disabled={loading || amount <= 0 || fromCurrency === toCurrency}
                className="w-full btn-kapitalist text-lg py-6"
                data-testid="convert-button"
              >
                {loading ? 'Converting...' : 'Convert Currency'}
              </Button>
            </CardContent>
          </Card>

          {/* Exchange Rates Card */}
          <Card className="glass-card border-purple-600/20">
            <CardHeader>
              <CardTitle className="text-2xl flex items-center gap-2">
                <TrendingUp className="text-purple-400" />
                Complete Exchange Matrix
              </CardTitle>
              <CardDescription>All currency pairs - Direct conversion rates</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {currencies.map(fromCurr => (
                  <div key={fromCurr} className="space-y-2">
                    <h3 className="text-lg font-bold text-purple-400">From {fromCurr}:</h3>
                    <div className="grid grid-cols-1 gap-2">
                      {currencies.map(toCurr => {
                        if (fromCurr === toCurr) return null;
                        const rateKey = `${fromCurr}_TO_${toCurr}`;
                        const rate = rates[rateKey];
                        if (!rate) return null;
                        
                        return (
                          <div
                            key={rateKey}
                            className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-purple-500 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3">
                                <div className="text-sm font-medium text-slate-400">1 {fromCurr}</div>
                                <ArrowRightLeft className="text-slate-600" size={16} />
                              </div>
                              <div className="text-right">
                                <div className="font-bold text-white">{rate.toFixed(3)} {toCurr}</div>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>

              {/* My Balances */}
              <div className="mt-6 p-4 bg-purple-600/10 border border-purple-600/30 rounded-lg">
                <h3 className="font-bold text-lg text-purple-400 mb-3">My Balances</h3>
                <div className="grid grid-cols-2 gap-3">
                  {currencies.map((curr) => (
                    <div key={curr} className="text-center p-2 bg-slate-800/50 rounded">
                      <div className="text-xs text-slate-500">{curr}</div>
                      <div className="text-lg font-bold text-white">{user.balances[curr]?.toFixed(2)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CurrencyExchange;

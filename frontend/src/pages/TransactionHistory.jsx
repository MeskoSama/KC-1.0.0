import React, { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowUpRight, ArrowDownRight, Home, Target, CreditCard, TrendingUp, Clock, Filter } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const TransactionHistory = ({ user, onLogout }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadTransactions();
  }, [filter]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const params = filter !== 'all' ? { transaction_type: filter } : {};
      const response = await axios.get(`${API}/transactions/history`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });
      setTransactions(response.data.transactions || []);
    } catch (error) {
      console.error('Failed to load transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'payment':
        return <CreditCard className="text-green-400" size={20} />;
      case 'investment':
        return <TrendingUp className="text-blue-400" size={20} />;
      case 'property':
        return <Home className="text-purple-400" size={20} />;
      case 'bounty_create':
        return <Target className="text-orange-400" size={20} />;
      case 'bounty_complete':
        return <Target className="text-emerald-400" size={20} />;
      default:
        return <ArrowUpRight className="text-slate-400" size={20} />;
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      completed: 'bg-emerald-600/20 text-emerald-400 border-emerald-600',
      pending: 'bg-amber-600/20 text-amber-400 border-amber-600',
      paid: 'bg-emerald-600/20 text-emerald-400 border-emerald-600',
      active: 'bg-blue-600/20 text-blue-400 border-blue-600',
      failed: 'bg-red-600/20 text-red-400 border-red-600'
    };

    return (
      <Badge className={`${variants[status] || variants.pending} border`}>
        {status}
      </Badge>
    );
  };

  const formatDate = (timestamp) => {
    if (!timestamp) return 'Unknown';
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount, currency) => {
    const isNegative = amount < 0;
    const absAmount = Math.abs(amount);
    return (
      <span className={isNegative ? 'text-red-400' : 'text-emerald-400'}>
        {isNegative ? '-' : '+'}
        {absAmount.toFixed(2)} {currency}
      </span>
    );
  };

  return (
    <div className="kapitalist-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-4xl font-black mb-2">
            <span className="text-purple-400 glow-text">Transaction History</span>
          </h1>
          <p className="text-slate-400 text-lg">Track all your activities and transactions</p>
        </div>

        {/* Filter Tabs */}
        <Tabs defaultValue="all" className="mb-6" onValueChange={setFilter}>
          <TabsList className="bg-slate-800/50 border border-slate-700">
            <TabsTrigger value="all" className="data-[state=active]:bg-purple-600">
              All
            </TabsTrigger>
            <TabsTrigger value="payment" className="data-[state=active]:bg-purple-600">
              Payments
            </TabsTrigger>
            <TabsTrigger value="investment" className="data-[state=active]:bg-purple-600">
              Investments
            </TabsTrigger>
            <TabsTrigger value="property" className="data-[state=active]:bg-purple-600">
              Properties
            </TabsTrigger>
            <TabsTrigger value="bounty_create" className="data-[state=active]:bg-purple-600">
              Bounties
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Transactions List */}
        <Card className="glass-card border-purple-600/20">
          <CardHeader>
            <CardTitle className="text-2xl flex items-center gap-2">
              <Clock size={24} className="text-purple-400" />
              Recent Transactions
            </CardTitle>
            <CardDescription>
              {transactions.length} transaction{transactions.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
                <p className="text-slate-400 mt-4">Loading transactions...</p>
              </div>
            ) : transactions.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-400 text-lg">No transactions found</p>
                <p className="text-slate-500 text-sm mt-2">Start trading to see your history here</p>
              </div>
            ) : (
              <div className="space-y-3">
                {transactions.map((txn) => (
                  <div
                    key={txn.id}
                    className="flex items-center justify-between p-4 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700 rounded-lg transition-all"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="p-3 bg-slate-800 rounded-lg">
                        {getTransactionIcon(txn.type)}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-white font-semibold mb-1">{txn.action}</h3>
                        <p className="text-slate-400 text-sm flex items-center gap-2">
                          <Clock size={14} />
                          {formatDate(txn.timestamp)}
                        </p>
                        {txn.details && Object.keys(txn.details).length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            {txn.details.symbol && (
                              <span className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">
                                {txn.details.symbol}
                              </span>
                            )}
                            {txn.details.quantity && (
                              <span className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">
                                Qty: {txn.details.quantity}
                              </span>
                            )}
                            {txn.details.location && (
                              <span className="text-xs px-2 py-1 bg-slate-700 rounded text-slate-300">
                                📍 {txn.details.location}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="font-bold text-lg">
                          {formatAmount(txn.amount, txn.currency)}
                        </div>
                      </div>
                      {getStatusBadge(txn.status)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TransactionHistory;

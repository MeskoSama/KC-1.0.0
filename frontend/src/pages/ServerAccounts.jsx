import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { 
  CreditCard, Wallet, TrendingUp, ChevronDown, ChevronRight, 
  Search, RefreshCw, DollarSign, Building2, User, Crown
} from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const ServerAccounts = ({ user, onLogout }) => {
  const [accounts, setAccounts] = useState([]);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Expansion state
  const [expandedAccounts, setExpandedAccounts] = useState({});
  const [expandedBanks, setExpandedBanks] = useState({});
  const [expandedCards, setExpandedCards] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [accountsRes, configRes] = await Promise.all([
        axios.get(`${API}/accounts`),
        axios.get(`${API}/accounts/config`)
      ]);
      
      setAccounts(accountsRes.data.accounts || []);
      setConfig(configRes.data);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (amount) => {
    if (amount === null || amount === undefined) return '***';
    if (amount >= 1e9) return (amount / 1e9).toFixed(2) + 'B';
    if (amount >= 1e6) return (amount / 1e6).toFixed(2) + 'M';
    if (amount >= 1e3) return (amount / 1e3).toFixed(1) + 'K';
    return amount.toLocaleString();
  };

  const getRankColor = (rank) => {
    if (!config?.ranking_colors) return '#fff';
    if (rank === 1) return config.ranking_colors["1"] || '#FFFF00';
    if (rank === 2) return config.ranking_colors["2"] || '#C0C0C0';
    if (rank === 3) return config.ranking_colors["3"] || '#B87333';
    return '#fff';
  };

  const getCardColor = (bankId, cardType) => {
    return config?.banks?.[bankId]?.card_colors?.[cardType] || '#666';
  };

  const getBankName = (bankId) => {
    return config?.banks?.[bankId]?.name || bankId;
  };

  const getHomeCurrency = (bankId) => {
    return config?.banks?.[bankId]?.home_currency || 'GRP';
  };

  const toggleAccount = (accountId) => {
    setExpandedAccounts(prev => ({
      ...prev,
      [accountId]: !prev[accountId]
    }));
  };

  const toggleBank = (accountId, bankId) => {
    const key = `${accountId}-${bankId}`;
    setExpandedBanks(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const toggleCard = (accountId, bankId, cardId) => {
    const key = `${accountId}-${bankId}-${cardId}`;
    setExpandedCards(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const shouldShowCurrency = (card, currency, bankId) => {
    const homeCurrency = getHomeCurrency(bankId);
    if (currency === homeCurrency) return true;
    
    const foreignOpened = card.foreign_currencies_opened || [];
    return foreignOpened.includes(currency);
  };

  const filteredAccounts = accounts.filter(account => 
    account.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getCardIcon = (cardType) => {
    switch (cardType) {
      case 'credit': return '💳';
      case 'debit': return '🏦';
      case 'government': return '🏛️';
      case 'platinum': return '💎';
      case 'gold': return '🥇';
      case 'investor': return '📈';
      default: return '💳';
    }
  };

  const getCardTypeName = (cardType) => {
    const names = {
      'credit': 'Credit Card',
      'debit': 'Bank Card (Debit)',
      'government': 'Government Card',
      'platinum': 'Platinum Card',
      'gold': 'Gold Card',
      'investor': 'Investor Card'
    };
    return names[cardType] || cardType;
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
      
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent flex items-center gap-2">
              <Wallet /> Server Account Sorting
            </h1>
            <p className="text-slate-400 text-sm">
              Bank accounts & wealth ranking • {accounts.length} accounts
            </p>
          </div>
          
          <div className="flex gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <Input
                placeholder="Search accounts..."
                className="pl-10 w-64 bg-slate-800 border-slate-700"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button variant="outline" onClick={loadData}>
              <RefreshCw size={18} />
            </Button>
          </div>
        </div>

        {/* Wealth Ranking List */}
        <Card className="glass-card border-yellow-600/20">
          <CardHeader className="py-4">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="text-yellow-400" />
              Wealth Ranking
            </CardTitle>
            <CardDescription>
              Click on a person to see their banks, click on a bank to see their cards
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {filteredAccounts.length === 0 ? (
              <p className="text-center text-slate-500 py-8">
                No accounts found. Admin can initialize sample accounts.
              </p>
            ) : (
              filteredAccounts.map((account) => (
                <div key={account.id} className="border border-slate-700/50 rounded-lg overflow-hidden">
                  {/* Account Row - Level 1 */}
                  <div 
                    className="flex items-center gap-4 p-4 bg-slate-800/50 cursor-pointer hover:bg-slate-800/80 transition-colors"
                    onClick={() => toggleAccount(account.id)}
                  >
                    <div className="flex items-center gap-2">
                      {expandedAccounts[account.id] ? (
                        <ChevronDown size={20} className="text-slate-400" />
                      ) : (
                        <ChevronRight size={20} className="text-slate-400" />
                      )}
                      
                      {/* Rank Badge */}
                      <div 
                        className="w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg"
                        style={{ 
                          backgroundColor: account.rank <= 3 ? getRankColor(account.rank) + '30' : '#374151',
                          color: getRankColor(account.rank),
                          textShadow: account.rank <= 3 ? `0 0 10px ${getRankColor(account.rank)}` : 'none'
                        }}
                      >
                        {account.rank <= 3 ? (
                          <Crown size={20} />
                        ) : (
                          account.rank
                        )}
                      </div>
                    </div>
                    
                    {/* Username */}
                    <div className="flex-1">
                      <span 
                        className="font-bold text-lg"
                        style={{ 
                          color: getRankColor(account.rank),
                          textShadow: account.rank <= 3 ? `0 0 8px ${getRankColor(account.rank)}` : 'none'
                        }}
                      >
                        {account.username}
                      </span>
                    </div>
                    
                    {/* Total Wealth */}
                    <div className="text-right">
                      <p className="text-sm text-slate-400">Total Wealth</p>
                      <p className="text-xl font-bold text-green-400">
                        {formatMoney(account.total_wealth)} GRP
                      </p>
                    </div>
                    
                    {/* Bank Count */}
                    <Badge variant="outline" className="ml-2">
                      {account.bank_accounts?.length || 0} Banks
                    </Badge>
                  </div>

                  {/* Expanded Banks - Level 2 */}
                  {expandedAccounts[account.id] && (
                    <div className="border-t border-slate-700/50 bg-slate-900/30">
                      {account.bank_accounts?.length === 0 ? (
                        <p className="p-4 text-slate-500 text-sm">No bank accounts</p>
                      ) : (
                        account.bank_accounts.map((bankAccount, bankIdx) => (
                          <div key={bankIdx} className="border-b border-slate-700/30 last:border-0">
                            {/* Bank Row */}
                            <div 
                              className="flex items-center gap-4 p-3 pl-14 cursor-pointer hover:bg-slate-800/30 transition-colors"
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleBank(account.id, bankAccount.bank_id);
                              }}
                            >
                              {expandedBanks[`${account.id}-${bankAccount.bank_id}`] ? (
                                <ChevronDown size={18} className="text-slate-400" />
                              ) : (
                                <ChevronRight size={18} className="text-slate-400" />
                              )}
                              
                              <Building2 size={20} className="text-blue-400" />
                              
                              <span className="font-semibold text-blue-300 flex-1">
                                {getBankName(bankAccount.bank_id)}
                              </span>
                              
                              <Badge variant="outline" className="text-xs">
                                {bankAccount.cards?.length || 0} Cards
                              </Badge>
                            </div>

                            {/* Expanded Cards - Level 3 */}
                            {expandedBanks[`${account.id}-${bankAccount.bank_id}`] && (
                              <div className="bg-slate-900/50 pl-20 pr-4 pb-2">
                                {bankAccount.cards?.length === 0 ? (
                                  <p className="p-2 text-slate-500 text-sm">No cards</p>
                                ) : (
                                  bankAccount.cards.map((card, cardIdx) => (
                                    <div key={cardIdx} className="mb-2">
                                      {/* Card Header */}
                                      <div 
                                        className="flex items-center gap-3 p-2 rounded cursor-pointer hover:bg-slate-800/50 transition-colors"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          toggleCard(account.id, bankAccount.bank_id, card.id || cardIdx);
                                        }}
                                        style={{
                                          borderLeft: `4px solid ${getCardColor(bankAccount.bank_id, card.card_type)}`
                                        }}
                                      >
                                        {expandedCards[`${account.id}-${bankAccount.bank_id}-${card.id || cardIdx}`] ? (
                                          <ChevronDown size={16} className="text-slate-400" />
                                        ) : (
                                          <ChevronRight size={16} className="text-slate-400" />
                                        )}
                                        
                                        <span className="text-lg">{getCardIcon(card.card_type)}</span>
                                        
                                        <span 
                                          className="font-medium"
                                          style={{ color: getCardColor(bankAccount.bank_id, card.card_type) }}
                                        >
                                          {getCardTypeName(card.card_type)}
                                        </span>
                                        
                                        <span className="text-slate-500 text-sm ml-auto">
                                          {card.card_type === 'credit' ? '(Debt)' : '(Balance)'}
                                        </span>
                                      </div>

                                      {/* Card Balances - Level 4 */}
                                      {expandedCards[`${account.id}-${bankAccount.bank_id}-${card.id || cardIdx}`] && (
                                        <div className="ml-8 mt-1 p-3 bg-slate-800/30 rounded-lg">
                                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                                            {config?.currencies?.map(currency => {
                                              const isCredit = card.card_type === 'credit';
                                              const value = isCredit 
                                                ? card.debt?.[currency] 
                                                : card.balances?.[currency];
                                              const canShow = shouldShowCurrency(card, currency, bankAccount.bank_id);
                                              const homeCurrency = getHomeCurrency(bankAccount.bank_id);
                                              const isHome = currency === homeCurrency;
                                              
                                              return (
                                                <div 
                                                  key={currency}
                                                  className={`p-2 rounded ${isHome ? 'bg-blue-900/30 border border-blue-600/30' : 'bg-slate-700/30'}`}
                                                >
                                                  <p className={`text-xs ${isHome ? 'text-blue-400' : 'text-slate-400'}`}>
                                                    {currency} {isHome && '(Home)'}
                                                  </p>
                                                  <p className={`font-mono font-bold ${
                                                    isCredit 
                                                      ? (value > 0 ? 'text-red-400' : 'text-slate-400')
                                                      : (value > 0 ? 'text-green-400' : 'text-slate-400')
                                                  }`}>
                                                    {canShow ? (
                                                      <>
                                                        {isCredit && value > 0 && '-'}
                                                        {formatMoney(value || 0)}
                                                        {isCredit && value > 0 && ' Debt'}
                                                      </>
                                                    ) : (
                                                      <span className="text-slate-500">***</span>
                                                    )}
                                                  </p>
                                                </div>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      )}
                                    </div>
                                  ))
                                )}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Legend */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Banks */}
          <Card className="glass-card border-blue-600/20">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Building2 size={16} className="text-blue-400" />
                Banks & Home Currencies
              </CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <div className="grid grid-cols-2 gap-2">
                {config?.banks && Object.entries(config.banks).map(([bankId, bank]) => (
                  <div key={bankId} className="flex items-center gap-2 text-sm">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: bank.card_colors.debit }} />
                    <span className="text-slate-300">{bank.name}</span>
                    <Badge variant="outline" className="text-xs ml-auto">{bank.home_currency}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Card Types */}
          <Card className="glass-card border-purple-600/20">
            <CardHeader className="py-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <CreditCard size={16} className="text-purple-400" />
                Card Types
              </CardTitle>
            </CardHeader>
            <CardContent className="py-2">
              <div className="grid grid-cols-2 gap-2">
                {config?.card_types?.map(cardType => (
                  <div key={cardType} className="flex items-center gap-2 text-sm">
                    <span>{getCardIcon(cardType)}</span>
                    <span className="text-slate-300">{getCardTypeName(cardType)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ServerAccounts;

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sparkles, ShoppingBag, Target, Trophy, Building2, CreditCard, Server } from 'lucide-react';

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: ShoppingBag,
      title: 'Marketplace',
      description: 'Buy in-game currency & exclusive ranks with VISA/MASTERCARD'
    },
    {
      icon: Building2,
      title: 'House Trading',
      description: 'Buy, sell, and rent virtual houses in the Minecraft server'
    },
    {
      icon: Target,
      title: 'Bounty System',
      description: 'Create PvP bounties or complete quests for rewards'
    },
    {
      icon: Trophy,
      title: 'Leaderboards',
      description: 'Compete to be the richest player or top trader'
    },
    {
      icon: CreditCard,
      title: 'Secure Payments',
      description: 'VISA & MASTERCARD payments via Stripe'
    },
    {
      icon: Sparkles,
      title: '4 Server Currencies',
      description: 'Trade with NIM, GRP, VDD, and KKD currencies'
    }
  ];

  const copyServerIP = () => {
    navigator.clipboard.writeText('KapitalistCraftRP.aternos.me');
    alert('Server IP copied to clipboard!');
  };

  return (
    <div className="kapitalist-bg min-h-screen">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <div className="inline-block mb-6 floating">
            <div className="w-24 h-24 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg pulse-glow flex items-center justify-center">
              <Sparkles size={48} className="text-white" />
            </div>
          </div>
          <h1 className="text-5xl md:text-7xl font-black mb-4 tracking-tight">
            <span className="text-purple-400 glow-text">KAPITALISTCRAFT</span>
          </h1>
          <p className="text-2xl md:text-3xl font-bold text-white mb-2">Trade Center & Marketplace</p>
          <p className="text-lg md:text-xl text-slate-300 mb-8 max-w-3xl mx-auto">The ultimate Minecraft server marketplace. Trade currencies, buy ranks, rent houses, and compete on leaderboards.</p>
          
          {/* Server Info */}
          <div className="inline-flex items-center gap-4 mb-8 p-4 bg-slate-900/50 border-2 border-purple-500 rounded-lg backdrop-blur-md">
            <Server className="text-purple-400" size={32} />
            <div className="text-left">
              <div className="text-sm text-slate-400 font-semibold">JOIN OUR SERVER</div>
              <div className="text-lg font-black text-white" onClick={copyServerIP} style={{ cursor: 'pointer' }} title="Click to copy">
                KapitalistCraftRP.aternos.me
              </div>
              <div className="text-xs text-purple-400">Version: 1.21.1 JAVA</div>
            </div>
          </div>
          
          <div className="flex gap-4 justify-center">
            <Button
              onClick={() => navigate('/auth')}
              size="lg"
              className="btn-kapitalist text-lg px-8 py-6 font-bold"
              data-testid="get-started-button"
            >
              GET STARTED
            </Button>
            <Button
              onClick={copyServerIP}
              size="lg"
              variant="outline"
              className="border-purple-500 text-purple-400 hover:bg-purple-950 text-lg px-8 py-6 font-bold"
            >
              COPY SERVER IP
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto mt-20">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className="stat-card group" data-testid={`feature-${index}`}>
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-lg bg-purple-600/20 flex items-center justify-center group-hover:bg-purple-600/40 transition-colors">
                    <Icon size={28} className="text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-2 text-slate-100">{feature.title}</h3>
                    <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Currencies Section */}
        <div className="mt-20 glass-card p-8 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-8 text-purple-400">Server Currencies</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'NIM', code: '10194', color: 'purple' },
              { name: 'GRP', code: '10997', color: 'pink' },
              { name: 'VDD', code: '20664', color: 'red' },
              { name: 'KKD', code: '90154', color: 'rose' }
            ].map((currency) => (
              <div key={currency.name} className="text-center p-4 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-purple-500 transition-colors">
                <div className={`text-3xl font-black text-${currency.color}-400 mb-2`}>{currency.name}</div>
                <div className="text-sm text-slate-500">Code: {currency.code}</div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center">
          <h2 className="text-4xl font-bold mb-6 text-slate-100">Ready to Start Trading?</h2>
          <p className="text-xl text-slate-400 mb-8">Join thousands of players in the ultimate Minecraft economy</p>
          <Button
            onClick={() => navigate('/auth')}
            size="lg"
            className="btn-kapitalist text-lg px-8 py-6 font-bold"
            data-testid="cta-join-button"
          >
            JOIN NOW
          </Button>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;

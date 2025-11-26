import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Sparkles, ShoppingBag, Target, Trophy, Building2, CreditCard } from 'lucide-react';

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

  return (
    <div className="minecraft-bg min-h-screen">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <div className="inline-block mb-6 floating">
            <div className="w-24 h-24 bg-emerald-600 rounded-lg pulse-glow flex items-center justify-center">
              <Sparkles size={48} className="text-white" />
            </div>
          </div>
          <h1 className="text-6xl md:text-7xl font-black mb-6 tracking-tight">
            <span className="text-emerald-400 glow-text">Kapitalist</span>
            <span className="text-slate-100">TRADERS</span>
          </h1>
          <p className="text-xl md:text-2xl text-slate-300 mb-8 max-w-3xl mx-auto font-light">
            The ultimate Minecraft server marketplace. Trade currencies, buy ranks, rent houses, and compete on leaderboards.
          </p>
          <Button
            onClick={() => navigate('/auth')}
            size="lg"
            className="btn-minecraft text-lg px-8 py-6 font-bold"
            data-testid="get-started-button"
          >
            GET STARTED
          </Button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto mt-20">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className="stat-card group" data-testid={`feature-${index}`}>
                <div className="flex items-start gap-4">
                  <div className="w-14 h-14 rounded-lg bg-emerald-600/20 flex items-center justify-center group-hover:bg-emerald-600/40 transition-colors">
                    <Icon size={28} className="text-emerald-400" />
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
          <h2 className="text-3xl font-bold text-center mb-8 text-emerald-400">Server Currencies</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: 'NIM', code: '10194', color: 'emerald' },
              { name: 'GRP', code: '10997', color: 'cyan' },
              { name: 'VDD', code: '20664', color: 'amber' },
              { name: 'KKD', code: '90154', color: 'rose' }
            ].map((currency) => (
              <div key={currency.name} className="text-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
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
            className="btn-minecraft text-lg px-8 py-6 font-bold"
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

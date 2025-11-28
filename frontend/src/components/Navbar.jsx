import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Home, ShoppingCart, Target, Trophy, Building2, LogOut, Shield, ArrowRightLeft, TrendingUp, History, Wallet, LineChart } from 'lucide-react';

export const Navbar = ({ user, onLogout }) => {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Dashboard' },
    { path: '/portfolio', icon: Wallet, label: 'Portfolio' },
    { path: '/marketplace', icon: ShoppingCart, label: 'Marketplace' },
    { path: '/investments', icon: TrendingUp, label: 'Investments' },
    { path: '/charts', icon: LineChart, label: 'Charts' },
    { path: '/exchange', icon: ArrowRightLeft, label: 'Exchange' },
    { path: '/houses', icon: Building2, label: 'Houses' },
    { path: '/bounties', icon: Target, label: 'Bounties' },
    { path: '/transactions', icon: History, label: 'History' },
    { path: '/scoreboard', icon: Trophy, label: 'Scoreboard' },
  ];
  
  if (user?.is_admin) {
    navItems.push({ path: '/admin', icon: Shield, label: 'Admin' });
  }

  return (
    <nav className="glass-card sticky top-0 z-50 mx-4 mt-4 mb-6">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <Link to="/dashboard" className="text-lg font-black tracking-tight">
              <span className="text-purple-400 glow-text">KAPITALISTCRAFT</span>
              <span className="text-white text-xs block -mt-1">Trade Center</span>
            </Link>
            <div className="hidden md:flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    data-testid={`nav-${item.label.toLowerCase()}`}
                  >
                    <Button
                      variant={isActive ? 'default' : 'ghost'}
                      className={`gap-2 ${isActive ? 'bg-purple-600 hover:bg-purple-700' : 'hover:bg-purple-950'}`}
                    >
                      <Icon size={18} />
                      {item.label}
                    </Button>
                  </Link>
                );
              })}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:flex flex-col items-end">
              <span className="text-sm text-slate-400">Player</span>
              <span className="font-bold text-purple-400" data-testid="navbar-username">{user.username}</span>
            </div>
            <div className="currency-badge" data-testid="navbar-balance">
              <span className="text-purple-400 font-bold">{user.balances[user.currency_type].toFixed(2)}</span>
              <span className="text-slate-300">{user.currency_type}</span>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={onLogout}
              className="border-red-600 text-red-600 hover:bg-red-950"
              data-testid="logout-button"
            >
              <LogOut size={18} />
            </Button>
          </div>
        </div>
      </div>
    </nav>
  );
};

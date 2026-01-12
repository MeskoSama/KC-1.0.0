import React, { useState, useEffect } from 'react';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Crown, Users, Building2, Vote, User, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';

const CountryLeaders = ({ user, onLogout }) => {
  const [governments, setGovernments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedCountry, setExpandedCountry] = useState(null);

  useEffect(() => {
    loadGovernments();
  }, []);

  const loadGovernments = async () => {
    try {
      const response = await axios.get(`${API}/countries/governments/all`);
      setGovernments(response.data.countries || []);
      if (response.data.countries?.length > 0) {
        setExpandedCountry(response.data.countries[0].country_id);
      }
    } catch (error) {
      console.error('Failed to load governments:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPartyColor = (index) => {
    const colors = ['#9333ea', '#ef4444', '#22c55e', '#f59e0b', '#3b82f6', '#ec4899', '#14b8a6', '#8b5cf6'];
    return colors[index % colors.length];
  };

  const PartyPieChart = ({ parties, totalSeats }) => {
    if (!parties || parties.length === 0 || totalSeats === 0) return null;

    const data = parties.map((party, idx) => ({
      name: party.name,
      value: party.seats,
      color: getPartyColor(idx)
    }));

    const CustomTooltip = ({ active, payload }) => {
      if (active && payload && payload.length) {
        const party = parties.find(p => p.name === payload[0].name);
        return (
          <div className="bg-slate-900 border border-purple-600/30 p-3 rounded-lg shadow-xl">
            <p className="text-white font-bold">{payload[0].name}</p>
            <p className="text-purple-400">{payload[0].value} seats ({((payload[0].value / totalSeats) * 100).toFixed(1)}%)</p>
            {party && <p className="text-slate-400 text-sm">Leader: {party.leader_name}</p>}
          </div>
        );
      }
      return null;
    };

    return (
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              outerRadius={80}
              innerRadius={40}
              fill="#8884d8"
              dataKey="value"
              label={({ name, percent }) => percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : ''}
              labelLine={false}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend formatter={(value) => <span className="text-slate-300 text-sm">{value}</span>} />
          </PieChart>
        </ResponsiveContainer>
      </div>
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
            👑 Country Leaders
          </h1>
          <p className="text-slate-400 mt-2">Leaders, ministers, councils, and political parties</p>
        </div>

        <div className="space-y-6">
          {governments.map((gov) => {
            const isExpanded = expandedCountry === gov.country_id;
            const government = gov.government || {};
            const hasCouncil = government.council?.length > 0;
            const hasMinistries = government.ministries?.length > 0;
            const hasParties = government.parties?.length > 0;

            return (
              <Card 
                key={gov.country_id} 
                className="glass-card border-purple-600/20 overflow-hidden"
                style={{ borderLeftColor: gov.color, borderLeftWidth: '4px' }}
              >
                {/* Header - Always Visible */}
                <div 
                  className="p-6 cursor-pointer hover:bg-slate-800/30 transition-colors"
                  onClick={() => setExpandedCountry(isExpanded ? null : gov.country_id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div 
                        className="w-12 h-12 rounded-xl flex items-center justify-center"
                        style={{ backgroundColor: `${gov.color}30` }}
                      >
                        <Crown size={24} style={{ color: gov.color }} />
                      </div>
                      <div>
                        <h2 className="text-2xl font-bold text-white">{gov.country_name}</h2>
                        <div className="flex items-center gap-3 mt-1">
                          <Badge variant="outline" className="border-purple-600/30 text-purple-400">
                            {government.government_system || 'Unknown System'}
                          </Badge>
                          <span className="text-slate-400">|</span>
                          <span className="text-slate-300">
                            <span className="text-slate-500">{government.leader_type || 'Leader'}:</span>{' '}
                            <span className="font-bold">{government.leader_name || 'None'}</span>
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right hidden md:block">
                        <div className="flex gap-4 text-sm text-slate-400">
                          <span>{government.council?.length || 0} Council</span>
                          <span>{government.ministries?.length || 0} Ministers</span>
                          <span>{government.parties?.length || 0} Parties</span>
                        </div>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="text-slate-400" size={24} />
                      ) : (
                        <ChevronDown className="text-slate-400" size={24} />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="border-t border-slate-700/50 p-6 space-y-6">
                    {/* Council Members */}
                    <div>
                      <h3 className="text-lg font-bold text-purple-400 flex items-center gap-2 mb-4">
                        <Users size={20} />
                        Council / Consular Members
                      </h3>
                      {hasCouncil ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                          {government.council.map((member, idx) => (
                            <div 
                              key={idx} 
                              className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30"
                            >
                              <div className="p-2 bg-purple-600/20 rounded-full">
                                <User size={16} className="text-purple-400" />
                              </div>
                              <div>
                                <p className="font-medium text-white">{member.name}</p>
                                <p className="text-xs text-slate-400">
                                  {member.role && <span className="text-purple-400">{member.role}</span>}
                                  {member.age > 0 && <span>, {member.age} years old</span>}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 italic p-4 bg-slate-800/20 rounded-lg border border-dashed border-slate-700">
                          No council members assigned
                        </p>
                      )}
                    </div>

                    {/* Ministries */}
                    <div>
                      <h3 className="text-lg font-bold text-blue-400 flex items-center gap-2 mb-4">
                        <Building2 size={20} />
                        Ministries
                      </h3>
                      {hasMinistries ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {government.ministries.map((minister, idx) => (
                            <div 
                              key={idx} 
                              className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30"
                            >
                              <div className="p-2 bg-blue-600/20 rounded-full">
                                <Building2 size={16} className="text-blue-400" />
                              </div>
                              <div>
                                <p className="font-medium text-white">{minister.name}</p>
                                <p className="text-xs">
                                  <span className="text-blue-400">{minister.position}</span>
                                  {minister.age > 0 && <span className="text-slate-400">, {minister.age} years old</span>}
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-slate-500 italic p-4 bg-slate-800/20 rounded-lg border border-dashed border-slate-700">
                          No ministries assigned
                        </p>
                      )}
                    </div>

                    {/* Political Parties */}
                    <div>
                      <h3 className="text-lg font-bold text-green-400 flex items-center gap-2 mb-4">
                        <Vote size={20} />
                        Political Parties
                        {government.total_seats > 0 && (
                          <span className="text-sm font-normal text-slate-400">
                            (Total Seats: {government.total_seats})
                          </span>
                        )}
                      </h3>
                      {hasParties ? (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          {/* Party List */}
                          <div className="space-y-3">
                            {government.parties.map((party, idx) => (
                              <div 
                                key={idx} 
                                className="p-4 bg-slate-800/30 rounded-lg border border-slate-700/30"
                                style={{ borderLeftColor: getPartyColor(idx), borderLeftWidth: '4px' }}
                              >
                                <div className="flex items-center justify-between">
                                  <div>
                                    <p className="font-bold text-white text-lg">{party.name}</p>
                                    <Badge 
                                      className={`mt-1 ${
                                        party.status === 'Current ruling government' 
                                          ? 'bg-green-600/20 text-green-400 border-green-600/30' 
                                          : 'bg-slate-600/20 text-slate-400 border-slate-600/30'
                                      }`}
                                    >
                                      {party.status}
                                    </Badge>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-2xl font-bold" style={{ color: getPartyColor(idx) }}>
                                      {party.seats}
                                    </p>
                                    <p className="text-xs text-slate-400">seats</p>
                                  </div>
                                </div>
                                {party.leader_name && (
                                  <p className="mt-2 text-sm text-slate-400">
                                    Leader: <span className="text-white">{party.leader_name}</span>
                                    {party.leader_role && <span className="text-purple-400"> ({party.leader_role})</span>}
                                    {party.leader_age > 0 && <span>, {party.leader_age} y/o</span>}
                                  </p>
                                )}
                              </div>
                            ))}
                          </div>
                          
                          {/* Pie Chart */}
                          {government.total_seats > 0 && (
                            <Card className="bg-slate-800/20 border-slate-700/30">
                              <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-slate-400">Seat Distribution</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <PartyPieChart parties={government.parties} totalSeats={government.total_seats} />
                              </CardContent>
                            </Card>
                          )}
                        </div>
                      ) : (
                        <p className="text-slate-500 italic p-4 bg-slate-800/20 rounded-lg border border-dashed border-slate-700">
                          No political parties
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CountryLeaders;

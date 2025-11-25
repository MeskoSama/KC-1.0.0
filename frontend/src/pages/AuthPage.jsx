import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';
import { Pickaxe } from 'lucide-react';

const AuthPage = ({ onLogin }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({
    minecraft_username: '',
    password: '',
    server_code: ''
  });
  const [registerForm, setRegisterForm] = useState({
    minecraft_username: '',
    password: '',
    server_code: ''
  });

  const serverCodes = [
    { code: '10194', currency: 'NIM' },
    { code: '10997', currency: 'GRP' },
    { code: '20664', currency: 'VDD' },
    { code: '90154', currency: 'KKD' }
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, loginForm);
      toast.success('Login successful!');
      onLogin(response.data.user, response.data.token);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/auth/register`, registerForm);
      toast.success('Registration successful!');
      onLogin(response.data.user, response.data.token);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="minecraft-bg min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-emerald-600 rounded-lg mb-4 pulse-glow">
            <Pickaxe size={32} className="text-white" />
          </div>
          <h1 className="text-4xl font-black mb-2">
            <span className="text-emerald-400 glow-text">PIXEL</span>
            <span className="text-slate-100">TRADERS</span>
          </h1>
          <p className="text-slate-400">Enter your Minecraft credentials</p>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-800/50" data-testid="auth-tabs">
            <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
            <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <Card className="glass-card border-emerald-600/20">
              <CardHeader>
                <CardTitle>Login</CardTitle>
                <CardDescription>Enter your Minecraft username and server code</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-username">Minecraft Username</Label>
                    <Input
                      id="login-username"
                      data-testid="login-username"
                      placeholder="Steve"
                      value={loginForm.minecraft_username}
                      onChange={(e) => setLoginForm({ ...loginForm, minecraft_username: e.target.value })}
                      required
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <Input
                      id="login-password"
                      data-testid="login-password"
                      type="password"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                      required
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-server">Server Code</Label>
                    <Select
                      value={loginForm.server_code}
                      onValueChange={(value) => setLoginForm({ ...loginForm, server_code: value })}
                      required
                    >
                      <SelectTrigger className="bg-slate-800/50 border-slate-700" data-testid="login-server-select">
                        <SelectValue placeholder="Select server code" />
                      </SelectTrigger>
                      <SelectContent>
                        {serverCodes.map((server) => (
                          <SelectItem key={server.code} value={server.code} data-testid={`server-${server.code}`}>
                            {server.code} - {server.currency}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    className="w-full btn-minecraft"
                    disabled={isLoading}
                    data-testid="login-submit-button"
                  >
                    {isLoading ? 'Logging in...' : 'Login'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="register">
            <Card className="glass-card border-emerald-600/20">
              <CardHeader>
                <CardTitle>Register</CardTitle>
                <CardDescription>Create a new account</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleRegister} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="register-username">Minecraft Username</Label>
                    <Input
                      id="register-username"
                      data-testid="register-username"
                      placeholder="Steve"
                      value={registerForm.minecraft_username}
                      onChange={(e) => setRegisterForm({ ...registerForm, minecraft_username: e.target.value })}
                      required
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-password">Password</Label>
                    <Input
                      id="register-password"
                      data-testid="register-password"
                      type="password"
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                      required
                      className="bg-slate-800/50 border-slate-700"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="register-server">Server Code</Label>
                    <Select
                      value={registerForm.server_code}
                      onValueChange={(value) => setRegisterForm({ ...registerForm, server_code: value })}
                      required
                    >
                      <SelectTrigger className="bg-slate-800/50 border-slate-700" data-testid="register-server-select">
                        <SelectValue placeholder="Select your server" />
                      </SelectTrigger>
                      <SelectContent>
                        {serverCodes.map((server) => (
                          <SelectItem key={server.code} value={server.code} data-testid={`server-register-${server.code}`}>
                            {server.code} - {server.currency}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    className="w-full btn-minecraft"
                    disabled={isLoading}
                    data-testid="register-submit-button"
                  >
                    {isLoading ? 'Creating account...' : 'Register'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default AuthPage;

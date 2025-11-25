import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CheckCircle, Loader2, XCircle } from 'lucide-react';
import axios from 'axios';
import { API } from '../App';
import { toast } from 'sonner';

const PaymentSuccess = ({ user, onLogout, onUpdateUser }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('checking'); // checking, success, failed
  const [attempts, setAttempts] = useState(0);
  const sessionId = searchParams.get('session_id');

  useEffect(() => {
    if (sessionId) {
      checkPaymentStatus();
    } else {
      setStatus('failed');
      toast.error('No session ID found');
    }
  }, [sessionId]);

  const checkPaymentStatus = async (attemptCount = 0) => {
    if (attemptCount >= 5) {
      setStatus('timeout');
      toast.error('Payment verification timed out. Please check your balance.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.payment_status === 'paid') {
        setStatus('success');
        toast.success('Payment successful! Your account has been updated.');
        onUpdateUser();
      } else if (response.data.status === 'expired') {
        setStatus('failed');
        toast.error('Payment session expired');
      } else {
        // Still pending, retry after 2 seconds
        setAttempts(attemptCount + 1);
        setTimeout(() => checkPaymentStatus(attemptCount + 1), 2000);
      }
    } catch (error) {
      setStatus('failed');
      toast.error('Failed to verify payment status');
    }
  };

  return (
    <div className="minecraft-bg min-h-screen pb-12">
      <Navbar user={user} onLogout={onLogout} />
      <div className="container mx-auto px-4 flex items-center justify-center min-h-[70vh]">
        <Card className="glass-card border-emerald-600/20 max-w-md w-full">
          <CardHeader>
            <CardTitle className="text-center text-2xl">
              {status === 'checking' && 'Verifying Payment...'}
              {status === 'success' && 'Payment Successful!'}
              {status === 'failed' && 'Payment Failed'}
              {status === 'timeout' && 'Verification Timeout'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex justify-center">
              {status === 'checking' && (
                <div className="text-center">
                  <Loader2 size={64} className="text-emerald-400 animate-spin mx-auto mb-4" />
                  <p className="text-slate-400">Checking payment status...</p>
                  <p className="text-sm text-slate-500 mt-2">Attempt {attempts + 1} of 5</p>
                </div>
              )}
              {status === 'success' && (
                <div className="text-center">
                  <CheckCircle size={64} className="text-emerald-400 mx-auto mb-4" />
                  <p className="text-slate-400">Your payment has been processed successfully!</p>
                  <p className="text-sm text-slate-500 mt-2">Your balance has been updated.</p>
                </div>
              )}
              {(status === 'failed' || status === 'timeout') && (
                <div className="text-center">
                  <XCircle size={64} className="text-red-400 mx-auto mb-4" />
                  <p className="text-slate-400">
                    {status === 'failed'
                      ? 'Payment was not completed. Please try again.'
                      : 'Payment verification timed out. Please check your balance or contact support.'}
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <Button
                onClick={() => navigate('/dashboard')}
                className="flex-1 btn-minecraft"
                data-testid="return-dashboard-button"
              >
                Go to Dashboard
              </Button>
              {status !== 'checking' && (
                <Button
                  onClick={() => navigate('/marketplace')}
                  variant="outline"
                  className="flex-1 border-emerald-600 hover:bg-emerald-950"
                  data-testid="return-marketplace-button"
                >
                  Back to Marketplace
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default PaymentSuccess;

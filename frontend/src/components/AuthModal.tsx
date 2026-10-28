import React, { useState } from 'react';
import { X, Lock, Mail, User as UserIcon, ArrowRight, AlertCircle } from 'lucide-react';
import { loginUser, registerUser } from '../services/api';
import { User } from '../types';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: User) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        if (!emailOrUsername || !password) {
          throw new Error('Please fill in all fields.');
        }
        const data = await loginUser(emailOrUsername, password);
        onSuccess(data.user);
        onClose();
      } else {
        if (!email || !username || !password) {
          throw new Error('Please fill in all registration fields.');
        }
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters long.');
        }
        const data = await registerUser(email, username, password);
        onSuccess(data.user);
        onClose();
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-studio-800 border border-studio-700 rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 text-studio-500 hover:text-studio-100 hover:bg-studio-700/50 rounded-lg transition"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="space-y-1.5 text-center">
          <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-500 flex items-center justify-center mx-auto mb-3 shadow-inner">
            <Lock className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            {mode === 'login' ? 'Sign In to AI 3D Studio' : 'Create Free Studio Account'}
          </h3>
          <p className="text-xs text-studio-500">
            {mode === 'login'
              ? 'Access your private projects, customized assets, and generation ledger.'
              : 'Save unlimited assets, organize projects, and export clean 3D files.'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-red-950/80 border border-red-700/70 p-3 rounded-xl flex items-start space-x-2.5 text-xs text-red-200">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-400 mt-0.5" />
            <span className="flex-1">{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === 'login' ? (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">
                Email or Username
              </label>
              <div className="relative">
                <UserIcon className="w-4 h-4 text-studio-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  value={emailOrUsername}
                  onChange={(e) => setEmailOrUsername(e.target.value)}
                  placeholder="name@example.com or username"
                  className="w-full bg-studio-900 border border-studio-700 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-studio-50 placeholder-studio-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
                />
              </div>
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-studio-500 absolute left-3 top-3.5" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@example.com"
                    className="w-full bg-studio-900 border border-studio-700 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-studio-50 placeholder-studio-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">
                  Username
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-studio-500 absolute left-3 top-3.5" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="architect_3d"
                    className="w-full bg-studio-900 border border-studio-700 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-studio-50 placeholder-studio-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
                  />
                </div>
              </div>
            </>
          )}

          <div className="space-y-1.5">
            <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-studio-500 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-studio-900 border border-studio-700 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-studio-50 placeholder-studio-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 transition"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold py-3 px-4 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-brand-500/20 transition active:scale-[0.99] mt-2"
          >
            <span>{loading ? 'Authenticating...' : mode === 'login' ? 'Sign In' : 'Create Account'}</span>
            {!loading && <ArrowRight className="w-4 h-4" />}
          </button>
        </form>

        {/* Toggle Mode Footer */}
        <div className="pt-2 text-center text-xs text-studio-500 border-t border-studio-700/60">
          {mode === 'login' ? (
            <span>
              Don't have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('register'); setError(null); }}
                className="text-brand-500 hover:text-brand-400 font-semibold underline underline-offset-2 ml-1"
              >
                Sign up free
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => { setMode('login'); setError(null); }}
                className="text-brand-500 hover:text-brand-400 font-semibold underline underline-offset-2 ml-1"
              >
                Sign in
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

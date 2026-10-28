import React from 'react';
import { Box, Sparkles, Folder, Home, ExternalLink, LogIn, LogOut, Code2 } from 'lucide-react';
import { User } from '../types';

interface NavbarProps {
  currentTab: 'landing' | 'studio' | 'library';
  onTabChange: (tab: 'landing' | 'studio' | 'library') => void;
  blenderAvailable: boolean;
  currentUser: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  onTabChange,
  blenderAvailable,
  currentUser,
  onOpenAuth,
  onLogout
}) => {
  return (
    <header className="h-14 bg-studio-800/95 border-b border-studio-700/80 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 backdrop-blur-md flex-shrink-0">
      {/* Brand */}
      <div
        onClick={() => onTabChange('landing')}
        className="flex items-center space-x-2.5 cursor-pointer select-none group"
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-600 flex items-center justify-center text-white shadow group-hover:scale-105 transition">
          <Box className="w-4 h-4" />
        </div>
        <div>
          <span className="font-extrabold text-sm sm:text-base tracking-tight text-white flex items-center space-x-1">
            <span>AI 3D Studio</span>
          </span>
          <div className="flex items-center space-x-1.5 text-[10px] text-studio-500">
            <span className={`w-1.5 h-1.5 rounded-full ${blenderAvailable ? 'bg-emerald-400' : 'bg-red-400'}`} />
            <span>Hybrid Pipeline</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center space-x-1 bg-studio-900/60 p-1 rounded-xl border border-studio-700/60">
        <button
          onClick={() => onTabChange('landing')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
            currentTab === 'landing'
              ? 'bg-studio-700 text-white shadow'
              : 'text-studio-100 hover:text-white hover:bg-studio-700/40'
          }`}
        >
          <Home className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Overview</span>
        </button>

        <button
          onClick={() => onTabChange('studio')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
            currentTab === 'studio'
              ? 'bg-brand-600 text-white shadow'
              : 'text-studio-100 hover:text-white hover:bg-studio-700/40'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>3D Studio</span>
        </button>

        <button
          onClick={() => onTabChange('library')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
            currentTab === 'library'
              ? 'bg-studio-700 text-white shadow'
              : 'text-studio-100 hover:text-white hover:bg-studio-700/40'
          }`}
        >
          <Folder className="w-3.5 h-3.5" />
          <span>Library</span>
        </button>
      </nav>

      {/* Right controls: API Docs & Auth */}
      <div className="flex items-center space-x-3">
        {/* Swagger / OpenAPI Interactive Documentation Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          title="Interactive FastAPI Swagger documentation (OpenAPI 3.1 specification for developers)"
          className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 bg-studio-900 border border-studio-700 text-[11px] text-studio-100 hover:text-white hover:border-brand-500 rounded-lg transition"
        >
          <Code2 className="w-3.5 h-3.5 text-brand-500" />
          <span>API Docs (Swagger)</span>
          <ExternalLink className="w-3 h-3 text-studio-500" />
        </a>

        {/* User Account / Auth Menu */}
        {currentUser ? (
          <div className="flex items-center space-x-2 bg-studio-900 border border-studio-700 rounded-xl px-2.5 py-1">
            <div className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center text-[10px] font-bold">
              {currentUser.username ? currentUser.username[0].toUpperCase() : 'U'}
            </div>
            <span className="text-xs font-medium text-studio-50 max-w-[100px] truncate hidden sm:inline">
              {currentUser.username || currentUser.email}
            </span>
            <button
              onClick={onLogout}
              title="Sign Out"
              className="p-1 text-studio-500 hover:text-red-400 hover:bg-studio-800 rounded transition"
            >
              <LogOut className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow transition"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </header>
  );
};

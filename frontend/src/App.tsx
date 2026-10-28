import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { StudioWorkspace } from './features/studio/StudioWorkspace';
import { ProjectLibrary } from './features/projects/ProjectLibrary';
import { AuthModal } from './components/AuthModal';
import { fetchCapabilities, fetchHealth, fetchCurrentUser, setAuthToken } from './services/api';
import { SystemCapabilities, User, Asset } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<'landing' | 'studio' | 'library'>('landing');
  const [capabilities, setCapabilities] = useState<SystemCapabilities | null>(null);
  const [blenderAvailable, setBlenderAvailable] = useState<boolean>(true);
  const [blenderVersion, setBlenderVersion] = useState<string>('5.2.0');

  // Authentication State
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState<boolean>(false);

  // Asset selected from Library to view in Studio
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);

  useEffect(() => {
    // Check logged-in user
    fetchCurrentUser().then((user) => {
      if (user) setCurrentUser(user);
    });

    // Check system capabilities
    fetchCapabilities()
      .then((data) => {
        setCapabilities(data);
        setBlenderAvailable(data.blender_available);
        if (data.blender_version) {
          setBlenderVersion(data.blender_version);
        }
      })
      .catch((err) => {
        console.warn('Backend capabilities query failed, checking health...', err);
        fetchHealth()
          .then((h) => {
            setBlenderAvailable(h.blender_available);
            if (h.blender_version) setBlenderVersion(h.blender_version);
          })
          .catch(() => {});
      });
  }, []);

  const handleLogout = () => {
    setAuthToken(null);
    setCurrentUser(null);
  };

  const handleLoadAssetInStudio = (asset: Asset) => {
    setSelectedAsset(asset);
    setCurrentTab('studio');
  };

  return (
    <div className="min-h-screen flex flex-col bg-studio-900 text-studio-100 font-sans">
      <Navbar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        blenderAvailable={blenderAvailable}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
      />

      <main className="flex-1 flex flex-col overflow-hidden min-h-0">
        {currentTab === 'landing' && (
          <LandingPage
            onEnterStudio={() => setCurrentTab('studio')}
            blenderAvailable={blenderAvailable}
            blenderVersion={blenderVersion}
            aiConfigured={capabilities?.ai_configured ?? false}
            aiProviderName={capabilities?.ai_provider ?? 'meshy'}
          />
        )}

        {currentTab === 'studio' && (
          <StudioWorkspace
            capabilities={capabilities}
            loadedAsset={selectedAsset}
          />
        )}

        {currentTab === 'library' && (
          <ProjectLibrary
            onLoadInStudio={handleLoadAssetInStudio}
          />
        )}
      </main>

      {/* Login & Register Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
        }}
      />
    </div>
  );
}

export default App;

import React, { useEffect, useState } from 'react';
import {
  Folder,
  Trash2,
  Download,
  RefreshCw,
  Plus,
  Box,
  Eye,
  FolderPlus,
  X,
  FileArchive,
  ArrowRight
} from 'lucide-react';
import { Project, Asset } from '../../types';
import {
  fetchProjects,
  createProject,
  deleteProject,
  fetchAssets,
  deleteAsset,
  updateAsset,
  requestExport,
  getExportJob,
  resolveAssetUrl
} from '../../services/api';

interface ProjectLibraryProps {
  onLoadInStudio: (asset: Asset) => void;
}

export const ProjectLibrary: React.FC<ProjectLibraryProps> = ({ onLoadInStudio }) => {
  const [activeTab, setActiveTab] = useState<'projects' | 'assets'>('assets');
  const [projects, setProjects] = useState<Project[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');

  // Create Project Modal
  const [showCreateProject, setShowCreateProject] = useState<boolean>(false);
  const [newProjectName, setNewProjectName] = useState<string>('');
  const [newProjectDesc, setNewProjectDesc] = useState<string>('');
  const [creatingProject, setCreatingProject] = useState<boolean>(false);

  // Export progress tracker
  const [exportingAssetId, setExportingAssetId] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [projs, allAssets] = await Promise.all([
        fetchProjects(),
        fetchAssets()
      ]);
      setProjects(projs);
      setAssets(allAssets);
    } catch (err: any) {
      setError(err.message || 'Failed to load library data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    setCreatingProject(true);
    try {
      const p = await createProject(newProjectName.trim(), newProjectDesc.trim() || undefined);
      setProjects(prev => [p, ...prev]);
      setShowCreateProject(false);
      setNewProjectName('');
      setNewProjectDesc('');
    } catch (err: any) {
      alert(`Failed to create project: ${err.message}`);
    } finally {
      setCreatingProject(false);
    }
  };

  const handleDeleteProject = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete project "${name}"? Stored assets will be deleted.`)) {
      return;
    }
    try {
      await deleteProject(id);
      setProjects(prev => prev.filter(p => p.id !== id));
      setAssets(prev => prev.filter(a => a.project_id !== id));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleDeleteAsset = async (assetId: string) => {
    if (!window.confirm('Are you sure you want to delete this 3D model? The asset file will be permanently removed.')) {
      return;
    }
    try {
      await deleteAsset(assetId);
      setAssets(prev => prev.filter(a => a.id !== assetId));
    } catch (err: any) {
      alert(`Failed to delete asset: ${err.message}`);
    }
  };

  const handleMoveAsset = async (assetId: string, targetProjectId: string | null) => {
    try {
      const updated = await updateAsset(assetId, targetProjectId);
      setAssets(prev => prev.map(a => a.id === assetId ? updated : a));
    } catch (err: any) {
      alert(`Failed to move asset: ${err.message}`);
    }
  };

  const handleExportZip = async (asset: Asset) => {
    setExportingAssetId(asset.id);
    try {
      const exp = await requestExport(asset.id, 'gltf_zip');
      // Poll export
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        const status = await getExportJob(exp.id);
        if (status.status === 'completed' && status.download_url) {
          clearInterval(poll);
          setExportingAssetId(null);
          window.location.href = resolveAssetUrl(status.download_url);
        } else if (status.status === 'failed' || attempts > 20) {
          clearInterval(poll);
          setExportingAssetId(null);
          alert('glTF ZIP package generation failed or timed out.');
        }
      }, 1500);
    } catch (err: any) {
      setExportingAssetId(null);
      alert(`Export request failed: ${err.message}`);
    }
  };

  const filteredAssets = selectedProjectId === 'all'
    ? assets
    : assets.filter(a => a.project_id === selectedProjectId);

  return (
    <div className="flex-1 overflow-y-auto overscroll-contain p-4 sm:p-8 max-w-7xl mx-auto w-full space-y-6">
      {/* Top Banner & Tab Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-studio-700">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center space-x-2.5">
            <Folder className="w-6 h-6 text-brand-500" />
            <span>Library & Asset Manager</span>
          </h2>
          <p className="text-xs text-studio-500 mt-1">
            Browse, manage, download, or re-open your generated 3D models and project collections.
          </p>
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
          <div className="bg-studio-800 p-1 rounded-xl border border-studio-700 flex space-x-1 text-xs">
            <button
              onClick={() => setActiveTab('assets')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                activeTab === 'assets' ? 'bg-brand-600 text-white' : 'text-studio-100 hover:text-white'
              }`}
            >
              <span>3D Models ({assets.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('projects')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                activeTab === 'projects' ? 'bg-brand-600 text-white' : 'text-studio-100 hover:text-white'
              }`}
            >
              <span>Projects ({projects.length})</span>
            </button>
          </div>

          <button
            onClick={loadData}
            title="Reload library"
            className="p-2 bg-studio-800 hover:bg-studio-700 border border-studio-700 text-studio-100 rounded-xl transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-950/80 border border-red-700 p-4 rounded-xl text-xs text-red-200">
          {error}
        </div>
      )}

      {/* -------------------- ASSETS TAB -------------------- */}
      {activeTab === 'assets' && (
        <div className="space-y-4">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-studio-800/60 p-3 rounded-xl border border-studio-700/70">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-studio-500 uppercase tracking-wider">Project:</span>
              <select
                value={selectedProjectId}
                onChange={(e) => setSelectedProjectId(e.target.value)}
                className="bg-studio-900 border border-studio-700 text-xs text-studio-50 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-brand-500"
              >
                <option value="all">All Projects & Loose Assets</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>

            <span className="text-xs text-studio-500 font-mono">
              Showing {filteredAssets.length} asset{filteredAssets.length === 1 ? '' : 's'}
            </span>
          </div>

          {loading ? (
            <div className="py-20 text-center text-studio-500 text-sm">
              <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3 text-brand-500" />
              Loading your 3D models...
            </div>
          ) : filteredAssets.length === 0 ? (
            <div className="py-20 text-center bg-studio-800/30 border border-dashed border-studio-700 rounded-2xl p-8 space-y-3">
              <Box className="w-12 h-12 text-studio-600 mx-auto" />
              <h3 className="text-sm font-semibold text-studio-100">No 3D Models in this Selection</h3>
              <p className="text-xs text-studio-500 max-w-sm mx-auto">
                Generate 3D assets in the Studio using natural language prompts or parametric dimensions.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredAssets.map((asset) => (
                <div
                  key={asset.id}
                  className="bg-studio-800 border border-studio-700 hover:border-studio-600 rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-xl transition group"
                >
                  <div className="space-y-3">
                    {/* Header badge & format */}
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-mono px-2 py-0.5 rounded uppercase font-semibold bg-brand-500/10 text-brand-400 border border-brand-500/20">
                        {asset.file_format} • {asset.validation_status}
                      </span>
                      <span className="text-[11px] text-studio-500">
                        {new Date(asset.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    {/* Prompt / Description */}
                    <div>
                      <h4 className="text-sm font-bold text-white group-hover:text-brand-400 transition line-clamp-2">
                        {asset.prompt || `3D Asset ${asset.id.slice(0, 8)}`}
                      </h4>
                      <p className="text-[11px] text-studio-500 mt-0.5">
                        Mode: <span className="font-medium text-studio-100">{asset.generation_mode || 'Procedural'}</span>
                      </p>
                    </div>

                    {/* Asset Metrics */}
                    <div className="grid grid-cols-2 gap-2 bg-studio-900/80 p-2.5 rounded-xl border border-studio-700/60 text-[11px]">
                      <div>
                        <span className="text-studio-500 block">Triangles</span>
                        <span className="font-mono text-studio-100 font-semibold">{asset.polygon_count.toLocaleString()}</span>
                      </div>
                      <div>
                        <span className="text-studio-500 block">File Size</span>
                        <span className="font-mono text-studio-100 font-semibold">{(asset.file_size / 1024).toFixed(1)} KB</span>
                      </div>
                      {asset.dimensions && (
                        <div className="col-span-2 pt-1 border-t border-studio-800">
                          <span className="text-studio-500 block">Dimensions (W × D × H)</span>
                          <span className="font-mono text-studio-100 font-semibold">
                            {asset.dimensions.x ?? 0}m × {asset.dimensions.y ?? 0}m × {asset.dimensions.z ?? 0}m
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Project Assignment */}
                    <div className="space-y-1">
                      <span className="text-[10px] uppercase font-semibold text-studio-500">Project Collection</span>
                      <select
                        value={asset.project_id || ''}
                        onChange={(e) => handleMoveAsset(asset.id, e.target.value || null)}
                        className="w-full bg-studio-900 border border-studio-700 text-xs text-studio-100 rounded-lg p-1.5 focus:outline-none"
                      >
                        <option value="">(None - Unassigned)</option>
                        {projects.map((p) => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="pt-3 border-t border-studio-700/60 space-y-2">
                    <button
                      type="button"
                      onClick={() => onLoadInStudio(asset)}
                      className="w-full bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold py-2 px-3 rounded-xl flex items-center justify-center space-x-1.5 shadow transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Open in 3D Viewport</span>
                    </button>

                    <div className="flex items-center space-x-2">
                      <a
                        href={asset.download_url}
                        download={`model_${asset.id.slice(0, 8)}.glb`}
                        className="flex-1 bg-studio-700 hover:bg-studio-600 text-studio-100 text-xs font-semibold py-1.5 px-2 rounded-lg text-center flex items-center justify-center space-x-1 transition"
                      >
                        <Download className="w-3 h-3" />
                        <span>GLB</span>
                      </a>

                      <button
                        type="button"
                        disabled={exportingAssetId === asset.id}
                        onClick={() => handleExportZip(asset)}
                        title="Package model.gltf + model.bin into standard ZIP"
                        className="flex-1 bg-studio-700 hover:bg-studio-600 text-studio-100 text-xs font-semibold py-1.5 px-2 rounded-lg text-center flex items-center justify-center space-x-1 transition disabled:opacity-50"
                      >
                        <FileArchive className="w-3 h-3 text-brand-400" />
                        <span>{exportingAssetId === asset.id ? 'Packaging...' : 'glTF ZIP'}</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleDeleteAsset(asset.id)}
                        title="Delete asset permanently"
                        className="p-2 text-studio-500 hover:text-red-400 hover:bg-studio-700/50 rounded-lg transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* -------------------- PROJECTS TAB -------------------- */}
      {activeTab === 'projects' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-studio-500">
              Project Folders & Collections
            </h3>
            <button
              onClick={() => setShowCreateProject(true)}
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-semibold rounded-xl shadow transition"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>New Project</span>
            </button>
          </div>

          {loading ? (
            <div className="py-20 text-center text-studio-500 text-sm">
              <RefreshCw className="w-8 h-8 mx-auto animate-spin mb-3 text-brand-500" />
              Loading projects...
            </div>
          ) : projects.length === 0 ? (
            <div className="py-20 text-center bg-studio-800/30 border border-dashed border-studio-700 rounded-2xl p-8 space-y-3">
              <FolderPlus className="w-12 h-12 text-studio-600 mx-auto" />
              <h3 className="text-sm font-semibold text-studio-100">No Projects Created Yet</h3>
              <p className="text-xs text-studio-500 max-w-sm mx-auto">
                Group your 3D assets into named folders for games, architectural scenes, or client designs.
              </p>
              <button
                onClick={() => setShowCreateProject(true)}
                className="inline-flex items-center space-x-1.5 px-4 py-2 bg-brand-600 text-white text-xs font-semibold rounded-xl"
              >
                <Plus className="w-4 h-4" />
                <span>Create Your First Project</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {projects.map((proj) => (
                <div
                  key={proj.id}
                  className="bg-studio-800 border border-studio-700 hover:border-studio-600 rounded-2xl p-5 flex flex-col justify-between space-y-4 shadow-xl transition"
                >
                  <div>
                    <div className="flex justify-between items-start">
                      <div className="flex items-center space-x-2 flex-1 min-w-0">
                        <Folder className="w-5 h-5 text-brand-500 flex-shrink-0" />
                        <h4 className="font-bold text-white text-sm truncate">{proj.name}</h4>
                      </div>
                      <button
                        onClick={() => handleDeleteProject(proj.id, proj.name)}
                        className="text-studio-500 hover:text-red-400 p-1 rounded transition ml-2"
                        title="Delete project"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    {proj.description && (
                      <p className="text-xs text-studio-500 mt-2 line-clamp-2">{proj.description}</p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-studio-700/60 flex items-center justify-between">
                    <span className="text-[11px] text-studio-500 font-mono">
                      {proj.asset_count} model{proj.asset_count === 1 ? '' : 's'}
                    </span>
                    <button
                      onClick={() => {
                        setSelectedProjectId(proj.id);
                        setActiveTab('assets');
                      }}
                      className="text-xs font-semibold text-brand-400 hover:text-brand-300 flex items-center space-x-1"
                    >
                      <span>View Models</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* New Project Dialog */}
      {showCreateProject && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in">
          <div className="bg-studio-800 border border-studio-700 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-studio-700">
              <div className="flex items-center space-x-2">
                <FolderPlus className="w-5 h-5 text-brand-500" />
                <h3 className="font-bold text-white">Create New Project</h3>
              </div>
              <button onClick={() => setShowCreateProject(false)} className="text-studio-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateProject} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">Project Name</label>
                <input
                  type="text"
                  required
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Cyberpunk Environment, Living Room Pack"
                  className="w-full bg-studio-900 border border-studio-700 rounded-xl p-2.5 text-xs text-studio-50 focus:outline-none focus:border-brand-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-studio-500">Description (Optional)</label>
                <textarea
                  rows={2}
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Brief notes about the models in this project"
                  className="w-full bg-studio-900 border border-studio-700 rounded-xl p-2.5 text-xs text-studio-50 focus:outline-none focus:border-brand-500 resize-none"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateProject(false)}
                  className="px-4 py-2 text-xs text-studio-100 hover:bg-studio-700 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creatingProject || !newProjectName.trim()}
                  className="px-4 py-2 text-xs bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl shadow transition disabled:opacity-50"
                >
                  {creatingProject ? 'Creating...' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

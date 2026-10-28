import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Upload,
  Sliders,
  Download,
  AlertTriangle,
  X,
  Info,
  Wand2,
  Eye,
  SlidersHorizontal
} from 'lucide-react';
import {
  GenerationCreateRequest,
  GenerationJob,
  Asset,
  GenerationMode,
  SystemCapabilities,
  RefineRequest
} from '../../types';
import {
  submitGeneration,
  getGenerationJob,
  cancelGenerationJob,
  fetchAsset,
  uploadReferenceImage,
  submitRefinement,
  resolveAssetUrl
} from '../../services/api';
import { ThreeViewer } from '../viewer/ThreeViewer';

interface StudioWorkspaceProps {
  capabilities: SystemCapabilities | null;
  loadedAsset?: Asset | null;
}

const CATEGORIES = [
  { id: 'table', label: 'Table / Desk' },
  { id: 'chair', label: 'Chair / Seat' },
  { id: 'cabinet', label: 'Cabinet / Shelves' },
  { id: 'house', label: 'House / Cottage' },
  { id: 'room', label: 'Room / Interior' },
  { id: 'column', label: 'Column / Pillar' },
  { id: 'road_segment', label: 'Road Segment' },
  { id: 'platform', label: 'Display Platform' }
];

const MATERIALS = [
  { id: 'wood', label: 'Oak Wood' },
  { id: 'dark_wood', label: 'Dark Walnut' },
  { id: 'metal_steel', label: 'Brushed Steel' },
  { id: 'metal_black', label: 'Matte Black Metal' },
  { id: 'metal_gold', label: 'Polished Gold' },
  { id: 'marble', label: 'Carrara Marble' },
  { id: 'concrete', label: 'Smooth Concrete' },
  { id: 'fabric_cushion', label: 'Fabric / Upholstery' },
  { id: 'plastic_white', label: 'Glossy White Plastic' }
];

const STYLES = [
  { id: 'modern', label: 'Modern' },
  { id: 'rustic', label: 'Rustic' },
  { id: 'minimalist', label: 'Minimalist' },
  { id: 'classic', label: 'Classic' },
  { id: 'scifi', label: 'Sci-Fi' }
];

export const StudioWorkspace: React.FC<StudioWorkspaceProps> = ({ capabilities, loadedAsset }) => {
  // Mobile / Small Screen tab toggle: 'controls' vs 'viewport'
  const [mobileTab, setMobileTab] = useState<'controls' | 'viewport'>('controls');

  // Generation inputs
  const [prompt, setPrompt] = useState<string>('modern wooden dining table with black steel legs 1.8m wide');
  const [generationMode, setGenerationMode] = useState<GenerationMode>('auto');
  const [category, setCategory] = useState<string>('table');
  const [style, setStyle] = useState<string>('modern');
  const [material, setMaterial] = useState<string>('wood');
  const [colorHex, setColorHex] = useState<string>('#8B5A2B');

  // Parametric Dimensions
  const [useCustomDimensions, setUseCustomDimensions] = useState<boolean>(true);
  const [width, setWidth] = useState<number>(1.8);
  const [depth, setDepth] = useState<number>(0.9);
  const [height, setHeight] = useState<number>(0.75);

  // Uploaded Image
  const [referenceImage, setReferenceImage] = useState<{ id: string; url: string; name: string } | null>(null);
  const [uploadingImage, setUploadingImage] = useState<boolean>(false);

  // Active Job State
  const [activeJob, setActiveJob] = useState<GenerationJob | null>(null);
  const [currentAsset, setCurrentAsset] = useState<Asset | null>(null);
  const [activeModelUrl, setActiveModelUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [explanationNote, setExplanationNote] = useState<string | null>(null);

  // Refine Modal
  const [showRefineModal, setShowRefineModal] = useState<boolean>(false);
  const [refinePrompt, setRefinePrompt] = useState<string>('');

  // Handle external asset loading (e.g. from Project Library)
  useEffect(() => {
    if (loadedAsset) {
      setCurrentAsset(loadedAsset);
      setActiveModelUrl(loadedAsset.download_url);
      if (loadedAsset.prompt) {
        setPrompt(loadedAsset.prompt);
      }
      if (loadedAsset.dimensions) {
        if (loadedAsset.dimensions.x) setWidth(loadedAsset.dimensions.x);
        if (loadedAsset.dimensions.y) setDepth(loadedAsset.dimensions.y);
        if (loadedAsset.dimensions.z) setHeight(loadedAsset.dimensions.z);
      }
      setMobileTab('viewport');
    }
  }, [loadedAsset]);

  // Poll active generation job
  useEffect(() => {
    if (!activeJob || activeJob.status === 'completed' || activeJob.status === 'failed' || activeJob.status === 'cancelled') {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getGenerationJob(activeJob.id);
        setActiveJob(updated);

        if (updated.status === 'completed' && updated.asset_id) {
          clearInterval(interval);
          const assetData = await fetchAsset(updated.asset_id);
          setCurrentAsset(assetData);
          setActiveModelUrl(assetData.download_url);
          setMobileTab('viewport'); // Auto-switch to viewport on mobile to view model
        } else if (updated.status === 'failed') {
          clearInterval(interval);
          setErrorMessage(updated.safe_error_message || 'Generation failed.');
        }
      } catch (err: any) {
        console.error('Job polling error:', err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeJob]);

  // Handle Reference Image Upload
  const handleImageFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingImage(true);
    setErrorMessage(null);
    try {
      const res = await uploadReferenceImage(file);
      setReferenceImage({
        id: res.upload_id,
        url: URL.createObjectURL(file),
        name: res.filename
      });
      if (generationMode === 'auto') {
        setGenerationMode('ai_image');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Image upload failed');
    } finally {
      setUploadingImage(false);
    }
  };

  // Trigger Generation
  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setErrorMessage('Please enter a natural language prompt.');
      return;
    }

    setErrorMessage(null);
    setExplanationNote(null);

    const payload: GenerationCreateRequest = {
      prompt: prompt.trim(),
      generation_mode: generationMode,
      object_category: category,
      style,
      material_preferences: {
        preset: material,
        color_hex: colorHex
      },
      export_format: 'glb'
    };

    if (useCustomDimensions) {
      payload.dimensions = { width, depth, height, units: 'meters' };
    }

    if (referenceImage) {
      payload.reference_image_id = referenceImage.id;
    }

    try {
      const job = await submitGeneration(payload);
      setActiveJob(job);
      if (job.safe_error_message) {
        setExplanationNote(job.safe_error_message);
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit generation job.');
    }
  };

  // Trigger Cancellation
  const handleCancel = async () => {
    if (!activeJob) return;
    try {
      await cancelGenerationJob(activeJob.id);
      setActiveJob(prev => prev ? { ...prev, status: 'cancelled' } : null);
    } catch (err) {
      console.error('Failed to cancel job:', err);
    }
  };

  // Trigger Refinement
  const handleRefineSubmit = async () => {
    if (!currentAsset) return;
    setShowRefineModal(false);
    setErrorMessage(null);

    const payload: RefineRequest = {
      prompt: refinePrompt.trim() || undefined,
      dimensions: useCustomDimensions ? { width, depth, height, units: 'meters' } : undefined,
      material_preferences: { preset: material, color_hex: colorHex },
      style,
      category
    };

    try {
      const job = await submitRefinement(currentAsset.id, payload);
      setActiveJob(job);
      setExplanationNote(`Refining asset ${currentAsset.id.slice(0, 8)}...`);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to submit refinement.');
    }
  };

  return (
    <div className="flex-1 w-full h-full flex flex-col min-h-0 overflow-hidden">
      {/* Mobile Top Tabs (visible on small/medium screens < lg) */}
      <div className="lg:hidden flex items-center justify-around bg-studio-800 border-b border-studio-700 px-3 py-1.5 flex-shrink-0 z-20">
        <button
          onClick={() => setMobileTab('controls')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
            mobileTab === 'controls' ? 'bg-brand-600 text-white' : 'text-studio-300 hover:bg-studio-700'
          }`}
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>Generator Controls</span>
        </button>

        <button
          onClick={() => setMobileTab('viewport')}
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-semibold transition ${
            mobileTab === 'viewport' ? 'bg-brand-600 text-white' : 'text-studio-300 hover:bg-studio-700'
          }`}
        >
          <Eye className="w-3.5 h-3.5" />
          <span>3D Viewport</span>
          {activeJob && (activeJob.status === 'running' || activeJob.status === 'queued') && (
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
          )}
        </button>
      </div>

      {/* Main Workspace Split View */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden min-h-0 w-full h-full">
        {/* Left Control Panel */}
        <div
          className={`w-full lg:w-[380px] xl:w-[410px] bg-studio-800 border-r border-studio-700/80 flex flex-col h-full min-h-0 flex-shrink-0 overflow-hidden ${
            mobileTab === 'viewport' ? 'hidden lg:flex' : 'flex'
          }`}
        >
          {/* Top Scrollable Controls Area */}
          <div className="flex-1 overflow-y-auto overscroll-contain custom-scrollbar p-3.5 space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between pb-0.5">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-brand-500" />
                <h2 className="text-sm font-bold text-white">3D Asset Studio</h2>
              </div>
              <span className="text-[10px] bg-brand-500/10 text-brand-400 border border-brand-500/20 px-2 py-0.5 rounded-full font-mono font-medium">
                {generationMode.toUpperCase()}
              </span>
            </div>

            {/* Prompt Input */}
            <div className="space-y-1">
              <div className="flex justify-between items-center text-[11px] font-semibold uppercase tracking-wider text-studio-400">
                <span>Prompt</span>
                <span className="text-[10px] text-studio-500 lowercase">{prompt.length}/1000</span>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your 3D asset in detail..."
                rows={2}
                className="w-full bg-studio-900 border border-studio-700 rounded-lg p-2.5 text-xs text-studio-50 placeholder-studio-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 resize-none transition"
              />
            </div>

            {/* Mode Selector */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-studio-400 block">
                Generation Engine
              </label>
              <div className="grid grid-cols-2 gap-1.5">
                <button
                  type="button"
                  onClick={() => setGenerationMode('auto')}
                  className={`p-2 rounded-lg border text-left text-xs transition ${
                    generationMode === 'auto'
                      ? 'border-brand-500 bg-brand-500/15 text-white font-medium shadow-sm'
                      : 'border-studio-700 bg-studio-900/60 text-studio-300 hover:border-studio-600'
                  }`}
                >
                  <div className="font-semibold text-[11px] flex items-center justify-between">
                    <span>Auto (Hybrid)</span>
                    <span className="text-[9px] bg-brand-500/20 text-brand-400 px-1 py-0.2 rounded font-mono">Smart</span>
                  </div>
                  <p className="text-[10px] text-studio-500 leading-tight mt-0.5 truncate">Parametric or AI route</p>
                </button>

                <button
                  type="button"
                  onClick={() => setGenerationMode('procedural')}
                  className={`p-2 rounded-lg border text-left text-xs transition ${
                    generationMode === 'procedural'
                      ? 'border-brand-500 bg-brand-500/15 text-white font-medium shadow-sm'
                      : 'border-studio-700 bg-studio-900/60 text-studio-300 hover:border-studio-600'
                  }`}
                >
                  <div className="font-semibold text-[11px] flex items-center justify-between">
                    <span>Blender (bpy)</span>
                    <span className="text-[9px] bg-emerald-500/20 text-emerald-400 px-1 py-0.2 rounded font-mono">Fast</span>
                  </div>
                  <p className="text-[10px] text-studio-500 leading-tight mt-0.5 truncate">Precision procedural mesh</p>
                </button>

                <button
                  type="button"
                  onClick={() => setGenerationMode('ai_text')}
                  className={`p-2 rounded-lg border text-left text-xs transition ${
                    generationMode === 'ai_text'
                      ? 'border-brand-500 bg-brand-500/15 text-white font-medium shadow-sm'
                      : 'border-studio-700 bg-studio-900/60 text-studio-300 hover:border-studio-600'
                  }`}
                >
                  <div className="font-semibold text-[11px] flex items-center justify-between">
                    <span>AI Text-to-3D</span>
                    <span className={`text-[9px] px-1 py-0.2 rounded font-mono ${capabilities?.ai_configured ? 'bg-purple-500/20 text-purple-400' : 'bg-amber-500/20 text-amber-400'}`}>
                      {capabilities?.ai_configured ? 'Live' : 'Key Req'}
                    </span>
                  </div>
                  <p className="text-[10px] text-studio-500 leading-tight mt-0.5 truncate">Free-form neural meshes</p>
                </button>

                <button
                  type="button"
                  onClick={() => setGenerationMode('ai_image')}
                  className={`p-2 rounded-lg border text-left text-xs transition ${
                    generationMode === 'ai_image'
                      ? 'border-brand-500 bg-brand-500/15 text-white font-medium shadow-sm'
                      : 'border-studio-700 bg-studio-900/60 text-studio-300 hover:border-studio-600'
                  }`}
                >
                  <div className="font-semibold text-[11px] flex items-center justify-between">
                    <span>AI Image-to-3D</span>
                    <span className="text-[9px] bg-sky-500/20 text-sky-400 px-1 py-0.2 rounded font-mono">Vision</span>
                  </div>
                  <p className="text-[10px] text-studio-500 leading-tight mt-0.5 truncate">Reference image mesh</p>
                </button>
              </div>
            </div>

            {/* Reference Image Upload */}
            <div className="space-y-1">
              <div className="flex justify-between items-center text-[11px] font-semibold uppercase tracking-wider text-studio-400">
                <span>Reference Image (Optional)</span>
                {referenceImage && (
                  <button
                    onClick={() => setReferenceImage(null)}
                    className="text-[10px] text-red-400 hover:underline"
                  >
                    Remove
                  </button>
                )}
              </div>

              {referenceImage ? (
                <div className="flex items-center space-x-2 bg-studio-900 p-2 rounded-lg border border-studio-700">
                  <img
                    src={referenceImage.url}
                    alt="Reference"
                    className="w-10 h-10 object-cover rounded border border-studio-700 flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-studio-100 truncate">{referenceImage.name}</p>
                    <p className="text-[10px] text-emerald-400">Attached for Image-to-3D</p>
                  </div>
                </div>
              ) : (
                <label className="flex items-center justify-center space-x-2 p-2 border border-dashed border-studio-700 rounded-lg hover:border-brand-500 cursor-pointer bg-studio-900/40 transition text-xs text-studio-300">
                  <Upload className="w-3.5 h-3.5 text-studio-400" />
                  <span className="text-[11px]">{uploadingImage ? 'Uploading image...' : 'Upload Reference Image (JPG, PNG)'}</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleImageFileChange}
                    className="hidden"
                  />
                </label>
              )}
            </div>

            {/* Structured Category & Style */}
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-studio-400 block">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 rounded-lg p-2 text-xs text-studio-100 focus:outline-none focus:border-brand-500"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c.id} value={c.id}>{c.label}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-studio-400 block">
                  Style
                </label>
                <select
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                  className="w-full bg-studio-900 border border-studio-700 rounded-lg p-2 text-xs text-studio-100 focus:outline-none focus:border-brand-500"
                >
                  {STYLES.map((s) => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Material Presets & Color */}
            <div className="space-y-1">
              <label className="text-[11px] font-semibold uppercase tracking-wider text-studio-400 block">
                Material Preset & Color
              </label>
              <div className="grid grid-cols-2 gap-2">
                <select
                  value={material}
                  onChange={(e) => setMaterial(e.target.value)}
                  className="bg-studio-900 border border-studio-700 rounded-lg p-2 text-xs text-studio-100 focus:outline-none focus:border-brand-500"
                >
                  {MATERIALS.map((m) => (
                    <option key={m.id} value={m.id}>{m.label}</option>
                  ))}
                </select>

                <div className="flex items-center space-x-2 bg-studio-900 border border-studio-700 rounded-lg px-2 py-1">
                  <input
                    type="color"
                    value={colorHex}
                    onChange={(e) => setColorHex(e.target.value)}
                    className="w-6 h-6 rounded border-none cursor-pointer bg-transparent"
                  />
                  <span className="text-xs font-mono text-studio-200">{colorHex}</span>
                </div>
              </div>
            </div>

            {/* Parametric Dimensions (Meters) */}
            <div className="space-y-2 pt-1 border-t border-studio-700/60">
              <div className="flex items-center justify-between">
                <label className="text-[11px] font-semibold uppercase tracking-wider text-studio-400 flex items-center space-x-1.5 cursor-pointer">
                  <Sliders className="w-3 h-3 text-brand-400" />
                  <span>Dimensions (Meters)</span>
                </label>
                <input
                  type="checkbox"
                  checked={useCustomDimensions}
                  onChange={(e) => setUseCustomDimensions(e.target.checked)}
                  className="rounded border-studio-700 text-brand-500 focus:ring-brand-500 cursor-pointer"
                />
              </div>

              {useCustomDimensions && (
                <div className="grid grid-cols-3 gap-1.5">
                  <div>
                    <span className="text-[10px] text-studio-400 block mb-0.5">Width (X)</span>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="50"
                      value={width}
                      onChange={(e) => setWidth(parseFloat(e.target.value) || 1.0)}
                      className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-100"
                    />
                  </div>
                  <div>
                    <span className="text-[10px] text-studio-400 block mb-0.5">Depth (Y)</span>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="50"
                      value={depth}
                      onChange={(e) => setDepth(parseFloat(e.target.value) || 1.0)}
                      className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-100"
                    />
                  </div>
                  <div>
                    <span className="text-[10px] text-studio-400 block mb-0.5">Height (Z)</span>
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="50"
                      value={height}
                      onChange={(e) => setHeight(parseFloat(e.target.value) || 1.0)}
                      className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-100"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Explanation Banner */}
            {explanationNote && (
              <div className="bg-brand-500/10 border border-brand-500/30 rounded-lg p-2.5 flex items-start space-x-2 text-xs text-brand-400">
                <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{explanationNote}</span>
              </div>
            )}

            {/* Error Banner */}
            {errorMessage && (
              <div className="bg-red-950/80 border border-red-700 text-red-200 rounded-lg p-2.5 flex items-start space-x-2 text-xs">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-400 mt-0.5" />
                <div className="flex-1">
                  <span>{errorMessage}</span>
                </div>
                <button onClick={() => setErrorMessage(null)} className="text-red-400 hover:text-white">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}
          </div>

          {/* Fixed Bottom Action Bar */}
          <div className="p-3 bg-studio-800 border-t border-studio-700/80 flex-shrink-0 space-y-2 z-10 shadow-lg">
            {activeJob && (activeJob.status === 'running' || activeJob.status === 'queued') ? (
              <div className="space-y-1.5 bg-studio-900 p-2.5 rounded-lg border border-studio-700">
                <div className="flex justify-between items-center text-xs">
                  <span className="font-semibold text-white flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-brand-500 animate-ping inline-block" />
                    <span>Processing ({activeJob.generation_mode})</span>
                  </span>
                  <span className="font-mono text-brand-400 font-bold">{activeJob.progress}%</span>
                </div>
                <div className="w-full bg-studio-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-brand-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${activeJob.progress}%` }}
                  />
                </div>
                <div className="flex justify-between items-center pt-0.5">
                  <span className="text-[10px] text-studio-400">Worker executing...</span>
                  <button
                    onClick={handleCancel}
                    className="text-[11px] text-red-400 hover:text-red-300 hover:underline"
                  >
                    Cancel Task
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={handleGenerate}
                className="w-full bg-brand-600 hover:bg-brand-500 text-white font-semibold py-2.5 px-4 rounded-lg text-xs sm:text-sm flex items-center justify-center space-x-2 shadow-lg transition active:scale-[0.99]"
              >
                <Sparkles className="w-4 h-4" />
                <span>Generate 3D Model</span>
              </button>
            )}

            {currentAsset && (
              <div className="flex space-x-2 pt-0.5">
                <button
                  type="button"
                  onClick={() => setShowRefineModal(true)}
                  className="flex-1 bg-studio-700 hover:bg-studio-600 text-studio-100 text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 transition"
                >
                  <Wand2 className="w-3.5 h-3.5 text-brand-400" />
                  <span>Refine</span>
                </button>

                <a
                  href={resolveAssetUrl(currentAsset.download_url || `/api/assets/${currentAsset.id}/file`)}
                  download={`model_${currentAsset.id.slice(0, 8)}.glb`}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center space-x-1.5 transition text-center"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Export GLB</span>
                </a>
              </div>
            )}
          </div>
        </div>

        {/* Right 3D Viewport Panel */}
        <div
          className={`flex-1 h-full min-h-0 relative overflow-hidden bg-studio-900 ${
            mobileTab === 'controls' ? 'hidden lg:flex' : 'flex'
          }`}
        >
          <ThreeViewer
            modelUrl={activeModelUrl}
            statistics={currentAsset ? {
              vertices: currentAsset.vertex_count,
              triangles: currentAsset.polygon_count,
              dimensions: currentAsset.dimensions,
              file_size_bytes: currentAsset.file_size
            } : undefined}
          />
        </div>
      </div>

      {/* Refine Modal Dialog */}
      {showRefineModal && currentAsset && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-studio-800 border border-studio-700 rounded-xl max-w-md w-full p-5 shadow-2xl space-y-3.5">
            <div className="flex justify-between items-center pb-2 border-b border-studio-700">
              <div className="flex items-center space-x-2">
                <Wand2 className="w-4 h-4 text-brand-500" />
                <h3 className="font-bold text-sm text-white">Refine 3D Asset</h3>
              </div>
              <button onClick={() => setShowRefineModal(false)} className="text-studio-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-studio-300">
              Adjust parameters or prompt. A new version of the asset will be generated and linked in project history.
            </p>

            <div className="space-y-1">
              <label className="text-[11px] font-semibold text-studio-400">Refined Prompt Notes (Optional)</label>
              <input
                type="text"
                value={refinePrompt}
                onChange={(e) => setRefinePrompt(e.target.value)}
                placeholder="e.g. increase table length to 2.2m"
                className="w-full bg-studio-900 border border-studio-700 rounded-lg p-2 text-xs text-studio-50"
              />
            </div>

            <div className="grid grid-cols-3 gap-2">
              <div>
                <span className="text-[10px] text-studio-400 block mb-0.5">Width (m)</span>
                <input
                  type="number"
                  step="0.1"
                  value={width}
                  onChange={(e) => setWidth(parseFloat(e.target.value) || 1.0)}
                  className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-50"
                />
              </div>
              <div>
                <span className="text-[10px] text-studio-400 block mb-0.5">Depth (m)</span>
                <input
                  type="number"
                  step="0.1"
                  value={depth}
                  onChange={(e) => setDepth(parseFloat(e.target.value) || 1.0)}
                  className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-50"
                />
              </div>
              <div>
                <span className="text-[10px] text-studio-400 block mb-0.5">Height (m)</span>
                <input
                  type="number"
                  step="0.1"
                  value={height}
                  onChange={(e) => setHeight(parseFloat(e.target.value) || 1.0)}
                  className="w-full bg-studio-900 border border-studio-700 rounded p-1.5 text-xs font-mono text-studio-50"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowRefineModal(false)}
                className="px-3 py-1.5 text-xs text-studio-300 hover:bg-studio-700 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleRefineSubmit}
                className="px-3.5 py-1.5 text-xs bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-lg shadow transition"
              >
                Re-generate Asset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

import React from 'react';
import {
  Sparkles,
  Cpu,
  ArrowRight,
  ShieldCheck,
  Zap,
  CheckCircle
} from 'lucide-react';

interface LandingPageProps {
  onEnterStudio: () => void;
  blenderAvailable: boolean;
  blenderVersion?: string;
  aiConfigured: boolean;
  aiProviderName: string;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onEnterStudio,
  blenderAvailable,
  blenderVersion,
  aiConfigured,
  aiProviderName
}) => {
  return (
    <div className="flex-1 overflow-y-auto">
      {/* Hero Section */}
      <section className="relative overflow-hidden py-20 px-6 max-w-6xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-500 text-xs font-semibold">
          <Zap className="w-3.5 h-3.5" />
          <span>Hybrid 3D Architecture: Blender Python + Generative AI</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight max-w-4xl mx-auto">
          Create Real 3D Assets with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">Precision & AI</span>
        </h1>

        <p className="text-base sm:text-lg text-studio-100 max-w-2xl mx-auto leading-relaxed">
          Describe your idea in natural language or upload a reference image. AI 3D Studio generates genuine, production-ready 3D models with interactive WebGL preview, clean topology, and glTF / GLB exports.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <button
            onClick={onEnterStudio}
            className="w-full sm:w-auto px-8 py-4 bg-brand-600 hover:bg-brand-500 text-white font-bold rounded-xl shadow-xl shadow-brand-500/20 flex items-center justify-center space-x-2 transition transform active:scale-95 text-base"
          >
            <span>Launch 3D Studio</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

        {/* Live Engine Badges */}
        <div className="pt-6 flex flex-wrap items-center justify-center gap-4 text-xs">
          <div className="flex items-center space-x-2 bg-studio-800 border border-studio-700 px-3.5 py-1.5 rounded-lg">
            <span className={`w-2.5 h-2.5 rounded-full ${blenderAvailable ? 'bg-emerald-400' : 'bg-red-500'}`} />
            <span className="text-studio-100">Blender Engine:</span>
            <span className="font-mono text-studio-50 font-semibold">{blenderVersion || 'Active (5.2)'}</span>
          </div>

          <div className="flex items-center space-x-2 bg-studio-800 border border-studio-700 px-3.5 py-1.5 rounded-lg">
            <span className={`w-2.5 h-2.5 rounded-full ${aiConfigured ? 'bg-purple-400' : 'bg-amber-400'}`} />
            <span className="text-studio-100">AI Provider:</span>
            <span className="font-mono text-studio-50 font-semibold uppercase">{aiProviderName}</span>
            <span className="text-[10px] text-studio-500">({aiConfigured ? 'Configured' : 'Credentials optional'})</span>
          </div>
        </div>
      </section>

      {/* Honest Comparison & Explanation */}
      <section className="py-16 px-6 max-w-6xl mx-auto border-t border-studio-700/60">
        <div className="text-center space-y-3 mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-studio-50">Two Real Generation Paths</h2>
          <p className="text-sm text-studio-500 max-w-xl mx-auto">
            We don't simulate or fake 3D generation. Depending on what you need, AI 3D Studio routes your prompt to the best genuine 3D engine:
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Procedural Path */}
          <div className="bg-studio-800/80 border border-studio-700 rounded-2xl p-6 space-y-4 hover:border-emerald-500/40 transition">
            <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center">
              <Cpu className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-studio-50">A. Procedural Modeling (Blender bpy)</h3>
            <p className="text-xs text-studio-100 leading-relaxed">
              Uses Blender's Python API in headless background workers to generate mathematically structured objects.
            </p>
            <ul className="text-xs text-studio-500 space-y-2">
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Supports tables, chairs, cabinets, houses, rooms, columns, roads, and platforms.</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Deterministic dimensions, exact units (meters), watertight geometry, and clean normals.</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Immediate execution (&lt;2 seconds) with zero API credit costs.</span>
              </li>
            </ul>
          </div>

          {/* AI Neural Path */}
          <div className="bg-studio-800/80 border border-studio-700 rounded-2xl p-6 space-y-4 hover:border-purple-500/40 transition">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-studio-50">B. AI Text/Image-to-3D (Meshy / Tripo)</h3>
            <p className="text-xs text-studio-100 leading-relaxed">
              Integrates external neural generation APIs for organic, sculpted, and free-form 3D geometry.
            </p>
            <ul className="text-xs text-studio-500 space-y-2">
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <span>Handles complex characters, sculpts, sci-fi vehicles, and novel concepts.</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <span>Accepts natural language prompts and reference image uploads.</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-purple-400 flex-shrink-0" />
                <span>Requires 60–180 seconds and configured provider API credentials.</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Trust & Transparency */}
      <section className="py-16 px-6 max-w-6xl mx-auto border-t border-studio-700/60 bg-studio-800/30 rounded-3xl my-8">
        <div className="max-w-3xl mx-auto space-y-6 text-center">
          <div className="inline-flex p-3 rounded-2xl bg-studio-800 border border-studio-700 text-brand-500">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-studio-50">Production Engineering & Ethics</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left text-xs text-studio-100">
            <div className="bg-studio-800 p-4 rounded-xl border border-studio-700 space-y-1">
              <span className="font-semibold text-studio-50">No Fake Demonstrations</span>
              <p className="text-studio-500">
                Every model loaded in the viewer is an actual exported GLB/glTF generated during the task or requested by the user.
              </p>
            </div>
            <div className="bg-studio-800 p-4 rounded-xl border border-studio-700 space-y-1">
              <span className="font-semibold text-studio-50">Strict Server-side Security</span>
              <p className="text-studio-500">
                User input is strictly parsed into validated parameters. Arbitrary Python/Blender scripts cannot be executed by client requests.
              </p>
            </div>
            <div className="bg-studio-800 p-4 rounded-xl border border-studio-700 space-y-1">
              <span className="font-semibold text-studio-50">glTF 2.0 Compliance</span>
              <p className="text-studio-500">
                Exports use official Khronos glTF 2.0 specs with binary buffers, embedded textures, and verified scene nodes.
              </p>
            </div>
            <div className="bg-studio-800 p-4 rounded-xl border border-studio-700 space-y-1">
              <span className="font-semibold text-studio-50">Cost & Quota Transparency</span>
              <p className="text-studio-500">
                Usage ledger tracks all compute operations. Missing API keys fail explicitly with actionable messages rather than silent mock substitutions.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

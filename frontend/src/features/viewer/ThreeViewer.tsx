import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import {
  RotateCw,
  Grid,
  Box,
  Layers,
  Maximize2,
  RefreshCw,
  AlertCircle,
  Compass
} from 'lucide-react';

interface ThreeViewerProps {
  modelUrl: string | null;
  statistics?: {
    vertices?: number;
    faces?: number;
    triangles?: number;
    dimensions?: { x?: number; y?: number; z?: number };
    file_size_bytes?: number;
  };
}

export const ThreeViewer: React.FC<ThreeViewerProps> = ({ modelUrl, statistics }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [loadProgress, setLoadProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Viewport controls
  const [wireframe, setWireframe] = useState<boolean>(false);
  const [showGrid, setShowGrid] = useState<boolean>(true);
  const [autoRotate, setAutoRotate] = useState<boolean>(false);

  // References to three objects
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const currentModelRef = useRef<THREE.Group | null>(null);
  const gridGroupRef = useRef<THREE.Group | null>(null);
  const initialCameraPosRef = useRef<THREE.Vector3>(new THREE.Vector3(3.0, 2.5, 4.0));

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = Math.max(container.clientWidth || 600, 200);
    const height = Math.max(container.clientHeight || 400, 200);

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0d1117');
    scene.fog = new THREE.FogExp2('#0d1117', 0.025);
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.05, 1000);
    camera.position.copy(initialCameraPosRef.current);
    camera.lookAt(0, 0.5, 0);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Remove any previous children in container
    while (container.firstChild) {
      container.removeChild(container.firstChild);
    }
    container.appendChild(renderer.domElement);

    // 4. Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.maxDistance = 60;
    controls.minDistance = 0.2;
    controls.target.set(0, 0.5, 0);
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const hemiLight = new THREE.HemisphereLight(0xffffff, 0x334155, 1.3);
    hemiLight.position.set(0, 20, 0);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
    keyLight.position.set(6, 10, 7);
    keyLight.castShadow = true;
    keyLight.shadow.mapSize.width = 1024;
    keyLight.shadow.mapSize.height = 1024;
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xa5b4fc, 1.1);
    fillLight.position.set(-6, 5, -5);
    scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.8);
    rimLight.position.set(0, 6, -8);
    scene.add(rimLight);

    // 6. Grid floor & coordinate visualizer
    const gridGroup = new THREE.Group();

    // Primary grid (high contrast)
    const primaryGrid = new THREE.GridHelper(16, 16, 0x6366f1, 0x374151);
    primaryGrid.position.y = 0;
    gridGroup.add(primaryGrid);

    // Sub-grid (fine lines)
    const subGrid = new THREE.GridHelper(16, 64, 0x4f46e5, 0x1f2633);
    subGrid.position.y = -0.001;
    gridGroup.add(subGrid);

    // Origin Axes Indicator
    const axesHelper = new THREE.AxesHelper(1.2);
    axesHelper.position.set(0, 0.002, 0);
    gridGroup.add(axesHelper);

    scene.add(gridGroup);
    gridGroupRef.current = gridGroup;

    // Animation Loop
    let animationId: number;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      if (controlsRef.current) {
        controlsRef.current.autoRotate = autoRotate;
        controlsRef.current.update();
      }
      renderer.render(scene, camera);
    };
    animate();

    // Safe Resize Handler with ResizeObserver
    const updateDimensions = () => {
      if (!container || !rendererRef.current || !cameraRef.current) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w > 20 && h > 20) {
        cameraRef.current.aspect = w / h;
        cameraRef.current.updateProjectionMatrix();
        rendererRef.current.setSize(w, h, false);
      }
    };

    const resizeObserver = new ResizeObserver(() => {
      updateDimensions();
    });
    resizeObserver.observe(container);

    // Double-check dimension after DOM paint
    const timer = setTimeout(updateDimensions, 100);

    return () => {
      clearTimeout(timer);
      resizeObserver.disconnect();
      cancelAnimationFrame(animationId);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update Grid helper visibility
  useEffect(() => {
    if (gridGroupRef.current) {
      gridGroupRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // Update Auto rotate
  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
    }
  }, [autoRotate]);

  // Update Wireframe
  useEffect(() => {
    if (!currentModelRef.current) return;
    currentModelRef.current.traverse((child) => {
      if ((child as THREE.Mesh).isMesh) {
        const mesh = child as THREE.Mesh;
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach((mat) => {
            if ('wireframe' in mat) (mat as any).wireframe = wireframe;
          });
        } else if (mesh.material && 'wireframe' in mesh.material) {
          (mesh.material as any).wireframe = wireframe;
        }
      }
    });
  }, [wireframe]);

  // Load Model whenever modelUrl changes
  useEffect(() => {
    if (!modelUrl || !sceneRef.current || !cameraRef.current || !controlsRef.current) return;

    setLoading(true);
    setLoadProgress(0);
    setErrorMessage(null);

    // Clean up previous model and dispose GPU buffers
    if (currentModelRef.current) {
      sceneRef.current.remove(currentModelRef.current);
      currentModelRef.current.traverse((child) => {
        if ((child as THREE.Mesh).isMesh) {
          const mesh = child as THREE.Mesh;
          mesh.geometry.dispose();
          if (Array.isArray(mesh.material)) {
            mesh.material.forEach((m) => m.dispose());
          } else if (mesh.material) {
            mesh.material.dispose();
          }
        }
      });
      currentModelRef.current = null;
    }

    const loader = new GLTFLoader();
    loader.load(
      modelUrl,
      (gltf) => {
        const model = gltf.scene;

        // Calculate bounding box and center model
        const box = new THREE.Box3().setFromObject(model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        // Center horizontally and rest on the ground plane (y=0)
        model.position.x = -center.x;
        model.position.z = -center.z;
        model.position.y = -box.min.y;

        // Apply wireframe and shadows
        model.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            if (wireframe) {
              if (Array.isArray(mesh.material)) {
                mesh.material.forEach((m) => {
                  if ('wireframe' in m) (m as any).wireframe = true;
                });
              } else if (mesh.material && 'wireframe' in mesh.material) {
                (mesh.material as any).wireframe = true;
              }
            }
          }
        });

        sceneRef.current?.add(model);
        currentModelRef.current = model;

        // Adjust camera to fit model comfortably in view
        const maxDim = Math.max(size.x, size.y, size.z, 0.6);
        const fov = cameraRef.current!.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.8;
        cameraZ = Math.max(cameraZ, 1.8);

        const newCamPos = new THREE.Vector3(cameraZ * 0.85, cameraZ * 0.65, cameraZ);
        cameraRef.current!.position.copy(newCamPos);
        controlsRef.current!.target.set(0, size.y / 2, 0);
        controlsRef.current!.update();

        setLoading(false);
      },
      (xhr) => {
        if (xhr.lengthComputable && xhr.total > 0) {
          setLoadProgress(Math.round((xhr.loaded / xhr.total) * 100));
        }
      },
      (error) => {
        console.error('Error loading 3D model:', error);
        setLoading(false);
        setErrorMessage('Failed to parse or render 3D model. Check network or file validity.');
      }
    );
  }, [modelUrl]);

  const handleResetCamera = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    cameraRef.current.position.copy(initialCameraPosRef.current);
    controlsRef.current.target.set(0, 0.5, 0);
    controlsRef.current.update();
  };

  return (
    <div className="relative w-full h-full min-h-0 flex flex-col bg-[#0d1117] overflow-hidden select-none">
      {/* 3D Canvas Mount */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Empty State Overlay when no model is active */}
      {!modelUrl && !loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none p-6 text-center z-10">
          <div className="bg-studio-800/80 backdrop-blur-md border border-studio-700/60 p-6 rounded-2xl max-w-sm shadow-2xl space-y-3">
            <div className="w-12 h-12 rounded-xl bg-brand-500/10 border border-brand-500/20 text-brand-400 flex items-center justify-center mx-auto shadow-inner">
              <Box className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center justify-center space-x-1.5">
                <span>3D Viewport Active</span>
              </h3>
              <p className="text-xs text-studio-400 mt-1.5 leading-relaxed">
                Describe an object and click <strong className="text-brand-400">Generate 3D Model</strong>, or load an asset from your library to view it here.
              </p>
            </div>
            <div className="pt-2 border-t border-studio-700/60 flex items-center justify-center space-x-3 text-[11px] text-studio-400 font-mono">
              <span>Orbit: LMB</span>
              <span>•</span>
              <span>Pan: RMB</span>
              <span>•</span>
              <span>Zoom: Wheel</span>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-studio-900/80 backdrop-blur-sm flex flex-col items-center justify-center z-20">
          <RefreshCw className="w-9 h-9 text-brand-500 animate-spin mb-3" />
          <p className="text-xs sm:text-sm font-medium text-studio-100">Loading 3D asset into viewport...</p>
          {loadProgress > 0 && (
            <div className="w-48 bg-studio-700 rounded-full h-2 mt-3 overflow-hidden">
              <div
                className="bg-brand-500 h-2 rounded-full transition-all duration-200"
                style={{ width: `${loadProgress}%` }}
              />
            </div>
          )}
        </div>
      )}

      {/* Error Banner */}
      {errorMessage && (
        <div className="absolute top-4 left-4 right-4 bg-red-950/90 border border-red-700/60 text-red-200 px-4 py-3 rounded-lg flex items-center space-x-3 z-30 shadow-xl">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-400" />
          <span className="text-xs sm:text-sm font-medium">{errorMessage}</span>
        </div>
      )}

      {/* Floating Viewport Toolbar */}
      <div className="absolute top-3 right-3 flex items-center bg-studio-800/90 border border-studio-700/70 rounded-lg p-1 backdrop-blur-md shadow-xl space-x-1 z-20">
        <button
          onClick={() => setShowGrid(!showGrid)}
          title={showGrid ? 'Hide Grid Floor' : 'Show Grid Floor'}
          className={`p-1.5 rounded-md transition-colors ${
            showGrid ? 'bg-studio-700 text-brand-400' : 'text-studio-300 hover:bg-studio-700/50'
          }`}
        >
          <Grid className="w-4 h-4" />
        </button>

        <button
          onClick={() => setWireframe(!wireframe)}
          title={wireframe ? 'Solid Surface Mode' : 'Wireframe Mode'}
          className={`p-1.5 rounded-md transition-colors ${
            wireframe ? 'bg-studio-700 text-brand-400' : 'text-studio-300 hover:bg-studio-700/50'
          }`}
        >
          <Box className="w-4 h-4" />
        </button>

        <button
          onClick={() => setAutoRotate(!autoRotate)}
          title={autoRotate ? 'Pause Turntable' : 'Start Turntable Rotation'}
          className={`p-1.5 rounded-md transition-colors ${
            autoRotate ? 'bg-studio-700 text-brand-400' : 'text-studio-300 hover:bg-studio-700/50'
          }`}
        >
          <RotateCw className="w-4 h-4" />
        </button>

        <div className="w-[1px] h-4 bg-studio-700 my-auto mx-0.5" />

        <button
          onClick={handleResetCamera}
          title="Reset Camera View"
          className="p-1.5 rounded-md text-studio-300 hover:bg-studio-700/50 transition-colors"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Model Statistics Overlay (when available) */}
      {statistics && (
        <div className="absolute bottom-3 left-3 bg-studio-800/90 border border-studio-700/70 rounded-lg p-2.5 backdrop-blur-md text-[11px] text-studio-200 shadow-xl space-y-1 z-20">
          <div className="font-semibold text-white flex items-center space-x-1.5 pb-1 border-b border-studio-700">
            <Layers className="w-3 h-3 text-brand-400" />
            <span>Asset Metrics</span>
          </div>
          {statistics.triangles !== undefined && (
            <div className="flex justify-between space-x-3">
              <span className="text-studio-400">Triangles:</span>
              <span className="font-mono text-white font-medium">
                {statistics.triangles.toLocaleString()}
              </span>
            </div>
          )}
          {statistics.vertices !== undefined && (
            <div className="flex justify-between space-x-3">
              <span className="text-studio-400">Vertices:</span>
              <span className="font-mono text-white font-medium">
                {statistics.vertices.toLocaleString()}
              </span>
            </div>
          )}
          {statistics.dimensions && (
            <div className="flex justify-between space-x-3">
              <span className="text-studio-400">Dimensions:</span>
              <span className="font-mono text-white font-medium">
                {statistics.dimensions.x ?? 0}m × {statistics.dimensions.y ?? 0}m × {statistics.dimensions.z ?? 0}m
              </span>
            </div>
          )}
          {statistics.file_size_bytes !== undefined && (
            <div className="flex justify-between space-x-3">
              <span className="text-studio-400">File Size:</span>
              <span className="font-mono text-white font-medium">
                {(statistics.file_size_bytes / 1024).toFixed(1)} KB
              </span>
            </div>
          )}
        </div>
      )}

      {/* Orbit Navigation Help Indicator */}
      <div className="absolute bottom-3 right-3 bg-studio-800/70 text-[10px] text-studio-400 px-2.5 py-1 rounded-md backdrop-blur border border-studio-700/40 pointer-events-none flex items-center space-x-1.5">
        <Compass className="w-3 h-3 text-brand-400" />
        <span>LMB: Orbit • RMB: Pan • Scroll: Zoom</span>
      </div>
    </div>
  );
};
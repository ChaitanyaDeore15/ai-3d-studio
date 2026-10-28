import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { RotateCw, Grid, Box, Layers, Maximize2, RefreshCw, AlertCircle } from 'lucide-react';

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
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);
  const initialCameraPosRef = useRef<THREE.Vector3>(new THREE.Vector3(2.5, 2.0, 3.5));

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // 1. Scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0d1117');
    sceneRef.current = scene;

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.05,
      1000
    );
    camera.position.copy(initialCameraPosRef.current);
    cameraRef.current = camera;

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;
    container.appendChild(renderer.domElement);

    // 4. Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxDistance = 50;
    controls.minDistance = 0.2;
    controlsRef.current = controls;

    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    scene.add(ambientLight);

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 2.0);
    dirLight1.position.set(5, 10, 7);
    dirLight1.castShadow = true;
    scene.add(dirLight1);

    const fillLight = new THREE.DirectionalLight(0x90b0e0, 1.0);
    fillLight.position.set(-5, 4, -5);
    scene.add(fillLight);

    // 6. Grid floor
    const grid = new THREE.GridHelper(10, 20, 0x3b82f6, 0x21262d);
    grid.position.y = 0;
    scene.add(grid);
    gridHelperRef.current = grid;

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

    // Resize handler
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      if (renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update Grid helper visibility
  useEffect(() => {
    if (gridHelperRef.current) {
      gridHelperRef.current.visible = showGrid;
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

        // Apply wireframe if active
        model.traverse((child) => {
          if ((child as THREE.Mesh).isMesh) {
            const mesh = child as THREE.Mesh;
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            if (wireframe) {
              if (Array.isArray(mesh.material)) {
                mesh.material.forEach((m) => { if ('wireframe' in m) (m as any).wireframe = true; });
              } else if (mesh.material && 'wireframe' in mesh.material) {
                (mesh.material as any).wireframe = true;
              }
            }
          }
        });

        sceneRef.current?.add(model);
        currentModelRef.current = model;

        // Adjust camera to fit model comfortably in view
        const maxDim = Math.max(size.x, size.y, size.z, 0.5);
        const fov = cameraRef.current!.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.8;
        cameraZ = Math.max(cameraZ, 1.5);

        const newCamPos = new THREE.Vector3(cameraZ * 0.8, cameraZ * 0.6, cameraZ);
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
    <div className="relative w-full h-full flex flex-col bg-studio-900 overflow-hidden select-none">
      {/* 3D Canvas Mount */}
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 bg-studio-900/80 backdrop-blur-sm flex flex-col items-center justify-center z-20">
          <RefreshCw className="w-10 h-10 text-brand-500 animate-spin mb-3" />
          <p className="text-sm font-medium text-studio-100">Loading 3D asset into viewport...</p>
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
      <div className="absolute top-4 right-4 flex items-center bg-studio-800/90 border border-studio-700/70 rounded-lg p-1.5 backdrop-blur-md shadow-xl space-x-1 z-10">
        <button
          onClick={() => setShowGrid(!showGrid)}
          title={showGrid ? "Hide Grid Floor" : "Show Grid Floor"}
          className={`p-2 rounded-md transition-colors ${
            showGrid ? "bg-studio-700 text-brand-500" : "text-studio-100 hover:bg-studio-700/50"
          }`}
        >
          <Grid className="w-4 h-4" />
        </button>

        <button
          onClick={() => setWireframe(!wireframe)}
          title={wireframe ? "Solid Surface Mode" : "Wireframe Mode"}
          className={`p-2 rounded-md transition-colors ${
            wireframe ? "bg-studio-700 text-brand-500" : "text-studio-100 hover:bg-studio-700/50"
          }`}
        >
          <Box className="w-4 h-4" />
        </button>

        <button
          onClick={() => setAutoRotate(!autoRotate)}
          title={autoRotate ? "Pause Turntable" : "Start Turntable Rotation"}
          className={`p-2 rounded-md transition-colors ${
            autoRotate ? "bg-studio-700 text-brand-500" : "text-studio-100 hover:bg-studio-700/50"
          }`}
        >
          <RotateCw className="w-4 h-4" />
        </button>

        <div className="w-[1px] h-4 bg-studio-700 my-auto mx-1" />

        <button
          onClick={handleResetCamera}
          title="Reset Camera View"
          className="p-2 rounded-md text-studio-100 hover:bg-studio-700/50 transition-colors"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Model Statistics Overlay (when available) */}
      {statistics && (
        <div className="absolute bottom-4 left-4 bg-studio-800/85 border border-studio-700/60 rounded-lg p-3 backdrop-blur-md text-xs text-studio-100 shadow-xl space-y-1.5 z-10">
          <div className="font-semibold text-studio-50 flex items-center space-x-1.5 pb-1 border-b border-studio-700">
            <Layers className="w-3.5 h-3.5 text-brand-500" />
            <span>Asset Metrics</span>
          </div>
          {statistics.triangles !== undefined && (
            <div className="flex justify-between space-x-4">
              <span className="text-studio-500">Triangles:</span>
              <span className="font-mono text-studio-50 font-medium">{statistics.triangles.toLocaleString()}</span>
            </div>
          )}
          {statistics.vertices !== undefined && (
            <div className="flex justify-between space-x-4">
              <span className="text-studio-500">Vertices:</span>
              <span className="font-mono text-studio-50 font-medium">{statistics.vertices.toLocaleString()}</span>
            </div>
          )}
          {statistics.dimensions && (
            <div className="flex justify-between space-x-4">
              <span className="text-studio-500">Dimensions:</span>
              <span className="font-mono text-studio-50 font-medium">
                {statistics.dimensions.x ?? 0}m × {statistics.dimensions.y ?? 0}m × {statistics.dimensions.z ?? 0}m
              </span>
            </div>
          )}
          {statistics.file_size_bytes !== undefined && (
            <div className="flex justify-between space-x-4">
              <span className="text-studio-500">File Size:</span>
              <span className="font-mono text-studio-50 font-medium">
                {(statistics.file_size_bytes / 1024).toFixed(1)} KB
              </span>
            </div>
          )}
        </div>
      )}

      {/* Orbit Navigation Help Indicator */}
      <div className="absolute bottom-4 right-4 bg-studio-800/60 text-[11px] text-studio-500 px-2.5 py-1 rounded backdrop-blur pointer-events-none">
        Left-click: Orbit • Right-click: Pan • Scroll: Zoom
      </div>
    </div>
  );
};

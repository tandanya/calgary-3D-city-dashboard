import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import * as THREE from 'three';

// Convert lat/lon to local coordinates
function latLonToLocal(lat, lon, centerLat, centerLon, scale) {
  const x = (centerLon - lon) * scale;
  const z = (lat - centerLat) * scale;
  return [x, z];
}

// Calculate building size based on land area
function calculateBuildingSize(building, defaultSize = 0.3) {
  // Use land_size_sf (square feet) to determine footprint
  const landSizeSf = building.land_size_sf || 0;
  
  if (landSizeSf > 0) {
    // Convert square feet to our scale
    // Assuming 1 unit = ~100 feet, so 10000 sf = 1 unit²
    const sizeInUnits = Math.sqrt(landSizeSf) / 500;
    // Clamp between min and max sizes
    return Math.max(0.15, Math.min(1.5, sizeInUnits));
  }
  
  // Fallback based on assessed value
  const value = building.assessed_value || 0;
  if (value > 10000000) return 0.6;
  if (value > 1000000) return 0.45;
  if (value > 100000) return 0.35;
  return defaultSize;
}

// Individual Building Component - FIXED
function Building({ building, isHighlighted, onClick, centerLat, centerLon, scale }) {
  const meshRef = useRef();
  const [hovered, setHovered] = useState(false);
  
  // Calculate position once
  const position = useMemo(() => {
    const [x, z] = latLonToLocal(
      building.latitude, 
      building.longitude, 
      centerLat, 
      centerLon, 
      scale
    );
    return { x, z };
  }, [building.latitude, building.longitude, centerLat, centerLon, scale]);
  
  // Calculate dimensions once
  const dimensions = useMemo(() => {
    const size = calculateBuildingSize(building);
    const height = Math.max(0.2, (building.height || 30) * 0.015);
    
    // Add slight variation to prevent z-fighting on identical buildings
    const variation = (parseInt(building.id.replace(/\D/g, '')) || 0) % 100 / 10000;
    
    return {
      width: size + variation,
      depth: size * (0.8 + Math.random() * 0.4), // Slight variation in aspect ratio
      height: height,
      baseY: height / 2
    };
  }, [building]);
  
  // Building color based on type and state
  const color = useMemo(() => {
    if (isHighlighted) return '#ffcc00';
    if (hovered) return '#88ccff';
    
    switch (building.building_type) {
      case 'Commercial': return '#4a90d9';
      case 'Residential': return '#5cb85c';
      case 'Industrial': return '#d9534f';
      case 'Mixed Use': return '#9b59b6';
      case 'Special Purpose': return 'rgb(243, 156, 18)';
      default: return '#95a5a6';
    }
  }, [isHighlighted, hovered, building.building_type]);
  
  // Animation ONLY for highlighted buildings - FIXED
  useFrame((state) => {
    if (!meshRef.current) return;
    
    if (isHighlighted) {
      // Gentle floating animation for highlighted buildings
      const floatOffset = Math.sin(state.clock.elapsedTime * 2) * 0.05;
      meshRef.current.position.y = dimensions.baseY + floatOffset;
    }
    // NO else branch - don't touch non-highlighted buildings
  });
  
  return (
    <mesh
      ref={meshRef}
      position={[position.x, dimensions.baseY, position.z]}
      onClick={(e) => {
        e.stopPropagation();
        onClick(building);
      }}
      onPointerOver={(e) => {
        e.stopPropagation();
        setHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = 'auto';
      }}
      castShadow
      receiveShadow
    >
      <boxGeometry args={[dimensions.width, dimensions.height, dimensions.depth]} />
      <meshStandardMaterial 
        color={color}
        emissive={isHighlighted ? '#ffcc00' : (hovered ? '#88ccff' : '#000000')}
        emissiveIntensity={isHighlighted ? 0.4 : (hovered ? 0.15 : 0)}
        metalness={0.1}
        roughness={0.7}
      />
    </mesh>
  );
}

// Ground plane
function Ground({ size = 30 }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
      <planeGeometry args={[size, size]} />
      <meshStandardMaterial color="#1a1a2e" />
    </mesh>
  );
}

// Scene lights
function Lights() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight
        position={[10, 20, 10]}
        intensity={1}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-far={50}
        shadow-camera-left={-20}
        shadow-camera-right={20}
        shadow-camera-top={20}
        shadow-camera-bottom={-20}
      />
      <pointLight position={[-10, 10, -10]} intensity={0.3} color="#6a9fd9" />
      <hemisphereLight args={['#87CEEB', '#1a1a2e', 0.3]} />
    </>
  );
}

// Legend component
function Legend() {
  const types = [
    { label: 'Commercial', color: '#4a90d9' },
    { label: 'Residential', color: '#5cb85c' },
    { label: 'Industrial', color: '#d9534f' },
    { label: 'Mixed Use', color: '#9b59b6' },
    { label: 'Special Purpose', color: '#f39c12' },
    { label: 'Highlighted', color: '#ffcc00' },
  ];
  
  return (
    <div className="legend">
      <h4>Building Types</h4>
      {types.map(({ label, color }) => (
        <div key={label} className="legend-item">
          <span className="legend-color" style={{ backgroundColor: color }}></span>
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}

// Stats overlay
function SceneStats({ buildings, highlightedCount }) {
  return (
    <div className="scene-stats">
      <span>{buildings.length} buildings</span>
      {highlightedCount > 0 && (
        <span className="highlighted-count">{highlightedCount} highlighted</span>
      )}
    </div>
  );
}

function CityScene({ buildings, highlightedIds, onBuildingClick }) {
  // Calculate scene parameters based on building data
  const sceneParams = useMemo(() => {
    if (buildings.length === 0) {
      return { 
        centerLat: 51.046, 
        centerLon: -114.063, 
        scale: 5000, 
        gridSize: 20 
      };
    }
    
    // Find bounds of all buildings
    let minLat = Infinity, maxLat = -Infinity;
    let minLon = Infinity, maxLon = -Infinity;
    
    buildings.forEach(b => {
      if (b.latitude && b.longitude) {
        minLat = Math.min(minLat, b.latitude);
        maxLat = Math.max(maxLat, b.latitude);
        minLon = Math.min(minLon, b.longitude);
        maxLon = Math.max(maxLon, b.longitude);
      }
    });
    
    const centerLat = (minLat + maxLat) / 2;
    const centerLon = (minLon + maxLon) / 2;
    
    // Calculate scale to fit buildings in view
    const latRange = maxLat - minLat;
    const lonRange = maxLon - minLon;
    const maxRange = Math.max(latRange, lonRange);
    
    // Target size for the scene (in 3D units)
    const targetSize = 70;
    const scale = maxRange > 0 ? targetSize / maxRange : 5000;
    
    // Grid should encompass all buildings with some padding
    const gridSize = targetSize + 10;
    
    console.log('Scene parameters:', { 
      centerLat: centerLat.toFixed(6), 
      centerLon: centerLon.toFixed(6), 
      scale: scale.toFixed(2),
      latRange: latRange.toFixed(6),
      lonRange: lonRange.toFixed(6)
    });
    
    return { centerLat, centerLon, scale, gridSize };
  }, [buildings]);
  
  return (
    <>
      <Canvas 
        shadows 
        camera={{ position: [15, 15, 15], fov: 50 }}
        onCreated={({ gl }) => {
          gl.shadowMap.enabled = true;
          gl.shadowMap.type = THREE.PCFSoftShadowMap;
        }}
      >
        <color attach="background" args={['#0a0a15']} />
        
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          minDistance={5}
          maxDistance={60}
          maxPolarAngle={Math.PI / 2.1}
          target={[0, 0, 0]}
        />
        
        <Lights />
        <Ground size={sceneParams.gridSize} />
        
        <Grid
          args={[sceneParams.gridSize, sceneParams.gridSize]}
          cellSize={1}
          cellThickness={0.5}
          cellColor="#2a2a4c"
          sectionSize={5}
          sectionThickness={1}
          sectionColor="#4a4a7c"
          fadeDistance={50}
          position={[0, 0.001, 0]}
        />
        
        {/* Render buildings */}
        {buildings.map((building) => (
          <Building
            key={building.id}
            building={building}
            isHighlighted={highlightedIds.includes(building.id)}
            onClick={onBuildingClick}
            centerLat={sceneParams.centerLat}
            centerLon={sceneParams.centerLon}
            scale={sceneParams.scale}
          />
        ))}
      </Canvas>
      
      <Legend />
      <SceneStats buildings={buildings} highlightedCount={highlightedIds.length} />
    </>
  );
}

export default CityScene;
# Mobile App Migration Plan: Flutter → Lightweight Cross-Platform

## Executive Summary

This document outlines a comprehensive plan to migrate the Luuniensuki LMS mobile app from Flutter to a lighter cross-platform solution while maintaining full iOS and Android compatibility.

### Current State
- **Framework**: Flutter SDK ^3.5.4
- **State Management**: Riverpod + Freezed
- **APK Size**: ~25-40 MB (estimated without 3D models)
- **3D Viewer**: `model_viewer_plus` (WebView-based)
- **Features**: 21 feature modules, 25+ screens
- **LOC**: ~30,000-40,000 lines

---

## Recommended Migration Paths

### Option 1: React Native (RECOMMENDED)
**Best Balance of Performance, Size, and 3D Support**

| Metric | Current (Flutter) | React Native |
|--------|-------------------|--------------|
| APK Size (base) | ~8 MB | ~5-7 MB |
| APK Size (production) | ~25-35 MB | ~15-25 MB |
| 3D Performance | WebView | Native-like via react-three-fiber |
| Code Sharing | 100% | 95%+ |

#### Pros
- ✅ 30-40% smaller APK size
- ✅ Excellent 3D support via `react-three-fiber` + `@react-three/drei`
- ✅ New Architecture (v0.76+) closes performance gap with Flutter
- ✅ Massive ecosystem (400k+ packages)
- ✅ TypeScript support for type safety
- ✅ Full FCM support via `@react-native-firebase`

#### Cons
- ⚠️ Different state management paradigm (Redux/Zustand/Jotai)
- ⚠️ Learning curve for Dart developers
- ⚠️ Native module configuration can be complex

---

### Option 2: Capacitor/Ionic
**Smallest Size, Web-First Approach**

| Metric | Current (Flutter) | Capacitor |
|--------|-------------------|-----------|
| APK Size (base) | ~8 MB | ~3-4 MB |
| APK Size (production) | ~25-35 MB | ~8-15 MB |
| 3D Performance | WebView | WebView (same) |
| Code Sharing | 100% | 100% |

#### Pros
- ✅ 50%+ smaller APK size
- ✅ Same `<model-viewer>` component already used
- ✅ Fastest migration (reuse web code patterns)
- ✅ Single codebase for web + mobile

#### Cons
- ⚠️ WebView performance limits on complex UIs
- ⚠️ Some WebGL context issues on newer iOS devices
- ⚠️ Less "native feel" on mobile

---

### Option 3: PWA (Progressive Web App)
**Zero Install, Instant Updates**

| Metric | Current (Flutter) | PWA |
|--------|-------------------|-----|
| APK Size | ~25-35 MB | 0 MB (web only) |
| Install Required | Yes | No (home screen) |
| 3D Performance | WebView | Native WebGL |

#### Pros
- ✅ No app store submission/review
- ✅ Instant updates
- ✅ Zero install friction
- ✅ Excellent 3D via `<model-viewer>`

#### Cons
- ❌ iOS push notifications severely limited
- ❌ Less "app-like" experience
- ❌ No Keychain/secure storage access
- ❌ Safari restrictions on iOS

---

### Option 4: React Native + Expo + Rust (Hybrid)
**Maximum Performance with Shared Native Logic**

| Metric | Current (Flutter) | RN + Rust |
|--------|-------------------|-----------|
| APK Size (base) | ~8 MB | ~8-12 MB |
| APK Size (production) | ~25-35 MB | ~18-28 MB |
| 3D Performance | WebView | Native-like + Rust processing |
| Performance-critical code | Dart | Rust (near-native) |

#### Integration Options
1. **uniffi-bindgen-react-native** - Mozilla's binding generator (recommended)
2. **Craby** - Type-safe Rust framework for React Native
3. **JSI Bridging** - Direct C++ to JavaScript via Rust FFI

#### Pros
- ✅ Near-native performance for computation-heavy tasks
- ✅ Memory safety guarantees (no crashes from memory bugs)
- ✅ Share Rust code with backend if backend uses Rust
- ✅ Cross-platform: iOS, Android, Web (via WASM), Desktop
- ✅ Future-proof for performance-critical features

#### Cons
- ⚠️ Significant build complexity (multiple toolchains)
- ⚠️ Steep learning curve (ownership, borrowing)
- ⚠️ Harder to hire Rust mobile developers
- ⚠️ Cross-language debugging is challenging
- ⚠️ 3D rendering still needs Three.js/expo-gl (Rust doesn't render directly)

#### Best Use Cases for Rust in This App
| Use Case | Benefit |
|----------|---------|
| 3D model file parsing | Faster GLB/glTF loading |
| Offline data compression | Smaller cache storage |
| Cryptographic operations | Security-critical auth |
| Complex search algorithms | Instant local search |
| Text processing | Markdown/Vietnamese text |

#### ⚠️ NOT Recommended for This App (Initial Migration)
For a cultural heritage learning app, Rust adds complexity without proportional benefits:
- 3D **rendering** still requires expo-gl/Three.js (Rust can't render directly to RN views)
- App is primarily content-focused, not computation-heavy
- Team investment in Rust may not justify returns

**Recommendation**: Start with pure React Native/Expo, add Rust modules later if specific bottlenecks emerge.

---

## Recommended Approach: React Native with Expo

### Why This Combination?
1. **Expo simplifies** native configuration and builds
2. **Development builds** allow full native module access
3. **EAS Build** eliminates local iOS/Android toolchain setup
4. **Smaller learning curve** than bare React Native

---

## Migration Phases

### Phase 1: Foundation (2-3 weeks)
**Goal**: Set up project structure and core infrastructure

#### Tasks
- [ ] Create new Expo project with TypeScript
- [ ] Configure ESLint, Prettier, and path aliases
- [ ] Set up navigation with React Navigation or Expo Router
- [ ] Implement theming system (matching current Flutter theme)
- [ ] Set up state management (Zustand recommended for simplicity)
- [ ] Configure Dio-equivalent HTTP client (Axios + interceptors)

#### Deliverables
- New project scaffold
- Navigation working with placeholder screens
- Theme system with light/dark mode
- API client with auth interceptor

---

### Phase 2: Authentication & Storage (1-2 weeks)
**Goal**: Implement auth flow and local storage

#### Tasks
- [ ] Implement secure storage with `expo-secure-store`
- [ ] Create auth context/store with token management
- [ ] Build login/register screens
- [ ] Implement session refresh logic
- [ ] Set up Hive-equivalent local storage (MMKV or AsyncStorage)

#### Deliverables
- Working auth flow
- Token persistence
- Auto-refresh mechanism

---

### Phase 3: 3D Viewer (2-3 weeks) ⚠️ CRITICAL PATH
**Goal**: Replicate 3D urn viewer with hotspots

#### Tasks
- [ ] Set up `expo-gl` and `expo-three`
- [ ] Integrate `react-three-fiber` with `@react-three/drei`
- [ ] Implement GLB model loading with `useGLTF`
- [ ] Create hotspot system using mesh raycasting
- [ ] Add model quality switching based on device RAM
- [ ] Implement loading states and error handling
- [ ] Port JavaScript bridge logic to native React

#### Deliverables
- 3D viewer with all 9 urns
- Interactive hotspots
- Quality variant selection
- Fallback handling

---

### Phase 4: Core Features (3-4 weeks)
**Goal**: Migrate main learning features

#### Tasks
- [ ] Explore screen with urn grid
- [ ] Motif detail/lesson screens
- [ ] Quiz system with auto-save
- [ ] Collection gallery
- [ ] Learning path progression
- [ ] Practice/review sessions

#### Deliverables
- Complete learning flow
- Quiz functionality
- Progress tracking

---

### Phase 5: Gamification (2 weeks)
**Goal**: Port gamification systems

#### Tasks
- [ ] Streak system with freeze support
- [ ] Daily goals and XP tracking
- [ ] Hearts/lives system
- [ ] Gems economy
- [ ] Badges/achievements
- [ ] Leaderboard

#### Deliverables
- Full gamification features
- Visual reward animations

---

### Phase 6: Social & Notifications (1-2 weeks)
**Goal**: Implement social features and push notifications

#### Tasks
- [ ] Configure Firebase for React Native
- [ ] Implement push notification handling
- [ ] Friends system
- [ ] AI chat integration
- [ ] Notification preferences

#### Deliverables
- Working push notifications
- Social features
- AI tutor integration

---

### Phase 7: Polish & Testing (2 weeks)
**Goal**: QA, performance optimization, and launch prep

#### Tasks
- [ ] Performance profiling and optimization
- [ ] Accessibility audit
- [ ] Device testing matrix
- [ ] App store asset preparation
- [ ] Beta testing
- [ ] Production deployment

#### Deliverables
- Production-ready apps
- App store submissions

---

## Technology Mapping

### Flutter → React Native Equivalents

| Flutter | React Native Equivalent |
|---------|------------------------|
| `flutter_riverpod` | Zustand or Jotai |
| `go_router` | Expo Router or React Navigation |
| `dio` | Axios + interceptors |
| `hive_flutter` | MMKV |
| `flutter_secure_storage` | expo-secure-store |
| `model_viewer_plus` | react-three-fiber + @react-three/drei |
| `cached_network_image` | expo-image or react-native-fast-image |
| `firebase_messaging` | @react-native-firebase/messaging |
| `flutter_local_notifications` | expo-notifications |
| `freezed` | TypeScript interfaces + Zod |
| `just_audio` | expo-av |
| `video_player` | expo-video |

---

## 3D Viewer Migration Detail

### Current Flutter Implementation
```dart
// WebView-based using model_viewer_plus
ModelViewer(
  src: 'https://lms.histolab.icu/assets/models/CAO-DINH-v1.glb',
  alt: 'Cao Đỉnh',
  ar: false,
  cameraControls: true,
)
```

### React Native Implementation
```tsx
import { Canvas } from '@react-three/fiber/native'
import { useGLTF, OrbitControls } from '@react-three/drei/native'

function UrnModel({ url, onHotspotClick }) {
  const { scene } = useGLTF(url)

  return (
    <Canvas>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} />
      <primitive
        object={scene}
        onClick={(e) => onHotspotClick(e.point)}
      />
      <OrbitControls enablePan={false} />
    </Canvas>
  )
}
```

### Hotspot System
```tsx
function Hotspot({ position, label, onClick }) {
  return (
    <mesh position={position} onClick={onClick}>
      <sphereGeometry args={[0.05, 16, 16]} />
      <meshBasicMaterial color="gold" />
    </mesh>
  )
}
```

---

## Estimated Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Foundation | 2-3 weeks | 3 weeks |
| Phase 2: Auth & Storage | 1-2 weeks | 5 weeks |
| Phase 3: 3D Viewer | 2-3 weeks | 8 weeks |
| Phase 4: Core Features | 3-4 weeks | 12 weeks |
| Phase 5: Gamification | 2 weeks | 14 weeks |
| Phase 6: Social & Notifications | 1-2 weeks | 16 weeks |
| Phase 7: Polish & Testing | 2 weeks | 18 weeks |

**Total Estimated Duration: 16-18 weeks (4-4.5 months)**

---

## Resource Requirements

### Team
- 1-2 React Native developers
- 1 QA engineer (part-time)
- Design support for platform-specific adjustments

### Infrastructure
- Expo EAS Build subscription ($99/month for team)
- Firebase project (same as current)
- CI/CD pipeline updates

---

## Risk Mitigation

### High-Risk: 3D Viewer Performance
**Mitigation**:
- Start Phase 3 early as proof-of-concept
- Test on mid-range devices immediately
- Have Capacitor as fallback (same WebView approach)

### Medium-Risk: State Management Migration
**Mitigation**:
- Document all Riverpod providers first
- Map to Zustand stores 1:1
- Maintain same data flow patterns

### Low-Risk: Push Notification Differences
**Mitigation**:
- Use `@react-native-firebase` (well-documented)
- Test on real devices early

---

## Decision Checkpoint

Before committing to full migration, complete a **2-week spike** to validate:

1. [ ] 3D GLB loading with react-three-fiber works on target devices
2. [ ] Hotspot interaction is responsive
3. [ ] App size meets targets (<20 MB base)
4. [ ] Auth flow with secure storage works

If spike fails, evaluate **Capacitor** as alternative (keeps same WebView 3D approach).

---

## Appendix: Quick Reference

### New Project Setup
```bash
# Create Expo project
npx create-expo-app@latest luuniensuki-mobile --template expo-template-blank-typescript

# Install core dependencies
npx expo install expo-secure-store expo-notifications expo-gl expo-three
npm install zustand axios @react-three/fiber @react-three/drei
npm install @react-native-firebase/app @react-native-firebase/messaging
```

### Folder Structure (Recommended)
```
src/
├── app/                    # Expo Router screens
├── components/             # Shared components
├── features/               # Feature modules (match Flutter structure)
│   ├── auth/
│   ├── urn-viewer/
│   ├── quiz/
│   └── ...
├── hooks/                  # Custom hooks
├── services/               # API, storage, notifications
├── stores/                 # Zustand stores
├── theme/                  # Colors, typography, spacing
└── utils/                  # Helpers
```

---

## Summary: Recommended Decision

| Criteria | Winner |
|----------|--------|
| **Smallest APK** | Capacitor/Ionic (~8-15 MB) |
| **Best 3D Performance** | React Native (react-three-fiber) |
| **Fastest Migration** | Capacitor (same WebView approach) |
| **Best Long-term Support** | React Native (largest community) |
| **Maximum Native Performance** | React Native + Rust (hybrid) |
| **Overall Recommendation** | **React Native with Expo** |

### Final Recommendation

**Migrate to React Native with Expo** for the best balance of:
- ✅ 30-40% smaller app size
- ✅ Better 3D performance potential
- ✅ Larger ecosystem and community
- ✅ Future-proof technology choice

**Rust Integration**: NOT recommended initially. Add Rust modules later only if specific performance bottlenecks emerge (3D loading, compression, crypto). The complexity overhead doesn't justify initial investment for a content-focused app.

**Alternative**: If 3D performance proves problematic in the spike, fallback to **Capacitor** which uses the same `<model-viewer>` WebView approach currently in use.

---

*Document created: January 2025*
*Last updated: January 2025*

---

## Appendix B: Rust + React Native Deep Dive

### When to Add Rust (Post-Migration)

After initial React Native migration is stable, consider Rust for:

| Trigger | Rust Solution |
|---------|---------------|
| 3D model loading is slow | Rust GLB parser via uniffi |
| Offline storage is large | Rust compression (zstd/lz4) |
| Auth tokens need encryption | Rust crypto (ring/rustls) |
| Search is sluggish | Rust search algorithms |
| Backend shares Rust code | Reuse Rust business logic |

### Integration Architecture

```
React Native App (TypeScript)
         ↓
   Expo Native Module
         ↓
   TurboModule Bridge (C++)
         ↓
     Rust Library (via uniffi)
         ↓
   Platform (iOS/Android)
```

### Setup Requirements

```bash
# Install Rust targets for mobile
rustup target add aarch64-apple-ios x86_64-apple-ios aarch64-apple-ios-sim
rustup target add aarch64-linux-android armv7-linux-androideabi i686-linux-android x86_64-linux-android

# Install cargo-ndk for Android
cargo install cargo-ndk

# Install uniffi-bindgen-react-native
cargo install uniffi-bindgen-react-native
```

### Example: Rust Module for Model Processing

**rust/model_processor/src/lib.rs:**
```rust
use uniffi;

#[uniffi::export]
pub fn process_glb_model(data: Vec<u8>) -> Result<ProcessedModel, ModelError> {
    // Fast native GLB parsing
    let model = parse_glb(&data)?;
    let optimized = optimize_for_mobile(model)?;
    Ok(optimized)
}

#[derive(uniffi::Record)]
pub struct ProcessedModel {
    pub vertices: Vec<f32>,
    pub indices: Vec<u32>,
    pub hotspots: Vec<Hotspot>,
}

#[derive(uniffi::Record)]
pub struct Hotspot {
    pub name: String,
    pub position: [f32; 3],
}

#[derive(uniffi::Error, Debug)]
pub enum ModelError {
    ParseError { message: String },
    OptimizationError { message: String },
}
```

**TypeScript usage (auto-generated bindings):**
```typescript
import { processGlbModel } from 'rust-model-processor';

const modelData = await fetch(modelUrl).then(r => r.arrayBuffer());
const processed = await processGlbModel(new Uint8Array(modelData));

// Use processed.vertices, processed.hotspots in Three.js
```

### Rust vs Kotlin Multiplatform Comparison

| Aspect | Rust | Kotlin Multiplatform |
|--------|------|---------------------|
| Performance | Near-native, no GC | JVM-based, GC pauses |
| Memory safety | Compile-time | Runtime |
| Learning curve | Steep | Gentle for Android devs |
| Tooling | Manual setup | IDE integration |
| Mobile maturity | Emerging | Production-ready |
| Best for | Perf/security critical | Business logic sharing |

### Production Examples Using Rust + Mobile

| Company | Use Case |
|---------|----------|
| **1Password** | Cryptography, security |
| **Matrix SDK** | End-to-end encryption |
| **Bitkey (Block)** | Crypto wallet |
| **Lipa** | Payment processing |

### Recommendation Summary

```
┌─────────────────────────────────────────────────┐
│           MIGRATION DECISION TREE               │
├─────────────────────────────────────────────────┤
│                                                 │
│  Q: Is the app computation-heavy?               │
│     NO → Pure React Native + Expo               │
│     YES ↓                                       │
│                                                 │
│  Q: Is backend already using Rust?              │
│     YES → Consider Rust from start              │
│     NO ↓                                        │
│                                                 │
│  Q: Team has Rust experience?                   │
│     YES → Consider Rust for bottlenecks         │
│     NO → Start pure RN, add Rust later          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**For Luuniensuki LMS (Cultural Heritage Learning App):**
- ✅ Start with **React Native + Expo** (simpler, faster migration)
- ⏳ Add Rust **later** if 3D loading or offline storage becomes slow
- ❌ Don't add Rust complexity initially for a content-focused app


import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// --------------------------------------------------
// 1. Scene setup
// --------------------------------------------------

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdce9e8);

const camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    100
);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;

document.querySelector('#app').appendChild(renderer.domElement);

// --------------------------------------------------
// 2. Lighting
// --------------------------------------------------

const ambientLight = new THREE.HemisphereLight(
    0xffffff,
    0x84949a,
    2
);
scene.add(ambientLight);

const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.position.set(5, 10, 7);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
scene.add(sun);

// --------------------------------------------------
// 3. Floor
// --------------------------------------------------

const floorGeometry = new THREE.PlaneGeometry(30, 30);

const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0xb8c9bd,
    roughness: 1
});

const floor = new THREE.Mesh(floorGeometry, floorMaterial);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);

const grid = new THREE.GridHelper(30, 30, 0x809b91, 0x9eafa5);
grid.position.y = 0.01;
scene.add(grid);

// --------------------------------------------------
// 4. Character and animation variables
// --------------------------------------------------

const loader = new GLTFLoader();

let mixer = null;
let clock = new THREE.Clock();
let pebble = null;

const status = document.querySelector('#status');

loader.load(
    '/models/pebble.glb',

    (gltf) => {
        pebble = gltf.scene;

        // Add Pebble to the scene.
        scene.add(pebble);

        // Enable shadows on the character.
        pebble.traverse((object) => {
            if (object.isMesh) {
                object.castShadow = true;
                object.receiveShadow = true;
            }
        });

        // Position the character on the floor.
        const box = new THREE.Box3().setFromObject(pebble);
        const size = box.getSize(new THREE.Vector3());
        const centre = box.getCenter(new THREE.Vector3());

        pebble.position.x -= centre.x;
        pebble.position.z -= centre.z;
        pebble.position.y -= box.min.y;

        // Frame the character with the camera.
        const height = Math.max(size.y, 1);
        const distance = height * 2.8;

        camera.position.set(
            0,
            height * 0.8,
            distance
        );

        camera.lookAt(0, height * 0.5, 0);

        // Set up the animation system.
        mixer = new THREE.AnimationMixer(pebble);

        console.log('Pebble loaded successfully!');
        console.log('Available animations:');

        gltf.animations.forEach((clip) => {
            console.log(`- ${clip.name}`);
        });

        // Find the idle animation.
        const idleClip = gltf.animations.find((clip) =>
            /idle/i.test(clip.name)
        );

        if (idleClip) {
            const idleAction = mixer.clipAction(idleClip);
            idleAction.reset();
            idleAction.play();

            status.textContent = `Pebble is here! Playing: ${idleClip.name}`;
        } else if (gltf.animations.length > 0) {
            // Temporary fallback if the idle clip has another name.
            const firstClip = gltf.animations[0];
            mixer.clipAction(firstClip).play();

            status.textContent = `Pebble loaded! Playing: ${firstClip.name}`;
        } else {
            status.textContent = 'Pebble loaded, but no animations were found.';
        }
    },

    (progress) => {
        if (progress.total > 0) {
            const percentage = Math.round(
                (progress.loaded / progress.total) * 100
            );

            status.textContent = `Loading Pebble... ${percentage}%`;
        }
    },

    (error) => {
        console.error('Could not load Pebble:', error);
        status.textContent = 'Could not load Pebble. Check the browser console.';
    }
);

// --------------------------------------------------
// 5. Animation loop
// --------------------------------------------------

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();

    if (mixer) {
        mixer.update(delta);
    }

    renderer.render(scene, camera);
}

animate();

// --------------------------------------------------
// 6. Window resizing
// --------------------------------------------------

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
});

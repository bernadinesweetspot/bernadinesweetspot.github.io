
import './style.css';
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

const ambientLight = new THREE.HemisphereLight(0xffffff, 0x84949a, 2);
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
// 4. Character and movement variables
// --------------------------------------------------

const loader = new GLTFLoader();

let pebble = null;
let mixer = null;

let idleAction = null;
let walkAction = null;
let activeAction = null;

const clock = new THREE.Clock();
const status = document.querySelector('#status');

const keys = new Set();

const moveSpeed = 2;
const turnSpeed = 8;

let cameraOffset = null;
let characterHeight = 1;

// --------------------------------------------------
// 5. Keyboard controls
// --------------------------------------------------

window.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();

    if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(key)) {
        event.preventDefault();
        keys.add(key);
    }
});

window.addEventListener('keyup', (event) => {
    keys.delete(event.key.toLowerCase());
});

window.addEventListener('blur', () => {
    keys.clear();
});

// --------------------------------------------------
// 6. Animation switching
// --------------------------------------------------

function playAnimation(nextAction) {
    if (!nextAction || nextAction === activeAction) {
        return;
    }

    nextAction.reset();
    nextAction.setLoop(THREE.LoopRepeat, Infinity);
    nextAction.clampWhenFinished = false;
    nextAction.fadeIn(0.2);
    nextAction.play();

    if (activeAction) {
        activeAction.fadeOut(0.2);
    }

    activeAction = nextAction;
}

// --------------------------------------------------
// 7. Load Pebble
// --------------------------------------------------

loader.load(
    '/models/pebble.glb',

    (gltf) => {
        pebble = gltf.scene;
        scene.add(pebble);

        // Enable character shadows.
        pebble.traverse((object) => {
            if (object.isMesh) {
                object.castShadow = true;
                object.receiveShadow = true;
            }
        });

        // Position Pebble on the floor.
        const box = new THREE.Box3().setFromObject(pebble);
        const size = box.getSize(new THREE.Vector3());
        const centre = box.getCenter(new THREE.Vector3());

        pebble.position.x -= centre.x;
        pebble.position.z -= centre.z;
        pebble.position.y -= box.min.y;

        // Position the camera.
        characterHeight = Math.max(size.y, 1);
        const distance = characterHeight * 2.8;

        camera.position.set(
            0,
            characterHeight * 0.8,
            distance
        );

        camera.lookAt(0, characterHeight * 0.5, 0);

        // Remember the camera's position relative to Pebble.
        cameraOffset = camera.position.clone().sub(pebble.position);

        // Set up the animation system.
        mixer = new THREE.AnimationMixer(pebble);

        // Find only the idle and walk animations.
        const idleClip = gltf.animations.find((clip) =>
            /idle/i.test(clip.name)
        );

        const walkClip = gltf.animations.find((clip) =>
            /walk/i.test(clip.name) && !/start|stop/i.test(clip.name)
        );

        // Create the animation actions.
        if (idleClip) {
            idleAction = mixer.clipAction(idleClip);
        }

        if (walkClip) {
            walkAction = mixer.clipAction(walkClip);
        }

        // Start with idle.
        if (idleAction) {
            playAnimation(idleAction);
        }

        // Show which animations were found.
        status.textContent =
            `Idle: ${!!idleAction} | Walk: ${!!walkAction}`;

        console.log('Pebble loaded successfully!');
        gltf.animations.forEach((clip) => {
            console.log('Animation:', clip.name);
        });
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
// 8. Movement and animation loop
// --------------------------------------------------

function animate() {
    requestAnimationFrame(animate);

    const delta = Math.min(clock.getDelta(), 0.05);

    if (pebble) {
        let moveX = 0;
        let moveZ = 0;

        // Read keyboard input.
        if (keys.has('w') || keys.has('arrowup')) moveZ -= 1;
        if (keys.has('s') || keys.has('arrowdown')) moveZ += 1;
        if (keys.has('a') || keys.has('arrowleft')) moveX -= 1;
        if (keys.has('d') || keys.has('arrowright')) moveX += 1;

        const isMoving = moveX !== 0 || moveZ !== 0;

        if (isMoving) {
            // Calculate the direction of travel.
            const direction = new THREE.Vector3(moveX, 0, moveZ).normalize();

            // Turn Pebble towards the direction of travel.
            const targetRotation = Math.atan2(direction.x, direction.z);

            const rotationDifference = Math.atan2(
                Math.sin(targetRotation - pebble.rotation.y),
                Math.cos(targetRotation - pebble.rotation.y)
            );

            pebble.rotation.y += rotationDifference * Math.min(1, turnSpeed * delta);

            // Move Pebble.
            pebble.position.x += direction.x * moveSpeed * delta;
            pebble.position.z += direction.z * moveSpeed * delta;

            // Keep Pebble inside the floor.
            pebble.position.x = THREE.MathUtils.clamp(pebble.position.x, -13, 13);
            pebble.position.z = THREE.MathUtils.clamp(pebble.position.z, -13, 13);

            // Play the looping walk animation.
            playAnimation(walkAction);

        } else {
            // Return to the looping idle animation.
            playAnimation(idleAction);
        }

        // Keep the camera following Pebble.
        if (cameraOffset) {
            camera.position.copy(pebble.position).add(cameraOffset);

            camera.lookAt(
                pebble.position.x,
                pebble.position.y + characterHeight * 0.5,
                pebble.position.z
            );
        }
    }

    if (mixer) {
        mixer.update(delta);
    }

    renderer.render(scene, camera);
}

animate();

// --------------------------------------------------
// 9. Window resizing
// --------------------------------------------------

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
});

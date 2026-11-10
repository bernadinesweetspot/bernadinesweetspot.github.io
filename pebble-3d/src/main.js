
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

const moveSpeed = 2;
const turnSpeed = 8;
const arrivalDistance = 0.08;

let cameraOffset = null;
let characterHeight = 1;

// The destination Pebble is currently walking towards.
let destination = null;
let destinationSource = null;

// --------------------------------------------------
// 5. Animation switching
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
// 6. Destination movement
// --------------------------------------------------

// Give Pebble a new destination.
// This function can eventually be called by Python.

function moveTo(x, z, source = 'user') {
    if (!pebble) {
        return;
    }

    destination = new THREE.Vector3(
        THREE.MathUtils.clamp(x, -13, 13),
        pebble.position.y,
        THREE.MathUtils.clamp(z, -13, 13)
    );

    destinationSource = source;

    status.textContent = 'Pebble is walking to a destination...';
}

// Make the movement function accessible for future testing
// and communication with the Python brain.

window.pebbleMoveTo = moveTo;
// --------------------------------------------------
// Receive movement instructions from Python
// --------------------------------------------------

async function checkPythonCommand() {
    try {
        const response = await fetch(
            'http://127.0.0.1:8765/api/command'
        );

        const data = await response.json();

        if (data.command && data.command.type === 'move_to') {
            moveTo(
                data.command.x,
                data.command.z,
                'python'
            );

            console.log('Python gave Pebble a destination:', data.command);
        }

    } catch (error) {
        // Python may not be running yet.
        // Avoid filling the console with connection errors.
    }
}

// Check for new Python instructions twice per second.
setInterval(checkPythonCommand, 500);


// Tell Python when Pebble reaches a Python-selected destination.
async function reportArrival() {
    try {
        await fetch('http://127.0.0.1:8765/api/arrived', {
            method: 'POST'
        });

        console.log('Pebble reported arrival to Python.');

    } catch (error) {
        console.error('Could not report arrival to Python:', error);
    }
}

// --------------------------------------------------
// 7. Click-to-move controls
// --------------------------------------------------

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

renderer.domElement.addEventListener('pointerdown', (event) => {
    if (!pebble) {
        return;
    }

    // Find the mouse position on the screen.
    const bounds = renderer.domElement.getBoundingClientRect();

    pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;

    // Project the mouse position into the 3D scene.
    raycaster.setFromCamera(pointer, camera);

    // Check whether the mouse clicked the floor.
    const intersections = raycaster.intersectObject(floor);

    if (intersections.length > 0) {
        const point = intersections[0].point;

        // Tell Pebble to walk to the clicked position.
        moveTo(point.x, point.z);
    }
});

// --------------------------------------------------
// 8. Load Pebble
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

        // Find the idle and in-place walk animations.
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

        status.textContent =
            `Idle: ${!!idleAction} | Walk: ${!!walkAction} | Click the floor to move Pebble`;

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
// 9. Movement and animation loop
// --------------------------------------------------

function animate() {
    requestAnimationFrame(animate);

    const delta = Math.min(clock.getDelta(), 0.05);

    if (pebble) {
        if (destination) {
            // Calculate the distance to the destination.
            const direction = new THREE.Vector3(
                destination.x - pebble.position.x,
                0,
                destination.z - pebble.position.z
            );

            const distance = direction.length();

            // Has Pebble reached its destination?
            if (distance <= arrivalDistance) {
                destination = null;

                const completedSource = destinationSource;
                destinationSource = null;

                playAnimation(idleAction);
                status.textContent = 'Pebble has arrived.';

                if (completedSource === 'python') {
                    reportArrival();
                }

            } else {
                // Work out the direction Pebble needs to face.
                direction.normalize();

                const targetRotation = Math.atan2(
                    direction.x,
                    direction.z
                );

                // Turn smoothly towards the destination.
                const rotationDifference = Math.atan2(
                    Math.sin(targetRotation - pebble.rotation.y),
                    Math.cos(targetRotation - pebble.rotation.y)
                );

                pebble.rotation.y +=
                    rotationDifference * Math.min(1, turnSpeed * delta);

                // Move towards the destination without overshooting it.
                const step = Math.min(moveSpeed * delta, distance);

                pebble.position.x += direction.x * step;
                pebble.position.z += direction.z * step;

                // Play the looping walk animation.
                playAnimation(walkAction);
            }

        } else {
            // No destination means Pebble should be idle.
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
// 10. Window resizing
// --------------------------------------------------

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    renderer.setSize(window.innerWidth, window.innerHeight);
});

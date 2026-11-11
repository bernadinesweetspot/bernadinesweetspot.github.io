
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


// --------------------------------------------------
// 3. Grassy clearing
// --------------------------------------------------

// Create the main grassy ground.
const floorGeometry = new THREE.PlaneGeometry(30, 30);

const floorMaterial = new THREE.MeshStandardMaterial({
    color: 0x78a96b,
    roughness: 1
});

const floor = new THREE.Mesh(floorGeometry, floorMaterial);

floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;

scene.add(floor);

 // --------------------------------------------------
 // 4. Woodland trees
 // --------------------------------------------------

// Shared materials.
const trunkMaterial = new THREE.MeshStandardMaterial({
    color: 0x795238,
    roughness: 1
});

const leafMaterials = [
    new THREE.MeshStandardMaterial({ color: 0x376b43, roughness: 1 }),
    new THREE.MeshStandardMaterial({ color: 0x477d4b, roughness: 1 }),
    new THREE.MeshStandardMaterial({ color: 0x568b50, roughness: 1 })
];

// Shared tree shapes.
const trunkGeometry = new THREE.CylinderGeometry(
    0.18, 0.25, 1.6, 7
);

const lowerLeavesGeometry = new THREE.ConeGeometry(
    1.25, 2.5, 7
);

const upperLeavesGeometry = new THREE.ConeGeometry(
    0.95, 2.1, 7
);

// Create one tree.
function createTree(x, z, scale = 1, leafColour = 0) {
    const tree = new THREE.Group();

    const trunk = new THREE.Mesh(
        trunkGeometry,
        trunkMaterial
    );

    trunk.position.y = 0.8;
    trunk.castShadow = true;
    tree.add(trunk);

    const lowerLeaves = new THREE.Mesh(
        lowerLeavesGeometry,
        leafMaterials[leafColour]
    );

    lowerLeaves.position.y = 2.5;
    lowerLeaves.castShadow = true;
    tree.add(lowerLeaves);

    const upperLeaves = new THREE.Mesh(
        upperLeavesGeometry,
        leafMaterials[(leafColour + 1) % leafMaterials.length]
    );

    upperLeaves.position.y = 3.6;
    upperLeaves.castShadow = true;
    tree.add(upperLeaves);

    tree.position.set(x, 0, z);
    tree.scale.setScalar(scale);

    scene.add(tree);
}

// Place trees around the outside of the clearing.
const treePositions = [
    [-14, -14, 1.0, 0],
    [-9, -14, 1.1, 1],
    [-3, -14, 0.9, 2],
    [4, -14, 1.2, 0],
    [10, -14, 1.0, 1],
    [14, -10, 1.1, 2],
    [14, -3, 0.9, 0],
    [14, 5, 1.2, 1],
    [12, 14, 1.0, 2],
    [5, 14, 1.1, 0],
    [-3, 14, 0.9, 1],
    [-11, 14, 1.2, 2],
    [-14, 8, 1.0, 0],
    [-14, 0, 1.1, 1]
];

treePositions.forEach(([x, z, scale, colour]) => {
    createTree(x, z, scale, colour);
});


 // --------------------------------------------------
 // 5. Woodland details
 // --------------------------------------------------

// Shared scenery materials.
const rockMaterial = new THREE.MeshStandardMaterial({
    color: 0x858b80,
    roughness: 1
});

const bushMaterials = [
    new THREE.MeshStandardMaterial({ color: 0x477b43, roughness: 1 }),
    new THREE.MeshStandardMaterial({ color: 0x568c4b, roughness: 1 }),
    new THREE.MeshStandardMaterial({ color: 0x699b56, roughness: 1 })
];

const logMaterial = new THREE.MeshStandardMaterial({
    color: 0x795238,
    roughness: 1
});

// Reusable shapes.
const rockGeometry = new THREE.DodecahedronGeometry(0.6, 0);

const bushGeometry = new THREE.SphereGeometry(0.7, 8, 6);

const logGeometry = new THREE.CylinderGeometry(
    0.22, 0.22, 2.2, 7
);

// Create a rock.
function createRock(x, z, scale = 1) {
    const rock = new THREE.Mesh(rockGeometry, rockMaterial);

    rock.position.set(x, 0.35 * scale, z);
    rock.scale.set(
        scale * 1.2,
        scale * 0.8,
        scale
    );

    rock.rotation.set(
        Math.random() * 0.3,
        Math.random() * Math.PI,
        Math.random() * 0.3
    );

    rock.castShadow = true;
    rock.receiveShadow = true;

    scene.add(rock);
}

// Create a bush.
function createBush(x, z, scale = 1, colour = 0) {
    const bush = new THREE.Group();

    // Three overlapping spheres create a leafy cluster.
    const positions = [
        [-0.35, 0.45, 0],
        [0.35, 0.5, 0.05],
        [0, 0.75, -0.3]
    ];

    positions.forEach(([offsetX, offsetY, offsetZ]) => {
        const leaves = new THREE.Mesh(
            bushGeometry,
            bushMaterials[colour]
        );

        leaves.position.set(offsetX, offsetY, offsetZ);
        leaves.scale.set(1, 0.85, 0.9);
        leaves.castShadow = true;

        bush.add(leaves);
    });

    bush.position.set(x, 0, z);
    bush.scale.setScalar(scale);

    scene.add(bush);
}

// Create a fallen log.
function createLog(x, z, rotation = 0, scale = 1) {
    const log = new THREE.Mesh(logGeometry, logMaterial);

    log.rotation.z = Math.PI / 2;
    log.rotation.y = rotation;

    log.position.set(x, 0.25 * scale, z);
    log.scale.setScalar(scale);

    log.castShadow = true;
    log.receiveShadow = true;

    scene.add(log);
}

// Scatter rocks around the woodland.
[
    [-12, -10, 0.8],
    [-8, -12, 0.6],
    [2, -12, 0.9],
    [9, -11, 0.7],
    [12, -6, 0.9],
    [13, 3, 0.6],
    [10, 11, 0.8],
    [3, 12, 0.7],
    [-7, 12, 0.9],
    [-12, 5, 0.7],
    [-13, -3, 0.8]
].forEach(([x, z, scale]) => {
    createRock(x, z, scale);
});

// Scatter bushes around the woodland.
[
    [-11, -8, 0.9, 0],
    [-5, -12, 1.0, 1],
    [6, -12, 0.8, 2],
    [12, -8, 1.1, 0],
    [13, 0, 0.9, 1],
    [11, 9, 1.0, 2],
    [6, 12, 0.8, 0],
    [-5, 13, 1.1, 1],
    [-12, 9, 0.9, 2],
    [-13, -1, 0.8, 0]
].forEach(([x, z, scale, colour]) => {
    createBush(x, z, scale, colour);
});

// Place fallen logs around the edges.
[
    [-10, -13, 0.3, 1.0],
    [10, -12, 0.8, 0.9],
    [13, 7, 1.2, 1.0],
    [-11, 11, -0.5, 1.1]
].forEach(([x, z, rotation, scale]) => {
    createLog(x, z, rotation, scale);
});


 // --------------------------------------------------
 // 6. Woodland pond
 // --------------------------------------------------

// Create the pond's outer bank.
const pondBankGeometry = new THREE.CircleGeometry(3.5, 32);

const pondBankMaterial = new THREE.MeshStandardMaterial({
    color: 0x9b9874,
    roughness: 1
});

const pondBank = new THREE.Mesh(
    pondBankGeometry,
    pondBankMaterial
);

pondBank.rotation.x = -Math.PI / 2;
pondBank.position.set(7, 0.025, 4);
pondBank.scale.set(1.15, 0.8, 1);
pondBank.receiveShadow = true;

scene.add(pondBank);

// Create the water.
const pondGeometry = new THREE.CircleGeometry(3, 32);

const pondMaterial = new THREE.MeshStandardMaterial({
    color: 0x438fa5,
    roughness: 0.2,
    metalness: 0.1
});

const pond = new THREE.Mesh(
    pondGeometry,
    pondMaterial
);

pond.rotation.x = -Math.PI / 2;
pond.position.set(7, 0.06, 4);
pond.scale.set(1.15, 0.8, 1);

scene.add(pond);

// Add stones around the pond.
[
    [3.8, 3.0, 0.45],
    [4.5, 1.6, 0.35],
    [6.0, 0.9, 0.4],
    [8.3, 1.3, 0.5],
    [10.0, 2.6, 0.35],
    [10.5, 4.4, 0.45],
    [9.0, 6.5, 0.4],
    [6.5, 6.9, 0.5],
    [4.2, 5.7, 0.4]
].forEach(([x, z, scale]) => {
    createRock(x, z, scale);
});

// Add a few plants around the water.
[
    [3.8, 5.0, 0.7, 1],
    [9.8, 5.8, 0.8, 2],
    [10.2, 2.0, 0.7, 0],
    [5.0, 1.8, 0.6, 1]
].forEach(([x, z, scale, colour]) => {
    createBush(x, z, scale, colour);
});

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

let stationaryActivity = null;
let activityActions = {};

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

    stationaryActivity = null;

    destination = new THREE.Vector3(
        THREE.MathUtils.clamp(x, -13, 13),
        pebble.position.y,
        THREE.MathUtils.clamp(z, -13, 13)
    );

    destinationSource = source;

    status.textContent = source === 'python'
        ? 'Pebble is exploring...'
        : 'Pebble is walking to a destination.';
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

        if (!data.command) {
            return;
        }

        if (data.command.type === 'move_to') {
            moveTo(
                data.command.x,
                data.command.z,
                'python'
            );

            console.log(
                'Python gave Pebble a destination:',
                data.command
            );
        }

        if (data.command.type === 'activity') {
            const activity = data.command.activity;

            const activityLabels = {
                explore: 'exploring',
                rest: 'resting',
                play: 'playing',
                reflect: 'reflecting'
            };

            if (activity === 'idle') {
                stationaryActivity = null;
                playAnimation(idleAction);
                status.textContent = 'Pebble is idle.';
            } else {
                const action = activityActions[activity];

                if (action) {
                    stationaryActivity = activity;
                    playAnimation(action);

                    status.textContent =
                        `Pebble is ${activityLabels[activity] || activity}...`;

                    console.log(`Playing ${activity} animation.`);
                } else {
                    console.warn(`No animation found for: ${activity}`);
                }
            }
        }

    } catch (error) {
        // Python may not be running yet.
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

        const restingClip = gltf.animations.find((clip) =>
            /resting/i.test(clip.name)
        );

        const playingClip = gltf.animations.find((clip) =>
            /playing/i.test(clip.name)
        );

        const reflectingClip = gltf.animations.find((clip) =>
            /reflecting/i.test(clip.name)
        );

        // Create the animation actions.
        if (idleClip) {
            idleAction = mixer.clipAction(idleClip);
        }

        if (walkClip) {
            walkAction = mixer.clipAction(walkClip);
        }

        if (restingClip) {
            activityActions.rest = mixer.clipAction(restingClip);
        }

        if (playingClip) {
            activityActions.play = mixer.clipAction(playingClip);
        }

        if (reflectingClip) {
            activityActions.reflect = mixer.clipAction(reflectingClip);
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
            // Only play idle if Pebble isn't doing another activity.
            if (!stationaryActivity) {
                playAnimation(idleAction);
            }
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

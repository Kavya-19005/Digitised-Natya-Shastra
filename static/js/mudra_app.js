const { GestureRecognizer, FilesetResolver, DrawingUtils } = window.MediaPipeTasksGestureRecognizer;

const modelPath = '/static/models/Bharatnatyam.task'; // Model path served by Flask
let gestureRecognizer;
let runningMode = "VIDEO"; // Use video mode for live webcam stream
let lastVideoTime = -1; // Timestamp for frame-rate consistency

const webcamElement = document.getElementById("webcam");
const canvasElement = document.getElementById("output_canvas");
const canvasCtx = canvasElement.getContext("2d");
const resultElement = document.getElementById("mudra-name");
const scoreElement = document.getElementById("mudra-score");
const statusDiv = document.getElementById("status");
const drawingUtils = new DrawingUtils(canvasCtx);


// 1. Initialize the Gesture Recognizer
async function createGestureRecognizer() {
    try {
        const filesetResolver = await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.0/wasm"
        );
        
        gestureRecognizer = await GestureRecognizer.create(filesetResolver, {
            baseOptions: {
                modelAssetPath: modelPath,
                runningMode: runningMode,
                // Setting up delegation to GPU (WebGPU or WebGL) for faster performance
                delegate: "GPU", 
            },
            numHands: 2 // Allow recognition of up to two hands
        });
        
        statusDiv.textContent = "Model loaded successfully. Starting webcam...";
        statusDiv.className = "success";
        
        enableCam();

    } catch (error) {
        statusDiv.textContent = `ERROR: Could not load model. Check console and ensure ${modelPath} exists.`;
        statusDiv.className = "error";
        console.error("Gesture Recognizer Initialization Error:", error);
    }
}


// 2. Start the Webcam Stream
function enableCam() {
    if (!gestureRecognizer) {
        console.log("Gesture Recognizer not initialized yet.");
        return;
    }

    // Get permission from user and start video stream
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(function (stream) {
                webcamElement.srcObject = stream;
                webcamElement.addEventListener("loadeddata", predictWebcam);
            })
            .catch(error => {
                statusDiv.textContent = "ERROR: Webcam access denied or failed.";
                statusDiv.className = "error";
                console.error("Webcam access error:", error);
            });
    } else {
        statusDiv.textContent = "ERROR: Your browser does not support webcam access.";
        statusDiv.className = "error";
    }
}


// 3. Real-time Prediction Loop
function predictWebcam() {
    // Set the canvas dimensions to match the video
    canvasElement.style.height = webcamElement.videoHeight;
    canvasElement.style.width = webcamElement.videoWidth;
    canvasElement.width = webcamElement.videoWidth;
    canvasElement.height = webcamElement.videoHeight;

    let results = null;

    // Use a timestamp check to maintain a consistent frame rate
    let nowInMs = performance.now();
    if (lastVideoTime !== webcamElement.currentTime) {
        lastVideoTime = webcamElement.currentTime;
        results = gestureRecognizer.recognizeForVideo(webcamElement, nowInMs);
    }
    
    // Clear the canvas
    canvasCtx.save();
    canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Draw landmarks and display results
    if (results && results.landmarks) {
        let mudraText = [];
        let confidenceScore = 0;

        for (const hand of results.landmarks) {
            // Draw the hand landmarks on the canvas
            drawingUtils.drawConnectors(canvasCtx, hand, window.MediaPipeTasksGestureRecognizer.HAND_CONNECTIONS, { color: "#00FF00", lineWidth: 5 });
            drawingUtils.drawLandmarks(canvasCtx, hand, { color: "#FF0000", lineWidth: 2 });
        }

        if (results.gestures.length > 0) {
            for (const gesture of results.gestures) {
                 // Format the result: e.g., "Pathakam (Left Hand)" or "Mushti (Right Hand)"
                const handLabel = gesture.handLabels[0].categoryName;
                const gestureName = mapGestureName(gesture.categoryName);
                
                mudraText.push(`${gestureName} (${handLabel})`);
                confidenceScore = Math.max(confidenceScore, gesture.categoryScore.toFixed(2));
            }
        }
        
        // Update the display elements
        resultElement.textContent = mudraText.length > 0 ? mudraText.join(' | ') : '(Waiting for mudra)';
        scoreElement.textContent = mudraText.length > 0 ? confidenceScore : '--';

    } else {
        resultElement.textContent = '(Waiting for hand)';
        scoreElement.textContent = '--';
    }

    canvasCtx.restore();

    // Loop the prediction process
    window.requestAnimationFrame(predictWebcam);
}


// Map the model's output labels (e.g., 'rock', 'paper') to the mudra names
function mapGestureName(modelName) {
    // Assuming your model outputs the original labels (rock, paper, scissors)
    switch (modelName.toLowerCase()) {
        case 'rock':
            return 'Mushti'; // Mudra similar to rock
        case 'paper':
            return 'Pathakam'; // Mudra similar to paper
        case 'scissors':
            return 'Karthari'; // Mudra similar to scissors (Karthari Mukha)
        default:
            return modelName.charAt(0).toUpperCase() + modelName.slice(1); // Default to title case
    }
}

// Start the whole process
createGestureRecognizer();

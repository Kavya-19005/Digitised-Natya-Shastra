/* static/js/app.js */

document.getElementById('upload-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const form = e.target;
    const statusDiv = document.getElementById('status');
    const submitBtn = document.getElementById('submit-btn');
    
    // Get form data (this includes all style parameters and the video file)
    const formData = new FormData(form);
    
    // Basic file validation
    const videoFile = formData.get('video');
    if (!videoFile || videoFile.size === 0) {
        statusDiv.className = 'error';
        statusDiv.textContent = 'Please select a video file to upload.';
        return;
    }

    // Update status and disable button
    statusDiv.className = 'processing';
    statusDiv.textContent = 'Processing video... This may take a moment.';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Processing...';

    try {
        // Use the RELATIVE path '/process' because the frontend is served by Flask
        const response = await fetch('/process', { 
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Success: Read the video data as a blob
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // Trigger automatic download
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'stick_figure_animation.mp4'; 
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url); // Clean up the object URL

            statusDiv.className = 'success';
            statusDiv.textContent = 'Success! Your video is downloading.';

        } else {
            // Handle server-side errors (Flask returns JSON for errors)
            let errorText = 'Video processing failed.';
            try {
                const errorData = await response.json();
                errorText = errorData.error || errorText;
            } catch (e) {
                errorText += ` (Status: ${response.status} ${response.statusText})`;
            }
            
            statusDiv.className = 'error';
            statusDiv.textContent = errorText;
        }

    } catch (error) {
        // Handle network errors
        statusDiv.className = 'error';
        statusDiv.textContent = `A network error occurred: ${error.message}. Ensure your Flask server is running.`;
        console.error('Fetch error:', error);
    } finally {
        // Re-enable the button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Process Video';
    }
});
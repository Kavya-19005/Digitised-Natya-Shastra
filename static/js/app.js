document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const statusDiv = document.getElementById('status');
    const submitBtn = document.getElementById('submit-btn');
    const videoElement = document.getElementById("resultVideo");
    const downloadLink = document.getElementById("downloadLink");

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // 1. Setup & Validation
        const formData = new FormData(form);
        const videoFile = formData.get('video');
        
        // Hide previous results
        videoElement.style.display = 'none';
        videoElement.src = '';
        downloadLink.style.display = 'none';

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
            // 2. Fetch Request to Flask Backend
            const response = await fetch('/process', { 
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Success: Read the video data as a blob
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                // 3. Display the video
                videoElement.src = url;
                videoElement.style.display = 'block';
                
                // 4. Set up the explicit download link
                downloadLink.href = url;
                downloadLink.download = 'stick_figure_animation.mp4';
                downloadLink.style.display = 'block';

                statusDiv.className = 'success';
                statusDiv.textContent = 'Success! The processed animation is displayed below.';

            } else {
                // Handle server-side errors
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
});
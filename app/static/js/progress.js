// Progress tracking functionality
let progressInterval;
let lastProgress = 0;
let retryCount = 0;
let maxRetries = 5;
let retryDelay = 3000; // Start with 3 seconds, will increase on failures
let lastResponseTime = null;

// Debug panel for deployment issues
function showDebugPanel() {
    if (!document.getElementById('debug-panel')) {
        // Create debug panel UI
        const debugPanel = document.createElement('div');
        debugPanel.id = 'debug-panel';
        debugPanel.className = 'card mt-4';
        debugPanel.innerHTML = `
            <div class="card-header bg-warning">
                <h5 class="mb-0"><i class="fas fa-bug me-2"></i>Debugging Information</h5>
            </div>
            <div class="card-body">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle me-2"></i>
                    Loading diagnostic information to help identify deployment issues...
                </div>
                <div id="debug-output" class="mt-3">
                    <p><strong>Last status update:</strong> <span id="last-status-time">Checking...</span></p>
                    <p><strong>Processing status:</strong> <span id="debug-process-status">Checking...</span></p>
                    <p><strong>Server time:</strong> <span id="server-time">Checking...</span></p>
                    <div id="directory-status"></div>
                </div>
                <button id="retry-processing" class="btn btn-primary mt-3">
                    <i class="fas fa-sync me-2"></i>Retry Processing
                </button>
            </div>
        `;
        
        // Add to the page
        document.querySelector('.container').appendChild(debugPanel);
        
        // Add event listener for retry button
        document.getElementById('retry-processing').addEventListener('click', function() {
            restartProgressTracking();
        });
        
        // Fetch debug logs
        fetchDebugLogs();
    }
}

// Fetch diagnostic information
function fetchDebugLogs() {
    fetch('/debug/logs')
        .then(response => response.json())
        .then(data => {
            console.log('Debug data:', data);
            document.getElementById('last-status-time').textContent = data.progress_data.timestamp || 'No updates';
            document.getElementById('debug-process-status').textContent = data.progress_data.message || 'No status';
            document.getElementById('server-time').textContent = data.current_time;
            
            // Show directory status
            let dirStatusHtml = '<h6 class="mt-3">Directory Status:</h6>';
            if (data.directories) {
                for (const [dirName, dirInfo] of Object.entries(data.directories)) {
                    const statusClass = dirInfo.exists && dirInfo.is_writable ? 'text-success' : 'text-danger';
                    const statusIcon = dirInfo.exists && dirInfo.is_writable ? 
                        '<i class="fas fa-check-circle me-1"></i>' : 
                        '<i class="fas fa-times-circle me-1"></i>';
                    
                    dirStatusHtml += `<p class="${statusClass}">${statusIcon}${dirName}: ${dirInfo.path}<br>
                        <small>${dirInfo.exists ? 'Exists' : 'Missing'}, 
                        ${dirInfo.is_writable ? 'Writable' : 'Not writable'}</small></p>`;
                }
            }
            document.getElementById('directory-status').innerHTML = dirStatusHtml;
        })
        .catch(error => {
            console.error('Error fetching debug logs:', error);
            document.getElementById('debug-output').innerHTML = 
                `<div class="alert alert-danger">Error fetching debug data: ${error.message}</div>`;
        });
}

function checkProgress() {
    fetch('/check_progress')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            lastResponseTime = new Date();
            retryCount = 0; // Reset retry count on success
            retryDelay = 3000; // Reset retry delay
            return response.json();
        })
        .then(data => {
            if (!data || data.status === 'none') {
                console.log('No progress data available');
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                }
                return;
            }
            
            updateProgressUI(data);
            
            // If processing is complete, stop polling
            if (data.complete === true) {
                if (progressInterval) {
                    clearInterval(progressInterval);
                    progressInterval = null;
                }
                
                // Handle completion - redirect to dashboard after delay
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 2000);
            } 
            // If progress hasn't changed for a long time, show diagnostic panel
            else if (lastProgress === data.progress && lastProgress > 0) {
                const stuckTime = Math.floor((new Date() - lastResponseTime) / 1000);
                if (stuckTime > 60) { // If stuck for over a minute
                    showDebugPanel();
                }
            }
            
            lastProgress = data.progress;
        })
        .catch(error => {
            console.error('Error checking progress:', error);
            retryCount++;
            
            // If we keep getting errors, slow down the requests
            retryDelay = Math.min(retryDelay * 1.5, 15000); // Max 15 seconds
            
            if (retryCount >= maxRetries) {
                console.log('Max retries reached, showing debug panel');
                showDebugPanel();
            }
        });
}

function updateProgressUI(data) {
    // Update the progress bar
    const progressBar = document.getElementById('progress-bar');
    if (progressBar) {
        progressBar.style.width = `${data.progress}%`;
        progressBar.setAttribute('aria-valuenow', data.progress);
        progressBar.textContent = `${data.progress}%`;
    }
    
    // Update the status message
    const statusMessage = document.getElementById('status-message');
    if (statusMessage && data.message) {
        statusMessage.textContent = data.message;
    }
    
    // Update progress step indicator if it exists
    if (data.step) {
        document.querySelectorAll('.progress-step').forEach(el => {
            el.classList.remove('active', 'done');
        });
        
        // Mark current and previous steps as done
        for (let i = 1; i <= data.step; i++) {
            const stepEl = document.getElementById(`step-${i}`);
            if (stepEl) {
                if (i < data.step) {
                    stepEl.classList.add('done');
                } else {
                    stepEl.classList.add('active');
                }
            }
        }
    }
}

function startProgressTracking() {
    lastResponseTime = new Date();
    checkProgress(); // Initial check
    progressInterval = setInterval(checkProgress, 2000); // Check every 2 seconds
}

function restartProgressTracking() {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    lastProgress = 0;
    retryCount = 0;
    retryDelay = 3000;
    startProgressTracking();
    
    // Update UI to show we're retrying
    const statusMessage = document.getElementById('status-message');
    if (statusMessage) {
        statusMessage.textContent = 'Restarting progress tracking...';
    }
}

// Start tracking when the page loads
document.addEventListener('DOMContentLoaded', function() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        startProgressTracking();
    }
}); 
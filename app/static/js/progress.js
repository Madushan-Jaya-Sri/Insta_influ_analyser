// Socket.IO Progress Handler

// Global variables
let socket = null;
let currentTaskId = null;
let progressBar = null;
let progressText = null;
let formSubmitted = false;

// Initialize Socket.IO connection
function initSocket() {
    // Check if Socket.IO is available
    if (typeof io === 'undefined') {
        console.error('Socket.IO client library not loaded');
        return false;
    }
    
    try {
        // Connect to the server
        socket = io.connect('/', {
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 5
        });
        
        // Set up event handlers
        socket.on('connect', function() {
            console.log('Connected to server');
            updateStatus('Connected to server');
        });
        
        socket.on('connection_response', function(data) {
            console.log('Connection response:', data);
            updateStatus(`Connection established (ID: ${data.client_id})`);
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from server');
            updateStatus('Disconnected from server');
        });
        
        socket.on('progress_update', function(data) {
            console.log('Progress update:', data);
            updateProgress(data);
        });
        
        socket.on('task_started', function(data) {
            console.log('Task started:', data);
            currentTaskId = data.task_id;
            updateStatus(`Task ${data.task_id} started`);
        });
        
        socket.on('connect_error', function(error) {
            console.error('Connection error:', error);
            updateStatus('Connection error', true);
        });
        
        return true;
    } catch (error) {
        console.error('Error initializing Socket.IO:', error);
        return false;
    }
}

// Update the progress bar
function updateProgress(data) {
    if (!progressBar || !progressText) {
        findProgressElements();
    }
    
    if (progressBar && progressText) {
        // Update the progress bar
        const progress = data.progress || 0;
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        
        // Update the progress text
        progressText.textContent = data.message || `Processing: ${progress}%`;
        
        // Show/hide elements based on status
        if (data.status === 'completed') {
            // Task completed, redirect if needed
            if (data.redirect_url) {
                setTimeout(function() {
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                // Just reload the page to see results
                setTimeout(function() {
                    window.location.reload();
                }, 1000);
            }
        } else if (data.status === 'error') {
            // Show error
            progressBar.classList.remove('bg-info', 'bg-success');
            progressBar.classList.add('bg-danger');
            progressText.classList.add('text-danger');
        }
    } else {
        console.warn('Progress elements not found');
    }
}

// Find progress elements in the DOM
function findProgressElements() {
    progressBar = document.querySelector('.progress-bar');
    progressText = document.querySelector('.progress-text');
    
    if (!progressBar || !progressText) {
        console.warn('Progress elements not found, creating them');
        createProgressElements();
    }
}

// Create progress elements if they don't exist
function createProgressElements() {
    // Find the form
    const form = document.querySelector('form');
    if (!form) return;
    
    // Create container
    const progressContainer = document.createElement('div');
    progressContainer.className = 'progress-container mt-4';
    
    // Create progress bar
    const progressWrapper = document.createElement('div');
    progressWrapper.className = 'progress';
    progressWrapper.style.height = '25px';
    
    progressBar = document.createElement('div');
    progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
    progressBar.style.width = '0%';
    progressBar.setAttribute('role', 'progressbar');
    progressBar.setAttribute('aria-valuenow', '0');
    progressBar.setAttribute('aria-valuemin', '0');
    progressBar.setAttribute('aria-valuemax', '100');
    
    progressWrapper.appendChild(progressBar);
    progressContainer.appendChild(progressWrapper);
    
    // Create progress text
    progressText = document.createElement('div');
    progressText.className = 'progress-text text-center mt-2';
    progressText.textContent = 'Waiting to start...';
    progressContainer.appendChild(progressText);
    
    // Insert after the form
    form.parentNode.insertBefore(progressContainer, form.nextSibling);
    
    // Initially hide the progress elements
    progressContainer.style.display = 'none';
}

// Update status text
function updateStatus(message, isError = false) {
    if (!progressText) {
        findProgressElements();
    }
    
    if (progressText) {
        progressText.textContent = message;
        
        if (isError) {
            progressText.classList.add('text-danger');
        } else {
            progressText.classList.remove('text-danger');
        }
    }
}

// Start a task
function startTask(taskId) {
    if (!socket) {
        console.error('Socket not initialized');
        return false;
    }
    
    try {
        socket.emit('start_task', { task_id: taskId });
        currentTaskId = taskId;
        return true;
    } catch (error) {
        console.error('Error starting task:', error);
        return false;
    }
}

// Handle form submission
function handleFormSubmit(event, formId = null) {
    // Find the form
    const form = formId ? document.getElementById(formId) : event.target;
    if (!form || !form.checkValidity()) return;
    
    // Prevent multiple submissions
    if (formSubmitted) {
        event.preventDefault();
        return;
    }
    
    // Mark as submitted
    formSubmitted = true;
    
    // Show progress elements
    findProgressElements();
    const progressContainer = document.querySelector('.progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    
    // Get form ID or create a unique task ID
    const taskId = form.id || 'form_' + new Date().getTime();
    
    // Initialize socket if not already done
    if (!socket) {
        initSocket();
    }
    
    // Start the task
    startTask(taskId);
    
    // Let the form submit normally
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Find all forms that should show progress
    const forms = document.querySelectorAll('form[data-show-progress="true"]');
    
    if (forms.length > 0) {
        // Create progress elements
        createProgressElements();
        
        // Initialize Socket.IO
        initSocket();
        
        // Add submit event listeners to forms
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                handleFormSubmit(event, form.id);
            });
        });
    }
});

// Export functions for use in other scripts
window.progressHandler = {
    initSocket,
    startTask,
    updateProgress,
    updateStatus
}; 
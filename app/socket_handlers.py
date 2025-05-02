from flask import request
from flask_socketio import SocketIO, emit
import time
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global dict to store progress for different sessions
progress_data = {}

def register_socket_handlers(socketio):
    """Register all socket event handlers with the provided SocketIO instance"""
    logger.info("Registering Socket.IO event handlers")
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        client_id = request.sid
        logger.info(f"Client connected: {client_id}")
        emit('connection_response', {'status': 'connected', 'client_id': client_id})

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        client_id = request.sid
        logger.info(f"Client disconnected: {client_id}")
        
        # Clean up any progress data for this client
        if client_id in progress_data:
            del progress_data[client_id]

    @socketio.on('start_task')
    def handle_start_task(data):
        """Start a background task and emit progress updates"""
        client_id = request.sid
        task_id = data.get('task_id', 'unknown')
        logger.info(f"Starting task {task_id} for client {client_id}")
        
        # Store initial progress
        progress_data[client_id] = {
            'task_id': task_id,
            'progress': 0,
            'status': 'running',
            'message': 'Task started'
        }
        
        # Start a background thread to simulate/track progress
        thread = threading.Thread(
            target=update_progress, 
            args=(socketio, client_id, task_id)
        )
        thread.daemon = True
        thread.start()
        
        # Return immediate response
        emit('task_started', {
            'task_id': task_id,
            'status': 'started'
        })
    
    logger.info("Socket.IO event handlers registered successfully")
    return socketio

def update_progress(socketio, client_id, task_id):
    """Update and emit progress periodically"""
    try:
        # Initial status
        socketio.emit('progress_update', {
            'task_id': task_id,
            'progress': 0,
            'status': 'running',
            'message': 'Processing started'
        }, room=client_id)
        
        # Simulate progress updates
        for i in range(1, 11):
            # Skip if client disconnected
            if client_id not in progress_data:
                logger.info(f"Client {client_id} disconnected, stopping updates")
                return
                
            # Update progress data
            progress = i * 10
            progress_data[client_id]['progress'] = progress
            progress_data[client_id]['message'] = f'Processing {progress}% complete'
            
            # Emit update to the specific client
            socketio.emit('progress_update', {
                'task_id': task_id,
                'progress': progress,
                'status': 'running',
                'message': f'Processing {progress}% complete'
            }, room=client_id)
            
            # Wait a bit
            time.sleep(1)
        
        # Final update
        socketio.emit('progress_update', {
            'task_id': task_id,
            'progress': 100,
            'status': 'completed',
            'message': 'Processing completed'
        }, room=client_id)
        
        # Clean up
        if client_id in progress_data:
            del progress_data[client_id]
            
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        socketio.emit('progress_update', {
            'task_id': task_id,
            'progress': 0,
            'status': 'error',
            'message': f'Error: {str(e)}'
        }, room=client_id)

# Function to be called from routes to update progress
def update_task_progress(socketio, task_id, progress, message, client_id=None):
    """Update task progress from any part of the application"""
    try:
        if client_id and client_id in progress_data:
            progress_data[client_id]['progress'] = progress
            progress_data[client_id]['message'] = message
            
            socketio.emit('progress_update', {
                'task_id': task_id,
                'progress': progress,
                'status': 'running' if progress < 100 else 'completed',
                'message': message
            }, room=client_id)
            
            return True
        else:
            # Broadcast to all clients if no specific client_id
            socketio.emit('progress_update', {
                'task_id': task_id,
                'progress': progress,
                'status': 'running' if progress < 100 else 'completed',
                'message': message
            })
            return True
    except Exception as e:
        logger.error(f"Error updating task progress: {str(e)}")
        return False 
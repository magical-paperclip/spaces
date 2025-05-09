
import os
import logging
import subprocess
import signal
import atexit
from app import app, db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create console handler with a higher log level
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)

# Add the handlers to the logger
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)

# Global variable to store the Hackatime service process
hackatime_process = None

def initialize_database():
    """Initialize the database and create all tables."""
    try:
        app.logger.info("Initializing database...")
        with app.app_context():
            db.create_all()
        app.logger.info("Database initialized successfully.")
        return True
    except Exception as e:
        app.logger.warning(f"Database initialization error: {e}")
        return False

def start_hackatime_service():
    """Start the Hackatime service as a subprocess."""
    global hackatime_process
    try:
        app.logger.info("Starting Hackatime service...")
        hackatime_process = subprocess.Popen(
            ['python', 'hackatime_service.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        app.logger.info(f"Hackatime service started with PID {hackatime_process.pid}")
    except Exception as e:
        app.logger.error(f"Error starting Hackatime service: {str(e)}")

def stop_hackatime_service():
    """Stop the Hackatime service when the main app exits."""
    global hackatime_process
    if hackatime_process and hackatime_process.poll() is None:
        app.logger.info(f"Stopping Hackatime service (PID {hackatime_process.pid})...")
        try:
            hackatime_process.send_signal(signal.SIGTERM)
            hackatime_process.wait(timeout=5)
            app.logger.info("Hackatime service stopped gracefully")
        except subprocess.TimeoutExpired:
            app.logger.warning("Timeout waiting for service to stop, forcing termination")
            hackatime_process.kill()
        except Exception as e:
            app.logger.error(f"Error stopping service: {str(e)}")
            hackatime_process.kill()

if __name__ == '__main__':
    app.logger.info("Starting Hack Club Spaces application")
    
    # Initialize database
    try:
        initialize_database()
    except Exception as e:
        app.logger.warning(f"Database initialization error: {e}")
    
    # Start Hackatime service
    start_hackatime_service()
    
    # Register the cleanup function to stop Hackatime service on exit
    atexit.register(stop_hackatime_service)
    
    # Start the main Flask application
    port = int(os.environ.get('PORT', 3000))
    app.logger.info(f"Server running on http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

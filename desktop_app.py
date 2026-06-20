import webview
import threading
import time
import sys
from app import app

def start_flask():
    # Run the Flask app on local port 5000
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a background daemon thread
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()
    
    # Wait for the Flask server to initialize
    time.sleep(1.5)
    
    # Create the webview window
    webview.create_window(
        title='Drip Irrigation Center MS',
        url='http://127.0.0.1:5000',
        width=1280,
        height=800,
        min_size=(1024, 768)
    )
    webview.start()

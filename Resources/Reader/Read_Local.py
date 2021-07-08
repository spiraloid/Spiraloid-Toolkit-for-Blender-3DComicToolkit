from http.server import HTTPServer, CGIHTTPRequestHandler
import webbrowser
import threading
import os

def start_server(path, port=8000):
    '''Start a simple webserver serving path on port'''
    os.chdir(path)
    httpd = HTTPServer(('', port), CGIHTTPRequestHandler)
    httpd.serve_forever()

# Start the server in a new thread
port = 8000
daemon = threading.Thread(name='daemon_server', target=start_server,args=('.', port))
daemon.setDaemon(True) # Set as a daemon so it will be killed once the main thread is dead.
daemon.start()

# Open the web browser 
webbrowser.open('http://localhost:8000/?lan=en&savepoint=0'.format(port))
# Simple-Python-Proxy-Web-Server
This project is a simple proxy web server implemented in Python, designed to handle basic HTTP requests. The server acts as an intermediary between clients and web servers, forwarding client requests and caching server responses for improved performance. 
It includes features such as request logging, error handling, and caching to enhance the overall web browsing experience.

Key Features:

Proxy Functionality:

Listens for incoming client connections and acts as a proxy between clients and web servers.
HTTP Request Handling:

Parses incoming HTTP requests, focusing on the GET method, and extracts relevant details such as the requested URL, host, and path.
Caching Mechanism:

Implements a basic caching mechanism to store previously fetched resources locally, reducing latency for repeated requests.
Logging:

Logs details of incoming client requests, including request length, method, and the requested URL. Additionally, logs details of the server's responses.
Error Handling:

Handles different types of errors gracefully, providing appropriate HTTP response codes and messages to clients.
Multi-Threading:

Utilizes multi-threading to handle multiple client connections concurrently, allowing for improved responsiveness.
How to Use:

Run the Server:

Execute the provided Python script to start the proxy server. The server will listen on a specified port (default is 8888).
Make HTTP Requests:

Open a web browser or use tools like telnet or curl to send HTTP requests to the proxy server. Observe the logs and server responses.
Test Caching:

Make repeated requests for the same resource and observe whether the server retrieves the resource from the cache.
Explore Logging:

Review the proxy_log.txt file to see detailed logs of client requests and server responses.
Customization:

Customize the server script to meet specific requirements, such as handling additional HTTP methods or extending the caching mechanism.

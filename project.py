from socket import *
import threading

import sys, time, re
import logging

logging.basicConfig(filename='proxy_log.txt', level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class Server:
    def __init__(self):
        try:
            self.server_socket = socket(AF_INET, SOCK_STREAM)
            self.server_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1) # Re-use the socket
        except error as e:
            logging.error('Unable to create/reuse the socket. Error: %s', e)
            sys.exit(1)

        self.server_socket.bind(('127.0.0.1', 8888))
        self.server_socket.listen(10)

        logging.info("Server listening on port 8888...")
    

    #listening to the clients:
    def listen_to_client(self):
        while True:
            #wait for a client connection
            client_socket, client_address = self.server_socket.accept()
            d = threading.Thread(name=str(client_address), target=self.proxy_thread,
                                 args=(client_socket, client_address))
            d.daemon = True
            d.start()
        #close the connection
        self.server_socket.close()
    def proxy_thread(self, client_connection_socket, client_address):
        # method to create a new thread for evervy client connected
        # starting the timer to calculate the elapsed time
        start_time = time.time()
        # getting the client request
        client_request = client_connection_socket.recv(1024).decode('utf-8')
        # if the request is not empty request i.e it contains some data
        if client_request:
            self.log_request_details(client_request, client_address)
            # getting request length
            request_length = len(client_request)

            # Parsing the request line and headers sent by the client
            # since the request will be of the form GET http://www.abc.com HTTP/1.1 extracting the http part
            resp_part = client_request.split(' ')[0]
            if resp_part == "GET":
                http_part = client_request.split(' ')[1]
                # stripping the http part to get only the URL and removing the trailing / from the request
                double_slash_pos = str(http_part).find("//")
                url_connect = ""
                url_slash_check = list()
                url_slash = str()
                # if no http part to the url
                if double_slash_pos == -1:
                    url_part = http_part[1:]
                    # getting the www.abc.com part
                    url_connect = url_part.split('/')[0]
                else:
                    # if the url ends with / removing it e.g: www.example.com/
                    if http_part.split('//')[1][-1] == "/":
                        url_part = http_part.split('//')[1][:-1]
                        # getting the www.abc.com part
                        url_connect = url_part.split('/')[0]
                    else:
                        url_part = http_part.split('//')[1]
                        # getting the www.abc.com part
                        url_connect = url_part.split('/')[0]

                # getting the part after the host
                url_slash_check = url_part.split('/')[1:]
                url_slash = ""
                if url_slash_check:
                    for path in url_slash_check:
                        url_slash += "/"
                        url_slash += path
                # checking if port number is provided
                client_request_port_start = str(url_part).find(":")
                # default port number
                port_number = 80
                # replacing all the non alphanumeric characters with under score
                url_file_name = re.sub('[^0-9a-zA-Z]+', '_', url_part)
                if client_request_port_start == -1:
                    pass
                else:
                    port_number = int(url_part.split(':')[1])
                self.find_file(url_file_name, client_connection_socket, port_number, client_address, start_time, url_connect, url_slash)
            else:
                # a call other than GET occurred
                message = "Client with port: " + str(client_address[1]) + " generated a call other than GET: " + resp_part + " \n"
                client_connection_socket.send("HTTP/1.1 405 Method Not Allowed\r\n\r\n")
                client_connection_socket.close()
                self.log_info(message)
                message = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
                self.log_info(message)
        else:
            # a blank request call was made by a client
            client_connection_socket.send("")
            client_connection_socket.close()
            message = "Client with port: " + str(client_address[1]) + " connection closed \n"
            self.log_info(message)
        client_connection_socket.close()
        end_time = time.time()
        logging.info("Client with port %d connection closed. Time Elapsed(RTT): %.2f seconds", client_address[1],
                     end_time - start_time)
    def find_file(self, url_file_name, client_connection_socket, port_number, client_address, start_time, url_connect, url_slash):
        try:
            if not url_file_name:
                raise FileNotFoundError("Empty file name")
            # getting the cached file for the url if it exists
            cached_file = open(url_file_name, "r")
            # reading the contents of the file
        except FileNotFoundError as e:
            message = "Client with port: " + str(client_address[1]) + ": Cache hit occurred" \
                                                                      "  for the request. Reading from file \n"
            self.log_request_details(message,client_address)
            # get proxy server details since the data is fetched from cache
            server_socket_details = getaddrinfo("localhost", port_number)
            server_details_message = "<body> Cached Server Details:- <br />"
            server_details_message += "Server host name: localhost <br /> Server port number: " + str(port_number) + " <br>"
            server_details_message += "Socket family: " + str(server_socket_details[0][0]) + "<br>"
            server_details_message += "Socket type: " + str(server_socket_details[0][1]) + "<br>"
            server_details_message += "Socket protocol: " + str(server_socket_details[0][2]) + "<br>"
            server_details_message += "Timeout: " + str(client_connection_socket.gettimeout()) + "<br> </body>"
            response_message = ""
            # print "reading data line by line and appending it"
            with open(url_file_name) as f:
                for line in f:
                    response_message += line
            # print 'finished reading the data'
            # appending the server details message to the response
            response_message += server_details_message
            # closing the file handler
            cached_file.close()
            # sending the cached data

            client_connection_socket.send(response_message)
            end_time = time.time()
            message = "Client with port: " + str(client_address[1]) + ": Response Length: " + str(len(response_message)) + " bytes\n"
            self.log_info(message)
            message = "Client with port: " + str(client_address[1]) + " Time Elapsed(RTT): "+str(end_time - start_time) + " seconds \n"
            self.log_info(message)
        except KeyboardInterrupt:
            # Handle KeyboardInterrupt to ensure a graceful exit
            print("KeyboardInterrupt: Exiting...")
            sys.exit(0)
        except IOError as e:
            message = "Client with port: " + str(client_address[1]) + " Cache miss occurred " \
                                                                      "for the request. Hitting web server \n"
            self.log_request_details("IOError: " + str(e), client_address)
            """there is no cached file for the specified URL,
            so we need to fetch the URL from the proxy server and cache it
            To get the URL we need to create a socket on proxy machine"""
            proxy_connection_socket = None
            try:
                # creating the socket from the proxy server
                proxy_connection_socket = socket(AF_INET, SOCK_STREAM)
                # setting time out so that after last packet if not other packet comes socket will auto close
                # in 2 seconds
            except error as e:
                print ("Unable to create the socket. Error: %s" % e)
                message = 'Unable to create the socket. Error: %s' % e
                self.log_request_details(message)
            try:
                proxy_connection_socket.settimeout(2)
                # connecting to the url specified by the client
                proxy_connection_socket.connect((url_connect, port_number))
                # sending GET request from client to the web server
                web_request = str()
                if url_slash:
                    web_request = b"GET /" + url_slash[1:] + " HTTP/1.1\nHost: " + url_connect + "\n\n"
                else:
                    web_request = b"GET / HTTP/1.1\nHost: " + url_connect + "\n\n"

                # print "GET web request: "+web_request
                proxy_connection_socket.send(web_request)
                message = "Client with port: " + str(client_address[1]) + " generated request of length " \
                                                                          "to web server "+str(len(web_request))+ " bytes \n"
                self.log_info(message)
                message = "Client with port: " + str(client_address[1]) + " generated request " \
                                                                          "to web server as: "+str(web_request) + " \n"
                self.log_info(message)
                # getting the web server response which is expected to be a file
                server_socket_details = getaddrinfo(url_connect, port_number)
                server_details_message = "<body> Web Server Details:- <br />"
                server_details_message += "Server host name: " + url_connect + " <br /> Server port number: " + str(port_number) + "<br />"
                server_details_message += "Socket family: " + str(server_socket_details[0][0]) + "<br />"
                server_details_message += "Socket type: " + str(server_socket_details[0][1]) + "<br />"
                server_details_message += "Socket protocol: " + str(server_socket_details[0][2]) + "<br />"
                server_details_message += "Timeout: " + str(client_connection_socket.gettimeout()) + "<br /> </body>"
                web_server_response_append = ""
                # to get server response in loop until zero data or timeout of 2 seconds is reached
                timeout_flag = False
                while True:
                    try:
                        web_server_response = proxy_connection_socket.recv(4096)
                    except timeout:
                        # a time out occurred on waiting for server response so break out of loop
                        if len(web_server_response_append) <= 0:
                            timeout_flag = True
                        break
                    if len(web_server_response) > 0:
                        web_server_response_append += web_server_response
                    else:
                        # all the data has been received so break out of the loop
                        break
                # variable to store response to file
                response_to_file = web_server_response_append
                # appending web server details to the response sent to client
                web_server_response_append += server_details_message
                if timeout_flag:
                    # got bored waiting for response
                    error_response = "HTTP/1.1 408 Request timeout\r\n\r\n"
                    error_response += server_details_message
                    client_connection_socket.send(error_response)
                else:
                    # sending the web server response back to client
                    client_connection_socket.send(web_server_response_append)
                end_time = time.time()
                message = "Client with port: " + str(client_address[1]) + " Time Elapsed(RTT): " + str(
                    end_time - start_time) + " seconds \n"
                # print "Response: " + web_server_response_append
                self.log_info(message)
                # caching the response on the proxy server
                proxy_temp_file = open(url_file_name, "wb")
                # writing the entire response to file
                proxy_temp_file.write(response_to_file)
                proxy_temp_file.close()
                message = "Client with port: " + str(client_address[1]) + " got " \
                                                                          "response of length " +str(len(response_to_file)) + " bytes \n"
                self.log_info(message)
                # closing the proxy server socket
                proxy_connection_socket.close()
            except error as e:
                # sending page not found response to client
                error_message = ""
                '''if str(e) == "timed out":
                    error_message = "HTTP/1.1 404 Not Found\r\n"
                    client_connection_socket.send("HTTP/1.1 408 Request timeout\r\n\r\n")
                else:'''
                error_message = "HTTP/1.1 404 Not Found\r\n\r\n"
                client_connection_socket.send('HTTP/1.1 404 not found\r\n\r\n')
                end_time = time.time()
                message = "Client with port: " + str(client_address[1]) + " Following error occurred : "+str(e) + "\n"
                self.log_info(message)
                message = "Client with port: " + str(client_address[1]) + " response sent: " + error_message + " \n"
                self.log_info(message)
                message = "Client with port: " + str(client_address[1]) + " Time Elapsed(RTT): " + str(
                    end_time - start_time) + " seconds \n"
                self.log_info(message)

        # closing the client connection socket
        client_connection_socket.close()
        message = "Client with port: " + str(client_address[1]) + " connection closed \n"
        self.log_info(message)
    def log_request_details(self, client_request, client_address):
        request_length = len(client_request)
        logging.info("Client with port %d request length is %d bytes", client_address[1], request_length)
        logging.info("Client with port %d generated request: %s", client_address[1], client_request.splitlines()[0])
if __name__ == "__main__":
    server = Server()
    server.listen_to_client()
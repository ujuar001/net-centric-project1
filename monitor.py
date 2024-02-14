import sys
import socket

# get urls_file name from command line
if len(sys.argv) != 2:
    print('Usage: monitor urls_file')
    sys.exit()

# text file to get list of urls
urls_file = sys.argv[1]

'''
Step 2. 

Function to parse file input. Cleans up each entry by removing trailing or leading whitespace and obtains the host,port,
and path (if given) and inserts them into a tuple for easier processing when creating sockets connections
'''
parsed_urls = [] #tuple that contains (host,port,path if given)
try:
    # Open the urls_file for reading
    with open(urls_file, 'r') as file:
        # Read each line
        for line in file:
            # Remove leading and trailing whitespace
            line = line.strip()
            cleaned_url = line
            host, port, path = None, None, None

            # Check if the URL starts with 'http://' or 'https://'
            if line.startswith("http://"):
                line = line.replace("http://", "", 1)
                port = 80
            elif line.startswith("https://"):
                line = line.replace("https://", "", 1)
                port = 443

            # Split the line by '/' to separate hostname and path if exists
            parts = line.split('/', 1)
            host = parts[0]
            path = "/" + parts[1] if len(parts) > 1 else None

            # Add the parsed URL to the list
            parsed_urls.append((cleaned_url, host, port, path))
            print("Hostname:", host, "Port:", port, "Path:", path)


except FileNotFoundError:
    print(f"Error: {urls_file} not found")
    sys.exit()

# Step 3
socket_connections = []
for url in parsed_urls:

    # Unpack the tuple and try to establish a connection
    original_url, host, port, path = url
    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=5)
        socket_connections.append(sock)
    except Exception as e:
        print(f'Network Error for entry {line}:\n {e}')
        print(f"URL: {original_url}\nStatus: Network Error")
print(socket_connections)

# # Example below
#
# # server, port, and path should be parsed from url
# host = 'inet.cs.fiu.edu'
# port = 80 # use port 80 for http and port 443 for https
# path = '/temp/fiu.jpg'
#
# sock = None
# # create client socket, connect to server
# try:
#     sock = socket.create_connection((host, port), timeout=5)
# except Exception as e:
#     print(f'Network Error:\n {e}')
#
# if sock:
#     # send http request
#     request = f'GET {path} HTTP/1.0\r\n'
#     request += f'Host: {host}\r\n'
#     request += '\r\n'
#     sock.send(bytes(request, 'utf-8'))
#
#     # receive http response
#     response = b''
#     while True:
#         data = sock.recv(4096)
#         if not data:
#             break
#         response += data
#     print(response.decode('utf-8'))
#     sock.close()

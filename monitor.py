import sys
import socket
import re
import ssl
'''
Helper functions below
'''
# Helper function to parse a URL
def parseUrl(line):
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

    return cleaned_url, host, port, path

# Function to analyze HTTP response status code
def analyze_response_status(response):
    header_end_index = response.find('\r\n\r\n')
    header_str = response[:header_end_index]
    body_str = response[header_end_index + 4:]

    # Split header string into lines
    header_lines = header_str.split('\r\n')

    # Extract status line
    status_line = header_lines[0]

    # Extract headers into a dictionary
    headers = {}
    for line in header_lines[1:]:
        key, value = line.split(': ', 1)
        headers[key] = value

    return status_line, headers, body_str

# Creates a new sock and establishes TCP connection
def createTCPConnection(original_url, host, port):
    sock = None
    # Step 2
    try:
        sock = socket.create_connection((host, port), timeout=5)
        if port == 443:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)
    except Exception as e:
        #Step 3
        print(f"URL: {original_url}\nStatus: Network Error\n")
        return None
    return sock
# Make gets request
def sendGetRequest(sock, path, url):
    #Step 4
    if sock:
        # send http request
        request = f'GET {path} HTTP/1.0\r\n'
        request += f'Host: {host}\r\n'
        request += '\r\n'
        sock.send(bytes(request, 'utf-8'))
        # receive http response
        response = b''
        while True:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                response += data
            except Exception as e:
                print(f"URL: {url}\nResponse: {e}")
                return None
        return response
    return None


# Function to fetch referenced objects (e.g., images)
import re
from urllib.parse import urljoin

def fetch_referenced_objects(html_content, host, original_url):
    # Find all image URLs in the HTML content
    image_urls = re.findall(r'<img[^>]*src\s*=\s*\"([^\"]+)\"', html_content, re.IGNORECASE)

    # Fetch each image URL
    for image_url in image_urls:
        # Fix format and ignore base64 encoded images
        if not image_url or 'base64' in image_url:
            continue

        # Construct absolute URL for the image
        if image_url.startswith(('http://', 'https://')):
            abs_image_url = image_url
        elif image_url.startswith('/'):
            abs_image_url = urljoin(f'http://{host}', image_url)
        else:
            abs_image_url = urljoin(original_url, image_url)

        # Fetch the image
        response = sendGetRequest(createTCPConnection(abs_image_url, host, port), abs_image_url, host)
        if not response:
            continue

        status, headers, body = analyze_response_status(response.decode('utf-8', errors='ignore'))
        print(f"Referenced URL: {abs_image_url}\nStatus: {extract_status_code(status)}")

def extract_status_code(response):
    return ' '.join(response.split(' ', 2)[1:])

'''
End of helper functions
'''
# get urls_file name from command line
if len(sys.argv) != 2:
    print('Usage: monitor urls_file')
    sys.exit()

# text file to get list of urls
urls_file = sys.argv[1]

'''
Parse the urls and create tuple to make them easy to work with
'''
parsed_urls = [] #tuple that contains (host,port,path if given)
try:
    # Open the urls_file for reading
    with open(urls_file, 'r') as file:
        # Read each line
        for line in file:
            tupledData = parseUrl(line)
            parsed_urls.append(tupledData)

except FileNotFoundError:
    print(f"Error: {urls_file} not found")
    sys.exit()

# Go through each url, create a sock and make get request. Handle redirects if neeed
for url in parsed_urls:

    # Unpack the tuple and try to establish a connection
    original_url, host, port, path = url

    # Create TCP connection, if fails, continue to next URL
    sock = createTCPConnection(original_url,host,port)
    if not sock: continue
    # Create HTTP Get request
    response = sendGetRequest(sock, path if path else "/", original_url)
    if response:
        status, headers, body = analyze_response_status(response.decode('utf-8', errors='ignore'))
        print(f"URL: {original_url}\nStatus: {extract_status_code(status)}")
        # Follow any potential redirects
        while '301' in status or '302' in status:
            original_url, host, port, path = parseUrl(headers['Location'])
            sock = createTCPConnection(original_url, host, port)
            response = sendGetRequest(sock, path if path else "/", original_url)
            status, headers, body = analyze_response_status(response.decode('utf-8', errors='ignore'))
            print(f"Redirected URL: {original_url}\nStatus: {extract_status_code(status)}") # formats status to remove extra info
        # extract image objects
        fetch_referenced_objects(body, host, original_url)
    print()
    sock.close()
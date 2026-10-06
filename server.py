import socket
from http import HTTPStatus
from urllib.parse import urlparse, parse_qs

HOST = '127.0.0.1'
PORT = 5000


def parse_status(query):
    """Вернуть код из GET-параметра status, либо 200 если он отсутствует/невалиден."""
    value = parse_qs(query).get('status', [''])[0]
    try:
        code = int(value)
        HTTPStatus(code)
        return code
    except (TypeError, ValueError):
        return 200


def build_response(request, addr):
    lines = request.split('\r\n')
    method, target = lines[0].split(' ', 2)[:2]

    headers = []
    for line in lines[1:]:
        if not line:
            break
        headers.append(line)

    code = parse_status(urlparse(target).query)
    phrase = HTTPStatus(code).phrase

    body_lines = [
        f'Request Method: {method}',
        f'Request Source: {addr}',
        f'Response Status: {code} {phrase}',
        *headers,
    ]
    body = '\r\n'.join(body_lines)

    return (
        f'HTTP/1.1 {code} {phrase}\r\n'
        f'Content-Type: text/plain; charset=utf-8\r\n'
        f'Content-Length: {len(body.encode())}\r\n'
        f'Connection: close\r\n'
        f'\r\n'
        f'{body}'
    )


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen()
        print(f'Echo server listening on {HOST}:{PORT}')
        while True:
            conn, addr = srv.accept()
            with conn:
                data = b''
                while b'\r\n\r\n' not in data:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                if data:
                    response = build_response(data.decode('utf-8', 'replace'), addr)
                    conn.sendall(response.encode())


if __name__ == '__main__':
    main()

import functools
import random
import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)


def retry_on_exception(exc, max_retries: int):
    def _on_exception(method):
        @functools.wraps(method)
        def wrapped(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return method(*args, **kwargs)
                except exc as e:
                    logger.error(f"Method '{method.__qualname__}()' failed with exception '{e}'. "
                                 f"Retrying {max_retries - i} more times.")
            return method(*args, **kwargs)

        return wrapped

    return _on_exception


@retry_on_exception(exc=ConnectionError, max_retries=3)
def send_random_python_program(host: str, port: int):
    with socket.socket() as sock:
        program = f"print({random.randint(1, 1000)})\n"

        logger.info(f"Sending Python program to {(host, port)}: {program.strip()}")

        sock.connect((host, port))
        sock.sendall(program.encode())

        # make sure we get a response
        sock.settimeout(20)
        sock.recv(4096)


def main():
    logging.basicConfig(level=logging.INFO)

    host = "localhost"
    port = 8888

    burst = 10   # number of requests per burst
    delay = 500  # ms between bursts
    count = 10   # number of bursts

    for _ in range(count):
        threads = []
        for _ in range(burst):
            t = threading.Thread(target=lambda: send_random_python_program(host, port))
            t.start()
            threads.append(t)
        time.sleep(delay / 1000)
        for t in threads:
            t.join()


if __name__ == "__main__":
    main()

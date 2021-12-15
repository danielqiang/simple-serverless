import logging
import random
import socket
import socketserver
import threading

from serverless.worker import Worker

logger = logging.getLogger(__name__)


class _LoadBalancerHandler(socketserver.StreamRequestHandler):
    def __init__(self, workers: list[Worker], *args, **kwargs):
        self.workers = workers
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        source = self.rfile.readline().strip()
        worker = random.choice(self.workers)

        logger.info(
            f"Forwarding source code to worker {(worker.host, worker.port)}: {source}"
        )
        with socket.socket() as s:
            s.connect((worker.host, worker.port))
            s.sendall(source + b"\n")

            # make sure we get a response
            s.recv(4096)

        self.wfile.write(b"\n")


class LoadBalancer:
    def __init__(self, host: str, port: int, workers: list[Worker], request_queue_size: int = 5):
        self.host = host
        self.port = port
        self.workers = workers
        self.server = socketserver.ThreadingTCPServer(
            (host, port),
            lambda *args, **kwargs: _LoadBalancerHandler(workers, *args, **kwargs),
        )
        self.server.request_queue_size = request_queue_size

    def run(self):
        logger.info(f"Starting load balancer on {(self.host, self.port)}")

        for worker in self.workers:
            threading.Thread(target=worker.run).start()
        self.server.serve_forever()

    def shutdown(self):
        for worker in self.workers:
            worker.shutdown()
        self.server.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.shutdown()

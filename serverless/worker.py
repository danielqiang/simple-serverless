import logging
import socketserver

from serverless.function import ServerlessPythonFunction

logger = logging.getLogger(__name__)


class _WorkerHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        with ServerlessPythonFunction(
            source=self.rfile.readline().strip().decode()
        ) as function:
            function.run()
        self.wfile.write(b"\n")


class Worker:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        self.server = socketserver.ThreadingTCPServer((host, port), _WorkerHandler)

    def run(self):
        logger.info(f"Starting worker on {(self.host, self.port)}")
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

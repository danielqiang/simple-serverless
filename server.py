import logging

from serverless.load_balancer import LoadBalancer
from serverless.worker import Worker


def main():
    logging.basicConfig(level=logging.INFO)

    with LoadBalancer(
        host="localhost",
        port=8888,
        workers=[
            Worker("localhost", 8789),
            Worker("localhost", 8790),
            Worker("localhost", 8791),
            Worker("localhost", 8792),
        ],
        request_queue_size=100
    ) as load_balancer:
        load_balancer.run()


if __name__ == "__main__":
    main()

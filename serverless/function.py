# make temporary directory
# generate dockerfile
# build docker image, capture image id
# create container, run image, redirect image stdout to file, delete container, delete image
# delete temporary directory

import logging
import pathlib
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def subprocess_run(commands, *args, **kwargs):
    logger.info(f"Executing command: {' '.join(commands)}")
    subprocess.run(commands, *args, **kwargs)


class ServerlessPythonFunction:
    _SOURCE_FILENAME = "temp.py"
    _DOCKER_IMAGE_ID_FILENAME = "image_id.txt"

    def __init__(self, source: str):
        self.source = source
        self._tempdir = tempfile.TemporaryDirectory(dir=".")
        # set by build_image()
        self._image_id = None

    @property
    def tempdir(self):
        return pathlib.Path(self._tempdir.name)

    def build_image(self):
        # write temp script file
        with open(self.tempdir / self._SOURCE_FILENAME, "w") as f:
            f.write(self.source)

        # write dockerfile
        dockerfile_contents = f"""FROM python:latest
WORKDIR /usr/app/src
COPY {self._SOURCE_FILENAME} ./
CMD [ "python", "{self._SOURCE_FILENAME}"]"""

        with open(self.tempdir / "Dockerfile", "w") as f:
            f.write(dockerfile_contents)

        # build image
        image_id_fpath = self.tempdir / self._DOCKER_IMAGE_ID_FILENAME
        subprocess_run(
            [f"docker build ./{self.tempdir.name} --iidfile {image_id_fpath}"],
            shell=True,
        )

        with open(image_id_fpath) as f:
            self._image_id = f.read()

    def run_image(self, outfile: str = None):
        if outfile:
            command = f"docker run --rm {self._image_id} > {outfile}"
        else:
            command = f"docker run --rm {self._image_id}"
        subprocess_run([command], shell=True)

    def run(self, outfile: str = None):
        self.tempdir.mkdir(parents=True, exist_ok=True)

        self.build_image()
        self.run_image(outfile=outfile)

    def cleanup(self):
        subprocess_run([f"docker rmi {self._image_id}"], shell=True)

        self._tempdir.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()


def main():
    source = """print("hello")
print("goodbye")
    """
    with ServerlessPythonFunction(source=source) as func:
        func.run()


if __name__ == "__main__":
    main()

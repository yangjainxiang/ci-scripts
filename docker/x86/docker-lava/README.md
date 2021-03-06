# Linaro's Automated Validation Architecture (LAVA) Docker Container
Preinstalls and preconfigures the latest LAVA server release.

## Building
To build an image locally, execute the following from the directory you cloned the repo:

```
sudo docker build -t [your_docker_registry]/kernelci/lava .
```

## Running
To run the image from a host terminal / command line execute the following:

```
sudo docker run -it \
                -v ~/huawei/tftp/:/var/lib/lava/dispatcher/tmp/  \
                -p 80:80 -p 5555:5555 -p 5556:5556 \
                -p 69:69/udp \
                -h <HOSTNAME> --privileged \
                [your_docker_registry]/kernelci/lava:latest
```
Where HOSTNAME is the hostname used during the container build process (check the docker build log), as that is the name used for the worker configuration. You can use `lava-docker` as the pre-built container hostname.

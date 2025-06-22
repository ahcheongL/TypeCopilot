FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir -p /root/typecopilot
COPY src /root/typecopilot/src
COPY script /root/typecopilot/script
COPY bc /root/typecopilot/bc
COPY groundtruth /root/typecopilot/groundtruth
COPY Makefile /root/typecopilot/Makefile
COPY CMakeLists.txt /root/typecopilot/CMakeLists.txt
COPY mlta /root/mlta

RUN apt update && apt install -y build-essential cmake wget python3 python3-pip git

RUN pip3 install tabulate pyyaml --break-system-packages

RUN python3 /root/typecopilot/script/llvm.py get 16
RUN python3 /root/typecopilot/script/llvm.py get 14

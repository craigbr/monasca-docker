from alpine:3.5

run apk add --no-cache py2-pip py2-yaml && \
    pip install dpath dotmap urllib3 ipaddress requests

add kubernetes.py check.py /

cmd ["python", "/check.py"]

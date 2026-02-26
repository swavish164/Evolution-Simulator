FROM ubuntu:latest
LABEL authors="swavish"

ENTRYPOINT ["top", "-b"]
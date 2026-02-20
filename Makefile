.PHONY: login build push all

-include .env
export

login:
	docker login --username $(DOCKER_USERNAME) --password $(DOCKER_PASSWORD) ghcr.io

build:
	docker buildx build --platform linux/amd64,linux/arm64 --no-cache -t ghcr.io/voyzark/beerbot:latest .

push:
	docker push ghcr.io/voyzark/beerbot:latest

all: login build push

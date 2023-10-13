---
component-id: facets-search-engine
name: Facets Music Search Engine
brief-description: "a faceted search-engine for musical documents"
type: Application
release-date: 2022-04-14
release-number: 0.5
work-package: WP1
pilot: FACETS
keywords:
  - "information retrieval"
  - "search engine"
changelog:
licence: GNU GPLv3
release link: 
image:
logo:
demo: http://neuma-dev.huma-num.fr
links: 
  - http://neuma.huma-num.fr
running-instance:
credits: CNAM vertigo Team
related-components:
bibliography: n/a
---

# Facets Music Search Engine

[![DOI](https://zenodo.org/badge/426643864.svg)](https://zenodo.org/badge/latestdoi/426643864)

This repository is dedicated to the Docker image of the FACETS pilot, focusing on the development of a faceted search-engine for musical documents. 

A demo version is live on the [HumaNum platform](http://neuma-dev.huma-num.fr), and an older version powers the search on the [NEUMA platform](http://neuma.huma-num.fr).

## Running with Docker

````
$ git clone https://github.com/polifonia-project/facets-search-engine.git
$ cd facets-search-engine
$ docker-compose up --build
````
Leave the terminal open, wait a bit so that Django and ElasticSearch are up.
Then go to [http://0.0.0.0:8000](http://0.0.0.0:8000).

Alternatively, one can use `$ docker-compose up --build -d` (notice the `-d`, for detaching), then use `docker logs Facets-WEB -f` or `docker logs Facets-ES -f` to view logs for the web app or Elasticsearch respectively.

## Running Django

````
$ git clone https://github.com/polifonia-project/facets-search-engine.git
$ cd facets-search-engine/facets
$ python -m venv venv
$ source venv/bin/activate
$ pip install -r requirements-versions.txt
$ mkdir staticfiles
$ sudo docker start facets-es # or any other ElasticSearch start method
$ python manage.py migrate
$ python manage.py runserver
````

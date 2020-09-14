#!/usr/bin/env bash


docker run --rm -p 5432:5432 -e POSTGRES_DB=atomresponder -e POSTGRES_USER=atomresponder -e POSTGRES_PASSWORD=atomresponder postgres:9.6
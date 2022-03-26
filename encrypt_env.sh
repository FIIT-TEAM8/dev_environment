#!/bin/bash

tar cz remote.env | openssl enc -aes-256-cbc -pbkdf2 -e -pass "pass:${1}" > remote.env.tar.gz.enc
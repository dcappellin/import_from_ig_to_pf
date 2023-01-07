#!/bin/bash

PRODUCTION_ENV_FILENAME=prod.env

if [ ! -f "$PRODUCTION_ENV_FILENAME" ]; then
    echo 'PIXELFED_API_TOKEN='`op item get 'Pixelfed API token' --field label=username` > $PRODUCTION_ENV_FILENAME
fi
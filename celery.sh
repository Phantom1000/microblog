#!/bin/bash
exec celery -A make_celery.celery_app worker --loglevel INFO
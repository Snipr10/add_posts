#!/bin/bash
celery -A add_posts multi stop workert1 -B
celery -A add_posts multi stop workert2 -B
celery -A add_posts multi stop workert3 -B
celery -A add_posts multi stop workert4 -B
celery -A add_posts multi stop workert5 -B

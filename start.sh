#!/bin/bash
celery -A add_posts multi start workert1 -B
celery -A add_posts multi start workert2 -B
celery -A add_posts multi start workert3 -B
celery -A add_posts multi start workert4 -B
celery -A add_posts multi start workert5 -B

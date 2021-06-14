# Makefile for an afinidata django service
# Modified from https://github.com/DS3Lab/easeml

# Paths to the parent directory of this makefile and the repo root directory.
MY_DIR_PATH := $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
ROOT_DIR_PATH := $(realpath $(MY_DIR_PATH)../..)

# Make functionality for this service
include $(ROOT_DIR_PATH)/dev/makefiles/services/django.mk

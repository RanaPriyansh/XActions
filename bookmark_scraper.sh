#!/bin/bash
dir=~/projects/XActions
cd $dir
xactions login
xactions get bookmarks @breadbaked_ > ~/obsidian-hermes-vault/bookmarks/bread-baked-bookmarks.md

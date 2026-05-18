#!/bin/bash
termux-wake-lock
cd ~/march7thassistant
proot-distro run march7thassistant \
  --bind config.yaml:/m7a/config.yaml \
  --bind logs:/m7a/logs \
  --bind 3rdparty/WebBrowser/UserProfile:/m7a/3rdparty/WebBrowser/UserProfile \
  --env MARCH7TH_AFTER_FINISH=Exit \
  --env MARCH7TH_LOG_LEVEL=DEBUG
# 取消注释下行以执行子任务，同时需在上一行末尾添加 \
# -- python main.py daily

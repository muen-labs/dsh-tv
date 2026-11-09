REPO := $(shell cd "$(dir $(lastword $(MAKEFILE_LIST)))" && pwd)

.PHONY: all apk shim install-apk install-shim daemon plugin pet-assets clean

all: apk shim

apk:
	bash android/tv-assistant/build.sh

shim:
	bash android/disney-shim/build.sh

install-apk: apk
	adb install -r -g android/tv-assistant/TVAssistant.apk
	adb shell pm grant com.jp.dshtv android.permission.RECORD_AUDIO

install-shim: shim
	adb install -r -g android/disney-shim/DisneyShim.apk

daemon:
	python3 host/whale_voice.py --serve --port 8766

plugin:
	./plugin/install.sh desktop

pet-assets:
	bash android/tv-assistant/make-pet-assets.sh

clean:
	rm -rf android/*/gen android/*/obj android/*/dex android/*/compiled \
	       android/*/unsigned.apk android/*/aligned.apk android/*/sources.txt android/*/classes.txt

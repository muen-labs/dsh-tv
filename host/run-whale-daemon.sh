#!/bin/zsh
# Run the voice daemon outside any agent sandbox (launchd), so its DSH child
# can start its own bash sandbox and drive the TV.
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export DSH_HOME="$HOME/.dsh"
export WHALE_REPO="/Volumes/External SSD/iptv/dsh-tv"
cd "/Volumes/External SSD/iptv/dsh-tv" || exit 1
exec /Users/thuypham/miniconda3/bin/python3 host/whale_voice.py --serve --port 8766

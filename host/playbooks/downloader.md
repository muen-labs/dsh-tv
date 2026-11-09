# Downloader — playbook

Package `com.esaba.downloader` · component `com.esaba.downloader/.ui.main.MainActivity`
Role: download/install APKs or files from a URL (sideloading).

## Flow
1. Launch; focus the **URL** field (OK opens keyboard) and type the direct link.
2. **Download** → wait; the APK opens the installer automatically (or select it
   in the file list).
3. Allow "install unknown apps" when prompted (Settings → Apps → Downloader).

## Notes
- Long URLs: type carefully or use Send Files To TV / adb install instead.
- Only install APKs the user explicitly asked for; check the package with
  `adb shell pm list packages` afterwards.

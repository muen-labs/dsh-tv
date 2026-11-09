# Projectivy Launcher — playbook

Package `com.spocky.projengmenu` · component `com.spocky.projengmenu/.ui.home.MainActivity`
Role: alternative TV launcher (home layout, dock, wallpapers, app hiding).

## Navigation
- Home: D-pad moves between rows/dock; OK opens; MENU/LEFT opens the launcher menu.
- Settings: gear tile or MENU → Settings; sections for Appearance, Dock, Apps,
  Wallpaper, Screensaver.

## Notes
- HOME should open **Google TV** (`com.google.android.apps.tv.launcherx`); launch
  Projectivy explicitly when the user asks for it.
- Icon/label changes may not refresh until Projectivy is force-stopped/rebooted.
- "Prevent system screensaver" in Projectivy can keep the TV awake — toggle it
  when the screensaver disappears.

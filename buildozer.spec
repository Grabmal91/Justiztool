[app]

# (str) Title of your application
title = JustizTool

# (str) Package name
package.name = justiztool

# (str) Package domain (needed for android/ios packaging)
package.domain = com.github.grabn

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,kv,atlas,db

# (list) Application version number
version = 2.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.1,requests,beautifulsoup4

# (str) Presplash of the application
presplash.filename = %(source.dir)s/presplash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/icon.png

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 21

# (list) Android architectures to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) Android NDK version
android.ndk = 23b

# (bool) Use Android SDK Tools
android.skip_update = False

# (str) Android SDK directory (leer lassen für auto-download)
android.sdk_path =

# (str) Android NDK directory (leer lassen für auto-download)
android.ndk_path =

[buildozer]

# (int) Log level
log_level = 2

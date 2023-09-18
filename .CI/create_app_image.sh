#! /bin/bash

# store repo root as variable

# build project and install files into AppDir

rm -r "./AppDir"

# now, build AppImage using linuxdeploy and linuxdeploy-plugin-qt
# download linuxdeploy and its Qt plugin
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget https://github.com/AppImage/AppImageKit/releases/download/12/appimagetool-x86_64.AppImage

# make them executable
chmod +x linuxdeploy-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage

# QtQuickApp does support "make install", but we don't use it because we want to show the manual packaging approach in this example
# initialize AppDir, bundle shared libraries, add desktop file and icon, use Qt plugin to bundle additional resources, and build AppImage, all in one command
./linuxdeploy-x86_64.AppImage --appdir AppDir \
  -e ./dist/ethz-document-fetcher/ethz-document-fetcher \
  -i ./dist/ethz-document-fetcher/gui/assets/logo/logo.svg \
  --icon-filename ethz-document-fetcher \
  --create-desktop-file

cp ./.CI/ethz-document-fetcher.desktop ./AppDir/usr/share/applications/ethz-document-fetcher.desktop
cp ./dist/ethz-document-fetcher/* ./AppDir -r
rm ./AppDir/ethz-document-fetcher

./appimagetool-x86_64.AppImage ./AppDir ethz-document-fetcher-linux-x86_64.AppImage


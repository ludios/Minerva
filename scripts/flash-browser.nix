# A browser that can still run Minerva's Flash socket transport, for
# tests/test_flash.py: Pale Moon (which keeps NPAPI plugin support) with the
# real Adobe Flash Player plugin, plus Xvfb to run it headless.
#
#   nix-build scripts/flash-browser.nix -o ../flash-browser
#
# makes ../flash-browser/bin/{palemoon,Xvfb}.  Flash Player 32.0.0.371 is the
# last release without Adobe's kill switch (from 2021-01-12, later releases
# refuse to run content).  Adobe's download site is gone, so the plugin comes
# from the Wayback Machine, checked against the hash nixpkgs pinned in 2020
# (commit d8fa222).
let
  # nixos-26.05: still has GTK2, which the Flash plugin links against.
  nixpkgs = fetchTarball {
    url = "https://github.com/NixOS/nixpkgs/archive/cf5e76507c6e23b59f7e0ffcc7baa2a39ddd8442.tar.gz";
    sha256 = "sha256-F+b8u43BVF5DlM0pz7JQSbtbwKy5PrHIT5zQUekXsD0=";
  };
  pkgs = import nixpkgs {
    config = { };
    overlays = [ ];
  };
  inherit (pkgs) lib stdenv;

  flashplayer = stdenv.mkDerivation {
    pname = "flashplayer";
    version = "32.0.0.371";

    src = pkgs.fetchurl {
      url = "https://web.archive.org/web/2020id_/https://fpdownload.adobe.com/get/flashplayer/pdc/32.0.0.371/flash_player_npapi_linux.x86_64.tar.gz";
      sha256 = "1zc90gjixfhjng7pbx8vci1l69wf5m40149178zwzs6kz4ma5hb2";
    };
    sourceRoot = ".";

    dontStrip = true;
    dontPatchELF = true;
    preferLocalBuild = true;

    # Besides its DT_NEEDED libraries, the plugin dlopen()s audio, curl,
    # udev, and VDPAU libraries.
    installPhase = ''
      install -Dm644 libflashplayer.so $out/lib/mozilla/plugins/libflashplayer.so
      patchelf --set-rpath ${
        lib.makeLibraryPath (
          with pkgs;
          [
            stdenv.cc.cc
            alsa-lib
            curl
            fontconfig
            freetype
            gdk-pixbuf
            glib
            gtk2-x11
            libglvnd
            libpulseaudio
            libvdpau
            libx11
            libxt
            nspr
            nss
            pango
            udev
          ]
        )
      } $out/lib/mozilla/plugins/libflashplayer.so
    '';
  };

  # Like nixpkgs' palemoon-gtk2-bin (removed after 26.05), but a newer
  # release, from Pale Moon's archive so that the URL stays put.
  palemoon = stdenv.mkDerivation {
    pname = "palemoon";
    version = "35.0.1";

    src = pkgs.fetchzip {
      url = "https://archive.palemoon.org/palemoon/35.x/35.0.1/Linux/palemoon-35.0.1.linux-x86_64-gtk2.tar.xz";
      hash = "sha256-DhdkWP37sqbCVqXme4hbe/bni3LfZ2zC8EDpH82y/dw=";
    };

    nativeBuildInputs = with pkgs; [
      autoPatchelfHook
      wrapGAppsHook3
    ];
    buildInputs = with pkgs; [
      alsa-lib
      gtk2-x11
      libxt
      (lib.getLib stdenv.cc.cc)
    ];

    dontConfigure = true;
    dontBuild = true;
    preferLocalBuild = true;

    installPhase = ''
      mkdir -p $out/{bin,lib/palemoon}
      cp -R * $out/lib/palemoon/
      ln -s $out/lib/palemoon/palemoon $out/bin/palemoon
    '';

    dontWrapGApps = true;
    preFixup = ''
      gappsWrapperArgs+=(
        --prefix LD_LIBRARY_PATH : ${
          lib.makeLibraryPath [
            pkgs.libglvnd
            pkgs.libpulseaudio
          ]
        }
        --set MOZ_PLUGIN_PATH ${flashplayer}/lib/mozilla/plugins
      )
      wrapGApp $out/lib/palemoon/palemoon
    '';
  };
in
pkgs.symlinkJoin {
  name = "minerva-flash-browser";
  paths = [
    palemoon
    pkgs.xvfb
  ];
}

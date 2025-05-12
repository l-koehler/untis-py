{
  description = "WebUntis Desktop App";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # custom webuntis and python-dateutil, as these aren't packaged
        python-with-overrides = pkgs.python3.override {
          packageOverrides = pyfinal: pyprev: {
            webuntis = pyfinal.callPackage ./webuntis.nix {};
            "python-dateutil" = pyfinal.callPackage ./python-dateutil.nix {};
          };
        };

        pyPkgs = python-with-overrides.pkgs;

        pyDeps = with pyPkgs; [
          pyqt6
          requests
          webuntis
          python-dateutil
          # indirect deps
          six
        ];
      in {
        packages.untis-py = pyPkgs.buildPythonApplication {
          pname = "untis-py";
          version = "1.1.0";
          src = ./.;
          format = "setuptools";
          propagatedBuildInputs = pyDeps;

          installPhase = ''
            runHook preInstall
            python setup.py install --prefix=$out

            # entrypoints are fucked somehow
            # fix that
            mkdir -p $out/bin
            echo '#!/bin/sh' > $out/bin/untis
            echo 'python -m untis_py.main "$@"' >> $out/bin/untis
            chmod +x $out/bin/untis

            mkdir -p $out/share/applications
            cp ${./untis-py.desktop} $out/share/applications/

            mkdir -p $out/share/icons/hicolor/48x48/apps
            cp ${./untis_py/icons/icon.png} $out/share/icons/hicolor/48x48/apps/untis-py.png
            mkdir -p $out/share/icons/hicolor/scalable/apps
            cp ${./untis_py/icons/icon.svg} $out/share/icons/hicolor/scalable/apps/untis-py.svg

            runHook postInstall
          '';

          meta = {
            description = "WebUntis Desktop App";
            homepage = "https://github.com/l-koehler/untis-py";
            license = pkgs.lib.licenses.gpl3Only;
          };
        };

        apps.untis-py = flake-utils.lib.mkApp {
          drv = self.packages.${system}.untis-py;
        };

        defaultPackage = self.packages.${system}.untis-py;
        defaultApp = self.apps.${system}.untis-py;

        devShell = pkgs.mkShell {
          packages = [
            (python-with-overrides.withPackages (_: pyDeps))
          ];
        };
      });
}

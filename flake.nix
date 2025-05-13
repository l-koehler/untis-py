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
          hatchling
          six
        ];
      in {
        packages.untis_py = pyPkgs.buildPythonPackage {
          pname = "untis_py";
          version = "1.1.0";
          src = ./.;
          format = "pyproject";
          propagatedBuildInputs = pyDeps;

          installPhase = ''
            runHook preInstall
            python3 -m pip install . --prefix=$out

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

        apps.untis_py = flake-utils.lib.mkApp {
          drv = self.packages.${system}.untis_py;
        };

        defaultPackage = self.packages.${system}.untis_py;
        defaultApp = self.apps.${system}.untis_py;

        devShell = pkgs.mkShell {
          packages = [
            (python-with-overrides.withPackages (_: pyDeps))
          ];
        };
      });
}

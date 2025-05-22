{
  description = "WebUntis Desktop App";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);

        project = pyproject.project;

        python-with-overrides = pkgs.python3.override {
          packageOverrides = pyfinal: pyprev: {
            webuntis = pyfinal.callPackage ./webuntis.nix {};
            "python-dateutil" = pyfinal.callPackage ./python-dateutil.nix {};
          };
        };

        package = pkgs.python3Packages.buildPythonPackage {
          pname = project.name;
          inherit (project) version;
          format = "pyproject";
          src = ./.;

          build-system = with pkgs.python3Packages; [
            setuptools
          ];

          propagatedBuildInputs = [
            pkgs.python3Packages.pyqt6
            pkgs.python3Packages.requests
            pkgs.python3Packages.six
            python-with-overrides.pkgs.webuntis
            python-with-overrides.pkgs.python-dateutil
            pkgs.qt6.full
          ];
        };

        editablePackage = pkgs.python3.pkgs.mkPythonEditablePackage {
          pname = project.name;
          inherit (project) scripts version;
          root = "$PWD";
        };
      in
      {
        packages = {
          "${project.name}" = package;
          default = self.packages.${system}.${project.name};
        };

        devShells = {
          default = pkgs.mkShell {
            inputsFrom = [
              package
            ];
            buildInputs = [
              editablePackage
            ];
          };
        };
      });
}

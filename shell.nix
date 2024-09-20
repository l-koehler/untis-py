with import <nixpkgs> {};

pkgs.mkShell {
  packages = [
    pkgs.python312
    pkgs.python312Packages.pip
    pkgs.python312Packages.pyqt6
  ];
  # 'webuntis' and 'py-dateutil' are not packaged for Nix
  shellHook = ''
    python -m venv .venv
    source .venv/bin/activate
    pip install webuntis py-dateutil
  '';
}

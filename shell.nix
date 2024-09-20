let
  pkgs = import <nixpkgs> {};

  python = pkgs.python3.override {
    self = python;
    packageOverrides = pyfinal: pyprev: {
      webuntis = pyfinal.callPackage ./webuntis.nix { };
      py-dateutil = pyfinal.callPackage ./python-dateutil.nix { };
    };
  };

in pkgs.mkShell {
  packages = [
    (python.withPackages (python-pkgs: [
      python-pkgs.pyqt6
      python-pkgs.webuntis
      python-pkgs.requests
      python-pkgs.python-dateutil
    ]))
  ];
}

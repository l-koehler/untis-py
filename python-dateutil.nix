{ lib, buildPythonPackage, fetchFromGitHub, setuptools, wheel, python }:

buildPythonPackage rec {
  pname = "python-dateutil";
  version = "2.9.0.post0";

  src = fetchFromGitHub {
    owner = "dateutil";
    repo = "dateutil";
    rev = "1ae807774053c071acc9e7d3d27778fba0a7773e";
    hash = "sha256-YaA/MeXwXbc6NNrNf52Ol9Z8eI+z6EXQW/vvrzBlYSo=";
  };

  nativeBuildInputs = [
    setuptools
    wheel
    python.pkgs.pip
    python.pkgs.setuptools_scm
  ];

  doCheck = false;

  meta = with lib; {
    description = "Useful extensions to the standard Python datetime features";
    homepage = "https://github.com/dateutil/dateutil";
    license = licenses.asl20; # apache 2
  };
}

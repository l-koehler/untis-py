{ lib
, buildPythonPackage
, fetchPypi
, setuptools
, wheel
, pkgs
}:

buildPythonPackage rec {
  pname = "webuntis";
  version = "0.1.23";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-kZepJC5VxvcqsCYaG1scYAFts1NMhDwdoRHoZIF+Xzc=";
  };


  buildInputs = [ pkgs.python3Packages.requests ];

  # do not run tests
  doCheck = false;

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  build-system = [
    setuptools
    wheel
  ];
}

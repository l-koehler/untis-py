{ lib
, buildPythonPackage
, fetchPypi
, setuptools
, wheel
}:

buildPythonPackage rec {
  pname = "python-dateutil";
  version = "2.9.0.post0";

  src = fetchPypi {
    inherit pname version;
    hash = "sha256-kZepJC5VxvcqsCYaG1scYAFts1NMhDwdoRHoZIF+Xzc=";
  };


  buildInputs = [  ];

  # do not run tests
  doCheck = false;

  # specific to buildPythonPackage, see its reference
  pyproject = true;
  build-system = [
    setuptools
    wheel
  ];
}

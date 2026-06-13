{ pkgs }: {
  deps = [
    # Core Python environment
    pkgs.python3
    pkgs.python3Packages.pip

    # C Toolchain required to compile the Levenshtein library
    pkgs.gcc
    pkgs.gnumake
    pkgs.python3Packages.setuptools

    # Native development libraries
    pkgs.libffi
    pkgs.openssl
  ];

  # Inject environment variables so Python can easily find compilers during pip install
  env = {
    PYTHONPATH = "";
  };
}
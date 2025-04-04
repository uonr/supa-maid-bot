{
  description = "My universal personal assistant";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonPackages =
          ps:
          with ps;
          (
            [
              setuptools
              python-telegram-bot
              python-dotenv
              black
              httpx
            ]
            ++ python-telegram-bot.optional-dependencies.job-queue
          );

        bot = pkgs.python3Packages.buildPythonApplication {
          pname = "supa-maid-bot";
          version = "0.1.0";
          src = ./.;
          buildInputs = [ pkgs.gallery-dl ];
          propagatedBuildInputs = (pythonPackages pkgs.python3.pkgs) ++ [ pkgs.gallery-dl ];
          nativeBuildInputs = [ pkgs.pkg-config ];
          PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
        };
      in
      {
        packages.default = bot;

        apps.default = {
          type = "app";
          program = "${bot}/bin/supa-maid-bot";
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            (pkgs.python3.withPackages pythonPackages)
            pkgs.yt-dlp
            pkgs.gallery-dl
          ];
          nativeBuildInputs = [ pkgs.pkg-config ];
          PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
        };
      }
    );
}

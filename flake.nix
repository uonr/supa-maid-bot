{
  description = "My universal personal assistant";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3.withPackages (p:
          with p; [
            python-telegram-bot
            python-dotenv
            black
            tweepy
            httpx
            (buildPythonPackage {
              pname = "PixivPy3";
              version = "3.7.2";
              src = pkgs.fetchFromGitHub {
                owner = "upbit";
                repo = "pixivpy";
                rev = "7b20c3bd158d10238d27135309525946d39bdbe4";
                hash = "sha256-trCb//nFEhRt7V2BXY90tqmdZ7UWwAbzurtKDd0IA9k=";
              };
              doCheck = false;
              propagatedBuildInputs = with pkgs.python3Packages; [
                cloudscraper
                requests
                requests-toolbelt
                typing-extensions
              ];
            })
          ]);
      in with pkgs; {
        devShells.default = mkShell {
          buildInputs = [ python you-get ];
          nativeBuildInputs = [ pkgs.pkg-config ];
          PKG_CONFIG_PATH = "${pkgs.openssl.dev}/lib/pkgconfig";
          shellHook = ''
            PYTHONPATH=${python}/${python.sitePackages}
          '';
        };
      });
}

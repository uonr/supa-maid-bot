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
        python = pkgs.python3.withPackages
          (p: with p; [ python-telegram-bot python-dotenv black tweepy httpx ]);
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

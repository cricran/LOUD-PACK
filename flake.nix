{
  description = "Development environment for Minecraft Loud Pack automation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python3.withPackages (
        ps: with ps; [
          requests
        ]
      );
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [
          pythonEnv
          pkgs.sox
          pkgs.zip
        ];

        shellHook = ''
          echo "Loud Pack dev environment loaded."
          echo "Python $(python --version)"
          echo "SoX version: $(sox --version | grep -o 'v[0-9].*')"
        '';
      };
    };
}

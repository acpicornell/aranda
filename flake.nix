{
  description = "aranda — digital edition of the 1768 Aranda census (Balearic section)";

  # nixpkgs pinned (see flake.lock) to the same revision as the sibling
  # ../../mapes/mut flake, so the Corpus Balear projects share one toolchain.
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/f205b5574fd0cb7da5b702a2da51507b7f4fdd1b";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" "aarch64-linux" ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f (import nixpkgs { inherit system; }));
    in
    {
      # Reproducible shell for the data-analysis tooling. `xlrd` reads the legacy
      # .xls tables IBESTAT exports (see scripts/ibestat_crosscheck.py); the rest
      # of the cross-check uses only the Python standard library.
      #
      # The heavy extraction pipeline (duckdb, anthropic, pillow, …) still runs
      # via `uv` against pyproject.toml — that is vision/LLM work that needs API
      # keys and is not reproduced here. This shell covers the offline analysis.
      devShells = forAllSystems (pkgs: {
        default = pkgs.mkShell {
          packages = [
            (pkgs.python3.withPackages (ps: with ps; [
              xlrd     # parse legacy .xls (BIFF) IBESTAT exports
              pillow   # crop/zoom page images for the manual prose review (scripts/crop_page.py)
            ]))
          ];
        };
      });
    };
}

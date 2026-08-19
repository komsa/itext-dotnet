# CLAUDE.md

Guidance for working in this repository.

## What this repo is

A KOMSA fork of [iText Core for .NET](https://github.com/itext/itext-dotnet) (AGPL v3 /
commercial dual license), living at `https://github.com/komsa/itext-dotnet`.

- `develop` tracks upstream. `Komsa/develop` carries the KOMSA changes. Feature branches
  (e.g. `Feature/Branding`) branch off `Komsa/develop`.
- The rebranding work and its rationale are written up in `issues/komsa-branding.md`. Read that
  before touching versioning, packaging or the producer line.
- `port-hash` records the upstream Java commit this .NET port was generated from. Leave it alone.

Keep the diff against upstream small. Every KOMSA change is a future merge conflict, so prefer
the narrow fix over the tidy refactor.

## Commits: Claude commits, Jan signs

All commits must end up GPG-signed and authored by **Jan Friedrich <freeandnil@apache.org>**
(key `583E491578F02D5D`). The private key is not reachable from the account Claude runs as, so:

- Commit with signing disabled for that one command:
  ```
  git -c commit.gpgsign=false commit -m "..."
  ```
  The repo sets `commit.gpgsign=true` locally, so a plain `git commit` fails with
  `No secret key` — that is deliberate, not a misconfiguration.
- **Never push.** Before a push is due, ask Jan to sign and hand him:
  ```
  git rebase --exec "git commit --amend --no-edit --reset-author -S" Komsa/develop
  ```
- End commit messages with the `Co-Authored-By: Claude ...` trailer as usual.

## Build

```
dotnet build iTextCore.sln -c Release
```

.NET 10 SDK. Libraries target **`netstandard2.0`**, tests **`net10.0`**. `net461` was removed
deliberately — do not reintroduce it.

## Test

Ghostscript and ImageMagick are **not installed** here, and the visual-comparison tests are not
relevant to this fork. Always run with the filter:

```
dotnet test iTextCore.sln -c Release --settings komsa.runsettings
```

In Visual Studio: *Test > Configure Run Settings > Select Solution Wide runsettings File*.

`komsa.runsettings` documents exactly what it excludes and why. Without it you get ~26 failures
that have nothing to do with your change.

Two things that will bite you:

- **Run assemblies sequentially when a green result matters.** A solution-wide `dotnet test`
  runs all 13 assemblies in parallel and can exhaust memory on this machine, producing
  `OutOfMemoryException` in BouncyCastle static init, `Insufficient system resources` from
  veraPDF, and network timeouts. These look alarming and are not regressions — re-run the
  affected project on its own before believing a failure.
- **`itext.brotli-compressor` and its test project are not in `iTextCore.sln`.** A solution-wide
  build or test run never covers them. Build them explicitly.

`CompareTool.CompareByContent` falls back to visual comparison on *any* mismatch, so a failing
content comparison reports a Ghostscript error rather than the real diff. Green runs are
trustworthy; diagnosing a red one needs Ghostscript installed.

## Version: one place only

`KomsaVersion` in the **repo-root `Directory.Build.props`** is the single source of truth. Do not
write a version literal anywhere else. It flows to:

| Consumer | Mechanism |
|---|---|
| Assembly attributes | `VersionPrefix` / `FileVersion` / `InformationalVersion` |
| `CommonsProductData.COMMONS_VERSION` | generated `KomsaBuildInfo.g.cs`, target in `itext/Directory.Build.targets` |
| `ITextCoreProductData.CORE_VERSION` | the same constant, via commons' `InternalsVisibleTo` on kernel |
| `itext.nuspec` | `$version$` token, supplied by `PackNugetFiles.ps1` |
| `PushNugetFiles.ps1` | reads `KomsaVersion` from the root props |

`AssemblyVersion` is pinned at `9.0.0.0` and does **not** track the release version, so servicing
rebuilds keep one binding identity.

`itext/Directory.Build.props` and `itext.tests/Directory.Build.props` **explicitly import** the
root file. MSBuild only auto-imports the nearest `Directory.Build.props`, so a nested one shadows
the root unless it imports upward. Don't remove those imports.

## Packaging

Nine packages, all `Komsa.*`, output to `artifacts/nuget`:

- **`Komsa.itext`** — the bundle, 11 assemblies in one package, still driven by the hand-written
  `itext.nuspec` (this is why it can't use `GeneratePackageOnBuild`).
- **8 module packages** — `commons`, `bouncy-castle-adapter`, `bouncy-castle-fips-adapter`,
  `brotli-compressor`, `pdftest`, `webp-image-support`, `font-asian`, `hyph` — via
  `GeneratePackageOnBuild` and `PackageId` in each `.csproj`.

```
powershell -File PackNugetFiles.ps1     # builds Release + packs bundle and modules
powershell -File PushNugetFiles.ps1     # pushes to the internal Azure DevOps feed
```

Packing the bundle needs `nuget.exe` at `D:\Git\TeamFoundation\Binaries\Stable\nuget.exe`
(`dotnet pack` cannot pack a standalone nuspec).

## Traps, all of which have already caused a bug here

- **`itext.io` carries `PackageId=Komsa.itext`.** A `ProjectReference` to an `IsPackable=false`
  project still becomes a package dependency named after that project's `PackageId`. Exactly one
  project may hold the bundle id — two cause `Ambiguous project name`, self-reference causes
  `NU1108`. Don't "fix" this.
- **`TargetFrameworks` in the props files must stay plural.** The singular `TargetFramework` wins
  over a project's own plural `TargetFrameworks` and silently collapses multi-targeted projects
  (the two brotli ones) to a single TFM.
- **`itext.font-asian`'s `AssemblyName` is `itext.font_asian`** (underscore) but its package id is
  hyphenated, so `PackageId` is set explicitly. `Komsa.$(AssemblyName)` would rename the package.
- **`GenerateAssemblyInfo` is `true`** with title/description/configuration disabled. Those three
  stay hand-maintained in each `Properties/AssemblyInfo.cs`; re-adding company, copyright or
  version attributes there causes `CS0579`.
- **Strong naming is removed.** No `.snk`, `InternalsVisibleTo` without `PublicKey=`. A
  strong-named consumer cannot reference these assemblies.

## Branding invariants

Produced PDFs must read:

```
iText® Core <version> ©2000-2026 KOMSA GmbH
```

No `(AGPL version)` suffix. There are **four** places branding is written — the first is the
obvious one, the rest are easy to miss:

1. `AbstractITextProductEventProcessor.cs` — the producer template.
2. `FlushPdfDocumentEvent.cs` — the "no events" fallback producer, used by any reader-only
   document. A separate hardcoded string.
3. `ImagePdfBytesInfo.cs` — the TIFF `Software` tag on extracted images.
4. `Directory.Build.props` — `Company` / `Copyright` / `Authors` assembly attributes.

`CompareTool` normalises producer lines before comparing document info: `COPYRIGHT_REGEXP`
accepts KOMSA alongside the upstream companies, and `AGPL_USAGE_TYPE_REGEXP` drops the usage type
so pre-existing `cmp_` reference files stay comparable. Consequence: `CompareTool` no longer
reports AGPL-vs-licensed producer differences.

If you change branding, grep for the company name across `itext/` — not just the template.

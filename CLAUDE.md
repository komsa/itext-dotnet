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

> **Never start a solution-wide test run on this machine, and never start one without asking
> first.** `dotnet test iTextCore.sln` runs all 13 assemblies in parallel; on 2026-08-25 it
> consumed all 64 GB of RAM and took the machine down. This is not a flaky-test annoyance, it
> costs the user their whole session.
>
> Use the wrapper, which pins the run to idle priority and enforces a hard memory cap through a
> Windows job object:
>
> ```
> python scripts/run_tests.py itext.tests/itext.commons.tests/itext.commons.tests.csproj
> python scripts/run_tests.py <project> --filter "FullyQualifiedName~<TheClass>"
> ```
>
> It refuses a `.sln` target unless `--allow-solution` is passed, reports the peak memory of the
> run, and reaps orphaned `testhost` processes when it exits. See the module docstring for the
> details. If a broader run really is needed, ask, then run the projects **one at a time**.

Ghostscript and ImageMagick are **not installed** here, and the visual-comparison tests are not
relevant to this fork. Always pass the runsettings:

```
--settings komsa.runsettings
```

In Visual Studio: *Test > Configure Run Settings > Select Solution Wide runsettings File*.

`komsa.runsettings` documents exactly what it excludes and why. Without it you get ~26 failures
that have nothing to do with your change.

Two things that will bite you:

- **Run assemblies sequentially, one project per invocation.** Beyond the memory blow-up above, a
  parallel solution-wide run also produces `OutOfMemoryException` in BouncyCastle static init,
  `Insufficient system resources` from veraPDF, and network timeouts. Those particular failures
  are artefacts of the parallelism, not regressions — re-run the affected project on its own
  before believing a failure.
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

## Deliberately left as upstream has it

- **`Komsa.itext.pdftest` depends on `NUnit 3.7.1`** while the test projects use `3.14.0`. This
  skew is upstream's; it only became visible because the old hand-written nuspec declared no
  dependencies at all. Decided to leave it — don't "align" it.

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

# KOMSA branding for `itext-dotnet`

Status: **commits 1–6 implemented** on `Feature/Branding`; commits 7 and 8 (§3, the producer
line and any `cmp_` regeneration) are still open. Sections carry a **[DONE]** marker where they
have landed, and the resolved **[VERIFY]** items have been replaced by **[VERIFIED]** findings.

Implementation notes and deviations from the original plan are collected in §14.

Goal: give the `Komsa/develop` fork of `itext-dotnet` the same kind of KOMSA branding and
in-house packaging that `komsa/itextsharp` (branch `Komsa/develop`) already has.

## 0. Starting point

- Branch `Komsa/develop` in this repo is currently **identical to `develop`** (0 commits ahead,
  0 behind). Everything below is greenfield.
- Upstream base: iText Core 9.8.0-SNAPSHOT, AGPL v3 / commercial dual license.
- Fork lives at `https://github.com/komsa/itext-dotnet` (the `komsa-ag` org was renamed to
  `komsa`; see §11).
- Toolchain verified: `dotnet` **10.0.301** (only SDK present) builds `itext.commons` clean for
  both `netstandard2.0` and `net461`. `nuget.exe` at
  `D:\Git\TeamFoundation\Binaries\Stable\nuget.exe` for the bundle package (§7a).

## 1. Decisions

| Topic | Decision |
|---|---|
| Producer line / copyright | **Change.** Keep the `iText®` prefix, swap `Apryse Group NV` → `KOMSA GmbH` |
| `(AGPL version)` suffix | **Strip** from the producer line |
| Target frameworks | **Drop `net461`.** Libraries → `netstandard2.0` only, tests → `net10.0` only |
| Package ids | `Komsa.*` |
| Bundle package | **Keep** the hand-written `itext.nuspec`, renamed to `Komsa.itext`, still bundling 11 DLLs |
| Module packages | Move the 8 module nuspecs to `GeneratePackageOnBuild` + `PackageId = Komsa.$(AssemblyName)` |
| Package set | **9 packages total** — the bundle + 8 modules. No standalone per-assembly packages |
| Version | Mirror upstream + KOMSA revision → `9.8.0.1` |
| `AssemblyVersion` | **Pinned to `9.0.0.0`**; `FileVersion`/`InformationalVersion`/`PackageVersion` carry `9.8.0.1` |
| Strong naming | **Remove** |
| Package icon | Keep `ITSC-avatar.png` |
| `Jenkinsfile` | Leave as is |
| Origin marker + SourceLink | Add both |

Note the packaging decision is a deliberate hybrid: `GeneratePackageOnBuild` for the modules,
but the bundle stays nuspec-driven because a single package containing 11 assemblies cannot be
produced by `PackageId = Komsa.$(AssemblyName)` on those 11 projects.

## 2. Where branding lives in this repo

Touch points found by inspecting the tree:

1. **`Properties/AssemblyInfo.cs` — 19 under `itext/`, 14 under `itext.tests/`.**
   `GenerateAssemblyInfo` is `false` (`itext/Directory.Build.props`), so these are
   hand-maintained. Each contains `AssemblyCompany("Apryse Group NV")`,
   `AssemblyProduct("iText")`, `AssemblyCopyright("Copyright (c) 1998-2026 Apryse Group NV")`,
   `AssemblyVersion`/`AssemblyFileVersion` `9.8.0.0`, `AssemblyInformationalVersion`
   `9.8.0-SNAPSHOT`, plus 20 `InternalsVisibleTo` entries carrying explicit `PublicKey=…`.
2. **PDF producer template** —
   `itext/itext.commons/itext/commons/actions/processors/AbstractITextProductEventProcessor.cs:46`.
   Placeholders filled from `CommonsProductData.cs` and `ITextCoreProductData.cs`
   (`*_VERSION`, `*_COPYRIGHT_SINCE` = 2000, `*_COPYRIGHT_TO` = 2026).
3. **Packaging** — `itext.nuspec` (bundle) + 8 module nuspecs, all hand-written, globbing
   pre-built DLLs from `bin/Release/{net461,netstandard2.0}`.
4. **Build config** — `itext/Directory.Build.props` (TFMs `netstandard2.0;net461`, signing on),
   `itext/Directory.Build.targets` (only `DocumentationFile`), `itext.tests/Directory.Build.props`
   (TFMs `net10.0;netcoreapp2.0;net461`), `itext/itext.pdftest/itext.pdftest.props`.
5. **`port-hash`** — records the upstream Java commit the .NET port came from. Leave untouched;
   reference it from the origin marker (§8).

## 3. Work item: producer line and copyright  [DONE - commits 7/8]

1. **`AbstractITextProductEventProcessor.cs:46`** — swap the company and drop the usage-type
   suffix. From:
   ```csharp
   return "iText\u00ae ${usedProducts:P V (T 'version')} \u00a9${copyrightSince}-${copyrightTo} Apryse Group NV";
   ```
   to:
   ```csharp
   return "iText\u00ae ${usedProducts:P V} \u00a9${copyrightSince}-${copyrightTo} KOMSA GmbH";
   ```
   Renders as `iText® Core 9.8.0.1 ©2000-2026 KOMSA GmbH` (previously
   `iText® Core 9.8.0-SNAPSHOT (AGPL version) ©2000-2026 Apryse Group NV`).

   In the `usedProducts` format, `P` = product name, `V` = version, `T` = usage type
   (`"AGPL"`, from `DefaultITextProductEventProcessor.cs:90`), and `'version'` is a quoted
   literal. Removing `(T 'version')` leaves `T` unused in the producer line — the usage type is
   still tracked internally, it just stops being printed.

   `${copyrightSince}`/`${copyrightTo}` keep their upstream values (2000 / 2026) — those come
   from `CommonsProductData.cs` and `ITextCoreProductData.cs`, which only need their version
   constants bumped (§6).

2. **`itext/itext.kernel/itext/kernel/utils/CompareTool.cs:82,84`** — this is the one that
   silently breaks everything if missed:
   ```csharp
   private const String COPYRIGHT_REGEXP = "©\\d+-\\d+ (?:iText Group NV|Apryse Group NV)";
   private const String COPYRIGHT_REPLACEMENT = "©<copyright years> Apryse Group NV";
   ```
   `CompareTool` normalises the producer line before comparing document info dictionaries. A
   KOMSA producer line does not match the regex, so it stays un-normalised and every info-dict
   comparison in the suite mismatches. Extend the alternation with `KOMSA GmbH` and update the
   replacement string to match whatever the `cmp_` files are regenerated against.

3. **Tests asserting the producer string directly** (only three files):
   - `itext.tests/itext.kernel.tests/itext/kernel/actions/events/FlushPdfDocumentEventTest.cs:125`
   - `itext.tests/itext.kernel.tests/itext/kernel/utils/CompareToolTest.cs:155,163,164`
   - `itext.tests/itext.sign.tests/itext/signatures/sign/PdfPadesSignerTest.cs:280`

4. **[VERIFIED — blast radius is small]** The feared mass `cmp_*.pdf` breakage does not apply.
   The producer string is only ever compared by `CompareTool.CompareDocumentInfo`, which is
   called **9 times across 4 files**:
   - `itext.tests/itext.kernel.tests/itext/kernel/pdf/PdfDocumentInfoTest.cs`
   - `itext.tests/itext.kernel.tests/itext/kernel/pdf/XMPMetadataTest.cs`
   - `itext.tests/itext.kernel.tests/itext/kernel/utils/CompareToolTest.cs`
   - `itext.tests/itext.pdfa.tests/itext/pdfa/PdfAXmpTest.cs`

   `CompareByContent` (2325 call sites) compares pages and the catalog while **explicitly
   ignoring `/Metadata`**, so neither the info-dictionary producer nor the XMP producer takes
   part in it. Total exposure for commit 7 is therefore these 4 files plus the 3
   direct-assertion files in §3.3 — not the whole suite.

5. **[VERIFIED]** No `UsedProductsPlaceholderPopulator` / `ProducerBuilder` test asserts the
   default template, so dropping `(T 'version')` did not touch them —
   `itext.commons.tests` stayed at 0 failed / 419 passed throughout.

6. **[FOUND DURING IMPLEMENTATION - not in the original plan]** The template is *not* the only
   hardcoded producer. Two further sites had to change, both discovered because
   `FlushPdfDocumentEventTest` kept passing after the template change when it should not have:

   - `itext/itext.kernel/itext/kernel/actions/events/FlushPdfDocumentEvent.cs:69` — the
     "no events" fallback producer, used whenever a document has no registered events (any
     reader-only document takes this path). Has no usage-type suffix, so only the company
     changed.
   - `itext/itext.kernel/itext/kernel/pdf/xobject/ImagePdfBytesInfo.cs:40` — the TIFF
     `Software` tag stamped onto extracted TIFF images.

   Both now say `KOMSA GmbH`. Had these been missed, roughly half the producer surface would
   have stayed `Apryse Group NV`.

7. **`(AGPL version)` in existing `cmp_` files — resolved by normalisation, not regeneration.**
   Stripping the suffix from output left 7 `CompareDocumentInfo` tests failing, because their
   reference PDFs still carry it (5 kernel, 2 pdfa). Two options were on the table: regenerate
   the 7 reference PDFs, or teach `ConvertProducerLine` to drop the suffix the way it already
   drops version and copyright drift. **Option B was chosen** — no binary churn, reversible:

   ```csharp
   private const String AGPL_USAGE_TYPE_REGEXP = " \(AGPL[- ]version\)";
   private const String AGPL_USAGE_TYPE_REPLACEMENT = "";
   ```

   applied as a third `ReplaceAll` in `ConvertProducerLine`. It matches both layouts found in
   reference files (`(AGPL version)` after the version, `(AGPL-version)` trailing the company in
   older 5.x files). `(licensed to ...)` is deliberately **not** stripped, so `VersionReplaceTest`
   still passes. Cost: `CompareTool` no longer reports AGPL-vs-licensed usage-type differences,
   and `CompareToolTest.DifferentProducerTest` needed its expected message updated.

8. **`AssemblyCompany` / `AssemblyCopyright`** in the 33 `AssemblyInfo.cs` files → KOMSA GmbH.
   Handled centrally by §6 rather than by editing 33 files.

## 4. Work item: drop net461  [DONE]

Libraries target `netstandard2.0` only; tests target `net10.0` only. `netstandard2.0` is
consumable from net10, so this is a pure removal — no retarget.

1. `itext/Directory.Build.props:4` — `<TargetFrameworks>netstandard2.0;net461</TargetFrameworks>`
   → `<TargetFrameworks>netstandard2.0</TargetFrameworks>`. **Keep the property plural.**
   Switching it to the singular `TargetFramework` silently wins over a project's own plural
   `TargetFrameworks`, collapsing multi-targeted projects to one TFM; the plural form lets a
   project override it, which is how upstream intended it. See §14.1.
2. `itext.tests/Directory.Build.props:4` — `net10.0;netcoreapp2.0;net461` → `net10.0`.
   Then delete the now-dead `net461` and `netcoreapp2.0` `ItemGroup`s (lines ~30–45) and the
   `net8.0` group, keeping only the `net10.0` package references. Line 26's
   `Condition="'$(TargetFramework)' != 'net461'"` guard around `DefineConstants=NETSTANDARD2_0`
   becomes unconditional — **keep the define**, the test code relies on it.
3. Delete the `Condition="'$(TargetFramework)' == 'net461'"` `ItemGroup`s from the 11 library
   csproj files that have them (`barcodes`, `bouncy-castle-adapter`, `bouncy-castle-connector`,
   `commons`, `forms`, `io`, `kernel`, `layout`, `pdfa`, `pdftest`, `pdfua`, `sign`,
   `styledxmlparser`, `svg`). These only add `<Reference Include="System" />`-style GAC
   references. Drop the now-redundant `== 'netstandard2.0'` conditions on the remaining groups.
4. `itext.nuspec` — delete the whole `net461` dependency group and all 22 `lib\net461` file
   entries (§7a).
5. **Source conditionals stay untouched.** The 43 `#if NETSTANDARD2_0` / `#if !NETSTANDARD2_0`
   sites keep compiling the same branch they do today, because `netstandard2.0` still defines
   the symbol. Note the `!NETSTANDARD2_0` branches (e.g. `JsonValueNewtonsoftConverter.cs`,
   `CommonsRuntime.cs:541,722`) become permanently dead code — leave them, removal is a
   separate cleanup and would enlarge the diff against upstream.
6. `itext/itext.bouncy-castle-fips-adapter` already targets `netstandard2.0` only — no change.
7. **[VERIFIED]** `iTextCore.sln` carries no TFM-specific configuration — it contains no
   `net461`/`netcoreapp`/`netstandard` string at all — and builds clean afterwards.
   Two projects are *not* in the solution: `itext.brotli-compressor` and
   `itext.brotli-compressor.tests`. They keep their own `TargetFrameworks`
   (`netstandard2.1;net8.0` and `net8.0;net10.0`) and had to gain an empty
   `<TargetFramework></TargetFramework>`, otherwise the single `TargetFramework` inherited
   from `Directory.Build.props` would have silently turned them into single-target builds.

## 5. Work item: strong naming removal  [DONE]

1. `SignAssembly=false` (or drop the property) in `itext/Directory.Build.props` and
   `itext.tests/Directory.Build.props`; remove `AssemblyOriginatorKeyFile` / `DelaySign`.
2. Delete the **33 `itext.snk` copies** (one per project folder, `itext/` and `itext.tests/`).
3. Strip `,PublicKey=…` from the **20 `InternalsVisibleTo`** declarations under `itext/`
   (leaving the bare assembly name), and check `itext.tests/` for any further ones.
4. **[VERIFIED]** No leftovers. `itext.pdftest.props` only contains verapdf `Content`
   entries; after the change there is no `.snk` file in the tree and no `PublicKey=` in any
   `.cs`/`.csproj`/`.props`/`.targets`/`.nuspec`. `itext.kernel.dll` reports
   `PublicKeyToken=null`.
5. Consumer note: unsigned assemblies cannot be referenced by strong-named projects. Any
   internal consumer that is itself strong-named will break. Worth a heads-up before release.

## 6. Work item: central versioning  [DONE]

Target values:

```
AssemblyVersion              9.0.0.0   (pinned — never changes across 9.x KOMSA revisions)
AssemblyFileVersion          9.8.0.1
AssemblyInformationalVersion 9.8.0.1
PackageVersion               9.8.0.1
```

Implementation: put `VersionPrefix`, `AssemblyVersion`, `FileVersion`, `Company`, `Product`,
`Copyright`, `Authors` in `itext/Directory.Build.props` and let the SDK emit them, instead of
maintaining 33 files by hand. Because `GenerateAssemblyInfo` is currently `false`, this means:

- set `GenerateAssemblyInfo=true`;
- set `GenerateAssemblyTitleAttribute=false`, `GenerateAssemblyDescriptionAttribute=false`,
  `GenerateAssemblyConfigurationAttribute=false` — those stay per-project in the hand-written
  files;
- **remove** `AssemblyVersion`, `AssemblyFileVersion`, `AssemblyInformationalVersion`,
  `AssemblyCompany`, `AssemblyProduct`, `AssemblyCopyright`, `AssemblyCulture`,
  `AssemblyTrademark` from all 33 `AssemblyInfo.cs`, or the build fails with duplicate-attribute
  errors (CS0579);
- keep `InternalsVisibleTo`, `ComVisible`, `Guid`, `AssemblyTitle`, `AssemblyDescription` in the
  hand-written files.

Also bump the version constants that are **not** assembly attributes and must be edited in code:
`CommonsProductData.COMMONS_VERSION` and `ITextCoreProductData.CORE_VERSION`
(`9.8.0-SNAPSHOT` → `9.8.0.1`).

**[VERIFIED]** `CompareTool.VERSION_REGEXP` (`"(\\d+\\.)+\\d+(-SNAPSHOT)?"`) matches `9.8.0.1`.
Nothing else parses the product version: `ProductData.GetVersion()` returns the raw string
and `UsedProductsPlaceholderPopulator` only substitutes it. The only other version constant,
`MINIMAL_COMPATIBLE_LICENSEKEY_VERSION = "4.1.0"`, is unrelated and unchanged.

## 7. Work item: packaging  [DONE]

### 7a. Bundle — `Komsa.itext` (keep `itext.nuspec`)  [DONE]

Edit in place:
- `<id>` → `Komsa.itext`
- `<version>` → `9.8.0.1`
- `<authors>` / `<owners>` → `KOMSA GmbH`
- `<repository url>` → `https://github.com/komsa/itext-dotnet`
- `<copyright>` → KOMSA GmbH (per §1)
- `<dependencies>` → **delete the `net461` group**; in the `netstandard2.0` group rename
  `itext.commons` → `Komsa.itext.commons`
- `<files>` → **delete the 22 `lib\net461` entries**, keep the 22 `netstandard2.0` ones
- keep `<icon>ITSC-avatar.png</icon>`, `<licenseUrl>` (AGPL), and the
  `NOTICE_*.txt` / `LICENSE.md` / `gnu-agpl-v3.0.md` entries
- **[DECIDED]** the three fields that still carried upstream identity are now KOMSA's:
  - `<title>` → `KOMSA GmbH` (was `iText Community`)
  - `<projectUrl>` → `https://github.com/komsa/itext-dotnet` (was `itextpdf.com/products/itext-core`)
  - `<releaseNotes>` → `https://github.com/komsa/itext-dotnet/releases` (was `itextpdf.com/itext7release`)

  `<description>`, `<summary>` and `<tags>` keep their upstream wording — they describe iText,
  which is what the package contains.

Pack with the confirmed local tool:

```
D:\Git\TeamFoundation\Binaries\Stable\nuget.exe pack itext.nuspec -OutputDirectory <out>
```

after a `dotnet build -c Release`, since the nuspec globs pre-built output.

### 7b. Modules — `GeneratePackageOnBuild`  [DONE]

Delete these 8 nuspecs and move their metadata into the corresponding `.csproj`:

| Old nuspec id | New `PackageId` |
|---|---|
| `itext.commons` | `Komsa.itext.commons` |
| `itext.bouncy-castle-adapter` | `Komsa.itext.bouncy-castle-adapter` |
| `itext.bouncy-castle-fips-adapter` | `Komsa.itext.bouncy-castle-fips-adapter` |
| `itext.brotli-compressor` | `Komsa.itext.brotli-compressor` |
| `itext.pdftest` | `Komsa.itext.pdftest` |
| `itext.webp-image-support` | `Komsa.itext.webp-image-support` |
| `itext.font-asian` | `Komsa.itext.font-asian` |
| `itext.hyph` | `Komsa.itext.hyph` |

**Trap:** `PackageId = Komsa.$(AssemblyName)` works for 7 of the 8, but `itext.font-asian`'s
`AssemblyName` is **`itext.font_asian`** (underscore) while its package id is hyphenated. Set
`PackageId` explicitly there, or the package silently changes name to `Komsa.itext.font_asian`.

Set `IsPackable=false` for the 11 projects that go into the bundle and for all of
`itext.tests/`, so `GeneratePackageOnBuild` in a shared props file doesn't emit 20 packages.

Shared package metadata (`Authors`, `Copyright`, `PackageProjectUrl`, `RepositoryUrl`,
`RepositoryType`, `PackageIcon`, `PackageLicense*`) goes in `itext/Directory.Build.props`.

**[VERIFIED]** The generated nuspecs were diffed against the old hand-written ones. Parity
holds, with these fixes:

- `itext.commons`, `itext.bouncy-castle-adapter`, `itext.font-asian`, `itext.hyph` matched
  out of the box.
- `itext.bouncy-castle-fips-adapter`: the `bc-fips-1.0.2.dll` / `bcpkix-fips-1.0.2.dll`
  assemblies are plain `<Reference>`s, so `dotnet pack` ignored them. They are now packed
  explicitly into `lib\netstandard2.0`, together with `NOTICE.txt`.
- `itext.pdftest`: the old nuspec declared **no** dependencies at all even though the
  project references NUnit, BouncyCastle and several `System.*` packages. The generated
  package now declares them — an improvement, not a regression. Its `Build\` payload
  (`itext.pdftest.props` + the two verapdf files) is packed explicitly. **The props file is
  packed as `build\Komsa.itext.pdftest.props`**: NuGet only auto-imports a build props file
  named after the package id, so keeping `itext.pdftest.props` would have silently stopped
  the verapdf wiring from being imported.
- Bundle dependency (`itext.brotli-compressor`, `itext.webp-image-support`,
  `itext.pdftest`): see §14 — a `ProjectReference` to an `IsPackable=false` project still
  becomes a package dependency, using that project's `PackageId`.
- Portable PDBs are packed next to each DLL via
  `AllowedOutputExtensionsInPackageBuildOutputFolder` (§9), and `IncludeSymbols` is off so
  no separate symbols package is produced.

### 7c. Push script  [DONE]

Add `PushNugetFiles.ps1` at the repo root, modelled on `src/PushNugetFiles.ps1` in `itextsharp`:
reads `VersionPrefix` out of `Directory.Build.props`, then

```
dotnet nuget push -s "https://tfs-01/DefaultCollection/_packaging/Komsa/nuget/v3/index.json" `
  -k AzureDevOps "<output>\Komsa.*.$currentVersion.nupkg"
```

Must pick up both the `dotnet pack` output of the 8 modules and the `nuget.exe pack` output of
the bundle. **[VERIFIED]** they do land in different places by default (`bin\Release\` per
project vs. the `nuget.exe` working directory), so `PackageOutputPath` is set to
`$(MSBuildThisFileDirectory)..\artifacts\nuget` in `itext/Directory.Build.props` and the
bundle is packed with `-OutputDirectory artifacts\nuget`. One glob
(`artifacts\nuget\Komsa.*.$currentVersion.nupkg`) then covers all 9.

The script reads `VersionPrefix` from `itext/Directory.Build.props` (not the repo root — this
repo has no root `Directory.Build.props`).

## 8. Work item: origin marker  [DONE]

New file `itext/KomsaSharedAssemblyInfo.cs`:

```csharp
using System.Reflection;

[assembly: AssemblyMetadata("Komsa: source", "https://github.com/komsa/itext-dotnet/tree/Komsa/develop")]
[assembly: AssemblyMetadata("Komsa: source original", "https://github.com/itext/itext-dotnet")]
[assembly: AssemblyMetadata("Komsa: upstream port-hash", "f5c62866e306a6cf902459feb525a3c5ad95d1d6")]
```

linked into every project via `itext/Directory.Build.targets`:

```xml
<ItemGroup>
  <Compile Include="$(MSBuildThisFileDirectory)KomsaSharedAssemblyInfo.cs" Link="Properties\KomsaSharedAssemblyInfo.cs" />
</ItemGroup>
```

The `port-hash` value above is the current content of the repo-root `port-hash` file; consider
reading it at build time instead of hard-coding, so it can't drift.

## 9. Work item: SourceLink + portable PDBs  [DONE]

In `itext/Directory.Build.props`:

```xml
<PublishRepositoryUrl>true</PublishRepositoryUrl>
<DebugType>portable</DebugType>
<PackageReference Include="Microsoft.SourceLink.GitHub" Version="8.0.0" PrivateAssets="All" />
```

and ship the `.pdb` alongside the `.dll` — for the bundle that means adding `pdb` paths to the
`<files>` list in `itext.nuspec`, next to each `dll`/`xml` entry.

`github.com/komsa/itext-dotnet` is presumably private; SourceLink then requires developers to be
authenticated to GitHub. It degrades gracefully (no source stepping) if they are not, so this is
safe to enable regardless.

## 10. Not doing

- **`Jenkinsfile`** — left untouched. It calls the iText-internal `pipeline-library`
  (`automaticDotnetBuild`) and is inert for KOMSA builds.
- **Standalone per-assembly packages** for the 11 bundled modules.
- **Re-keying** with a KOMSA strong-name key — strong naming is removed outright (§5).
- **Removing the now-dead `!NETSTANDARD2_0` code branches** left over from dropping net461 (§4.5).

## 11. `itextsharp` repo — out of scope

**Decision: leave `D:\Git\komsa\itextsharp` untouched.** That fork is being abandoned, so none
of the following gets fixed — recorded only so nobody rediscovers it and assumes it was an
oversight:

- `src/Directory.Build.props:24` and `src/KomsaSharedAssemblyInfo.cs` still point at the
  pre-rename `komsa-ag` org (the git remote itself is already correct)
- `src/core/iTextSharp/text/Version.cs:88` still says `©2000-2025 KOMSA AG` (old legal form)

It does remain the reference implementation this plan was modelled on (§0), and
`src/PushNugetFiles.ps1` there is the template for §7c.

## 12. Commit plan

Eight commits, each building on its own, ordered so the riskiest step lands against a
known-green tree.

| # | Commit | Scope | Status |
|---|---|---|---|
| 1 | `build: add KOMSA origin marker and SourceLink` | §8 + §9 | **done** `dfd8d51f6` |
| 2 | `build: drop net461, target netstandard2.0 only` | §4 | **done** `1fdba11fb` |
| 3 | `build: centralize versioning and branding metadata` | §6 — central props, strip 8 attributes from 33 `AssemblyInfo.cs`, bump the two `*ProductData` constants | **done** `6183900f2` |
| 4 | `build: remove strong naming` | §5 | **done** `428749ad0` |
| 5 | `build: publish module packages as Komsa.*` | §7b | **done** `bf90a691b` |
| 6 | `build: rename bundle package to Komsa.itext` | §7a + §7c | **done** `475deebb7` |
| 7 | `feat: use KOMSA producer line` | §3.1–§3.3 | open |
| 8 | `test: regenerate cmp reference files` | §3.4 — **only if** the suite requires it; kept separate because it may be a large binary diff | open |

`dotnet build iTextCore.sln -c Release` was green after every one of commits 1–6 (and
`itext.brotli-compressor`, which is not in the solution, was built separately).

All eight land in this repo on `Komsa/develop`; nothing touches the `itextsharp` fork (§11).

Commits 3 and 4 both edit all 33 `AssemblyInfo.cs` but are kept apart because they fail
differently: 3 breaks the build loudly if an attribute is missed, 4 only where
`InternalsVisibleTo` matters. Commit 2 lands early so everything after it builds one TFM
instead of two.

## 13. Verification checklist

- [x] `dotnet build iTextCore.sln -c Release` clean, no CS0579 duplicate-attribute errors
      (0 warnings, 0 errors; `itext.brotli-compressor` built separately, see §14.1)
- [x] No `net461` or `netcoreapp2.0` left in any `.csproj` / `.props` / `.nuspec`
- [ ] Full test suite green on `net10.0` — record the baseline **before** commit 7 so
      producer-line fallout is attributable *(not run yet; belongs to commit 7)*.
      Run it with the filter (§15):
      `dotnet test iTextCore.sln -c Release --settings komsa.runsettings --logger "trx;LogFileName=baseline.trx" --results-directory TestResults`
- [x] `Komsa.itext.nupkg` contains 11 `dll` + 11 `xml` + 11 `pdb` under `lib\netstandard2.0`
      only, and depends on `Komsa.itext.commons` 9.8.0.1
- [x] All 9 package ids correct — `Komsa.itext.font-asian` verified (the assembly inside is
      still `itext.font_asian.dll`, as before)
- [x] No `.snk` left in the tree; `itext.kernel.dll` reports `PublicKeyToken=null`
- [x] A produced PDF's `/Producer` reads `iText® Core 9.8.0.1 ©2000-2026 KOMSA GmbH` — no
      `(AGPL version)` suffix. Confirmed by writing a PDF and reading it back; the pre-change
      value was `iText® Core 9.8.0.1 (AGPL version) ©2000-2026 Apryse Group NV`
- [x] Assembly metadata shows `9.0.0.0` / `9.8.0.1` / `9.8.0.1`, `KOMSA GmbH`, and the three
      `Komsa: …` origin `AssemblyMetadata` entries

## 14. Implementation notes and deviations (commits 1–6)

1. **`itext.brotli-compressor` is not in `iTextCore.sln`** (nor is its test project). Building
   the solution never touches it — build it explicitly. Both projects needed an empty
   `<TargetFramework></TargetFramework>` next to their own `<TargetFrameworks>`, because §4.1
   replaced the inherited `TargetFrameworks` with a singular `TargetFramework`, which the SDK
   treats as "not cross-targeting" and would have silently reduced them to one TFM.

2. **`itext.bouncy-castle-fips-adapter` lost its redundant `<TargetFrameworks>netstandard2.0`
   override** (§4.6 said "no change"). It now just inherits the single TFM. Behaviourally
   identical, one less thing that looks like it does something.

3. **§6 was applied to `itext.tests/Directory.Build.props` as well**, not only
   `itext/Directory.Build.props`. The plan says "put … in `itext/Directory.Build.props`" but also
   "remove the attributes from all 33 `AssemblyInfo.cs`" — the test assemblies would otherwise
   have ended up with no version/company attributes at all. There is no repo-root
   `Directory.Build.props` to share, so the property block is duplicated in the two files.

4. **`IncludeSourceRevisionInInformationalVersion=false`** was added. The .NET SDK otherwise
   appends `+<commit sha>` to `AssemblyInformationalVersion` once SourceLink is on, which would
   have contradicted the "`AssemblyInformationalVersion 9.8.0.1`" target in §6.

5. **`PackageId = Komsa.itext` on `itext.io`.** This is the one genuinely surprising thing.
   A `ProjectReference` to a project with `IsPackable=false` still becomes a package
   *dependency*, named after that project's `PackageId`. Three module packages reference bundled
   projects (`brotli-compressor` → `kernel`, `webp-image-support` → `io`, `pdftest` → `io`), so
   without intervention they would have shipped dependencies on non-existent `itext.kernel` /
   `itext.io` packages.

   Setting `PackageId=Komsa.itext` on *all 11* bundled projects fixes the id but breaks restore
   (`error : Ambiguous project name 'Komsa.itext'`); on *two* of them it produces
   `error NU1108: Cycle detected … Komsa.itext -> Komsa.itext`. Exactly one project may carry the
   bundle id, and `itext.io` was chosen because it is the bundle's lowest-level assembly.
   `itext.brotli-compressor` therefore marks its `itext.kernel` reference `PrivateAssets="all"`
   and adds an `itext.io` reference to carry the `Komsa.itext` dependency. All three module
   packages now correctly depend on `Komsa.itext` 9.8.0.1.

   The other 10 bundled projects keep their default (never published) package ids.

6. **`build\Komsa.itext.pdftest.props`** — see §7b. Renaming the package id would otherwise have
   silently disabled the automatic import of the verapdf props file.

7. **Module packages get `PackageLicenseExpression=AGPL-3.0-only`** rather than the deprecated
   `licenseUrl` the old module nuspecs used. The bundle nuspec keeps `<licenseUrl>` as §7a
   requires (`nuget.exe pack` warns NU5125 about it).

8. **`PackageProjectUrl` for the modules is `https://github.com/komsa/itext-dotnet`**, matching
   the bundle's `<projectUrl>` (§7a). Initially left as `https://itextpdf.com/`, changed when the
   bundle's upstream-identity fields were decided. `RepositoryUrl` points at the same URL.

9. **`LICENSE.md` + `gnu-agpl-v3.0.md` are now in every module package**, where previously only
   `pdftest`, `font-asian` and `hyph` carried them. Simplification, not a decision.

10. **Produced package set** (`artifacts\nuget`, all at `9.8.0.1`):
    `Komsa.itext`, `Komsa.itext.commons`, `Komsa.itext.bouncy-castle-adapter`,
    `Komsa.itext.bouncy-castle-fips-adapter`, `Komsa.itext.brotli-compressor`,
    `Komsa.itext.pdftest`, `Komsa.itext.webp-image-support`, `Komsa.itext.font-asian`,
    `Komsa.itext.hyph`. The bundle contains 11 `dll` + 11 `xml` + 11 `pdb` under
    `lib\netstandard2.0` only.

11. **Not verified because it belongs to commit 7:** the test suite was not run. §13's
    "record the baseline before commit 7" is still outstanding.

## 15. Test filtering: Ghostscript / ImageMagick

`BUILDING.md` requires Ghostscript and ImageMagick, wired up through the `ITEXT_GS_EXEC` and
`ITEXT_MAGICK_COMPARE_EXEC` environment variables, for the visual-comparison tests. **Decision:
those tools are not installed at KOMSA and the visual comparisons are not relevant for this
fork**, so the affected tests are filtered out via `komsa.runsettings` at the repo root.

In Visual Studio: *Test > Configure Run Settings > Select Solution Wide runsettings File*.

Two groups are excluded:

1. Tests of the helpers themselves — `GhostscriptHelperTest`, `GhostScriptHelperUnitTest`,
   `ImageMagickHelperTest`, `ImageMagickHelperUnitTest`.
2. The 14 classes calling `CompareTool.CompareVisually` (53 call sites): `AnnotationsSigningTest`,
   `Pdf20SigningTest`, `PdfASigningTest`, `PdfMergerTest`, `PolygonSvgNodeRendererTest`,
   `PolylineSvgNodeRendererTest`, `RotationTest`, `SignDeferredTest`, `SignatureAppearanceTest`,
   `SignatureFieldAppearanceTest`, `SignedAppearanceTextTest`, `SimpleSigningTest`,
   `TaggedPdfSigningTest`, `WebPIntegrationTest`.

`CompareToolTest` is filtered **per-method**, not whole-class, because it also holds the
producer-line assertions (`DifferentProducerTest`, `VersionReplaceTest`) that commit 7 needs.

`SystemUtilTest` is also filtered per-method (`SystemUtilTest.RunProcessAnd`). Its
`RunProcessAndWaitWithWorkingDirectoryTest` and `RunProcessAndGetProcessInfoTest` read the
ImageMagick path directly from the environment variable and pass it to the process starter, so
with the variable unset they throw `ArgumentNullException` on a null executable — a third way of
depending on the tools, distinct from the two groups above. The other eight methods in the class
are pure string-splitting tests and keep running. Measured on `itext.commons.tests`: **0 failed /
419 passed** with the filter.

Measured effect on `itext.io.tests`: unfiltered **34 failed / 989 passed / 1025 total**;
filtered **0 failed / 965 passed / 967 total**. All 34 failures were Ghostscript/ImageMagick.

### Baseline run (before commit 7)

`dotnet test iTextCore.sln -c Release --settings komsa.runsettings`, 13 test assemblies,
~44 min: **17590 passed, 8 failed, 36 skipped**. All 8 failures were environmental, none
related to commits 1-6:

| Assembly | Failures |
|---|---|
| `itext.commons.tests` | 2 - `SystemUtilTest.RunProcessAnd*` (null ImageMagick path) |
| `itext.kernel.tests` | 6 - all `CompareToolTest`: `CompareToolErrorReportTest01`-`04`, `BaseFontAbsenceInOutPdfTest`, `DumpMemoryFirstWriterOnDiskTest` |

The 6 kernel failures are the "known limitation" below in action: these tests deliberately
compare mismatching PDFs, so `CompareByContent` reaches the Ghostscript fallback every time by
design. All 8 are now excluded by the filter.

Note `itext.brotli-compressor.tests` is **not in `iTextCore.sln`**, so a solution-wide run never
covers it (see also §14.1).

**Known limitation the filter cannot remove.** `CompareTool.CompareByContent` falls back to
`CompareVisuallyAndCombineReports` (`CompareTool.cs:2062`) whenever it finds a difference, which
invokes Ghostscript and throws `GS_ENVIRONMENT_VARIABLE_IS_NOT_SPECIFIED`. Passing content
comparisons are unaffected, but a **failing** one reports a Ghostscript error instead of the
actual diff. A green run is trustworthy; diagnosing a red one needs Ghostscript installed.

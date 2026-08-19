# KOMSA branding for `itext-dotnet`

Status: **decided, ready to implement.** Remaining unknowns are marked **[VERIFY]** — they are
things to measure during implementation, not decisions to make.

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

## 3. Work item: producer line and copyright

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

4. **[VERIFY]** How many `cmp_*.pdf` reference files carry the producer string in a way that
   survives the §3.2 normalisation. Run the full suite after §3.1–§3.3 and quantify before
   deciding whether to regenerate reference files or widen the normalisation.

5. **[VERIFY]** Dropping `(T 'version')` may affect tests that assert the *format* rather than
   the company — check `UsedProductsPlaceholderPopulator` and `ProducerBuilder` tests under
   `itext.tests/itext.commons.tests/itext/commons/actions/producer/`.

6. **`AssemblyCompany` / `AssemblyCopyright`** in the 33 `AssemblyInfo.cs` files → KOMSA GmbH.
   Handled centrally by §6 rather than by editing 33 files.

## 4. Work item: drop net461

Libraries target `netstandard2.0` only; tests target `net10.0` only. `netstandard2.0` is
consumable from net10, so this is a pure removal — no retarget.

1. `itext/Directory.Build.props:4` — `<TargetFrameworks>netstandard2.0;net461</TargetFrameworks>`
   → `<TargetFramework>netstandard2.0</TargetFramework>`.
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
7. **[VERIFY]** `iTextCore.sln` may carry per-TFM build configurations; check it still builds.

## 5. Work item: strong naming removal

1. `SignAssembly=false` (or drop the property) in `itext/Directory.Build.props` and
   `itext.tests/Directory.Build.props`; remove `AssemblyOriginatorKeyFile` / `DelaySign`.
2. Delete the **33 `itext.snk` copies** (one per project folder, `itext/` and `itext.tests/`).
3. Strip `,PublicKey=…` from the **20 `InternalsVisibleTo`** declarations under `itext/`
   (leaving the bare assembly name), and check `itext.tests/` for any further ones.
4. **[VERIFY]** Grep for leftover `.snk` / `PublicKey` references in
   `itext/itext.pdftest/itext.pdftest.props` and any `.csproj`.
5. Consumer note: unsigned assemblies cannot be referenced by strong-named projects. Any
   internal consumer that is itself strong-named will break. Worth a heads-up before release.

## 6. Work item: central versioning

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

**[VERIFY]** `CompareTool.VERSION_REGEXP` is `"(\\d+\\.)+\\d+(-SNAPSHOT)?"`, which matches
`9.8.0.1` fine — but confirm nothing else parses the version as three-part.

## 7. Work item: packaging

### 7a. Bundle — `Komsa.itext` (keep `itext.nuspec`)

Edit in place:
- `<id>` → `Komsa.itext`
- `<version>` → `9.8.0.1`
- `<authors>` / `<owners>` → `KOMSA GmbH`
- `<repository url>` → `https://github.com/komsa/itext-dotnet`
- `<copyright>` → KOMSA GmbH (per §1)
- `<dependencies>` → **delete the `net461` group**; in the `netstandard2.0` group rename
  `itext.commons` → `Komsa.itext.commons`
- `<files>` → **delete the 22 `lib\net461` entries**, keep the 22 `netstandard2.0` ones
- keep `<icon>ITSC-avatar.png</icon>`, `<licenseUrl>` (AGPL), `<projectUrl>`, and the
  `NOTICE_*.txt` / `LICENSE.md` / `gnu-agpl-v3.0.md` entries
- **[VERIFY]** `<releaseNotes>` still points at `itextpdf.com/itext7release` — decide whether to
  drop it

Pack with the confirmed local tool:

```
D:\Git\TeamFoundation\Binaries\Stable\nuget.exe pack itext.nuspec -OutputDirectory <out>
```

after a `dotnet build -c Release`, since the nuspec globs pre-built output.

### 7b. Modules — `GeneratePackageOnBuild`

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

**[VERIFY]** Each module nuspec's `<dependencies>` must be reproduced by the csproj's real
`PackageReference`/`ProjectReference` set. Diff the generated `.nuspec` inside each produced
`.nupkg` against the old file before publishing.

### 7c. Push script

Add `PushNugetFiles.ps1` at the repo root, modelled on `src/PushNugetFiles.ps1` in `itextsharp`:
reads `VersionPrefix` out of `Directory.Build.props`, then

```
dotnet nuget push -s "https://tfs-01/DefaultCollection/_packaging/Komsa/nuget/v3/index.json" `
  -k AzureDevOps "<output>\Komsa.*.$currentVersion.nupkg"
```

Must pick up both the `dotnet pack` output of the 8 modules and the `nuget.exe pack` output of
the bundle — **[VERIFY]** these land in different directories by default; normalise the output
path so one glob covers all 9.

## 8. Work item: origin marker

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

## 9. Work item: SourceLink + portable PDBs

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

| # | Commit | Scope |
|---|---|---|
| 1 | `build: add KOMSA origin marker and SourceLink` | §8 + §9 |
| 2 | `build: drop net461, target netstandard2.0 only` | §4 |
| 3 | `build: centralize versioning and branding metadata` | §6 — central props, strip 8 attributes from 33 `AssemblyInfo.cs`, bump the two `*ProductData` constants |
| 4 | `build: remove strong naming` | §5 |
| 5 | `build: publish module packages as Komsa.*` | §7b |
| 6 | `build: rename bundle package to Komsa.itext` | §7a + §7c |
| 7 | `feat: use KOMSA producer line` | §3.1–§3.3 |
| 8 | `test: regenerate cmp reference files` | §3.4 — **only if** the suite requires it; kept separate because it may be a large binary diff |

All eight land in this repo on `Komsa/develop`; nothing touches the `itextsharp` fork (§11).

Commits 3 and 4 both edit all 33 `AssemblyInfo.cs` but are kept apart because they fail
differently: 3 breaks the build loudly if an attribute is missed, 4 only where
`InternalsVisibleTo` matters. Commit 2 lands early so everything after it builds one TFM
instead of two.

## 13. Verification checklist

- [ ] `dotnet build iTextCore.sln -c Release` clean, no CS0579 duplicate-attribute errors
- [ ] No `net461` or `netcoreapp2.0` left in any `.csproj` / `.props` / `.nuspec`
- [ ] Full test suite green on `net10.0` — record the baseline **before** commit 7 so
      producer-line fallout is attributable
- [ ] `Komsa.itext.nupkg` contains 11 `dll` + 11 `xml` (+ `pdb`) under `lib\netstandard2.0`
      only, and depends on `Komsa.itext.commons`
- [ ] All 9 package ids correct — especially `Komsa.itext.font-asian`, not `…font_asian`
- [ ] No `.snk` left in the tree; assemblies confirmed unsigned
- [ ] A produced PDF's `/Producer` reads `iText® Core 9.8.0.1 ©2000-2026 KOMSA GmbH` — no
      `(AGPL version)` suffix
- [ ] Assembly metadata shows `9.0.0.0` / `9.8.0.1` / `9.8.0.1` and the KOMSA origin URLs

# Releasing

GitHub Actions builds everything from pinned public inputs
([`.github/workflows/build.yml`](../.github/workflows/build.yml)). Every pull
request, push to `main` and version tag builds the driver, FSR4 runtime, SDK,
demo and showcase. The workflow checks the pinned pipeline cache,
runs the host tests and packages the build. A version tag publishes that
package as a GitHub pre-release.
Every run keeps the showcase ZIP, PKG and their SHA-256 files as a workflow artifact; a pull request's is
named by its number and commit ([pull-request builds](PULL_REQUEST_BUILDS.md)).

## What a release contains

| Asset | Contents |
| --- | --- |
| `ps5-fsr4-showcase-VERSION-PPSA99011.zip` | The [showcase app](../examples/fsr4_showcase/README.md) folder, a README, `notices/` and `SHA256SUMS` |
| `ps5-fsr4-showcase-VERSION-PPSA99011.pkg` | Installable showcase with notices |
| `ps5-fsr4-sdk-VERSION.zip` | `dist-sdk`: `libps5_fsr4.a` and its header, the driver SDK, the cache if available, the [SDK guide](FSR4_SDK.md), `notices/` and `SHA256SUMS` |
| `ps5-fsr4-VERSION-source.tar.gz` | Corresponding source of the GPL code: this repository without `comparisons/`, the Vulkan driver, ps5-agc-gears and the native app template at the built commits |
| `pipeline-cache-ps5-HASH.bin` | The PS5-generated cache bundled in the SDK and showcase, named by its SHA-256 prefix |
| `SHA256SUMS` | SHA-256 of all five assets |

`notices/` holds AMD's notice for the FSR4 material (MIT; see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md#amd-fsr4-material)), the provenance of that
material from AMD's SDK through the BC250 build to this one, BC250's own
provenance note, and the licenses of everything else in the archive
(`THIRD-PARTY.md`). `tools/package_fsr4_release.py` writes all of it, and
`make release VERSION=01.000.000` builds the same assets locally after `make sdk`.

The PKG, two ZIPs, pipeline cache and source tarball published by the workflow can be checked with
`gh attestation verify <file> -R BlackBearRevived/ps5-fsr4 --signer-workflow BlackBearRevived/ps5-fsr4/.github/workflows/build.yml`.

A release's files are the ones the workflow run for its tag built and attested;
none is attached by hand. If a release for the tag already exists (notes
written ahead, or a draft), the run adds the files it does not have yet and
leaves its title and notes as they are. A file the release already has is never
replaced or removed: the run prints a warning that it did not come from this
run and may have no attestation, and ends green.

## Inputs

[`tools/build_inputs.json`](../tools/build_inputs.json) pins what the build
downloads; `make inputs` (`tools/fetch_build_inputs.py`) fetches and verifies it
into `build/`:

- the native app template at its commit, from which the payload SDK v0.42, the
  generated `libc.prx` and the packaging tool come;
- dxil-spirv at the converter's commit;
- DXC from Microsoft's release (the pass tables read DXIL with `dxc -dumpbin`);
- the BC250 RC12 upscaler DLL and its notices from BC250's release;
- the optional pipeline cache from the `build-inputs` pre-release, when the
  pinned asset is available.

`eval "$(python3 tools/fetch_build_inputs.py --env)"` then points the builds at
them. The driver pins its own dependencies (`make driver-deps`). The workflow
runs on an Ubuntu 24.04 runner. The cache is only valid for SPIR-V that is
byte-identical to what it was made from, which needs the same glslang and
SPIRV-Tools releases: the script builds those (glslang 16.6.0, SPIRV-Tools
v2026.4) into `build/inputs/shader-tools` and puts them first on `PATH`, unless
the system's are those releases already. LLVM 21, which the payload SDK builds
with, comes from [apt.llvm.org](https://apt.llvm.org).

## The pipeline cache

The RC12 showcase ZIP and PKG both install the PS5-generated cache at
`assets/pipeline-cache.bin`. The SDK ships the same bytes at
`share/ps5fsr4/pipeline-cache-ps5.bin`. CI checks the provider, driver cache
identity and generated pass tables with `python3 tools/fetch_build_inputs.py
--check-cache`. It also checks the cache digest in the ZIP and the installed
path and size in the PKG manifest.

To refresh the cache after changing the provider, driver or shaders:

1. Build the runtime test without a cache (`tools/build_fsr4_runtime_test.py`),
   run it on the PS5 and fetch the `fsr4-rt-pipeline-cache.bin` it saves.
2. `python3 tools/fetch_build_inputs.py --pin-cache fsr4-rt-pipeline-cache.bin`
   checks that the driver saved it, updates `tools/build_inputs.json` and prints
   the `gh release upload build-inputs ...` command for the renamed file.
3. Create the `build-inputs` pre-release for the existing tag if needed.
   Upload the file, then commit the new pin. Earlier caches stay on the
   `build-inputs` release for the commits that pin them.

## Cutting a release

1. Validate the commit on a PS5: build the showcase's self-test
   (`make showcase SHOWCASE_ARGS=--selftest`), run it, and check that it ends
   with `FSR4_SHOWCASE_SELFTEST_DONE`, that every `FSR4_SHOWCASE_OUTPUT` line
   contains the expected output, and that the frames it saved look right.
   Check that `FSR4_SHOWCASE_READY cache_in` reports the packaged cache size
   and compare the first output's `setup_ms` with a launch without the cache.
2. Tag and push. Releases are numbered like PlayStation content versions,
   which is also what the console reports for the installed showcase:
   `git tag v01.000.000 && git push origin v01.000.000`.
3. The workflow builds, tests and packages the tag, then publishes the
   pre-release with the notes `tools/package_fsr4_release.py` writes (or adds
   its files to the release already written for that tag).

To try the packaging without publishing, run the workflow by hand
(Actions → Build → Run workflow) with a version: the assets are kept as a
workflow artifact for a week.

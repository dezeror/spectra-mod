#!/usr/bin/env python3
"""Applies the Spectra overlay onto a Nagram (or NekoX-style) clone.

Usage:
    python3 apply_overlay.py --repo /path/to/Nagram [--app-id 12834 --app-hash c84d9...]

Steps:
  1. Copy org.telegram.spectra sources into the app module.
  2. Install launcher icons (all densities + adaptive) and in-app logo.
  3. Rebrand: applicationId -> org.spectra.messenger, manifest labels -> Spectra.
  4. Inject APP_ID / APP_HASH (public Telegram-FOSS pair by default).
  5. Ship Spectra_Dark.attheme into res/raw for sharing.
  6. Add a "Spectra Settings" entry to NekoSettingsActivity (self-healing).
Idempotent: safe to re-run. Optional failures print WARN and never abort.
"""
import argparse
import os
import re
import shutil
import sys

OVERLAY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # spectra-mod/overlay

FOSS_APP_ID = "12834"
FOSS_APP_HASH = "c84d9229db1d6be95c067b02b126352c"

ok = []
warn = []

def step(name, good, detail=""):
    (ok if good else warn).append((name, detail))
    print(("  OK  " if good else " WARN ") + name + ((" — " + detail) if detail else ""))

def copytree(src, dst):
    os.makedirs(dst, exist_ok=True)
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        target = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(target, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(root, f), os.path.join(target, f))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--app-id", default=FOSS_APP_ID)
    ap.add_argument("--app-hash", default=FOSS_APP_HASH)
    ap.add_argument("--app-name", default="Spectra")
    ap.add_argument("--application-id", default="org.spectra.messenger")
    ap.add_argument("--abi", default="arm64-v8a",
                    help="restrict native build + splits to one ABI (pass empty string to build all)")
    ap.add_argument("--no-settings-entry", action="store_true")
    args = ap.parse_args()

    repo = os.path.abspath(args.repo)
    app = os.path.join(repo, "TMessagesProj")
    main_dir = os.path.join(app, "src", "main")
    if not os.path.isdir(main_dir):
        print(f"ERROR: {main_dir} not found — is this a Telegram/Nagram checkout?")
        sys.exit(1)
    res = os.path.join(main_dir, "res")

    print(f"Applying Spectra overlay to {repo}")

    # 1. Java sources (overlay/java contains org/telegram/spectra/... — copy to src root)
    dst = os.path.join(main_dir, "java")
    copytree(os.path.join(OVERLAY, "java"), dst)
    pkg_dir = os.path.join(dst, "org", "telegram", "spectra")
    n = sum(len(files) for _r, _d, files in os.walk(pkg_dir)) if os.path.isdir(pkg_dir) else 0
    step(f"java sources -> org/telegram/spectra ({n} files)", n >= 20)

    # 2. Icons
    icons = 0
    for entry in os.listdir(os.path.join(OVERLAY, "res")):
        s = os.path.join(OVERLAY, "res", entry)
        if not os.path.isdir(s):
            continue
        d = os.path.join(res, entry)
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(s):
            shutil.copy2(os.path.join(s, f), os.path.join(d, f))
            icons += 1
    step(f"launcher icons + adaptive layers + logo ({icons} files)", True)

    # 3. applicationId (supports both `applicationId "x"` and `defaultConfig.applicationId = "x"`)
    gradle = os.path.join(app, "build.gradle")
    if os.path.isfile(gradle):
        text = open(gradle, encoding="utf-8").read()
        new, count = re.subn(r'(applicationId\s*=?\s*)"[^"]+"', rf'\g<1>"{args.application_id}"', text)
        if count:
            open(gradle, "w", encoding="utf-8").write(new)
        step(f'applicationId -> "{args.application_id}" ({count} occurrences)', count > 0, "TMessagesProj/build.gradle")
    else:
        step("applicationId patch", False, "TMessagesProj/build.gradle not found")

    # 3b. Restrict native compilation + ABI splits to one ABI (huge CI time saver)
    if os.path.isfile(gradle) and args.abi:
        text = open(gradle, encoding="utf-8").read()
        if f'abiFilters "{args.abi}"' not in text:
            new, c = re.subn(r"(targets 'tmessages\.49')",
                             rf'\1\n                abiFilters "{args.abi}"', text, count=1)
            if c:
                open(gradle, "w", encoding="utf-8").write(new)
            step(f'abiFilters "{args.abi}" injected (native builds only for this ABI)', bool(c),
                 "TMessagesProj/build.gradle defaultConfig")
        else:
            step(f'abiFilters "{args.abi}" already present', True)

    # 4. App label: rebrand every @string key used as android:label in the manifest
    manifest = os.path.join(main_dir, "AndroidManifest.xml")
    label_keys = set()
    if os.path.isfile(manifest):
        man = open(manifest, encoding="utf-8").read()
        label_keys.update(re.findall(r'android:label="@string/(\w+)"', man))
    if label_keys:
        count = 0
        values_root = os.path.join(res, "values")
        candidates = []
        if os.path.isdir(values_root):
            candidates.append(values_root)
        for entry in os.listdir(res):
            if entry.startswith("values-") and os.path.isdir(os.path.join(res, entry)):
                candidates.append(os.path.join(res, entry))
        for vdir in candidates:
            for f in os.listdir(vdir):
                if not (f.startswith("strings") and f.endswith(".xml")):
                    continue
                path = os.path.join(vdir, f)
                text = open(path, encoding="utf-8").read()
                original = text
                for key in label_keys:
                    text, c = re.subn(rf'(<string name="{key}"[^>]*>)[^<]*(</string>)', rf'\g<1>{args.app_name}\g<2>', text)
                    count += c
                if text != original:
                    open(path, "w", encoding="utf-8").write(text)
        step(f'app labels -> "{args.app_name}" ({count} strings: {sorted(label_keys)})', count > 0)
    else:
        step("app label patch", False, "manifest label keys not found")

    # 5. APP_ID / APP_HASH in BuildVars.java
    bv = os.path.join(main_dir, "java", "org", "telegram", "messenger", "BuildVars.java")
    if os.path.isfile(bv):
        text = open(bv, encoding="utf-8").read()
        t2, c1 = re.subn(r'(APP_ID\s*=\s*)(\d+)', rf'\g<1>{args.app_id}', text)
        t2, c2 = re.subn(r'(APP_HASH\s*=\s*)"[0-9a-fA-F]{16,}"', rf'\g<1>"{args.app_hash}"', t2)
        if c1 or c2:
            open(bv, "w", encoding="utf-8").write(t2)
        step(f"APP_ID/APP_HASH -> {args.app_id} ({c1}/{c2} replacements)", True, "BuildVars.java")
    else:
        step("APP_ID patch", False, "BuildVars.java not found — inject buildConfigField manually")
    if os.path.isfile(gradle):
        text = open(gradle, encoding="utf-8").read()
        if "APP_ID" not in text and "appId" not in text.lower():
            inject = (f'    buildConfigField "int", "APP_ID", "{args.app_id}"\n'
                      f'    buildConfigField "String", "APP_HASH", "\\"{args.app_hash}\\""\n')
            new, c = re.subn(r'(defaultConfig\s*\{)', r'\1\n' + inject, text, count=1)
            if c:
                open(gradle, "w", encoding="utf-8").write(new)
            step("APP_ID/APP_HASH buildConfigField injected", bool(c), "build.gradle defaultConfig")

    # 6. Theme into res/raw
    theme_src = os.path.join(OVERLAY, "theme", "Spectra_Dark.attheme")
    if os.path.isfile(theme_src):
        raw = os.path.join(res, "raw")
        os.makedirs(raw, exist_ok=True)
        shutil.copy2(theme_src, os.path.join(raw, "spectra_dark.attheme"))
        step("Spectra_Dark.attheme -> res/raw/spectra_dark.attheme", True)

    # 7. Docs
    docs_dst = os.path.join(repo, "docs", "spectra")
    copytree(os.path.join(OVERLAY, "docs"), docs_dst)
    step("docs -> docs/spectra (HOOKS.md, FEATURES.md, TESTING.md)", True)

    # 7b. ProGuard keep rules for the Spectra overlay (release/minify builds)
    pg = os.path.join(app, "proguard-rules.pro")
    if os.path.isfile(pg):
        text = open(pg, encoding="utf-8").read()
        if "-keep class org.telegram.spectra.**" not in text:
            with open(pg, "a", encoding="utf-8") as f:
                f.write("\n# --- Spectra mod: keep the whole overlay ---\n"
                        "-keep class org.telegram.spectra.** { *; }\n"
                        "-dontwarn org.telegram.spectra.**\n")
            step("proguard-rules.pro: Spectra keep rules appended", True)
        else:
            step("proguard-rules.pro: Spectra keep rules present", True)
    else:
        step("proguard-rules.pro", False, "file not found")

    # 8. Spectra Settings entry in NekoSettingsActivity (self-healing)
    if not args.no_settings_entry:
        ns = os.path.join(main_dir, "java", "tw", "nekomimi", "nekogram", "settings", "NekoSettingsActivity.java")
        if os.path.isfile(ns):
            text = open(ns, encoding="utf-8").read()
            original = text

            # a) normalize any previous partial insert
            text = re.sub(r'spectraSettingsRow = addRow\([^)]*\);', 'spectraSettingsRow = addRow("spectra");', text)
            if "spectraSettingsRow = addRow(\"spectra\")" not in text:
                m = re.search(r'^(\s*)importSettingsRow = addRow\("importSettings"\);', text, re.M)
                if m:
                    text = text[:m.end()] + '\n' + m.group(1) + 'spectraSettingsRow = addRow("spectra");' + text[m.end():]

            # b) field declaration
            if "private int spectraSettingsRow;" not in text:
                m = re.search(r'^(\s*)private int importSettingsRow;', text, re.M)
                if m:
                    text = text[:m.end()] + "\n" + m.group(1) + "private int spectraSettingsRow;" + text[m.end():]

            # c) click handling
            if "position == spectraSettingsRow" not in text:
                m = re.search(r'(if \(position == generalRow\) \{)', text)
                if m:
                    ins = ('if (position == spectraSettingsRow) {\n'
                           '            presentFragment(new org.telegram.spectra.SpectraSettingsActivity());\n'
                           '        } else ' + m.group(1))
                    text = text[:m.start()] + ins + text[m.end():]

            # d) row text binding
            if 'position == spectraSettingsRow' in text and 'textCell.setText("Spectra Settings"' not in text:
                m = re.search(r'(if \(position == channelRow\) \{)', text)
                if m:
                    ins = ('if (position == spectraSettingsRow) {\n'
                           '                        textCell.setText("Spectra Settings", divider);\n'
                           '                    } else ' + m.group(1))
                    text = text[:m.start()] + ins + text[m.end():]

            if text != original:
                open(ns, "w", encoding="utf-8").write(text)
            # verify all four pieces
            good = all(x in text for x in (
                'private int spectraSettingsRow;',
                'spectraSettingsRow = addRow("spectra");',
                'position == spectraSettingsRow',
                'textCell.setText("Spectra Settings"'))
            step("Spectra Settings entry added to NekoSettingsActivity", good,
                 "" if good else "some insertion pieces missing — check manually")
        else:
            step("Spectra Settings entry", False, "NekoSettingsActivity.java not found")

    print("\n=== SUMMARY ===")
    for name, detail in ok:
        print(f"  OK   {name}" + (f" — {detail}" if detail else ""))
    for name, detail in warn:
        print(f"  WARN {name}" + (f" — {detail}" if detail else ""))
    print("\nNext: cd %s && NATIVE_TARGET=%s ./gradlew TMessagesProj:assembleRelease" % (repo, args.abi or ""))
    print("APK:  TMessagesProj/build/outputs/apk/ — *arm64-v8a*.apk")

if __name__ == "__main__":
    main()

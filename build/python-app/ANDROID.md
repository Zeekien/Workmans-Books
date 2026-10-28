# Work-Man's Books - Android Build & Development

`mobile_app.py` is the Android-compatible mobile entry point built with Flet.
It uses SQLite database storage and supports scheduling jobs, client management, invoice tracking, and business settings with touch-friendly controls.

## Run a Mobile Preview

```powershell
python -m pip install -r requirements.txt
flet run mobile_app.py
```

## Build a Production Release APK

To build a standalone signed release APK for **Work-Man's Books**:

```powershell
flet build apk . --module-name mobile_app --project "Work-Man's Books" --product "Work-Man's Books" --build-number 1
```

The generated APK will be placed in `build\apk`.

## Build an Android App Bundle (AAB) for Google Play

```powershell
flet build aab . --module-name mobile_app --project "Work-Man's Books" --product "Work-Man's Books" --build-number 1
```

The generated `.aab` file will be placed in `build\aab`.

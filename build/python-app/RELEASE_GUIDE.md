# Work-Man's Books - Client Release & Distribution Guide

This guide details how to build, sign, and distribute **Work-Man's Books** (`com.workmansbooks.app`) for client use or publication on the Google Play Store.

---

## 1. Release Configuration

### Package Identification
- **Application Name**: Work-Man's Books
- **Package ID**: `com.workmansbooks.app`
- **Main Entry Point**: `mobile_app.py`

---

## 2. Release Keystore & App Signing Setup

Before building a signed APK or AAB for client release:

1. **Generate a Release Keystore** (if you don't already have one):
   ```powershell
   keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias workmansbooks
   ```

2. **Configure `key.properties`**:
   Copy `key.properties.example` to `build\flutter\android\key.properties` or the project root and enter your credentials:
   ```properties
   storePassword=your_keystore_password
   keyPassword=your_key_password
   keyAlias=workmansbooks
   storeFile=C:/path/to/release.jks
   ```

   The Android Gradle plugin (`build.gradle.kts`) automatically detects `key.properties` and uses it for signing release builds.

---

## 3. Building Release Artifacts

### Option A: Standalone Signed Release APK (Direct Client Distribution)

To build a standalone APK for direct installation on Android devices:

```powershell
flet build apk . --module-name mobile_app --project "Work-Man's Books" --product "Work-Man's Books" --build-number 1
```

- **Output Location**: `build\apk\app-release.apk`
- **Client Installation**: Transfer the `.apk` file to the user's Android device and open it to install.

---

### Option B: Android App Bundle (AAB for Google Play Store)

To build an App Bundle for publication to the Google Play Console:

```powershell
flet build aab . --module-name mobile_app --project "Work-Man's Books" --product "Work-Man's Books" --build-number 1
```

- **Output Location**: `build\aab\app-release.aab`
- **Play Store Deployment**: Upload the `.aab` file in the Google Play Console under **Production** or **Testing**.

---

## 4. App Version Updates

When releasing updates to clients or the Play Store, increment the `--build-number`:

```powershell
flet build apk . --module-name mobile_app --project "Work-Man's Books" --product "Work-Man's Books" --build-number 2
```

---

## 5. Client Data & Database Management

- **Database Path**: `main.db` is saved in persistent application data storage (`FLET_APP_STORAGE_DATA`).
- **Database Backups**:
  Clients can back up their database at any time in the app by going to **Settings -> Database Management -> Export Database Backup**.
  This creates a timestamped copy (e.g. `main_backup_20260330_120000.db`) in their app data directory.

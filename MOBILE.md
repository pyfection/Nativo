# Mobile apps (Android + iOS)

The store apps are the same React app wrapped with [Capacitor](https://capacitorjs.com).
The web build (`frontend/dist`) is copied into the native projects in
`frontend/android` and `frontend/ios`; there is no separate mobile codebase.

- App id: `io.github.pyfection.nativo` (in `frontend/capacitor.config.ts`).
  **Permanent once published**, so change it before the first upload if you
  want a different one.
- The app calls the API at `VITE_API_URL` (from `frontend/.env.production`),
  like the website does.
- Offline: reads are kept in IndexedDB (`services/readCache.ts`) and writes made
  offline wait in the outbox (`services/outbox.ts`). This works the same in the
  apps and on the web. The service worker is web-only.

## One-time backend setup

Allow the app origins in the API's CORS list, next to the website:

```bash
fly secrets set BACKEND_CORS_ORIGINS='["https://nativo.pages.dev","https://localhost","capacitor://localhost"]'
```

`https://localhost` is the Android app and `capacitor://localhost` is the iOS app.
Without them the app shows "Failed to load languages".

## Everyday commands (from `frontend/`)

```bash
npm run app:sync      # build the web app and copy it into both native projects
npm run app:android   # …then open Android Studio
npm run app:ios       # …then open Xcode (macOS only)
```

Run `app:sync` after every web change. The native projects themselves only need
edits for permissions, icons or native settings.

- **Android**: needs Android Studio (or JDK 21 + Android SDK 36).
  `cd android && ./gradlew assembleDebug` builds `app/build/outputs/apk/debug/app-debug.apk`.
  CI builds the same APK on every push to `master` (Actions → "Android app" →
  artifact `nativo-debug-apk`). Install it on a phone to test.
- **iOS**: needs a Mac with Xcode. Open the project with `npm run app:ios`, pick
  your team under Signing & Capabilities, and run it on a device or simulator.
  Swift Package Manager handles dependencies, so CocoaPods isn't needed.

Icons and splash screens are generated from `frontend/assets/logo.png`:

```bash
npx @capacitor/assets generate --ios --android \
  --iconBackgroundColor '#ffffff' --iconBackgroundColorDark '#15171a' \
  --splashBackgroundColor '#F6F4EF' --splashBackgroundColorDark '#15171a'
```

## Publishing

### Accounts (one-time)

| | Google Play | Apple App Store |
|---|---|---|
| Account | Play Console, $25 once | Apple Developer Program, $99/year |
| Before release | New personal accounts must run a closed test with at least 12 testers for 14 days | TestFlight is optional |

### Signing

- **Android**: create an upload key once and keep it safe (losing it means
  contacting Google support):
  `keytool -genkey -v -keystore nativo-upload.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload`.
  Build the release bundle in Android Studio (Build → Generate Signed App Bundle)
  and upload the `.aab`. Turn on Play App Signing (the default).
- **iOS**: Xcode manages certificates. Product → Archive → Distribute App → App Store Connect.

### Required by both stores before release

- [ ] **Privacy policy URL**: `https://<your site>/privacy` (text in
      `frontend/src/content/privacy.md`). Fill in the `[…]` placeholders and have
      it checked before publishing.
- [x] **Account deletion inside the app**: user menu → Delete account
      (`/account/delete`). Contributions stay, credited to `deleted-user-…`;
      login, memberships, learning progress and API tokens are removed. Play
      also asks for a web link where people can delete their account: use
      `https://<your site>/account/delete`.
- [ ] Data safety form (Play) and App Privacy details (Apple): email, username,
      audio recordings, user content; nothing is used for tracking or ads.
- [ ] Store listing: name, short and full description, screenshots (phone; plus
      iPad if iPad stays enabled), feature graphic (Play, 1024×500).
- [ ] A reviewer account (Apple asks for login details to review apps with accounts).
- [ ] Bump `versionCode`/`versionName` (`android/app/build.gradle`) and the
      version/build in Xcode for every upload.

Apple can reject apps that are "just a website" (guideline 4.2). What helps
Nativo: it works offline, records audio with the microphone, and has a
phone-first layout. Put those in the review notes.

## Not done yet

- Push notifications (e.g. "your suggestion was approved").
- Opening email links (verify email, reset password) in the app instead of the browser.
- Keeping the login token in the phone's secure storage instead of browser storage.
- Offline audio playback.

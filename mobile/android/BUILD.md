# Android build

## 环境

- JDK 17+
- Android SDK（compileSdk/targetSdk 见 `app/build.gradle`）
- 在 `mobile/android/local.properties` 写入本机 SDK 路径，例如：

```properties
sdk.dir=C:\\Users\\you\\AppData\\Local\\Android\\Sdk
```

`local.properties`、`build/`、`.gradle/` 都是本机生成物，不提交到 Git。

## 构建 debug APK

Windows：

```bat
cd mobile\android
gradlew.bat assembleDebug
```

Linux/macOS：

```sh
cd mobile/android
./gradlew assembleDebug
```

产物：

```text
mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

发布用 APK 上传到 GitHub Release，不提交进 Git；构建目录可由源码重新生成。

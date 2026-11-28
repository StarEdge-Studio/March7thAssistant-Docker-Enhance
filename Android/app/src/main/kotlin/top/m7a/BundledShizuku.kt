package top.m7a

import android.content.Context
import android.os.Build
import android.util.AtomicFile
import java.io.File
import java.io.IOException

internal const val BUNDLED_SHIZUKU_APK = "shizuku/Shizuku.apk"
internal const val BUNDLED_SHIZUKU_COMPAT_APK = "shizuku-compat/Shizuku.apk"
private val shizukuApkLock = Any()

internal enum class BundledShizuku(val assetPath: String, val cacheName: String, val releaseUrl: String) {
    OFFICIAL(BUNDLED_SHIZUKU_APK, "Shizuku.apk", "https://github.com/RikkaApps/Shizuku/releases/latest"),
    ANDROID17(
        BUNDLED_SHIZUKU_COMPAT_APK, "Shizuku-compat.apk",
        "https://github.com/thedjchi/Shizuku/releases/tag/v13.7.0-thedjchi",
    ),
}

internal fun bundledShizukuForSdk(sdk: Int): BundledShizuku =
    if (sdk >= 37) BundledShizuku.ANDROID17 else BundledShizuku.OFFICIAL

/** 在 I/O 线程准备安装器可读的副本。权限引导和应用更新各自使用独立缓存。 */
internal fun prepareBundledShizuku(context: Context): File = synchronized(shizukuApkLock) {
    val bundled = bundledShizukuForSdk(Build.VERSION.SDK_INT)
    val directory = File(context.cacheDir, "shizuku-install")
    if (!directory.isDirectory && !directory.mkdirs()) throw IOException("Cannot create Shizuku install cache")
    val apk = File(directory, bundled.cacheName)
    val atomic = AtomicFile(apk)
    val output = atomic.startWrite()
    try {
        context.assets.open(bundled.assetPath).use { it.copyTo(output) }
        atomic.finishWrite(output)
    } catch (error: Exception) {
        atomic.failWrite(output)
        throw error
    }
    apk
}

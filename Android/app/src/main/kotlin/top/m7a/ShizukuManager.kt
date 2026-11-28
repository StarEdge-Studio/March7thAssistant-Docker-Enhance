package top.m7a

import android.content.Context
import android.content.pm.PackageManager
import java.security.MessageDigest
import java.util.Locale

internal const val SHIZUKU_MANAGER_PACKAGE = "moe.shizuku.privileged.api"
internal const val OFFICIAL_SHIZUKU_CERTIFICATE = "268b5590e868fb08bae7e0ac413564cd1ff88f5ccff74af9dbd0dc918e30db30"
internal const val THEDJCHI_SHIZUKU_CERTIFICATE = "947e81ed49d6cde4006bd64b94ab69e63f50074ce01451d1bf30acb14e591f37"

internal data class ShizukuManagerInfo(
    val packageName: String,
    val versionName: String?,
    val versionCode: Long,
    val certificates: List<String>,
)

internal fun certificateSha256(certificate: ByteArray): String =
    MessageDigest.getInstance("SHA-256").digest(certificate).joinToString("") { "%02x".format(it) }

internal fun shizukuSignerLabel(sha256: String): String = when (val digest = sha256.lowercase(Locale.ROOT)) {
    OFFICIAL_SHIZUKU_CERTIFICATE -> "官方 RikkaApps"
    THEDJCHI_SHIZUKU_CERTIFICATE -> "thedjchi"
    else -> "其他签名 ${digest.take(16)}"
}

internal fun ShizukuManagerInfo.logDescription(): String {
    val signers = certificates.joinToString("、", transform = ::shizukuSignerLabel).ifEmpty { "签名未知" }
    return "$packageName $versionName ($versionCode), $signers"
}

internal fun Context.readShizukuManager(packageName: String): ShizukuManagerInfo? {
    // 签名读取失败时仍保留已安装包的版本，不能阻碍服务启动。
    val info = try {
        packageManager.getPackageInfo(packageName, PackageManager.GET_SIGNING_CERTIFICATES)
    } catch (_: PackageManager.NameNotFoundException) {
        return null
    } catch (_: Exception) {
        runCatching { packageManager.getPackageInfo(packageName, 0) }.getOrNull() ?: return null
    }
    val certificates = runCatching {
        info.signingInfo?.apkContentsSigners?.map { certificateSha256(it.toByteArray()) }.orEmpty()
    }.getOrDefault(emptyList())
    return ShizukuManagerInfo(packageName, info.versionName, info.longVersionCode, certificates)
}

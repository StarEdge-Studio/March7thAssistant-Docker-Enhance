package top.m7a

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test
import java.io.File
import java.security.MessageDigest
import java.util.HexFormat

class BundledShizukuTest {
    @Test
    fun bundledAssetMatchesTheOfficialRelease() {
        assertAsset(BundledShizuku.OFFICIAL, "6e273ab0e991c4e79bc8b1bbb9b9dd739ccac1a8712a541a214078886b7b790f")
    }

    @Test
    fun bundledCompatAssetMatchesTheRelease() {
        assertAsset(BundledShizuku.ANDROID17, "6ea6dee65d5ddc626b6b75b2c2f67f8cc547fa47d7b437e6892639c37eaffe43")
    }

    @Test
    fun android17SelectsASeparateAssetAndCache() {
        assertEquals(BundledShizuku.OFFICIAL, bundledShizukuForSdk(36))
        for (sdk in listOf(37, 38)) assertEquals(BundledShizuku.ANDROID17, bundledShizukuForSdk(sdk))
        assertNotEquals(BundledShizuku.OFFICIAL.assetPath, BundledShizuku.ANDROID17.assetPath)
        assertNotEquals(BundledShizuku.OFFICIAL.cacheName, BundledShizuku.ANDROID17.cacheName)
    }

    private fun assertAsset(bundled: BundledShizuku, expected: String) {
        val apk = File("src/main/assets", bundled.assetPath)
        val source = File(apk.parentFile, "SOURCE.txt").readText()
        val documented = Regex("APK SHA-256\\s+([0-9a-f]{64})").find(source)!!.groupValues[1]
        assertEquals(expected, documented)
        assertEquals(
            documented,
            HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(apk.readBytes())),
        )
    }
}

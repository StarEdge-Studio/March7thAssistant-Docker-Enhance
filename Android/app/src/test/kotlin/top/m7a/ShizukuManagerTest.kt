package top.m7a

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ShizukuManagerTest {
    @Test
    fun recognizesReleaseCertificatesInsteadOfVersionNames() {
        assertEquals("官方 RikkaApps", shizukuSignerLabel(OFFICIAL_SHIZUKU_CERTIFICATE))
        assertEquals("thedjchi", shizukuSignerLabel(THEDJCHI_SHIZUKU_CERTIFICATE.uppercase()))
        assertEquals("其他签名 0123456789abcdef", shizukuSignerLabel("0123456789abcdef" + "0".repeat(48)))
    }

    @Test
    fun fingerprintsCertificateBytes() {
        assertEquals(
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            certificateSha256("abc".toByteArray()),
        )
    }

    @Test
    fun logsEveryCurrentSignerAlongsideThePackageVersion() {
        val text = ShizukuManagerInfo(
            SHIZUKU_MANAGER_PACKAGE, "13.7.0-thedjchi", 1361,
            listOf(THEDJCHI_SHIZUKU_CERTIFICATE, "0".repeat(64)),
        ).logDescription()
        assertTrue(text.contains("13.7.0-thedjchi (1361)"))
        assertTrue(text.contains("thedjchi、其他签名 0000000000000000"))
    }

    @Test
    fun missingSigningInfoKeepsTheVersionAndReportsUnknown() {
        assertEquals(
            "$SHIZUKU_MANAGER_PACKAGE 13.6.0 (1086), 签名未知",
            ShizukuManagerInfo(SHIZUKU_MANAGER_PACKAGE, "13.6.0", 1086, emptyList()).logDescription(),
        )
    }
}

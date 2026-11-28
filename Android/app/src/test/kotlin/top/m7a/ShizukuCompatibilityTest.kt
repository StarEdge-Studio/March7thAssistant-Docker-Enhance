package top.m7a

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ShizukuCompatibilityTest {
    @Test
    fun warnsOnlyForAnUnavailableOldOfficialManagerOnAndroid17() {
        for (sdk in listOf(36, 37, 38)) {
            for (certificate in listOf(OFFICIAL_SHIZUKU_CERTIFICATE, THEDJCHI_SHIZUKU_CERTIFICATE, "0".repeat(64))) {
                for (version in listOf(1085L, 1086L, 1087L, 1361L)) {
                    for (permission in PermissionState.entries) {
                        val manager = ShizukuManagerInfo(SHIZUKU_MANAGER_PACKAGE, "13.6.0", version, listOf(certificate))
                        assertEquals(
                            "sdk=$sdk, certificate=$certificate, version=$version, permission=$permission",
                            sdk >= 37 && certificate == OFFICIAL_SHIZUKU_CERTIFICATE && version <= 1086 && permission != PermissionState.READY,
                            needsAndroid17ShizukuWarning(sdk, manager, permission),
                        )
                    }
                }
            }
        }
    }

    @Test
    fun unknownSignaturesAndOtherManagersDoNotTriggerMigrationAdvice() {
        val official = ShizukuManagerInfo(SHIZUKU_MANAGER_PACKAGE, "13.6.0", 1086, listOf(OFFICIAL_SHIZUKU_CERTIFICATE))
        for (manager in listOf(
            null,
            official.copy(packageName = "roro.stellar.manager"),
            official.copy(certificates = emptyList()),
            official.copy(certificates = listOf(OFFICIAL_SHIZUKU_CERTIFICATE, THEDJCHI_SHIZUKU_CERTIFICATE)),
        )) {
            assertFalse(needsAndroid17ShizukuWarning(37, manager, PermissionState.NOT_RUNNING))
        }
    }
}

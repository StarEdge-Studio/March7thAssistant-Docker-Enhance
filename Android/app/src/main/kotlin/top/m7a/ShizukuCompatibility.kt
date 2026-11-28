package top.m7a

internal fun needsAndroid17ShizukuWarning(sdk: Int, manager: ShizukuManagerInfo?, permission: PermissionState): Boolean =
    sdk >= 37 && permission != PermissionState.READY && manager != null &&
        manager.packageName == SHIZUKU_MANAGER_PACKAGE && manager.versionCode <= 1086 &&
        manager.certificates.isNotEmpty() && manager.certificates.all { it.equals(OFFICIAL_SHIZUKU_CERTIFICATE, ignoreCase = true) }

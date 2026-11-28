package top.m7a

import android.app.ActivityManager
import android.content.Context
import android.os.Build
import java.time.Instant

internal fun processExitDescription(reason: Int, description: String?, timestamp: Long, pss: Long, rss: Long): String {
    val name = when (reason) {
        0 -> "未知"
        1 -> "自行退出"
        2 -> "系统信号"
        3 -> "系统内存不足"
        4 -> "应用崩溃"
        5 -> "原生代码崩溃"
        6 -> "应用无响应"
        7 -> "初始化失败"
        8 -> "权限变更"
        9 -> "资源使用过量"
        10 -> "用户请求"
        11 -> "用户停止"
        12 -> "依赖进程退出"
        13 -> "其他"
        14 -> "进程冻结"
        15 -> "安装包状态变更"
        16 -> "应用更新"
        else -> "未知"
    }
    val detail = description?.replace('\n', ' ')?.replace('\r', ' ')?.takeIf { it.isNotBlank() } ?: "无"
    return "上次退出：原因=$name($reason)，描述=$detail，时间=${Instant.ofEpochMilli(timestamp)}，pss=$pss KB，rss=$rss KB"
}

internal fun Context.lastProcessExitDescription(): String {
    if (Build.VERSION.SDK_INT < 30) return "上次退出：当前系统不支持查询"
    return runCatching {
        val manager = getSystemService(ActivityManager::class.java)
        val info = manager.getHistoricalProcessExitReasons(packageName, 0, 1).firstOrNull()
        if (info == null) "上次退出：暂无记录"
        else processExitDescription(info.reason, info.description, info.timestamp, info.pss, info.rss)
    }.getOrElse { "上次退出：读取失败（${it.javaClass.simpleName}）" }
}

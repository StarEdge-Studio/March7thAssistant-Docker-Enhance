package top.m7a

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class ProcessExitDiagnosticsTest {
    @Test
    fun preservesTheMemoryLimiterMarkerAndSystemMeasurements() {
        assertEquals(
            "上次退出：原因=其他(13)，描述=MemoryLimiter:AnonSwap limit exceeded，时间=1970-01-01T00:00:01Z，pss=123 KB，rss=456 KB",
            processExitDescription(13, "MemoryLimiter:AnonSwap limit exceeded", 1000, 123, 456),
        )
    }

    @Test
    fun unknownReasonsAndUnavailableMeasurementsRemainVisible() {
        assertEquals(
            "上次退出：原因=未知(99)，描述=无，时间=1970-01-01T00:00:00Z，pss=0 KB，rss=0 KB",
            processExitDescription(99, null, 0, 0, 0),
        )
    }

    @Test
    fun writesDescriptionsAsOneLogLine() {
        val text = processExitDescription(4, "crash\r\nmessage", 0, 0, 0)
        assertFalse(text.contains('\n'))
        assertFalse(text.contains('\r'))
    }
}

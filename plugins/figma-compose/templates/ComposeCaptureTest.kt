package __FIXTURE_PACKAGE__

import android.content.res.Configuration
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Text
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.SemanticsNode
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.semantics.SemanticsProperties
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.v2.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.unit.dp
import com.github.takahirom.roborazzi.captureRoboImage
import __FIXTURE_PACKAGE__.core.components.GraphicFixture
import __FIXTURE_PACKAGE__.core.components.GraphicNode
import __FIXTURE_PACKAGE__.core.theme.AppTheme
import __FIXTURE_PACKAGE__.core.theme.AppThemeIdentity
import __FIXTURE_PACKAGE__.core.theme.LocalAppTokens
import java.io.File
import java.security.MessageDigest
import javax.imageio.ImageIO
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assume.assumeTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [36], qualifiers = "en-rUS-ldltr-w160dp-h160dp-notnight-mdpi")
class ComposeCaptureTest {
    @get:Rule val compose = createComposeRule()

    @Test fun home() = capture(GraphicNode.Home)
    @Test fun button() = capture(GraphicNode.Button)
    @Test fun card() = capture(GraphicNode.Card)
    @Test @Config(qualifiers = "en-rUS-ldrtl-w160dp-h160dp-night-mdpi")
    fun review() = capture(GraphicNode.Review)
    @Test @Config(qualifiers = "en-rUS-ldrtl-w160dp-h160dp-night-mdpi")
    fun badge() = capture(GraphicNode.Badge)

    @Test @Config(qualifiers = "en-rUS-ldltr-w240dp-h160dp-notnight-mdpi")
    fun wideHome() = capture(GraphicNode.Home, width = 240)
    @Test fun scaledHome() = capture(GraphicNode.Home, scale = 1.5f)
    @Test fun robotoText() = capture(GraphicNode.Home, text = true)
    @Test @Config(qualifiers = "en-rUS-ldrtl-w240dp-h160dp-night-mdpi")
    fun rtlScaledRobotoText() = capture(GraphicNode.Review, width = 240, scale = 1.5f, text = true)

    private fun hasText(node: SemanticsNode): Boolean =
        node.config.contains(SemanticsProperties.Text) || node.config.contains(SemanticsProperties.EditableText) || node.children.any(::hasText)

    private fun capture(node: GraphicNode, width: Int = 160, scale: Float = 1f, text: Boolean = false) {
        assumeTrue("Candidate recording must be explicitly enabled", System.getProperty("roborazzi.test.record") == "true")
        RuntimeEnvironment.getApplication().resources.configuration.fontScale = scale
        compose.mainClock.autoAdvance = false
        val dark = node == GraphicNode.Review || node == GraphicNode.Badge
        var observed = JSONObject()
        compose.setContent {
            val configuration = LocalConfiguration.current
            val direction = if (configuration.layoutDirection == 1) LayoutDirection.Rtl else LayoutDirection.Ltr
            CompositionLocalProvider(LocalLayoutDirection provides direction) {
                val density = LocalDensity.current
                val layoutDirection = LocalLayoutDirection.current
                SideEffect {
                    observed = JSONObject().put("density", density.density).put("fontScale", density.fontScale)
                        .put("locale", configuration.locales[0].toLanguageTag())
                        .put("direction", if (layoutDirection == LayoutDirection.Rtl) "rtl" else "ltr")
                        .put("theme", if (configuration.uiMode and Configuration.UI_MODE_NIGHT_MASK == Configuration.UI_MODE_NIGHT_YES) "dark" else "light")
                }
                AppTheme(dark = dark) {
                    val tokens = LocalAppTokens.current
                    Box(Modifier.size(width.dp, 160.dp).background(tokens.colorBackground).testTag("capture-frame")) {
                        if (text) Text("Roboto text", style = tokens.typeBody, color = tokens.colorPrimary)
                        else GraphicFixture(node)
                    }
                }
            }
        }
        compose.mainClock.advanceTimeByFrame()
        compose.waitForIdle()
        val target = compose.onNodeWithTag("capture-frame").assertIsDisplayed()
        val semantics = target.fetchSemanticsNode()
        val containsText = hasText(semantics)
        assertEquals(text, containsText)
        val bounds = semantics.boundsInRoot
        assertEquals(width.toFloat(), bounds.width, 0f)
        assertEquals(160f, bounds.height, 0f)
        val metrics = RuntimeEnvironment.getApplication().resources.displayMetrics
        assertEquals(metrics.density, observed.getDouble("density").toFloat(), 0f)
        assertEquals(if (dark) "dark" else "light", observed.getString("theme"))
        assertEquals(if (dark) "rtl" else "ltr", observed.getString("direction"))
        val variant = node.name.lowercase() + (if (text) "-text" else "") + (if (width != 160) "-w$width" else "") + (if (scale != 1f) "-fs150" else "")
        val folder = File("build/figma-candidates/$variant").apply { mkdirs() }
        val image = File(folder, "actual.png")
        target.captureRoboImage(image.absolutePath)
        val png = ImageIO.read(image)
        assertEquals(true, png.colorModel.colorSpace.isCS_sRGB)
        if (text) {
            val repeat = File(folder, "repeat.png")
            compose.mainClock.advanceTimeByFrame()
            compose.waitForIdle()
            target.captureRoboImage(repeat.absolutePath)
            assertEquals(image.readBytes().toList(), repeat.readBytes().toList())
        }
        val fonts = JSONObject()
        if (text) {
            val bytes = RuntimeEnvironment.getApplication().resources.openRawResource(R.font.roboto_regular).use { it.readBytes() }
            fonts.put("roboto_regular.ttf", MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) })
        }
        val density = observed.getDouble("density")
        observed.put("schemaVersion", 1)
            .put("nodeId", "synthetic:${if (text) "text" else if (node == GraphicNode.Home || node == GraphicNode.Review) "screen" else "component"}:$variant")
            .put("sourceRevision", "synthetic-v1")
            .put("pixelSize", JSONArray(listOf(png.width, png.height)))
            .put("logicalSize", JSONArray(listOf(bounds.width / density, bounds.height / density)))
            .put("targetBounds", JSONArray(listOf(bounds.left, bounds.top, bounds.right, bounds.bottom)))
            .put("crop", JSONArray(listOf(0, 0, png.width, png.height)))
            .put("insets", JSONArray(listOf(0, 0, 0, 0)))
            .put("containsText", containsText).put("usedFontHashes", fonts)
            .put("animation", "settled").put("clockAutoAdvance", compose.mainClock.autoAdvance)
            .put("colorSpace", "srgb").put("platform", "android").put("renderer", "robolectric-native")
            .put("imageHash", MessageDigest.getInstance("SHA-256").digest(image.readBytes()).joinToString("") { "%02x".format(it) })
            .put("themeIdentity", JSONObject().put("tokenHash", AppThemeIdentity.tokenHash)
                .put("manifestHash", AppThemeIdentity.manifestHash).put("configHash", AppThemeIdentity.configHash))
            .put("versions", JSONObject().put("sdk", android.os.Build.VERSION.SDK_INT.toString())
                .put("roborazzi", BuildConfig.ROBORAZZI_VERSION).put("robolectric", BuildConfig.ROBOLECTRIC_VERSION))
        assertEquals(2, observed.getJSONArray("pixelSize").length())
        assertEquals(4, observed.getJSONArray("targetBounds").length())
        File(folder, "capture-receipt.json").writeText(observed.toString(2) + "\n")
    }
}



package dev.figma.fixture

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertWidthIsEqualTo
import androidx.compose.ui.test.assertHeightIsEqualTo
import androidx.compose.ui.unit.dp
import androidx.compose.ui.test.onNodeWithTag
import dev.figma.fixture.core.components.GraphicFixture
import dev.figma.fixture.core.components.GraphicNode
import dev.figma.fixture.core.theme.AppTheme
import dev.figma.fixture.presentation.FixtureRoute
import dev.figma.fixture.presentation.FixtureViewModel
import dev.figma.fixture.presentation.FixtureScreenId
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [36])
class FixtureTest {
    @get:Rule val compose = createComposeRule()
    @Test fun graphicSceneHasStableCaptureTarget() {
        compose.setContent { AppTheme(dark = false) { GraphicFixture(GraphicNode.Home) } }
        compose.onNodeWithTag("synthetic-graphic-frame").assertIsDisplayed()
            .assertWidthIsEqualTo(160.dp).assertHeightIsEqualTo(160.dp)
    }
    @Test fun continueSelectsReview() {
        val model = FixtureViewModel()
        compose.setContent { AppTheme(dark = false) { FixtureRoute(model) } }
        compose.onNodeWithText("Continue").performClick()
        compose.onNodeWithText("Review").assertIsDisplayed()
        assertEquals(FixtureScreenId.Review, model.state.value.screen)
    }
}

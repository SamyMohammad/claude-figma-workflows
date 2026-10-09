package dev.figma.fixture

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import dev.figma.fixture.core.theme.AppTheme
import dev.figma.fixture.presentation.FixtureRoute

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { AppTheme(dark = false) { FixtureRoute() } }
    }
}

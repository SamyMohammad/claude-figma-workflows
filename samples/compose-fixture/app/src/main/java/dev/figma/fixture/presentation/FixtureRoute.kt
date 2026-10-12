package dev.figma.fixture.presentation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun FixtureRoute(model: FixtureViewModel = viewModel()) {
    val state by model.state.collectAsStateWithLifecycle()
    FixtureScreen(state = state, onContinue = { model.select(FixtureScreenId.Review) },
        onBack = { model.select(FixtureScreenId.Home) })
}

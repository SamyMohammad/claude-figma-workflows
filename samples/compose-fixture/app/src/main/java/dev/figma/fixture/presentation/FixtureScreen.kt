package dev.figma.fixture.presentation

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import dev.figma.fixture.core.components.ActionButton
import dev.figma.fixture.core.components.ActionButtonState
import dev.figma.fixture.core.components.ContentCard
import dev.figma.fixture.core.components.ContentCardState
import dev.figma.fixture.core.components.StatusBadge
import dev.figma.fixture.core.components.StatusBadgeState
import dev.figma.fixture.core.theme.LocalAppTokens

@Composable
fun FixtureScreen(state: FixtureUiState, onContinue: () -> Unit, onBack: () -> Unit) {
    val tokens = LocalAppTokens.current
    Column(modifier = Modifier.fillMaxSize().background(tokens.colorBackground).padding(tokens.spaceSmall),
        verticalArrangement = Arrangement.spacedBy(tokens.spaceSmall)) {
        Text(if (state.screen == FixtureScreenId.Home) "Home" else "Review",
            style = tokens.typeBody, color = tokens.colorPrimary)
        ContentCard(ContentCardState("Synthetic content"))
        StatusBadge(StatusBadgeState.Ready)
        if (state.screen == FixtureScreenId.Home) ActionButton(ActionButtonState("Continue"), onContinue)
        else ActionButton(ActionButtonState("Back"), onBack)
    }
}

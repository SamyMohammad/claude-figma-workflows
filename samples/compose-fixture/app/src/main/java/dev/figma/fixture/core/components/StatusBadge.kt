package dev.figma.fixture.core.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import dev.figma.fixture.core.theme.LocalAppTokens

enum class StatusBadgeState { Ready }

@Composable
fun StatusBadge(state: StatusBadgeState, modifier: Modifier = Modifier) {
    val tokens = LocalAppTokens.current
    Box(modifier.background(tokens.colorPrimary, RoundedCornerShape(tokens.shapeRadius)).padding(tokens.spaceSmall)) {
        Text(when (state) { StatusBadgeState.Ready -> "Ready" }, style = tokens.typeBody, color = tokens.colorOnPrimary)
    }
}

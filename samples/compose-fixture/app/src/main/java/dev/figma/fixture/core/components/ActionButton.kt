package dev.figma.fixture.core.components

import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.foundation.shape.RoundedCornerShape
import dev.figma.fixture.core.theme.LocalAppTokens

data class ActionButtonState(val label: String, val enabled: Boolean = true)

@Composable
fun ActionButton(state: ActionButtonState, onClick: () -> Unit, modifier: Modifier = Modifier) {
    val tokens = LocalAppTokens.current
    Button(onClick = onClick, enabled = state.enabled, modifier = modifier.height(tokens.controlHeight),
        shape = RoundedCornerShape(tokens.shapeRadius),
        colors = ButtonDefaults.buttonColors(containerColor = tokens.colorPrimary, contentColor = tokens.colorOnPrimary)) {
        Text(state.label, style = tokens.typeBody)
    }
}
